"""Acesso a dados de papéis de acesso."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import RoleName
from app.models.user import Role


def get_by_name(db: Session, name: RoleName) -> Role | None:
    """Busca um papel pelo nome (ADMIN ou STUDENT)."""
    return db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
