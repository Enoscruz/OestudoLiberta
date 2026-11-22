"""Modelos de conteúdo educacional: categoria, curso e aula."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CategoryStatus, CourseStatus, LessonStatus
from app.models.base import Base, CreatedAtMixin, IdMixin, TimestampMixin, enum_type

if TYPE_CHECKING:
    from app.models.commerce import Enrollment, Purchase


class Category(IdMixin, CreatedAtMixin, Base):
    """Categoria que agrupa cursos."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CategoryStatus] = mapped_column(
        enum_type(CategoryStatus, "category_status", 20),
        nullable=False,
        server_default=CategoryStatus.ACTIVE.value,
    )

    courses: Mapped[list[Course]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Course(IdMixin, TimestampMixin, Base):
    """Curso vendido individualmente."""

    __tablename__ = "courses"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    status: Mapped[CourseStatus] = mapped_column(
        enum_type(CourseStatus, "course_status", 20),
        nullable=False,
        server_default=CourseStatus.DRAFT.value,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category: Mapped[Category] = relationship(back_populates="courses")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="course")
    purchases: Mapped[list[Purchase]] = relationship(back_populates="course")

    def __repr__(self) -> str:
        return f"<Course {self.title}>"


class Lesson(IdMixin, CreatedAtMixin, Base):
    """Aula em vídeo (máximo de 15 minutos)."""

    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint(
            "duration_seconds IS NULL OR (duration_seconds >= 0 AND duration_seconds <= 900)",
            name="duration_max_15_minutes",
        ),
        CheckConstraint("lesson_order > 0", name="lesson_order_positive"),
        UniqueConstraint(
            "course_id", "lesson_order", name="uq_lessons_course_id_lesson_order"
        ),
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    video_uid: Mapped[str | None] = mapped_column(String(200))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    status: Mapped[LessonStatus] = mapped_column(
        enum_type(LessonStatus, "lesson_status", 20),
        nullable=False,
        server_default=LessonStatus.DRAFT.value,
    )
    material_url: Mapped[str | None] = mapped_column(String(500))

    course: Mapped[Course] = relationship(back_populates="lessons")

    def __repr__(self) -> str:
        return f"<Lesson {self.lesson_order} - {self.title}>"
