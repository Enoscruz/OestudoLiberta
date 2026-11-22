"""Acesso a dados de cursos."""

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import CourseStatus
from app.models.commerce import Enrollment
from app.models.content import Course


def list_all(db: Session, *, status: CourseStatus | None = None) -> list[Course]:
    """Lista cursos, opcionalmente filtrados por status."""
    stmt = select(Course).order_by(Course.created_at.desc())
    if status is not None:
        stmt = stmt.where(Course.status == status)
    return list(db.execute(stmt).scalars())


def list_published(
    db: Session,
    *,
    category_id: int | None = None,
    search: str | None = None,
) -> list[Course]:
    """Lista os cursos publicados (vitrine pública), com a categoria carregada."""
    stmt = (
        select(Course)
        .options(joinedload(Course.category))
        .where(Course.status == CourseStatus.PUBLISHED)
        .order_by(Course.published_at.desc())
    )
    if category_id is not None:
        stmt = stmt.where(Course.category_id == category_id)
    if search:
        stmt = stmt.where(Course.title.ilike(f"%{search}%"))
    return list(db.execute(stmt).unique().scalars())


def get_published(db: Session, course_id: int) -> Course | None:
    """Busca um curso publicado pela chave primária."""
    stmt = (
        select(Course)
        .options(joinedload(Course.category))
        .where(Course.id == course_id, Course.status == CourseStatus.PUBLISHED)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def get(db: Session, course_id: int) -> Course | None:
    """Busca um curso pela chave primária."""
    return db.get(Course, course_id)


def create(
    db: Session,
    *,
    category_id: int,
    title: str,
    description: str | None,
    cover_image: str | None,
    price: Decimal,
) -> Course:
    """Insere um novo curso."""
    course = Course(
        category_id=category_id,
        title=title,
        description=description,
        cover_image=cover_image,
        price=price,
    )
    db.add(course)
    return course


def update(db: Session, course: Course, changes: dict[str, Any]) -> Course:
    """Aplica alterações a um curso."""
    for field, value in changes.items():
        setattr(course, field, value)
    return course


def count_by_category(db: Session, category_id: int) -> int:
    """Quantos cursos existem em uma categoria."""
    return db.execute(
        select(func.count()).select_from(Course).where(Course.category_id == category_id)
    ).scalar_one()


def count_enrollments(db: Session, course_id: int) -> int:
    """Quantos alunos têm acesso liberado a um curso."""
    return db.execute(
        select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
    ).scalar_one()
