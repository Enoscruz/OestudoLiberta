"""Contratos Pydantic do catálogo público.

Expõem apenas conteúdo publicado (cursos ``PUBLISHED`` e suas aulas publicadas),
omitindo dados internos como ``video_uid`` e ``status``.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CatalogCategoryRead(BaseModel):
    """Categoria ativa exposta na vitrine."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class CatalogLessonRead(BaseModel):
    """Aula publicada exibida no currículo do curso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    lesson_order: int
    duration_seconds: int | None


class CatalogCourseRead(BaseModel):
    """Curso publicado exibido na listagem do catálogo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    cover_image: str | None
    price: Decimal
    category_id: int
    category_name: str | None
    lessons_count: int
    published_at: datetime | None


class CatalogCourseDetail(CatalogCourseRead):
    """Curso publicado com o currículo completo."""

    lessons: list[CatalogLessonRead] = Field(default_factory=list)
