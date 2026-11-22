"""Acesso a dados de categorias."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import CategoryStatus
from app.models.content import Category


def list_all(db: Session) -> list[Category]:
    """Lista as categorias em ordem alfabética."""
    return list(db.execute(select(Category).order_by(Category.name)).scalars())


def list_active(db: Session) -> list[Category]:
    """Lista apenas as categorias ativas, em ordem alfabética."""
    stmt = (
        select(Category)
        .where(Category.status == CategoryStatus.ACTIVE)
        .order_by(Category.name)
    )
    return list(db.execute(stmt).scalars())


def get(db: Session, category_id: int) -> Category | None:
    """Busca uma categoria pela chave primária."""
    return db.get(Category, category_id)


def get_by_name(db: Session, name: str) -> Category | None:
    """Busca uma categoria pelo nome."""
    return db.execute(select(Category).where(Category.name == name)).scalar_one_or_none()


def create(
    db: Session, *, name: str, description: str | None, status: CategoryStatus
) -> Category:
    """Insere uma nova categoria."""
    category = Category(name=name, description=description, status=status)
    db.add(category)
    return category
