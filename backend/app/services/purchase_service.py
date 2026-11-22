"""Regras de negócio de compras e do checkout.

O acesso a um curso nunca é liberado pelo frontend: quem libera é o webhook
validado do gateway (ver ``payment_service``). Aqui apenas criamos a compra e o
endereço de pagamento — ou liberamos na hora, no caso de curso gratuito.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import CourseStatus, PaymentStatus, PurchaseStatus
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    UpstreamError,
)
from app.integrations import mercado_pago
from app.models.content import Course
from app.models.user import User
from app.repositories import (
    audit_repository,
    course_repository,
    enrollment_repository,
    payment_repository,
    purchase_repository,
)
from app.schemas.purchase import CheckoutCreate, CheckoutRead, PurchaseRead

_ENTITY = "purchases"

_RETURN_STATUSES = ("success", "pending", "failure")


def _back_urls(purchase_id: int) -> dict[str, str]:
    """Endereços para os quais o Mercado Pago devolve o aluno após o checkout."""
    base = get_settings().frontend_base_url.rstrip("/")
    return {
        status: f"{base}/compras/retorno?status={status}&purchase_id={purchase_id}"
        for status in _RETURN_STATUSES
    }


def create_checkout(db: Session, user: User, data: CheckoutCreate) -> CheckoutRead:
    """Inicia a compra de um curso.

    Cursos gratuitos liberam o acesso imediatamente; os demais geram uma
    preferência de pagamento no Mercado Pago e devolvem o endereço de checkout.
    """
    course = course_repository.get(db, data.course_id)
    if course is None or course.status != CourseStatus.PUBLISHED:
        raise NotFoundError("Curso não encontrado.")

    if enrollment_repository.get_active(db, user.id, course.id) is not None:
        raise ConflictError("Você já tem acesso a este curso.")

    if course.price <= 0:
        return _grant_free_access(db, user, course)

    purchase = purchase_repository.create(
        db,
        user_id=user.id,
        course_id=course.id,
        total_amount=course.price,
        status=PurchaseStatus.PENDING,
    )
    db.flush()

    try:
        preference = mercado_pago.create_preference(
            purchase_id=purchase.id,
            course_id=course.id,
            title=course.title,
            amount=course.price,
            description=course.description,
            payer_email=user.email,
            back_urls=_back_urls(purchase.id),
            notification_url=get_settings().mercado_pago_notification_url,
        )
    except mercado_pago.MercadoPagoNotConfiguredError as exc:
        raise ServiceUnavailableError(
            "Pagamentos indisponíveis: Mercado Pago não configurado."
        ) from exc
    except mercado_pago.MercadoPagoError as exc:
        raise UpstreamError("Não foi possível iniciar o pagamento agora.") from exc

    audit_repository.record(
        db,
        user_id=user.id,
        action="purchase.checkout_created",
        entity=_ENTITY,
        entity_id=purchase.id,
    )
    db.commit()

    return CheckoutRead(
        purchase_id=purchase.id,
        status=purchase.status,
        amount=purchase.total_amount,
        init_point=preference.init_point,
        requires_payment=True,
    )


def _grant_free_access(db: Session, user: User, course: Course) -> CheckoutRead:
    """Libera na hora o acesso a um curso sem custo."""
    purchase = purchase_repository.create(
        db,
        user_id=user.id,
        course_id=course.id,
        total_amount=Decimal("0.00"),
        status=PurchaseStatus.PAID,
    )
    db.flush()
    payment_repository.create(
        db,
        purchase_id=purchase.id,
        external_payment_id=None,
        amount=Decimal("0.00"),
        status=PaymentStatus.APPROVED,
        paid_at=datetime.now(UTC),
    )
    enrollment_repository.create(
        db, user_id=user.id, course_id=course.id, purchase_id=purchase.id
    )
    audit_repository.record(
        db,
        user_id=user.id,
        action="purchase.free_enrollment",
        entity=_ENTITY,
        entity_id=purchase.id,
    )
    db.commit()

    return CheckoutRead(
        purchase_id=purchase.id,
        status=purchase.status,
        amount=purchase.total_amount,
        init_point=None,
        requires_payment=False,
    )


def list_my_purchases(db: Session, user: User) -> list[PurchaseRead]:
    """Lista as compras do aluno, da mais recente para a mais antiga."""
    return [
        PurchaseRead(
            id=purchase.id,
            course_id=purchase.course_id,
            course_title=purchase.course.title if purchase.course else None,
            total_amount=purchase.total_amount,
            status=purchase.status,
            created_at=purchase.created_at,
        )
        for purchase in purchase_repository.list_by_user(db, user.id)
    ]
