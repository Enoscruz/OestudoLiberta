"""Acesso a dados do progresso de aprendizagem."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import LessonStatus
from app.models.content import Lesson
from app.models.learning import LessonProgress


@dataclass(frozen=True)
class CourseProgress:
    """Progresso agregado de um aluno em um curso."""

    completed_lessons: int
    watched_seconds: int
    last_activity_at: datetime | None


def get(db: Session, *, user_id: int, lesson_id: int) -> LessonProgress | None:
    """Busca o progresso de um aluno em uma aula."""
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert(
    db: Session,
    *,
    user_id: int,
    lesson_id: int,
    progress_seconds: int,
    completed: bool,
) -> LessonProgress:
    """Grava o progresso de uma aula, criando a linha se ainda não existir.

    O progresso nunca regride: se a posição informada for menor do que a já
    registrada, a maior prevalece (evita perder avanço quando o aluno volta a
    assistir um trecho anterior).
    """
    row = get(db, user_id=user_id, lesson_id=lesson_id)
    if row is None:
        row = LessonProgress(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
    else:
        progress_seconds = max(progress_seconds, row.progress_seconds)

    row.progress_seconds = progress_seconds

    # `completed_at` marca a primeira conclusão e não é apagado depois.
    if completed and row.completed_at is None:
        row.completed_at = datetime.now(UTC)
    return row


def list_by_user_and_lessons(
    db: Session, user_id: int, lesson_ids: list[int]
) -> dict[int, LessonProgress]:
    """Progresso do aluno nas aulas informadas, indexado pelo id da aula."""
    if not lesson_ids:
        return {}
    rows = db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_(lesson_ids),
        )
    ).scalars()
    return {row.lesson_id: row for row in rows}


def aggregate_by_course(
    db: Session, user_id: int, course_ids: list[int]
) -> dict[int, CourseProgress]:
    """Progresso do aluno por curso, em uma única consulta.

    Considera apenas aulas atualmente publicadas, para que o percentual seja
    sempre medido contra o conteúdo que o aluno realmente enxerga.
    """
    if not course_ids:
        return {}

    rows = db.execute(
        select(
            Lesson.course_id,
            func.count(LessonProgress.id).filter(LessonProgress.completed_at.is_not(None)),
            func.coalesce(func.sum(LessonProgress.progress_seconds), 0),
            func.max(LessonProgress.updated_at),
        )
        .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
        .where(
            LessonProgress.user_id == user_id,
            Lesson.course_id.in_(course_ids),
            Lesson.status == LessonStatus.PUBLISHED,
        )
        .group_by(Lesson.course_id)
    ).all()

    return {
        course_id: CourseProgress(
            completed_lessons=int(completed_lessons),
            watched_seconds=int(watched_seconds),
            last_activity_at=last_activity_at,
        )
        for course_id, completed_lessons, watched_seconds, last_activity_at in rows
    }
