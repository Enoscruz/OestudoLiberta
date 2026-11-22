"""Regras de negócio do progresso de aprendizagem.

O progresso é sempre por aula e obedece à mesma autorização da reprodução
(ver ``learning_service``): a aula precisa estar publicada e o aluno precisa ter
matrícula ativa no curso. Aqui também vive a consolidação usada pelo dashboard e
pelo histórico — o percentual é sempre medido contra as aulas publicadas.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import LessonStatus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.learning import LessonProgress
from app.models.user import User
from app.repositories import (
    enrollment_repository,
    lesson_progress_repository,
    lesson_repository,
)
from app.schemas.learning import (
    LearningCourseRead,
    LearningHistoryRead,
    LearningSummaryRead,
    LessonProgressRead,
    LessonProgressUpdate,
)


def percent(completed: int, total: int) -> int:
    """Percentual inteiro de conclusão (0 quando não há aulas publicadas)."""
    if total <= 0:
        return 0
    return round(completed * 100 / total)


def record_progress(
    db: Session, user: User, lesson_id: int, data: LessonProgressUpdate
) -> LessonProgressRead:
    """Registra o progresso do aluno em uma aula.

    O tempo informado é limitado à duração da aula e a conclusão é automática
    quando o aluno alcança o fim do vídeo — o player não decide sozinho se a
    aula terminou.
    """
    lesson = lesson_repository.get(db, lesson_id)
    if lesson is None or lesson.status != LessonStatus.PUBLISHED:
        raise NotFoundError("Aula não encontrada.")

    if enrollment_repository.get_active(db, user.id, lesson.course_id) is None:
        raise ForbiddenError("Você não tem acesso a este curso.")

    seconds = max(0, data.progress_seconds)
    if lesson.duration_seconds:
        seconds = min(seconds, lesson.duration_seconds)

    reached_end = (
        lesson.duration_seconds is not None and seconds >= lesson.duration_seconds
    )

    row = lesson_progress_repository.upsert(
        db,
        user_id=user.id,
        lesson_id=lesson_id,
        progress_seconds=seconds,
        completed=data.completed or reached_end,
    )
    db.commit()
    db.refresh(row)

    return _to_read(row)


def get_history(db: Session, user: User) -> LearningHistoryRead:
    """Consolida indicadores e o histórico de aprendizagem do aluno."""
    enrollments = enrollment_repository.list_active_by_user(db, user.id)
    course_ids = [enrollment.course_id for enrollment in enrollments]
    lesson_counts = lesson_repository.count_published_by_course(db, course_ids)
    aggregates = lesson_progress_repository.aggregate_by_course(db, user.id, course_ids)

    courses: list[LearningCourseRead] = []
    for enrollment in enrollments:
        course = enrollment.course
        total = lesson_counts.get(course.id, 0)
        progress = aggregates.get(course.id)
        completed = progress.completed_lessons if progress else 0
        courses.append(
            LearningCourseRead(
                id=course.id,
                title=course.title,
                cover_image=course.cover_image,
                category_name=course.category.name if course.category else None,
                lessons_count=total,
                completed_lessons=completed,
                progress_percent=percent(completed, total),
                completed=total > 0 and completed >= total,
                last_activity_at=progress.last_activity_at if progress else None,
            )
        )

    # Mais recente primeiro; o id desempata atividades do mesmo instante e
    # cursos ainda não iniciados vão para o fim.
    courses.sort(
        key=lambda item: (
            item.last_activity_at or datetime.min.replace(tzinfo=UTC),
            item.id,
        ),
        reverse=True,
    )

    summary = LearningSummaryRead(
        courses_owned=len(courses),
        courses_completed=sum(1 for course in courses if course.completed),
        lessons_completed=sum(course.completed_lessons for course in courses),
        lessons_available=sum(course.lessons_count for course in courses),
        watched_seconds=sum(item.watched_seconds for item in aggregates.values()),
    )

    return LearningHistoryRead(summary=summary, courses=courses)


def _to_read(row: LessonProgress) -> LessonProgressRead:
    return LessonProgressRead(
        lesson_id=row.lesson_id,
        progress_seconds=row.progress_seconds,
        completed=row.completed_at is not None,
        completed_at=row.completed_at,
        updated_at=row.updated_at,
    )
