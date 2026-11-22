"""Base declarativa, mixins e utilitários de modelagem."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Identity, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

__all__ = [
    "Base",
    "CreatedAtMixin",
    "IdMixin",
    "TimestampMixin",
    "enum_type",
]


class IdMixin:
    """Chave primária ``bigint`` gerada por IDENTITY."""

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)


class CreatedAtMixin:
    """Instante de criação do registro."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    """Instante de criação e de última atualização do registro."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def enum_type(enum_cls: type[StrEnum], name: str, length: int) -> SAEnum:
    """Cria o tipo de coluna para um enum de domínio.

    Gera ``VARCHAR(length)`` com um ``CHECK`` restringindo os valores aceitos,
    em vez de um enum nativo do PostgreSQL.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
        validate_strings=True,
        values_callable=lambda cls: [member.value for member in cls],
    )
