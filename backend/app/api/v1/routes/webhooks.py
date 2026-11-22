"""Rotas públicas de notificação dos gateways de pagamento.

Estas rotas **não** exigem autenticação: quem chama é o gateway. A segurança
vem da validação da assinatura (quando configurada) e, principalmente, da
reconsulta do pagamento na origem antes de qualquer liberação de acesso.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError
from app.services import payment_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


async def _json_body(request: Request) -> dict[str, Any]:
    """Corpo JSON da notificação, tolerando um corpo vazio ou inválido."""
    try:
        body = await request.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


@router.post("/mercadopago", summary="Notificações do Mercado Pago")
async def mercadopago(
    request: Request,
    db: DbSession,
    x_signature: Annotated[str | None, Header()] = None,
    x_request_id: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Recebe a notificação de mudança de status de um pagamento."""
    body = await _json_body(request)
    data = body.get("data")
    data_id = request.query_params.get("data.id") or (
        str(data.get("id")) if isinstance(data, dict) and data.get("id") else None
    )
    notification_id = body.get("id") or request.query_params.get("id") or data_id
    event_type = (
        body.get("action")
        or body.get("type")
        or request.query_params.get("type")
        or "payment"
    )

    if not data_id or notification_id is None:
        raise BusinessRuleError("Notificação sem identificador de pagamento.")

    outcome = payment_service.handle_notification(
        db,
        event_id=str(notification_id),
        event_type=str(event_type),
        payment_id=str(data_id),
        x_signature=x_signature,
        x_request_id=x_request_id,
    )
    return {"status": outcome}
