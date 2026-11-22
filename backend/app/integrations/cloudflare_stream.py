"""Integração com a Cloudflare Stream.

Responsabilidade única: negociar uploads diretos de vídeo e emitir tokens
temporários de reprodução. O arquivo nunca passa pelo backend — o frontend
envia direto para a Cloudflare usando uma URL de upload de uso único, e apenas
o ``uid`` do vídeo é guardado no banco.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import get_settings

_API_BASE = "https://api.cloudflare.com/client/v4"
_TIMEOUT_SECONDS = 15.0

# O endpoint ``/token`` emite tokens válidos por uma hora.
_PLAYBACK_TOKEN_TTL = timedelta(hours=1)


class CloudflareNotConfiguredError(RuntimeError):
    """Credenciais da Cloudflare Stream ausentes no ambiente."""


class CloudflareStreamError(RuntimeError):
    """A Cloudflare Stream respondeu com erro ou em formato inesperado."""


@dataclass(frozen=True)
class DirectUpload:
    """URL de upload de uso único e o ``uid`` do vídeo resultante."""

    uid: str
    upload_url: str


def create_direct_upload(*, max_duration_seconds: int) -> DirectUpload:
    """Cria um upload direto na Cloudflare Stream.

    Devolve a URL para a qual o frontend deve enviar o arquivo. O token da API
    nunca é exposto ao cliente.
    """
    settings = get_settings()
    if not settings.cloudflare_account_id or not settings.cloudflare_stream_api_token:
        raise CloudflareNotConfiguredError(
            "CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_STREAM_API_TOKEN não configurados."
        )

    url = f"{_API_BASE}/accounts/{settings.cloudflare_account_id}/stream/direct_upload"
    headers = {"Authorization": f"Bearer {settings.cloudflare_stream_api_token}"}
    payload = {"maxDurationSeconds": max_duration_seconds}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise CloudflareStreamError(f"Falha de comunicação com a Cloudflare: {exc}") from exc

    if response.status_code >= 400:
        raise CloudflareStreamError(
            f"Cloudflare Stream respondeu com status {response.status_code}."
        )

    body = response.json()
    result = body.get("result") or {}
    uid = result.get("uid")
    upload_url = result.get("uploadURL")
    if not body.get("success") or not uid or not upload_url:
        raise CloudflareStreamError("Resposta inesperada da Cloudflare Stream.")

    return DirectUpload(uid=uid, upload_url=upload_url)


@dataclass(frozen=True)
class Playback:
    """Token temporário de reprodução e as URLs prontas para o player."""

    token: str
    iframe_url: str
    hls_url: str
    expires_at: datetime


def create_playback(*, video_uid: str) -> Playback:
    """Emite um token temporário de reprodução para o vídeo informado.

    O vídeo nunca é exposto publicamente: o frontend recebe apenas as URLs
    assinadas, válidas por uma hora.
    """
    settings = get_settings()
    if not settings.cloudflare_account_id or not settings.cloudflare_stream_api_token:
        raise CloudflareNotConfiguredError(
            "CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_STREAM_API_TOKEN não configurados."
        )
    if not settings.cloudflare_stream_customer_code:
        raise CloudflareNotConfiguredError(
            "CLOUDFLARE_STREAM_CUSTOMER_CODE não configurado."
        )

    url = f"{_API_BASE}/accounts/{settings.cloudflare_account_id}/stream/{video_uid}/token"
    headers = {"Authorization": f"Bearer {settings.cloudflare_stream_api_token}"}

    try:
        response = httpx.post(url, headers=headers, timeout=_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise CloudflareStreamError(f"Falha de comunicação com a Cloudflare: {exc}") from exc

    if response.status_code >= 400:
        raise CloudflareStreamError(
            f"Cloudflare Stream respondeu com status {response.status_code}."
        )

    body = response.json()
    token = (body.get("result") or {}).get("token")
    if not body.get("success") or not token:
        raise CloudflareStreamError("Resposta inesperada da Cloudflare Stream.")

    base = (
        f"https://customer-{settings.cloudflare_stream_customer_code}"
        f".cloudflarestream.com/{token}"
    )
    return Playback(
        token=token,
        iframe_url=f"{base}/iframe",
        hls_url=f"{base}/manifest/video.m3u8",
        expires_at=datetime.now(UTC) + _PLAYBACK_TOKEN_TTL,
    )
