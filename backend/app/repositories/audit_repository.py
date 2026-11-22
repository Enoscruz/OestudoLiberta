"""Acesso a dados de auditoria."""

from sqlalchemy.orm import Session

from app.models.system import AuditLog


def record(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
) -> AuditLog:
    """Registra uma ação administrativa no histórico de auditoria."""
    log = AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id)
    db.add(log)
    return log
