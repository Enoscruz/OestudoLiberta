"""Testes de autenticação e autorização (Firebase mockado)."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations import firebase
from app.integrations.firebase import FirebaseIdentity

ADMIN_EMAIL = "admin.bootstrap@oestudoliberta.test"
STUDENT_EMAIL = "aluno.teste@oestudoliberta.test"


def _identity(uid: str, email: str, *, verified: bool = True) -> FirebaseIdentity:
    return FirebaseIdentity(uid=uid, email=email, email_verified=verified, name="Nome Teste")


def _patch_tokens(monkeypatch, tokens: dict[str, FirebaseIdentity]) -> None:
    """Intercepta a validação do ID Token para os tokens informados."""

    def fake_verify(id_token: str) -> FirebaseIdentity:
        if id_token not in tokens:
            raise firebase.InvalidTokenError("token desconhecido")
        return tokens[id_token]

    monkeypatch.setattr(firebase, "verify_id_token", fake_verify)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_sem_token_retorna_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_com_token_invalido_retorna_401(client: TestClient, monkeypatch) -> None:
    _patch_tokens(monkeypatch, {})
    response = client.get("/api/v1/auth/me", headers=_auth("token-invalido"))
    assert response.status_code == 401


def test_me_sincroniza_novo_usuario_como_student(client: TestClient, monkeypatch) -> None:
    _patch_tokens(monkeypatch, {"tok-aluno": _identity("uid-aluno", STUDENT_EMAIL)})

    response = client.get("/api/v1/auth/me", headers=_auth("tok-aluno"))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == STUDENT_EMAIL
    assert body["role"]["name"] == "STUDENT"
    assert body["email_verified"] is True


def test_bootstrap_promove_admin_por_email(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    _patch_tokens(monkeypatch, {"tok-admin": _identity("uid-admin", ADMIN_EMAIL)})

    response = client.get("/api/v1/auth/me", headers=_auth("tok-admin"))

    assert response.status_code == 200
    assert response.json()["role"]["name"] == "ADMIN"


def test_email_nao_verificado_bloqueia_area_restrita(client: TestClient, monkeypatch) -> None:
    _patch_tokens(
        monkeypatch,
        {"tok-nao-verificado": _identity("uid-nv", STUDENT_EMAIL, verified=False)},
    )

    response = client.get("/api/v1/users", headers=_auth("tok-nao-verificado"))

    assert response.status_code == 403
    assert "e-mail" in response.json()["detail"].lower()


def test_student_nao_acessa_area_administrativa(client: TestClient, monkeypatch) -> None:
    _patch_tokens(monkeypatch, {"tok-aluno": _identity("uid-aluno", STUDENT_EMAIL)})

    response = client.get("/api/v1/users", headers=_auth("tok-aluno"))

    assert response.status_code == 403
    assert "administradores" in response.json()["detail"].lower()


def test_admin_lista_usuarios(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    _patch_tokens(monkeypatch, {"tok-admin": _identity("uid-admin", ADMIN_EMAIL)})

    response = client.get("/api/v1/users", headers=_auth("tok-admin"))

    assert response.status_code == 200
    emails = [user["email"] for user in response.json()]
    assert ADMIN_EMAIL in emails
