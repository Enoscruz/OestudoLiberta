"""Regras de negócio relacionadas a usuários."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repository


def list_users(db: Session) -> list[User]:
    """Lista os usuários da plataforma (operação administrativa)."""
    return user_repository.list_all(db)
