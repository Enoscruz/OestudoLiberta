"""Testes do fluxo de pagamento: checkout, webhook idempotente e liberação de acesso."""

import hashlib
import hmac
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import PurchaseStatus
from app.integrations import firebase, mercado_pago
from app.integrations.firebase import FirebaseIdentity
from app.integrations.mercado_pago import PaymentInfo, Preference
from app.models.commerce import Enrollment, Purchase
from app.models.system import WebhookEvent

ADMIN_EMAIL = "admin.pagamentos@oestudoliberta.test"
ADMIN_TOKEN = "tok-admin-pagamentos"
STUDENT_EMAIL = "aluno.pagamentos@oestudoliberta.test"
STUDENT_TOKEN = "tok-aluno-pagamentos"

WEBHOOK_PATH = "/api/v1/webhooks/mercadopago"


def _identity(uid: str, email: str) -> FirebaseIdentity:
    return FirebaseIdentity(uid=uid, email=email, email_verified=True, name="Nome Teste")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_tokens(monkeypatch) -> None:
    """Registra o administrador de bootstrap e o aluno no verificador de tokens."""
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    tokens = {
        ADMIN_TOKEN: _identity("uid-admin-pagamentos", ADMIN_EMAIL),
        STUDENT_TOKEN: _identity("uid-aluno-pagamentos", STUDENT_EMAIL),
    }

    def fake_verify(id_token: str) -> FirebaseIdentity:
        if id_token not in tokens:
            raise firebase.InvalidTokenError("token desconhecido")
        return tokens[id_token]

    monkeypatch.setattr(firebase, "verify_id_token", fake_verify)


def _published_course(
    client: TestClient, admin: dict[str, str], *, title: str = "Python", price: str = "199.90"
) -> int:
    """Cria um curso publicado com uma aula publicada."""
    category = client.post(
        "/api/v1/categories", json={"name": f"Categoria {title}"}, headers=admin
    )
    assert category.status_code == 201
    course = client.post(
        "/api/v1/courses",
        json={"category_id": category.json()["id"], "title": title, "price": price},
        headers=admin,
    )
    assert course.status_code == 201
    course_id = course.json()["id"]

    lesson = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Introdução", "status": "PUBLISHED"},
        headers=admin,
    )
    assert lesson.status_code == 201

    published = client.post(f"/api/v1/courses/{course_id}/publish", headers=admin)
    assert published.status_code == 200
    return course_id


def _student_id(client: TestClient, student: dict[str, str]) -> int:
    response = client.get("/api/v1/auth/me", headers=student)
    assert response.status_code == 200
    return response.json()["id"]


def _fake_preference(**_: object) -> Preference:
    return Preference(id="pref-1", init_point="https://www.mercadopago.com.br/checkout/v1/redirect")


def _payment_info(
    *,
    payment_id: str = "pay-1",
    status: str = "approved",
    amount: Decimal = Decimal("199.90"),
    external_reference: str | None,
) -> PaymentInfo:
    return PaymentInfo(
        id=payment_id,
        status=status,
        status_detail=None,
        amount=amount,
        external_reference=external_reference,
        metadata={},
    )


def _notify(
    client: TestClient,
    *,
    payment_id: str = "pay-1",
    notification_id: int = 9001,
    headers: dict[str, str] | None = None,
) -> object:
    """Envia a notificação como o Mercado Pago faz: id no corpo e na query."""
    return client.post(
        f"{WEBHOOK_PATH}?data.id={payment_id}&type=payment",
        json={
            "id": notification_id,
            "type": "payment",
            "action": "payment.updated",
            "data": {"id": payment_id},
        },
        headers=headers or {},
    )


def _signature(*, secret: str, data_id: str, request_id: str, ts: str) -> str:
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={digest}"


def _checkout(client: TestClient, student: dict[str, str], course_id: int) -> dict:
    response = client.post(
        "/api/v1/purchases", json={"course_id": course_id}, headers=student
    )
    assert response.status_code == 201, response.text
    return response.json()


def _webhook_events(db_session: Session) -> int:
    return db_session.execute(select(func.count()).select_from(WebhookEvent)).scalar_one()


def _enrollment_status(db_session: Session, *, user_id: int, course_id: int) -> str | None:
    enrollment = db_session.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id, Enrollment.course_id == course_id
        )
    ).scalar_one_or_none()
    return enrollment.status.value if enrollment else None


# ── Checkout ─────────────────────────────────────────────────────────────


def test_checkout_exige_autenticacao(client: TestClient) -> None:
    response = client.post("/api/v1/purchases", json={"course_id": 1})

    assert response.status_code == 401


def test_checkout_de_curso_inexistente_retorna_404(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)

    response = client.post(
        "/api/v1/purchases", json={"course_id": 4242}, headers=_auth(STUDENT_TOKEN)
    )

    assert response.status_code == 404


def test_checkout_de_curso_em_rascunho_retorna_404(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    category = client.post("/api/v1/categories", json={"name": "Rascunho"}, headers=admin)
    course = client.post(
        "/api/v1/courses",
        json={"category_id": category.json()["id"], "title": "Oculto", "price": "50.00"},
        headers=admin,
    )

    response = client.post(
        "/api/v1/purchases",
        json={"course_id": course.json()["id"]},
        headers=_auth(STUDENT_TOKEN),
    )

    assert response.status_code == 404


def test_checkout_cria_compra_e_devolve_checkout(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    course_id = _published_course(client, _auth(ADMIN_TOKEN))
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    body = _checkout(client, _auth(STUDENT_TOKEN), course_id)

    assert body["requires_payment"] is True
    assert body["status"] == "PENDING"
    assert body["amount"] == "199.90"
    assert body["init_point"].startswith("https://www.mercadopago.com.br/")

    purchase = db_session.get(Purchase, body["purchase_id"])
    assert purchase is not None
    assert purchase.course_id == course_id
    assert purchase.status is PurchaseStatus.PENDING


def test_checkout_de_curso_ja_adquirido_retorna_409(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    user_id = _student_id(client, student)

    purchase = Purchase(
        user_id=user_id,
        course_id=course_id,
        total_amount=Decimal("199.90"),
        status=PurchaseStatus.PAID,
    )
    db_session.add(purchase)
    db_session.flush()
    db_session.add(
        Enrollment(user_id=user_id, course_id=course_id, purchase_id=purchase.id)
    )
    db_session.flush()

    response = client.post(
        "/api/v1/purchases", json={"course_id": course_id}, headers=student
    )

    assert response.status_code == 409


def test_checkout_sem_mercado_pago_configurado_retorna_503(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    course_id = _published_course(client, _auth(ADMIN_TOKEN))

    def _raise(**_: object) -> Preference:
        raise mercado_pago.MercadoPagoNotConfiguredError("sem credenciais")

    monkeypatch.setattr(mercado_pago, "create_preference", _raise)

    response = client.post(
        "/api/v1/purchases", json={"course_id": course_id}, headers=_auth(STUDENT_TOKEN)
    )

    assert response.status_code == 503


def test_checkout_de_curso_gratuito_libera_acesso(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin, title="Gratuito", price="0.00")

    body = _checkout(client, student, course_id)

    assert body["requires_payment"] is False
    assert body["init_point"] is None
    assert body["status"] == "PAID"

    my_courses = client.get("/api/v1/me/courses", headers=student)
    assert [course["id"] for course in my_courses.json()] == [course_id]


# ── Webhook ──────────────────────────────────────────────────────────────


def test_webhook_aprovado_libera_acesso(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    user_id = _student_id(client, student)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(external_reference=str(purchase_id)),
    )

    response = _notify(client)

    assert response.status_code == 200
    assert response.json() == {"status": "processed"}

    db_session.expire_all()
    purchase = db_session.get(Purchase, purchase_id)
    assert purchase is not None
    assert purchase.status is PurchaseStatus.PAID
    assert _enrollment_status(db_session, user_id=user_id, course_id=course_id) == "ACTIVE"

    my_courses = client.get("/api/v1/me/courses", headers=student)
    assert [course["id"] for course in my_courses.json()] == [course_id]


def test_webhook_reenviado_e_idempotente(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    user_id = _student_id(client, student)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    payments = {"pay-1": _payment_info(external_reference=str(purchase_id))}
    monkeypatch.setattr(mercado_pago, "get_payment", lambda payment_id: payments[payment_id])

    first = _notify(client)
    second = _notify(client)

    assert first.json() == {"status": "processed"}
    assert second.json() == {"status": "duplicate"}

    db_session.expire_all()
    assert _webhook_events(db_session) == 1
    enrollments = db_session.execute(select(func.count()).select_from(Enrollment)).scalar_one()
    assert enrollments == 1
    assert _enrollment_status(db_session, user_id=user_id, course_id=course_id) == "ACTIVE"


def test_webhook_com_valor_divergente_nao_libera(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    user_id = _student_id(client, student)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(
            amount=Decimal("1.00"), external_reference=str(purchase_id)
        ),
    )

    response = _notify(client)

    assert response.json() == {"status": "mismatch"}

    db_session.expire_all()
    purchase = db_session.get(Purchase, purchase_id)
    assert purchase is not None
    assert purchase.status is PurchaseStatus.PENDING
    assert _enrollment_status(db_session, user_id=user_id, course_id=course_id) is None


def test_webhook_recusado_marca_compra_como_falha(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(
            status="rejected", external_reference=str(purchase_id)
        ),
    )

    response = _notify(client)

    assert response.json() == {"status": "processed"}

    db_session.expire_all()
    purchase = db_session.get(Purchase, purchase_id)
    assert purchase is not None
    assert purchase.status is PurchaseStatus.FAILED


def test_webhook_de_estorno_revoga_acesso(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    user_id = _student_id(client, student)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(external_reference=str(purchase_id)),
    )
    _notify(client, notification_id=9001)

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(
            status="refunded", external_reference=str(purchase_id)
        ),
    )
    _notify(client, notification_id=9002)

    db_session.expire_all()
    purchase = db_session.get(Purchase, purchase_id)
    assert purchase is not None
    assert purchase.status is PurchaseStatus.REFUNDED
    assert _enrollment_status(db_session, user_id=user_id, course_id=course_id) == "REVOKED"

    my_courses = client.get("/api/v1/me/courses", headers=student)
    assert my_courses.json() == []


def test_webhook_de_compra_desconhecida_e_ignorado(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(external_reference="999999"),
    )

    response = _notify(client)

    assert response.json() == {"status": "ignored"}
    db_session.expire_all()
    assert _webhook_events(db_session) == 1


def test_webhook_com_assinatura_invalida_retorna_403(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    monkeypatch.setattr(get_settings(), "mercado_pago_webhook_secret", "segredo-de-teste")

    response = _notify(
        client, headers={"x-signature": "ts=1,v1=assinatura-errada", "x-request-id": "req-1"}
    )

    assert response.status_code == 403


def test_webhook_com_assinatura_valida_e_aceito(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id = _published_course(client, admin)
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    purchase_id = _checkout(client, student, course_id)["purchase_id"]

    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(external_reference=str(purchase_id)),
    )
    monkeypatch.setattr(get_settings(), "mercado_pago_webhook_secret", "segredo-de-teste")

    response = _notify(
        client,
        headers={
            "x-signature": _signature(
                secret="segredo-de-teste", data_id="pay-1", request_id="req-1", ts="1700000000"
            ),
            "x-request-id": "req-1",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "processed"}


# ── Histórico ────────────────────────────────────────────────────────────


def test_minhas_compras_lista_em_ordem_decrescente(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    first_course = _published_course(client, admin, title="Python")
    second_course = _published_course(client, admin, title="Django")
    monkeypatch.setattr(mercado_pago, "create_preference", _fake_preference)

    _checkout(client, student, first_course)
    _checkout(client, student, second_course)

    response = client.get("/api/v1/purchases", headers=student)

    assert response.status_code == 200
    body = response.json()
    assert [purchase["course_title"] for purchase in body] == ["Django", "Python"]
    assert all(purchase["status"] == "PENDING" for purchase in body)


def test_minhas_compras_de_outro_aluno_nao_aparecem(
    client: TestClient, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    response = client.get("/api/v1/purchases", headers=_auth(STUDENT_TOKEN))

    assert response.status_code == 200
    assert response.json() == []


def test_webhook_expirado_nao_afeta_o_historico(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    """Um evento sem pagamento associado não cria compra nem matrícula."""
    _setup_tokens(monkeypatch)
    monkeypatch.setattr(
        mercado_pago,
        "get_payment",
        lambda payment_id: _payment_info(status="approved", external_reference=None),
    )

    response = _notify(client)

    assert response.json() == {"status": "ignored"}
    db_session.expire_all()
    revenues = db_session.execute(select(func.count()).select_from(Purchase)).scalar_one()
    assert revenues == 0
