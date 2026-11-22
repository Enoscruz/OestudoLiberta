"""Processamento das notificações de pagamento do Mercado Pago.

Duas garantias sustentam este serviço:

1. **Idempotência** — o evento é registrado em ``webhook_events`` (único por
   gateway + id externo) antes de qualquer efeito; reenvios são ignorados.
2. **Validação na origem** — o pagamento é sempre reconsultado na API do
   Mercado Pago e o valor pago é comparado ao valor da compra. O acesso só é
   liberado quando os dois conferem.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import (
    EnrollmentStatus,
    Gateway,
    PaymentStatus,
    PurchaseStatus,
    WebhookStatus,
)
from app.core.exceptions import ForbiddenError, ServiceUnavailableError, UpstreamError
from app.integrations import mercado_pago
from app.integrations.mercado_pago import PaymentInfo
from app.models.commerce import Purchase
from app.repositories import (
    audit_repository,
    enrollment_repository,
    payment_repository,
    purchase_repository,
    webhook_repository,
)

_ENTITY = "purchases"

# Tradução do status do Mercado Pago para o status do nosso domínio.
_PAYMENT_STATUS = {
    "approved": PaymentStatus.APPROVED,
    "pending": PaymentStatus.PENDING,
    "in_process": PaymentStatus.IN_PROCESS,
    "authorized": PaymentStatus.IN_PROCESS,
    "rejected": PaymentStatus.REJECTED,
    "cancelled": PaymentStatus.REJECTED,
    "refunded": PaymentStatus.REFUNDED,
    "charged_back": PaymentStatus.REFUNDED,
}

_PURCHASE_STATUS = {
    PaymentStatus.APPROVED: PurchaseStatus.PAID,
    PaymentStatus.PENDING: PurchaseStatus.PENDING,
    PaymentStatus.IN_PROCESS: PurchaseStatus.PENDING,
    PaymentStatus.REJECTED: PurchaseStatus.FAILED,
    PaymentStatus.REFUNDED: PurchaseStatus.REFUNDED,
}

_WEBHOOK_STATUS = {
    "processed": WebhookStatus.PROCESSED,
    "ignored": WebhookStatus.IGNORED,
    "mismatch": WebhookStatus.FAILED,
}


def handle_notification(
    db: Session,
    *,
    event_id: str,
    event_type: str,
    payment_id: str,
    x_signature: str | None,
    x_request_id: str | None,
) -> str:
    """Processa uma notificação do Mercado Pago e devolve o desfecho."""
    secret = get_settings().mercado_pago_webhook_secret
    if secret and not mercado_pago.verify_webhook_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=payment_id,
        secret=secret,
    ):
        raise ForbiddenError("Assinatura do webhook inválida.")

    event = webhook_repository.register(
        db,
        gateway=Gateway.MERCADO_PAGO,
        external_event_id=event_id,
        event_type=event_type,
    )
    if event is None:
        return "duplicate"

    try:
        payment = mercado_pago.get_payment(payment_id)
    except mercado_pago.MercadoPagoNotConfiguredError as exc:
        raise ServiceUnavailableError(
            "Pagamentos indisponíveis: Mercado Pago não configurado."
        ) from exc
    except mercado_pago.MercadoPagoError as exc:
        raise UpstreamError(
            "Não foi possível consultar o pagamento no Mercado Pago."
        ) from exc

    purchase = _resolve_purchase(db, payment)
    if purchase is None:
        outcome = "ignored"
    else:
        outcome = _apply_payment(db, purchase, payment)

    webhook_repository.mark_processed(db, event, status=_WEBHOOK_STATUS[outcome])
    db.commit()
    return outcome


def _resolve_purchase(db: Session, payment: PaymentInfo) -> Purchase | None:
    """Reencontra a compra local pelo ``external_reference`` gravado na origem."""
    reference = payment.external_reference
    if not reference or not reference.isdigit():
        return None
    return purchase_repository.get(db, int(reference))


def _apply_payment(db: Session, purchase: Purchase, payment: PaymentInfo) -> str:
    """Aplica o pagamento à compra e libera (ou revoga) o acesso."""
    payment_status = _PAYMENT_STATUS.get(payment.status)
    if payment_status is None:
        return "ignored"

    if (
        payment_status is PaymentStatus.APPROVED
        and payment.amount != purchase.total_amount
    ):
        # Valor divergente: nada é liberado e o caso fica registrado.
        audit_repository.record(
            db,
            user_id=None,
            action="payment.amount_mismatch",
            entity=_ENTITY,
            entity_id=purchase.id,
        )
        return "mismatch"

    _upsert_payment(db, purchase, payment, payment_status)
    purchase.status = _PURCHASE_STATUS[payment_status]

    if purchase.status is PurchaseStatus.PAID:
        _grant_access(db, purchase)
    elif purchase.status is PurchaseStatus.REFUNDED:
        _revoke_access(db, purchase)

    audit_repository.record(
        db,
        user_id=None,
        action=f"payment.{payment.status}",
        entity=_ENTITY,
        entity_id=purchase.id,
    )
    return "processed"


def _upsert_payment(
    db: Session, purchase: Purchase, payment: PaymentInfo, payment_status: PaymentStatus
) -> None:
    """Cria ou atualiza o pagamento, sem duplicar o mesmo id do gateway."""
    paid_at = datetime.now(UTC) if payment_status is PaymentStatus.APPROVED else None
    existing = payment_repository.get_by_external_id(
        db, gateway=Gateway.MERCADO_PAGO, external_payment_id=payment.id
    )
    if existing is None:
        payment_repository.create(
            db,
            purchase_id=purchase.id,
            external_payment_id=payment.id,
            amount=payment.amount,
            status=payment_status,
            paid_at=paid_at,
        )
        return

    existing.status = payment_status
    existing.amount = payment.amount
    existing.paid_at = paid_at


def _grant_access(db: Session, purchase: Purchase) -> None:
    """Libera (ou reativa) o acesso do aluno ao curso adquirido."""
    enrollment = enrollment_repository.get_any(
        db, purchase.user_id, purchase.course_id
    )
    if enrollment is None:
        enrollment_repository.create(
            db,
            user_id=purchase.user_id,
            course_id=purchase.course_id,
            purchase_id=purchase.id,
        )
        return

    enrollment.status = EnrollmentStatus.ACTIVE
    enrollment.purchase_id = purchase.id


def _revoke_access(db: Session, purchase: Purchase) -> None:
    """Revoga o acesso quando o pagamento é estornado ou contestado."""
    enrollment = enrollment_repository.get_any(
        db, purchase.user_id, purchase.course_id
    )
    if enrollment is not None:
        enrollment.status = EnrollmentStatus.REVOKED
