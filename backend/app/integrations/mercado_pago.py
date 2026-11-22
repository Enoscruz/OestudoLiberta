"""Integração com o Mercado Pago (Checkout Pro).

Responsabilidade única: criar a preferência de pagamento, **reconsultar** um
pagamento na origem e validar a assinatura dos webhooks. Nenhum dado de cartão
passa por aqui — o aluno paga na página do Mercado Pago e voltamos a consultar
o pagamento antes de liberar qualquer acesso.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings

_API_BASE = "https://api.mercadopago.com"
_TIMEOUT_SECONDS = 15.0


class MercadoPagoNotConfiguredError(RuntimeError):
    """Credenciais do Mercado Pago ausentes no ambiente."""


class MercadoPagoError(RuntimeError):
    """O Mercado Pago respondeu com erro ou em formato inesperado."""


def _access_token() -> str:
    token = get_settings().mercado_pago_access_token
    if not token:
        raise MercadoPagoNotConfiguredError("MERCADO_PAGO_ACCESS_TOKEN não configurado.")
    return token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_access_token()}"}


@dataclass(frozen=True)
class Preference:
    """Preferência de pagamento e o endereço do checkout."""

    id: str
    init_point: str


def create_preference(
    *,
    purchase_id: int,
    course_id: int,
    title: str,
    amount: Decimal,
    description: str | None,
    payer_email: str | None,
    back_urls: dict[str, str],
    notification_url: str | None,
) -> Preference:
    """Cria uma preferência de Checkout Pro e devolve o endereço de pagamento.

    O ``external_reference`` guarda o id da compra: é por ele que o webhook
    reencontra o registro local. O ``metadata`` reforça o vínculo com o curso.
    """
    payload: dict[str, Any] = {
        "items": [
            {
                "id": str(course_id),
                "title": title,
                "description": description or title,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(amount),
            }
        ],
        "external_reference": str(purchase_id),
        "metadata": {"purchase_id": purchase_id, "course_id": course_id},
        "back_urls": back_urls,
    }
    if payer_email:
        payload["payer"] = {"email": payer_email}
    if notification_url:
        payload["notification_url"] = notification_url
    # O Mercado Pago só aceita `auto_return` com `back_urls.success` em HTTPS.
    if back_urls.get("success", "").startswith("https://"):
        payload["auto_return"] = "approved"

    try:
        response = httpx.post(
            f"{_API_BASE}/checkout/preferences",
            json=payload,
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise MercadoPagoError(f"Falha de comunicação com o Mercado Pago: {exc}") from exc

    if response.status_code >= 400:
        raise MercadoPagoError(
            f"Mercado Pago respondeu com status {response.status_code} ao criar a preferência."
        )

    body = response.json()
    init_point = body.get("init_point") or body.get("sandbox_init_point")
    preference_id = body.get("id")
    if not preference_id or not init_point:
        raise MercadoPagoError("Resposta inesperada do Mercado Pago ao criar a preferência.")

    return Preference(id=str(preference_id), init_point=init_point)


@dataclass(frozen=True)
class PaymentInfo:
    """Situação de um pagamento, conforme registrada no Mercado Pago."""

    id: str
    status: str
    status_detail: str | None
    amount: Decimal
    external_reference: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


def get_payment(payment_id: str) -> PaymentInfo:
    """Reconsulta um pagamento na origem.

    Esta consulta é obrigatória: nunca confiamos no conteúdo do webhook para
    decidir se um pagamento foi aprovado.
    """
    try:
        response = httpx.get(
            f"{_API_BASE}/v1/payments/{payment_id}",
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise MercadoPagoError(f"Falha de comunicação com o Mercado Pago: {exc}") from exc

    if response.status_code >= 400:
        raise MercadoPagoError(
            f"Mercado Pago respondeu com status {response.status_code} ao consultar o pagamento."
        )

    body = response.json()
    payment_id_result = body.get("id")
    status = body.get("status")
    if payment_id_result is None or not status:
        raise MercadoPagoError("Resposta inesperada do Mercado Pago ao consultar o pagamento.")

    metadata = body.get("metadata")
    return PaymentInfo(
        id=str(payment_id_result),
        status=str(status),
        status_detail=body.get("status_detail"),
        amount=Decimal(str(body.get("transaction_amount") or "0")),
        external_reference=body.get("external_reference"),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def verify_webhook_signature(
    *,
    x_signature: str | None,
    x_request_id: str | None,
    data_id: str | None,
    secret: str,
) -> bool:
    """Valida o cabeçalho ``x-signature`` de uma notificação.

    O manifesto é montado conforme a documentação do Mercado Pago:
    ``id:<data.id>;request-id:<x-request-id>;ts:<ts>;`` e assinado com
    HMAC-SHA256 usando a chave secreta do webhook.
    """
    if not x_signature or not data_id:
        return False

    parts = {
        key.strip(): value.strip()
        for key, _, value in (item.partition("=") for item in x_signature.split(","))
        if key
    }
    ts = parts.get("ts")
    received = parts.get("v1")
    if not ts or not received:
        return False

    manifest = f"id:{data_id.lower()};request-id:{x_request_id or ''};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
