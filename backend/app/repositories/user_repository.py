"""Acesso a dados de usuários."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User


def get_by_firebase_uid(db: Session, firebase_uid: str) -> User | None:
    """Busca um usuário pelo UID do Firebase."""
    return db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    ).scalar_one_or_none()


def get_by_email(db: Session, email: str) -> User | None:
    """Busca um usuário pelo e-mail, ignorando a caixa."""
    return db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    ).scalar_one_or_none()


def create(
    db: Session,
    *,
    firebase_uid: str,
    name: str,
    email: str,
    role_id: int,
    email_verified: bool,
) -> User:
    """Insere um novo usuário."""
    user = User(
        firebase_uid=firebase_uid,
        name=name,
        email=email,
        role_id=role_id,
        email_verified=email_verified,
    )
    db.add(user)
    return user


def list_all(db: Session) -> list[User]:
    """Lista todos os usuários, do mais recente para o mais antigo."""
    return list(
        db.execute(
            select(User).options(selectinload(User.role)).order_by(User.created_at.desc())
        ).scalars()
    )
