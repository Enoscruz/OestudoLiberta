"""Acesso a dados dos eventos de webhook — a base da idempotência.

A unicidade ``(gateway, external_event_id)`` garante que o mesmo evento,
reenviado pelo gateway, seja registrado e processado uma única vez.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import Gateway, WebhookStatus
from app.models.system import WebhookEvent


def get(db: Session, *, gateway: Gateway, external_event_id: str) -> WebhookEvent | None:
    """Busca um evento já recebido."""
    stmt = select(WebhookEvent).where(
        WebhookEvent.gateway == gateway,
        WebhookEvent.external_event_id == external_event_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def register(
    db: Session, *, gateway: Gateway, external_event_id: str, event_type: str
) -> WebhookEvent | None:
    """Registra o evento e devolve ``None`` se ele já havia sido recebido.

    A inserção roda dentro de um savepoint: se dois reenvios chegarem ao mesmo
    tempo, o perdedor detecta o conflito sem invalidar a transação principal.
    """
    if get(db, gateway=gateway, external_event_id=external_event_id) is not None:
        return None

    event = WebhookEvent(
        gateway=gateway, external_event_id=external_event_id, event_type=event_type
    )
    try:
        with db.begin_nested():
            db.add(event)
    except IntegrityError:
        return None
    return event


def mark_processed(db: Session, event: WebhookEvent, *, status: WebhookStatus) -> None:
    """Registra o desfecho do processamento do evento."""
    event.processing_status = status
    event.processed_at = datetime.now(UTC)
