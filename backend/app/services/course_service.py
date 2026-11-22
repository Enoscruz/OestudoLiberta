"""Regras de negócio de cursos."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import CourseStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.content import Course
from app.models.user import User
from app.repositories import (
    audit_repository,
    category_repository,
    course_repository,
    lesson_repository,
)
from app.schemas.course import CourseCreate, CourseUpdate

_ENTITY = "course"


def list_courses(db: Session, *, status: CourseStatus | None = None) -> list[Course]:
    """Lista os cursos, opcionalmente filtrados por status."""
    return course_repository.list_all(db, status=status)


def get_course(db: Session, course_id: int) -> Course:
    """Busca um curso, exigindo que ele exista."""
    course = course_repository.get(db, course_id)
    if course is None:
        raise NotFoundError("Curso não encontrado.")
    return course


def _require_category(db: Session, category_id: int) -> None:
    if category_repository.get(db, category_id) is None:
        raise BusinessRuleError("A categoria informada não existe.")


def create_course(db: Session, actor: User, data: CourseCreate) -> Course:
    """Cria um curso em rascunho vinculado a uma categoria existente."""
    _require_category(db, data.category_id)

    course = course_repository.create(
        db,
        category_id=data.category_id,
        title=data.title,
        description=data.description,
        cover_image=data.cover_image,
        price=data.price,
    )
    db.flush()
    audit_repository.record(
        db, user_id=actor.id, action="course.create", entity=_ENTITY, entity_id=course.id
    )
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, actor: User, course_id: int, data: CourseUpdate) -> Course:
    """Atualiza os dados de um curso."""
    course = get_course(db, course_id)
    changes = data.model_dump(exclude_unset=True)

    new_category_id = changes.get("category_id")
    if new_category_id is not None and new_category_id != course.category_id:
        _require_category(db, new_category_id)

    for field, value in changes.items():
        setattr(course, field, value)

    audit_repository.record(
        db, user_id=actor.id, action="course.update", entity=_ENTITY, entity_id=course.id
    )
    db.commit()
    db.refresh(course)
    return course


def publish_course(db: Session, actor: User, course_id: int) -> Course:
    """Publica um curso. Exige ao menos uma aula publicada."""
    course = get_course(db, course_id)
    if course.status == CourseStatus.PUBLISHED:
        raise ConflictError("O curso já está publicado.")
    if not lesson_repository.list_by_course(db, course_id, only_published=True):
        raise BusinessRuleError("Publique ao menos uma aula antes de publicar o curso.")

    course.status = CourseStatus.PUBLISHED
    course.published_at = datetime.now(UTC)

    audit_repository.record(
        db, user_id=actor.id, action="course.publish", entity=_ENTITY, entity_id=course.id
    )
    db.commit()
    db.refresh(course)
    return course


def unpublish_course(db: Session, actor: User, course_id: int) -> Course:
    """Despublica um curso, devolvendo-o ao estado de rascunho."""
    course = get_course(db, course_id)
    if course.status != CourseStatus.PUBLISHED:
        raise ConflictError("O curso não está publicado.")

    course.status = CourseStatus.DRAFT
    course.published_at = None

    audit_repository.record(
        db, user_id=actor.id, action="course.unpublish", entity=_ENTITY, entity_id=course.id
    )
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, actor: User, course_id: int) -> None:
    """Remove um curso que não possua alunos matriculados."""
    course = get_course(db, course_id)
    if course_repository.count_enrollments(db, course_id) > 0:
        raise ConflictError("Não é possível remover um curso com alunos matriculados.")

    audit_repository.record(
        db, user_id=actor.id, action="course.delete", entity=_ENTITY, entity_id=course.id
    )
    db.delete(course)
    db.commit()
