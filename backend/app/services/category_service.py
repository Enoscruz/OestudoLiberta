"""Regras de negócio de categorias."""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.content import Category
from app.models.user import User
from app.repositories import audit_repository, category_repository, course_repository
from app.schemas.category import CategoryCreate, CategoryUpdate

_ENTITY = "category"


def list_categories(db: Session) -> list[Category]:
    """Lista todas as categorias."""
    return category_repository.list_all(db)


def get_category(db: Session, category_id: int) -> Category:
    """Busca uma categoria, exigindo que ela exista."""
    category = category_repository.get(db, category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada.")
    return category


def create_category(db: Session, actor: User, data: CategoryCreate) -> Category:
    """Cria uma categoria, impedindo nomes duplicados."""
    if category_repository.get_by_name(db, data.name) is not None:
        raise ConflictError("Já existe uma categoria com este nome.")

    category = category_repository.create(
        db, name=data.name, description=data.description, status=data.status
    )
    db.flush()
    audit_repository.record(
        db, user_id=actor.id, action="category.create", entity=_ENTITY, entity_id=category.id
    )
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, actor: User, category_id: int, data: CategoryUpdate
) -> Category:
    """Atualiza uma categoria existente."""
    category = get_category(db, category_id)
    changes = data.model_dump(exclude_unset=True)

    new_name = changes.get("name")
    if new_name is not None and new_name != category.name:
        existing = category_repository.get_by_name(db, new_name)
        if existing is not None:
            raise ConflictError("Já existe uma categoria com este nome.")

    for field, value in changes.items():
        setattr(category, field, value)

    audit_repository.record(
        db, user_id=actor.id, action="category.update", entity=_ENTITY, entity_id=category.id
    )
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, actor: User, category_id: int) -> None:
    """Remove uma categoria que não possua cursos vinculados."""
    category = get_category(db, category_id)
    if course_repository.count_by_category(db, category_id) > 0:
        raise ConflictError("Não é possível remover uma categoria que possui cursos.")

    audit_repository.record(
        db, user_id=actor.id, action="category.delete", entity=_ENTITY, entity_id=category.id
    )
    db.delete(category)
    db.commit()
