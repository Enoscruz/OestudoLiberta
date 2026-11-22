"""Rotas administrativas de usuários."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.services import user_service

router = APIRouter()


@router.get("", response_model=list[UserRead], summary="Lista usuários (ADMIN)")
def list_users(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> list[User]:
    """Lista todos os usuários da plataforma. Restrito a administradores."""
    return user_service.list_users(db)
