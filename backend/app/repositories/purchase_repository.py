"""Acesso a dados de compras."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import PurchaseStatus
from app.models.commerce import Purchase


def get(db: Session, purchase_id: int) -> Purchase | None:
    """Busca uma compra pela chave primária."""
    return db.get(Purchase, purchase_id)


def list_by_user(db: Session, user_id: int) -> list[Purchase]:
    """Lista as compras de um aluno, da mais recente para a mais antiga.

    O desempate por ``id`` garante ordem determinística quando duas compras são
    criadas no mesmo instante (timestamps idênticos dentro da mesma transação).
    """
    stmt = (
        select(Purchase)
        .options(joinedload(Purchase.course))
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.created_at.desc(), Purchase.id.desc())
    )
    return list(db.execute(stmt).unique().scalars())


def create(
    db: Session,
    *,
    user_id: int,
    course_id: int,
    total_amount: Decimal,
    status: PurchaseStatus,
) -> Purchase:
    """Insere uma nova compra."""
    purchase = Purchase(
        user_id=user_id,
        course_id=course_id,
        total_amount=total_amount,
        status=status,
    )
    db.add(purchase)
    return purchase
