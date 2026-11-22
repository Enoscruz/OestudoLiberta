"""Contratos Pydantic de compras e do checkout."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.enums import PurchaseStatus


class CheckoutCreate(BaseModel):
    """Pedido de compra de um curso."""

    course_id: int


class CheckoutRead(BaseModel):
    """Resultado do pedido de compra.

    Quando ``requires_payment`` é ``False`` (curso gratuito) o acesso já foi
    liberado e ``init_point`` vem nulo — não há checkout a abrir.
    """

    purchase_id: int
    status: PurchaseStatus
    amount: Decimal
    init_point: str | None
    requires_payment: bool


class PurchaseRead(BaseModel):
    """Compra do aluno, com o curso correspondente."""

    id: int
    course_id: int
    course_title: str | None
    total_amount: Decimal
    status: PurchaseStatus
    created_at: datetime
