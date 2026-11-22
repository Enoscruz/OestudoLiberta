"""Consultas públicas do catálogo.

Diferente de ``course_service``/``category_service`` (área administrativa), este
serviço expõe somente conteúdo publicado e não exige autenticação.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.content import Course
from app.repositories import category_repository, course_repository, lesson_repository
from app.schemas.catalog import (
    CatalogCategoryRead,
    CatalogCourseDetail,
    CatalogCourseRead,
    CatalogLessonRead,
)


def list_categories(db: Session) -> list[CatalogCategoryRead]:
    """Lista as categorias ativas exibidas na vitrine."""
    return [
        CatalogCategoryRead.model_validate(category)
        for category in category_repository.list_active(db)
    ]


def _course_fields(course: Course, *, lessons_count: int) -> dict:
    """Campos comuns entre o resumo e o detalhe de um curso."""
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "cover_image": course.cover_image,
        "price": course.price,
        "category_id": course.category_id,
        "category_name": course.category.name if course.category else None,
        "lessons_count": lessons_count,
        "published_at": course.published_at,
    }


def list_courses(
    db: Session,
    *,
    category_id: int | None = None,
    search: str | None = None,
) -> list[CatalogCourseRead]:
    """Lista os cursos publicados, opcionalmente filtrando por categoria ou título."""
    courses = course_repository.list_published(db, category_id=category_id, search=search)
    lesson_counts = lesson_repository.count_published_by_course(db, [c.id for c in courses])
    return [
        CatalogCourseRead(**_course_fields(course, lessons_count=lesson_counts.get(course.id, 0)))
        for course in courses
    ]


def get_course(db: Session, course_id: int) -> CatalogCourseDetail:
    """Detalha um curso publicado com o currículo de aulas publicadas."""
    course = course_repository.get_published(db, course_id)
    if course is None:
        raise NotFoundError("Curso não encontrado.")

    lessons = lesson_repository.list_by_course(db, course_id, only_published=True)
    return CatalogCourseDetail(
        **_course_fields(course, lessons_count=len(lessons)),
        lessons=[CatalogLessonRead.model_validate(lesson) for lesson in lessons],
    )
