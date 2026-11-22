"""Rotas administrativas de aulas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.core.database import get_db
from app.models.content import Lesson
from app.schemas.lesson import (
    LessonCreate,
    LessonRead,
    LessonUpdate,
    LessonVideoUploadRead,
)
from app.services import lesson_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[LessonRead], summary="Lista aulas de um curso (ADMIN)")
def list_lessons(
    _: AdminUser,
    db: DbSession,
    course_id: Annotated[int, Query()],
    only_published: Annotated[bool, Query()] = False,
) -> list[Lesson]:
    """Lista as aulas de um curso na ordem de exibição."""
    return lesson_service.list_lessons(db, course_id, only_published=only_published)


@router.post("", response_model=LessonRead, status_code=201, summary="Cria aula (ADMIN)")
def create_lesson(payload: LessonCreate, actor: AdminUser, db: DbSession) -> Lesson:
    """Cria uma aula em um curso."""
    return lesson_service.create_lesson(db, actor, payload)


@router.get("/{lesson_id}", response_model=LessonRead, summary="Detalha aula (ADMIN)")
def get_lesson(lesson_id: int, _: AdminUser, db: DbSession) -> Lesson:
    """Detalha uma aula."""
    return lesson_service.get_lesson(db, lesson_id)


@router.patch("/{lesson_id}", response_model=LessonRead, summary="Atualiza aula (ADMIN)")
def update_lesson(
    lesson_id: int, payload: LessonUpdate, actor: AdminUser, db: DbSession
) -> Lesson:
    """Atualiza os dados de uma aula."""
    return lesson_service.update_lesson(db, actor, lesson_id, payload)


@router.delete("/{lesson_id}", status_code=204, summary="Remove aula (ADMIN)")
def delete_lesson(lesson_id: int, actor: AdminUser, db: DbSession) -> None:
    """Remove uma aula."""
    lesson_service.delete_lesson(db, actor, lesson_id)


@router.post(
    "/{lesson_id}/video-upload",
    response_model=LessonVideoUploadRead,
    summary="Negocia upload de vídeo da aula (ADMIN)",
)
def create_video_upload(
    lesson_id: int, actor: AdminUser, db: DbSession
) -> LessonVideoUploadRead:
    """Devolve a URL de upload direto (Cloudflare Stream) para a aula."""
    return lesson_service.create_video_upload(db, actor, lesson_id)
