"""Contratos Pydantic de aulas e de upload de vídeo."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import LessonStatus

# Regra de negócio: nenhuma aula pode passar de 15 minutos.
MAX_LESSON_SECONDS = 900


class LessonCreate(BaseModel):
    """Dados para criar uma aula."""

    course_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    lesson_order: int | None = Field(default=None, ge=1)
    duration_seconds: int | None = Field(default=None, ge=0, le=MAX_LESSON_SECONDS)
    material_url: str | None = Field(default=None, max_length=500)
    status: LessonStatus = LessonStatus.DRAFT


class LessonUpdate(BaseModel):
    """Dados para atualizar uma aula (campos opcionais)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    lesson_order: int | None = Field(default=None, ge=1)
    duration_seconds: int | None = Field(default=None, ge=0, le=MAX_LESSON_SECONDS)
    material_url: str | None = Field(default=None, max_length=500)
    status: LessonStatus | None = None


class LessonRead(BaseModel):
    """Aula exposta pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: str | None
    video_uid: str | None
    duration_seconds: int | None
    lesson_order: int
    status: LessonStatus
    material_url: str | None
    created_at: datetime


class LessonVideoUploadRead(BaseModel):
    """Instruções de upload direto do vídeo da aula."""

    lesson_id: int
    video_uid: str
    upload_url: str
    max_duration_seconds: int
