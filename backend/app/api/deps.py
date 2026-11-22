"""Dependências de autenticação e autorização."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import RoleName
from app.core.exceptions import ServiceUnavailableError
from app.integrations import firebase
from app.models.user import User
from app.services import auth_service

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Valida o ID Token do Firebase e devolve o usuário sincronizado."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais de autenticação ausentes.",
            headers=_UNAUTHORIZED_HEADERS,
        )

    try:
        identity = firebase.verify_id_token(credentials.credentials)
    except firebase.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido ou expirado.",
            headers=_UNAUTHORIZED_HEADERS,
        ) from None
    except firebase.FirebaseNotConfiguredError as exc:
        raise ServiceUnavailableError("Autenticação não configurada no servidor.") from exc

    return auth_service.sync_user(db, identity)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_verified_email(user: CurrentUser) -> User:
    """Exige que o e-mail esteja confirmado no Firebase."""
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirmação de e-mail obrigatória.",
        )
    return user


VerifiedUser = Annotated[User, Depends(require_verified_email)]


def require_admin(user: VerifiedUser) -> User:
    """Restringe o acesso a administradores."""
    if user.role.name != RoleName.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]
