"""Rotas administrativas de categorias."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.core.database import get_db
from app.models.content import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CategoryRead], summary="Lista categorias (ADMIN)")
def list_categories(_: AdminUser, db: DbSession) -> list[Category]:
    """Lista todas as categorias."""
    return category_service.list_categories(db)


@router.post(
    "", response_model=CategoryRead, status_code=201, summary="Cria categoria (ADMIN)"
)
def create_category(
    payload: CategoryCreate, actor: AdminUser, db: DbSession
) -> Category:
    """Cria uma nova categoria."""
    return category_service.create_category(db, actor, payload)


@router.get("/{category_id}", response_model=CategoryRead, summary="Detalha categoria (ADMIN)")
def get_category(category_id: int, _: AdminUser, db: DbSession) -> Category:
    """Detalha uma categoria."""
    return category_service.get_category(db, category_id)


@router.patch(
    "/{category_id}", response_model=CategoryRead, summary="Atualiza categoria (ADMIN)"
)
def update_category(
    category_id: int, payload: CategoryUpdate, actor: AdminUser, db: DbSession
) -> Category:
    """Atualiza uma categoria existente."""
    return category_service.update_category(db, actor, category_id, payload)


@router.delete("/{category_id}", status_code=204, summary="Remove categoria (ADMIN)")
def delete_category(category_id: int, actor: AdminUser, db: DbSession) -> None:
    """Remove uma categoria sem cursos vinculados."""
    category_service.delete_category(db, actor, category_id)
