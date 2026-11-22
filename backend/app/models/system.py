"""Modelos de sistema: eventos de webhook e auditoria."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Gateway, WebhookStatus
from app.models.base import Base, IdMixin, enum_type

if TYPE_CHECKING:
    from app.models.user import User


class WebhookEvent(IdMixin, Base):
    """Evento recebido de um gateway. A unicidade garante a idempotência."""

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "gateway",
            "external_event_id",
            name="uq_webhook_events_gateway_external_event_id",
        ),
    )

    gateway: Mapped[Gateway] = mapped_column(
        enum_type(Gateway, "webhook_gateway", 30), nullable=False
    )
    external_event_id: Mapped[str] = mapped_column(String(150), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    processing_status: Mapped[WebhookStatus] = mapped_column(
        enum_type(WebhookStatus, "webhook_status", 20),
        nullable=False,
        server_default=WebhookStatus.RECEIVED.value,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.gateway} {self.external_event_id}>"


class AuditLog(IdMixin, Base):
    """Registro de auditoria das ações administrativas."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity", "entity", "entity_id"),)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User | None] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity}#{self.entity_id}>"
