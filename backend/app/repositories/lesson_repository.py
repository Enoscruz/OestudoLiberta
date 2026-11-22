"""Acesso a dados de aulas."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import LessonStatus
from app.models.content import Lesson


def list_by_course(
    db: Session, course_id: int, *, only_published: bool = False
) -> list[Lesson]:
    """Lista as aulas de um curso na ordem de exibição."""
    stmt = select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.lesson_order)
    if only_published:
        stmt = stmt.where(Lesson.status == LessonStatus.PUBLISHED)
    return list(db.execute(stmt).scalars())


def get(db: Session, lesson_id: int) -> Lesson | None:
    """Busca uma aula pela chave primária."""
    return db.get(Lesson, lesson_id)


def create(
    db: Session,
    *,
    course_id: int,
    title: str,
    description: str | None,
    lesson_order: int,
    duration_seconds: int | None,
    material_url: str | None,
    status: LessonStatus,
) -> Lesson:
    """Insere uma nova aula."""
    lesson = Lesson(
        course_id=course_id,
        title=title,
        description=description,
        lesson_order=lesson_order,
        duration_seconds=duration_seconds,
        material_url=material_url,
        status=status,
    )
    db.add(lesson)
    return lesson


def update(db: Session, lesson: Lesson, changes: dict[str, Any]) -> Lesson:
    """Aplica alterações a uma aula."""
    for field, value in changes.items():
        setattr(lesson, field, value)
    return lesson


def count_published_by_course(db: Session, course_ids: list[int]) -> dict[int, int]:
    """Quantidade de aulas publicadas por curso, em uma única consulta."""
    if not course_ids:
        return {}
    rows = db.execute(
        select(Lesson.course_id, func.count(Lesson.id))
        .where(Lesson.course_id.in_(course_ids), Lesson.status == LessonStatus.PUBLISHED)
        .group_by(Lesson.course_id)
    ).all()
    return {course_id: count for course_id, count in rows}


def max_order(db: Session, course_id: int) -> int:
    """Maior posição de aula já usada no curso (0 se não houver aulas)."""
    value = db.execute(
        select(func.max(Lesson.lesson_order)).where(Lesson.course_id == course_id)
    ).scalar()
    return value or 0


def order_taken(db: Session, course_id: int, order: int, *, exclude_id: int | None = None) -> bool:
    """Verifica se uma posição já está ocupada no curso."""
    stmt = select(Lesson.id).where(
        Lesson.course_id == course_id, Lesson.lesson_order == order
    )
    if exclude_id is not None:
        stmt = stmt.where(Lesson.id != exclude_id)
    return db.execute(stmt).first() is not None
