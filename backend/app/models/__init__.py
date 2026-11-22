"""Modelos ORM da plataforma.

Importar todos os modelos aqui garante que o Alembic (autogenerate) os descubra.
"""

from app.models.base import Base
from app.models.commerce import Enrollment, Payment, Purchase
from app.models.content import Category, Course, Lesson
from app.models.learning import LessonProgress
from app.models.system import AuditLog, WebhookEvent
from app.models.user import Role, User

__all__ = [
    "AuditLog",
    "Base",
    "Category",
    "Course",
    "Enrollment",
    "Lesson",
    "LessonProgress",
    "Payment",
    "Purchase",
    "Role",
    "User",
    "WebhookEvent",
]
