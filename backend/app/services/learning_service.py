"""Regras de negócio da área do aluno (meus cursos, reprodução e progresso).

Toda leitura exige uma matrícula ``ACTIVE``: o acesso é concedido pela compra
(SPRINT 4) e não pelo simples fato de o curso estar publicado.
"""

from sqlalchemy.orm import Session

from app.core.enums import LessonStatus
from app.core.exceptions import (
    BusinessRuleError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UpstreamError,
)
from app.integrations import cloudflare_stream
from app.models.commerce import Enrollment
from app.models.content import Lesson
from app.models.learning import LessonProgress
from app.models.user import User
from app.repositories import (
    course_repository,
    enrollment_repository,
    lesson_progress_repository,
    lesson_repository,
)
from app.schemas.learning import (
    LessonPlaybackRead,
    MyCourseDetail,
    MyCourseRead,
    MyLessonRead,
)
from app.services import progress_service


def _course_fields(enrollment: Enrollment, *, lessons_count: int) -> dict:
    """Campos comuns entre o resumo e o detalhe de um curso do aluno."""
    course = enrollment.course
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "cover_image": course.cover_image,
        "category_name": course.category.name if course.category else None,
        "lessons_count": lessons_count,
        "granted_at": enrollment.granted_at,
    }


def _lesson_read(lesson: Lesson, progress: LessonProgress | None) -> MyLessonRead:
    """Aula do currículo acrescida do progresso do aluno (SPRINT 5)."""
    return MyLessonRead.model_validate(lesson).model_copy(
        update={
            "progress_seconds": progress.progress_seconds if progress else 0,
            "completed": bool(progress and progress.completed_at),
        }
    )


def list_my_courses(db: Session, user: User) -> list[MyCourseRead]:
    """Lista os cursos liberados para o aluno, com o progresso consolidado."""
    enrollments = enrollment_repository.list_active_by_user(db, user.id)
    course_ids = [enrollment.course_id for enrollment in enrollments]
    lesson_counts = lesson_repository.count_published_by_course(db, course_ids)
    aggregates = lesson_progress_repository.aggregate_by_course(db, user.id, course_ids)

    courses: list[MyCourseRead] = []
    for enrollment in enrollments:
        total = lesson_counts.get(enrollment.course_id, 0)
        progress = aggregates.get(enrollment.course_id)
        completed = progress.completed_lessons if progress else 0
        courses.append(
            MyCourseRead(
                **_course_fields(enrollment, lessons_count=total),
                completed_lessons=completed,
                progress_percent=progress_service.percent(completed, total),
            )
        )
    return courses


def get_my_course(db: Session, user: User, course_id: int) -> MyCourseDetail:
    """Detalha um curso liberado, com o currículo e o progresso em cada aula."""
    course = course_repository.get(db, course_id)
    if course is None:
        raise NotFoundError("Curso não encontrado.")

    enrollment = enrollment_repository.get_active(db, user.id, course_id)
    if enrollment is None:
        raise ForbiddenError("Você não tem acesso a este curso.")

    lessons = lesson_repository.list_by_course(db, course_id, only_published=True)
    progresses = lesson_progress_repository.list_by_user_and_lessons(
        db, user.id, [lesson.id for lesson in lessons]
    )
    completed = sum(
        1 for lesson in lessons if (row := progresses.get(lesson.id)) and row.completed_at
    )

    return MyCourseDetail(
        **_course_fields(enrollment, lessons_count=len(lessons)),
        completed_lessons=completed,
        progress_percent=progress_service.percent(completed, len(lessons)),
        lessons=[
            _lesson_read(lesson, progresses.get(lesson.id)) for lesson in lessons
        ],
    )


def get_lesson_playback(db: Session, user: User, lesson_id: int) -> LessonPlaybackRead:
    """Emite as URLs assinadas de reprodução de uma aula.

    A aula só é liberada para quem tem matrícula ativa no curso e está
    publicada com vídeo enviado.
    """
    lesson = lesson_repository.get(db, lesson_id)
    if lesson is None or lesson.status != LessonStatus.PUBLISHED:
        raise NotFoundError("Aula não encontrada.")

    if enrollment_repository.get_active(db, user.id, lesson.course_id) is None:
        raise ForbiddenError("Você não tem acesso a este curso.")

    if not lesson.video_uid:
        raise BusinessRuleError("Esta aula ainda não tem vídeo disponível.")

    try:
        playback = cloudflare_stream.create_playback(video_uid=lesson.video_uid)
    except cloudflare_stream.CloudflareNotConfiguredError as exc:
        raise ServiceUnavailableError(
            "Reprodução indisponível: Cloudflare Stream não configurada."
        ) from exc
    except cloudflare_stream.CloudflareStreamError as exc:
        raise UpstreamError("Falha ao preparar a reprodução do vídeo.") from exc

    return LessonPlaybackRead(
        lesson_id=lesson.id,
        title=lesson.title,
        iframe_url=playback.iframe_url,
        hls_url=playback.hls_url,
        expires_at=playback.expires_at,
    )
