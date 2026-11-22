"""Rotas públicas do catálogo (sem autenticação)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import CatalogCategoryRead, CatalogCourseDetail, CatalogCourseRead
from app.services import catalog_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/categories",
    response_model=list[CatalogCategoryRead],
    summary="Lista categorias ativas",
)
def list_categories(db: DbSession) -> list[CatalogCategoryRead]:
    """Lista as categorias ativas exibidas na vitrine."""
    return catalog_service.list_categories(db)


@router.get(
    "/courses",
    response_model=list[CatalogCourseRead],
    summary="Lista cursos publicados",
)
def list_courses(
    db: DbSession,
    category_id: Annotated[int | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> list[CatalogCourseRead]:
    """Lista os cursos publicados, com filtro opcional por categoria ou título."""
    return catalog_service.list_courses(db, category_id=category_id, search=search)


@router.get(
    "/courses/{course_id}",
    response_model=CatalogCourseDetail,
    summary="Detalha curso publicado",
)
def get_course(course_id: int, db: DbSession) -> CatalogCourseDetail:
    """Detalha um curso publicado, incluindo o currículo de aulas publicadas."""
    return catalog_service.get_course(db, course_id)
