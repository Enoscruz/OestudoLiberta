"""Integração com o Firebase Authentication.

Responsabilidade única: validar o ID Token recebido do frontend usando o
Firebase Admin SDK e devolver uma identidade normalizada. Nenhuma regra de
negócio vive aqui.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import REPO_ROOT, get_settings


class FirebaseNotConfiguredError(RuntimeError):
    """O Firebase Admin SDK não está configurado no ambiente."""


class InvalidTokenError(Exception):
    """O ID Token é inválido, expirado ou foi revogado."""


@dataclass(frozen=True)
class FirebaseIdentity:
    """Dados confiáveis extraídos de um ID Token já validado."""

    uid: str
    email: str | None
    email_verified: bool
    name: str | None


def _resolve_credentials_path(raw_path: str) -> Path:
    """Resolve caminhos relativos a partir da raiz do monorepo."""
    path = Path(raw_path)
    return path if path.is_absolute() else REPO_ROOT / path


def _get_app() -> firebase_admin.App:
    """Inicializa (uma única vez) e devolve a app do Firebase Admin."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    settings = get_settings()
    if not settings.firebase_credentials_path:
        raise FirebaseNotConfiguredError(
            "FIREBASE_CREDENTIALS_PATH não configurado no ambiente."
        )

    path = _resolve_credentials_path(settings.firebase_credentials_path)
    if not path.is_file():
        raise FirebaseNotConfiguredError(
            f"Arquivo de credenciais do Firebase não encontrado: {path}"
        )

    credential = credentials.Certificate(str(path))
    options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
    return firebase_admin.initialize_app(credential, options)


def verify_id_token(id_token: str) -> FirebaseIdentity:
    """Valida um ID Token e devolve a identidade do usuário.

    Levanta ``InvalidTokenError`` para tokens inválidos/expirados/revogados e
    ``FirebaseNotConfiguredError`` quando o SDK não está configurado.
    """
    app = _get_app()
    try:
        claims = auth.verify_id_token(id_token, app=app, check_revoked=True)
    except (
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
        auth.CertificateFetchError,
    ) as exc:
        raise InvalidTokenError(str(exc)) from exc

    return FirebaseIdentity(
        uid=claims["uid"],
        email=claims.get("email"),
        email_verified=bool(claims.get("email_verified", False)),
        name=claims.get("name"),
    )
