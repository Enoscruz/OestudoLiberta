"""Rotas da área do aluno (cursos liberados, reprodução e progresso)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import VerifiedUser
from app.core.database import get_db
from app.schemas.learning import (
    LearningHistoryRead,
    LessonPlaybackRead,
    LessonProgressRead,
    LessonProgressUpdate,
    MyCourseDetail,
    MyCourseRead,
)
from app.services import learning_service, progress_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/courses", response_model=list[MyCourseRead], summary="Meus cursos")
def list_my_courses(user: VerifiedUser, db: DbSession) -> list[MyCourseRead]:
    """Lista os cursos aos quais o aluno tem acesso liberado."""
    return learning_service.list_my_courses(db, user)


@router.get(
    "/courses/{course_id}",
    response_model=MyCourseDetail,
    summary="Detalha um curso liberado",
)
def get_my_course(course_id: int, user: VerifiedUser, db: DbSession) -> MyCourseDetail:
    """Detalha um curso do aluno, incluindo o currículo de aulas publicadas."""
    return learning_service.get_my_course(db, user, course_id)


@router.get(
    "/lessons/{lesson_id}/playback",
    response_model=LessonPlaybackRead,
    summary="Prepara a reprodução de uma aula",
)
def get_lesson_playback(
    lesson_id: int, user: VerifiedUser, db: DbSession
) -> LessonPlaybackRead:
    """Devolve as URLs assinadas para reproduzir a aula."""
    return learning_service.get_lesson_playback(db, user, lesson_id)


@router.put(
    "/lessons/{lesson_id}/progress",
    response_model=LessonProgressRead,
    summary="Registra o progresso em uma aula",
)
def save_lesson_progress(
    lesson_id: int,
    payload: LessonProgressUpdate,
    user: VerifiedUser,
    db: DbSession,
) -> LessonProgressRead:
    """Grava o progresso do aluno em uma aula do curso que ele possui."""
    return progress_service.record_progress(db, user, lesson_id, payload)


@router.get(
    "/history",
    response_model=LearningHistoryRead,
    summary="Histórico de aprendizagem",
)
def get_learning_history(user: VerifiedUser, db: DbSession) -> LearningHistoryRead:
    """Consolida indicadores e a evolução do aluno em cada curso."""
    return progress_service.get_history(db, user)
