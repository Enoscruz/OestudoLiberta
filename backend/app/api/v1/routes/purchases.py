"""Rotas de compras do aluno."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import VerifiedUser
from app.core.database import get_db
from app.schemas.purchase import CheckoutCreate, CheckoutRead, PurchaseRead
from app.services import purchase_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=CheckoutRead,
    status_code=201,
    summary="Inicia a compra de um curso",
)
def create_checkout(
    payload: CheckoutCreate, user: VerifiedUser, db: DbSession
) -> CheckoutRead:
    """Cria a compra e devolve o endereço de checkout do Mercado Pago."""
    return purchase_service.create_checkout(db, user, payload)


@router.get("", response_model=list[PurchaseRead], summary="Minhas compras")
def list_my_purchases(user: VerifiedUser, db: DbSession) -> list[PurchaseRead]:
    """Lista as compras do aluno, da mais recente para a mais antiga."""
    return purchase_service.list_my_purchases(db, user)
