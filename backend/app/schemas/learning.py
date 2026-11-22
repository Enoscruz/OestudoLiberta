"""Contratos Pydantic da área do aluno (meus cursos e reprodução de aulas).

Nada aqui expõe ``video_uid``: o aluno recebe somente as URLs assinadas de
reprodução, emitidas sob demanda.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MyLessonRead(BaseModel):
    """Aula publicada de um curso ao qual o aluno tem acesso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    lesson_order: int
    duration_seconds: int | None
    material_url: str | None
    progress_seconds: int = 0
    completed: bool = False


class MyCourseRead(BaseModel):
    """Curso liberado para o aluno."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    cover_image: str | None
    category_name: str | None
    lessons_count: int
    granted_at: datetime
    completed_lessons: int = 0
    progress_percent: int = 0


class MyCourseDetail(MyCourseRead):
    """Curso liberado com o currículo de aulas publicadas."""

    lessons: list[MyLessonRead] = Field(default_factory=list)


class LessonPlaybackRead(BaseModel):
    """URLs assinadas para reproduzir uma aula."""

    lesson_id: int
    title: str
    iframe_url: str
    hls_url: str
    expires_at: datetime


# ── Progresso de aprendizagem (SPRINT 5) ──────────────────────────────────


class LessonProgressUpdate(BaseModel):
    """Progresso enviado pelo player.

    O teto de 24 h na validação é apenas um limite defensivo: quem manda de
    verdade é a duração da aula, aplicada no serviço.
    """

    progress_seconds: int = Field(default=0, ge=0, le=86_400)
    completed: bool = False


class LessonProgressRead(BaseModel):
    """Progresso registrado em uma aula."""

    lesson_id: int
    progress_seconds: int
    completed: bool
    completed_at: datetime | None
    updated_at: datetime


class LearningSummaryRead(BaseModel):
    """Indicadores gerais de aprendizagem."""

    courses_owned: int
    courses_completed: int
    lessons_completed: int
    lessons_available: int
    watched_seconds: int


class LearningCourseRead(BaseModel):
    """Um curso no histórico de aprendizagem, com o progresso consolidado."""

    id: int
    title: str
    cover_image: str | None
    category_name: str | None
    lessons_count: int
    completed_lessons: int
    progress_percent: int
    completed: bool
    last_activity_at: datetime | None


class LearningHistoryRead(BaseModel):
    """Histórico de aprendizagem: indicadores + cursos do aluno."""

    summary: LearningSummaryRead
    courses: list[LearningCourseRead] = Field(default_factory=list)
