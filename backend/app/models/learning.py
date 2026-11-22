"""Modelos de acompanhamento de aprendizagem."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.user import User


class LessonProgress(IdMixin, Base):
    """Progresso de um aluno em uma aula."""

    __tablename__ = "lesson_progress"
    __table_args__ = (
        CheckConstraint("progress_seconds >= 0", name="progress_seconds_non_negative"),
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_id_lesson_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    progress_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="lesson_progress")
    lesson: Mapped[Lesson] = relationship()

    def __repr__(self) -> str:
        return f"<LessonProgress user={self.user_id} lesson={self.lesson_id}>"
