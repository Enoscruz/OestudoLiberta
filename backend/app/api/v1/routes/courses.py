"""Rotas administrativas de cursos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.core.database import get_db
from app.core.enums import CourseStatus
from app.models.content import Course
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services import course_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CourseRead], summary="Lista cursos (ADMIN)")
def list_courses(
    _: AdminUser,
    db: DbSession,
    status: Annotated[CourseStatus | None, Query()] = None,
) -> list[Course]:
    """Lista os cursos, opcionalmente filtrando por status."""
    return course_service.list_courses(db, status=status)


@router.post("", response_model=CourseRead, status_code=201, summary="Cria curso (ADMIN)")
def create_course(payload: CourseCreate, actor: AdminUser, db: DbSession) -> Course:
    """Cria um curso em rascunho."""
    return course_service.create_course(db, actor, payload)


@router.get("/{course_id}", response_model=CourseRead, summary="Detalha curso (ADMIN)")
def get_course(course_id: int, _: AdminUser, db: DbSession) -> Course:
    """Detalha um curso."""
    return course_service.get_course(db, course_id)


@router.patch("/{course_id}", response_model=CourseRead, summary="Atualiza curso (ADMIN)")
def update_course(
    course_id: int, payload: CourseUpdate, actor: AdminUser, db: DbSession
) -> Course:
    """Atualiza os dados de um curso."""
    return course_service.update_course(db, actor, course_id, payload)


@router.post(
    "/{course_id}/publish", response_model=CourseRead, summary="Publica curso (ADMIN)"
)
def publish_course(course_id: int, actor: AdminUser, db: DbSession) -> Course:
    """Publica um curso (exige ao menos uma aula publicada)."""
    return course_service.publish_course(db, actor, course_id)


@router.post(
    "/{course_id}/unpublish", response_model=CourseRead, summary="Despublica curso (ADMIN)"
)
def unpublish_course(course_id: int, actor: AdminUser, db: DbSession) -> Course:
    """Despublica um curso, devolvendo-o ao estado de rascunho."""
    return course_service.unpublish_course(db, actor, course_id)


@router.delete("/{course_id}", status_code=204, summary="Remove curso (ADMIN)")
def delete_course(course_id: int, actor: AdminUser, db: DbSession) -> None:
    """Remove um curso sem alunos matriculados."""
    course_service.delete_course(db, actor, course_id)
