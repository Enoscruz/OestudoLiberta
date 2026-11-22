"""Enumerações de domínio da plataforma.

Cada enum é persistido no banco como ``VARCHAR`` + ``CHECK`` (sem enum nativo do
PostgreSQL), conforme decidido em ``docs/01-architecture.md`` (seção 4.1).
"""

from enum import StrEnum


class RoleName(StrEnum):
    """Perfis de acesso."""

    ADMIN = "ADMIN"
    STUDENT = "STUDENT"


class UserStatus(StrEnum):
    """Situação do usuário na plataforma."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"


class CategoryStatus(StrEnum):
    """Situação da categoria."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CourseStatus(StrEnum):
    """Situação do curso."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class LessonStatus(StrEnum):
    """Situação da aula."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class PurchaseStatus(StrEnum):
    """Situação da compra."""

    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class PaymentStatus(StrEnum):
    """Situação do pagamento."""

    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"


class Gateway(StrEnum):
    """Gateways de pagamento suportados."""

    MERCADO_PAGO = "MERCADO_PAGO"


class EnrollmentStatus(StrEnum):
    """Situação do acesso do aluno ao curso."""

    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class WebhookStatus(StrEnum):
    """Situação de processamento de um evento de gateway."""

    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"
