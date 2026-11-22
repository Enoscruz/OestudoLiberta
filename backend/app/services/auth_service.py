"""Regras de autenticação: sincronização do usuário do Firebase com o PostgreSQL."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import RoleName
from app.core.exceptions import ForbiddenError
from app.integrations.firebase import FirebaseIdentity
from app.models.user import User
from app.repositories import role_repository, user_repository


class AuthError(ForbiddenError):
    """Falha de negócio durante a sincronização do usuário."""


def _resolve_role_name(email: str) -> RoleName:
    """Define o papel inicial: ADMIN apenas para o e-mail de bootstrap."""
    admin_email = (get_settings().admin_bootstrap_email or "").strip().lower()
    if admin_email and email.strip().lower() == admin_email:
        return RoleName.ADMIN
    return RoleName.STUDENT


def _display_name(identity: FirebaseIdentity) -> str:
    if identity.name:
        return identity.name
    return identity.email.split("@")[0] if identity.email else "Aluno"


def _apply_mirrored_fields(user: User, identity: FirebaseIdentity) -> None:
    """Espelha no banco os campos mantidos pelo Firebase."""
    if identity.email_verified:
        user.email_verified = True
    if identity.name:
        user.name = identity.name


def sync_user(db: Session, identity: FirebaseIdentity) -> User:
    """Garante que o usuário autenticado exista no PostgreSQL.

    - Primeiro acesso: cria o usuário (STUDENT, ou ADMIN se for o e-mail de bootstrap).
    - Acessos seguintes: apenas atualiza os campos espelhados do Firebase.
    - Nunca altera o papel de um usuário já existente (nenhum usuário muda o próprio perfil).
    """
    if not identity.email:
        raise AuthError("O provedor de autenticação não informou um e-mail.")

    user = user_repository.get_by_firebase_uid(db, identity.uid)

    if user is None:
        user = user_repository.get_by_email(db, identity.email)
        if user is not None:
            # Conta recriada no Firebase: religa o registro existente ao novo UID.
            user.firebase_uid = identity.uid
        else:
            role = role_repository.get_by_name(db, _resolve_role_name(identity.email))
            if role is None:
                raise AuthError("Papéis base ausentes. Execute as migrações (seed de roles).")
            user = user_repository.create(
                db,
                firebase_uid=identity.uid,
                name=_display_name(identity),
                email=identity.email,
                role_id=role.id,
                email_verified=identity.email_verified,
            )

    _apply_mirrored_fields(user, identity)
    db.commit()
    db.refresh(user)
    return user
