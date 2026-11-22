"""Contratos Pydantic de categorias."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CategoryStatus


class CategoryCreate(BaseModel):
    """Dados para criar uma categoria."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    status: CategoryStatus = CategoryStatus.ACTIVE


class CategoryUpdate(BaseModel):
    """Dados para atualizar uma categoria (campos opcionais)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    status: CategoryStatus | None = None


class CategoryRead(BaseModel):
    """Categoria exposta pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: CategoryStatus
    created_at: datetime
