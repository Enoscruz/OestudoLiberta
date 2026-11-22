"""Modelos de usuário e perfil de acesso."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RoleName, UserStatus
from app.models.base import Base, IdMixin, TimestampMixin, enum_type

if TYPE_CHECKING:
    from app.models.commerce import Enrollment, Purchase
    from app.models.learning import LessonProgress
    from app.models.system import AuditLog


class Role(IdMixin, Base):
    """Perfil de acesso (ADMIN ou STUDENT)."""

    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        enum_type(RoleName, "role_name", 30), nullable=False, unique=True
    )
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(IdMixin, TimestampMixin, Base):
    """Usuário da plataforma. A senha vive exclusivamente no Firebase Authentication."""

    __tablename__ = "users"

    firebase_uid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[UserStatus] = mapped_column(
        enum_type(UserStatus, "user_status", 20),
        nullable=False,
        server_default=UserStatus.ACTIVE.value,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    role: Mapped[Role] = relationship(back_populates="users")
    purchases: Mapped[list[Purchase]] = relationship(back_populates="user")
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="user")
    lesson_progress: Mapped[list[LessonProgress]] = relationship(back_populates="user")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# Unicidade de e-mail ignorando a caixa: Enos@x.com e enos@x.com são o mesmo usuário.
Index("uq_users_email_lower", func.lower(User.email), unique=True)
