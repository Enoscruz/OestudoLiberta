"""seed roles

Insere os papéis base (ADMIN e STUDENT) de forma idempotente, garantindo que
existam em qualquer ambiente.

Revision ID: 74efadc0de0e
Revises: 805089c00163
Create Date: 2026-11-01 22:37:33.659419

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Identificadores de revisão, usados pelo Alembic.
revision: str = '74efadc0de0e'
down_revision: str | None = '805089c00163'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLES = [
    {"name": "ADMIN", "description": "Administrador da plataforma"},
    {"name": "STUDENT", "description": "Aluno da plataforma"},
]


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO roles (name, description) "
            "VALUES (:name, :description) "
            "ON CONFLICT (name) DO NOTHING"
        ),
        _ROLES,
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM roles WHERE name IN ('ADMIN', 'STUDENT')")
    )
