"""Regras de negócio de aulas e do fluxo de upload de vídeo."""

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    UpstreamError,
)
from app.integrations import cloudflare_stream
from app.models.content import Lesson
from app.models.user import User
from app.repositories import audit_repository, course_repository, lesson_repository
from app.schemas.lesson import (
    MAX_LESSON_SECONDS,
    LessonCreate,
    LessonUpdate,
    LessonVideoUploadRead,
)

_ENTITY = "lesson"


def list_lessons(db: Session, course_id: int, *, only_published: bool = False) -> list[Lesson]:
    """Lista as aulas de um curso, exigindo que o curso exista."""
    if course_repository.get(db, course_id) is None:
        raise NotFoundError("Curso não encontrado.")
    return lesson_repository.list_by_course(db, course_id, only_published=only_published)


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    """Busca uma aula, exigindo que ela exista."""
    lesson = lesson_repository.get(db, lesson_id)
    if lesson is None:
        raise NotFoundError("Aula não encontrada.")
    return lesson


def create_lesson(db: Session, actor: User, data: LessonCreate) -> Lesson:
    """Cria uma aula no curso informado.

    Se a ordem não for informada, a aula é posicionada ao final do curso.
    Ordens já ocupadas são recusadas.
    """
    if course_repository.get(db, data.course_id) is None:
        raise NotFoundError("Curso não encontrado.")

    order = data.lesson_order
    if order is None:
        order = lesson_repository.max_order(db, data.course_id) + 1
    elif lesson_repository.order_taken(db, data.course_id, order):
        raise ConflictError(f"A posição {order} já está ocupada neste curso.")

    lesson = lesson_repository.create(
        db,
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        lesson_order=order,
        duration_seconds=data.duration_seconds,
        material_url=data.material_url,
        status=data.status,
    )
    db.flush()
    audit_repository.record(
        db, user_id=actor.id, action="lesson.create", entity=_ENTITY, entity_id=lesson.id
    )
    db.commit()
    db.refresh(lesson)
    return lesson


def update_lesson(db: Session, actor: User, lesson_id: int, data: LessonUpdate) -> Lesson:
    """Atualiza os dados de uma aula, validando a ordem de exibição."""
    lesson = get_lesson(db, lesson_id)
    changes = data.model_dump(exclude_unset=True)

    new_order = changes.get("lesson_order")
    if new_order is not None and new_order != lesson.lesson_order:
        if lesson_repository.order_taken(
            db, lesson.course_id, new_order, exclude_id=lesson.id
        ):
            raise ConflictError(f"A posição {new_order} já está ocupada neste curso.")

    for field, value in changes.items():
        setattr(lesson, field, value)

    audit_repository.record(
        db, user_id=actor.id, action="lesson.update", entity=_ENTITY, entity_id=lesson.id
    )
    db.commit()
    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, actor: User, lesson_id: int) -> None:
    """Remove uma aula."""
    lesson = get_lesson(db, lesson_id)

    audit_repository.record(
        db, user_id=actor.id, action="lesson.delete", entity=_ENTITY, entity_id=lesson.id
    )
    db.delete(lesson)
    db.commit()


def create_video_upload(
    db: Session, actor: User, lesson_id: int
) -> LessonVideoUploadRead:
    """Negocia um upload direto de vídeo e associa o ``uid`` à aula.

    O arquivo nunca trafega pelo backend: apenas devolvemos a URL de upload de
    uso único para o frontend enviar o vídeo direto à Cloudflare. O limite de
    duração é o mesmo imposto às aulas (15 minutos).
    """
    lesson = get_lesson(db, lesson_id)

    try:
        upload = cloudflare_stream.create_direct_upload(
            max_duration_seconds=MAX_LESSON_SECONDS
        )
    except cloudflare_stream.CloudflareNotConfiguredError as exc:
        raise ServiceUnavailableError(
            "Upload de vídeo indisponível: Cloudflare Stream não configurada."
        ) from exc
    except cloudflare_stream.CloudflareStreamError as exc:
        raise UpstreamError("Falha ao negociar o upload do vídeo.") from exc

    lesson.video_uid = upload.uid
    audit_repository.record(
        db, user_id=actor.id, action="lesson.video_upload", entity=_ENTITY, entity_id=lesson.id
    )
    db.commit()

    return LessonVideoUploadRead(
        lesson_id=lesson.id,
        video_uid=upload.uid,
        upload_url=upload.upload_url,
        max_duration_seconds=MAX_LESSON_SECONDS,
    )
