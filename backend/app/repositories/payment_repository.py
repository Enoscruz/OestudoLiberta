"""Acesso a dados de pagamentos."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import Gateway, PaymentStatus
from app.models.commerce import Payment


def get_by_external_id(
    db: Session, *, gateway: Gateway, external_payment_id: str
) -> Payment | None:
    """Busca um pagamento pelo identificador dele no gateway."""
    stmt = select(Payment).where(
        Payment.gateway == gateway,
        Payment.external_payment_id == external_payment_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def create(
    db: Session,
    *,
    purchase_id: int,
    external_payment_id: str | None,
    amount: Decimal,
    status: PaymentStatus,
    paid_at: datetime | None,
) -> Payment:
    """Insere um novo pagamento vinculado a uma compra."""
    payment = Payment(
        purchase_id=purchase_id,
        gateway=Gateway.MERCADO_PAGO,
        external_payment_id=external_payment_id,
        amount=amount,
        status=status,
        paid_at=paid_at,
    )
    db.add(payment)
    return payment
