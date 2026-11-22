"""Contratos Pydantic de cursos."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CourseStatus


class CourseCreate(BaseModel):
    """Dados para criar um curso."""

    category_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    cover_image: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)


class CourseUpdate(BaseModel):
    """Dados para atualizar um curso (campos opcionais)."""

    category_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    cover_image: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)


class CourseRead(BaseModel):
    """Curso exposto pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    title: str
    description: str | None
    cover_image: str | None
    price: Decimal
    status: CourseStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
