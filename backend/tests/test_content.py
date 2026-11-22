"""Testes de gestão de conteúdo: categorias, cursos, aulas e upload de vídeo."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations import cloudflare_stream, firebase
from app.integrations.cloudflare_stream import DirectUpload
from app.integrations.firebase import FirebaseIdentity

ADMIN_EMAIL = "admin.conteudo@oestudoliberta.test"
STUDENT_EMAIL = "aluno.conteudo@oestudoliberta.test"


def _identity(uid: str, email: str) -> FirebaseIdentity:
    return FirebaseIdentity(uid=uid, email=email, email_verified=True, name="Nome Teste")


def _patch_tokens(monkeypatch, tokens: dict[str, FirebaseIdentity]) -> None:
    def fake_verify(id_token: str) -> FirebaseIdentity:
        if id_token not in tokens:
            raise firebase.InvalidTokenError("token desconhecido")
        return tokens[id_token]

    monkeypatch.setattr(firebase, "verify_id_token", fake_verify)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(monkeypatch) -> dict[str, str]:
    """Prepara um administrador autenticado e devolve o cabeçalho de autorização."""
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    _patch_tokens(
        monkeypatch, {"tok-admin": _identity("uid-admin-conteudo", ADMIN_EMAIL)}
    )
    return _auth("tok-admin")


def _create_category(client: TestClient, headers: dict[str, str], name: str = "Programação") -> int:
    response = client.post("/api/v1/categories", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def _create_course(
    client: TestClient, headers: dict[str, str], category_id: int, title: str = "Python"
) -> int:
    response = client.post(
        "/api/v1/courses",
        json={"category_id": category_id, "title": title, "price": "199.90"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_student_nao_gerencia_categorias(client: TestClient, monkeypatch) -> None:
    _patch_tokens(monkeypatch, {"tok-aluno": _identity("uid-aluno-conteudo", STUDENT_EMAIL)})

    response = client.post(
        "/api/v1/categories", json={"name": "Proibida"}, headers=_auth("tok-aluno")
    )

    assert response.status_code == 403


def test_cria_e_lista_categorias(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)

    _create_category(client, headers, "Marketing")

    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    assert "Marketing" in [c["name"] for c in response.json()]


def test_categoria_duplicada_retorna_409(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    _create_category(client, headers, "Design")

    response = client.post("/api/v1/categories", json={"name": "Design"}, headers=headers)

    assert response.status_code == 409


def test_remove_categoria_com_cursos_retorna_409(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Dados")
    _create_course(client, headers, category_id, "Análise de Dados")

    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers)

    assert response.status_code == 409


def test_curso_com_categoria_inexistente_retorna_422(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)

    response = client.post(
        "/api/v1/courses",
        json={"category_id": 999999, "title": "Fantasma"},
        headers=headers,
    )

    assert response.status_code == 422


def test_publicar_curso_sem_aula_publicada_retorna_422(
    client: TestClient, monkeypatch
) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Segurança")
    course_id = _create_course(client, headers, category_id, "AppSec")

    response = client.post(f"/api/v1/courses/{course_id}/publish", headers=headers)

    assert response.status_code == 422


def test_fluxo_completo_publica_curso(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Cloud")
    course_id = _create_course(client, headers, category_id, "AWS")

    lesson = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Introdução", "status": "PUBLISHED"},
        headers=headers,
    )
    assert lesson.status_code == 201
    assert lesson.json()["lesson_order"] == 1

    response = client.post(f"/api/v1/courses/{course_id}/publish", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PUBLISHED"
    assert body["published_at"] is not None


def test_ordem_de_aula_ocupada_retorna_409(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Mobile")
    course_id = _create_course(client, headers, category_id, "Android")
    client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Aula 1", "lesson_order": 1},
        headers=headers,
    )

    response = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Conflito", "lesson_order": 1},
        headers=headers,
    )

    assert response.status_code == 409


def test_upload_de_video_associa_uid(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Frontend")
    course_id = _create_course(client, headers, category_id, "React")
    lesson_id = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Componentes"},
        headers=headers,
    ).json()["id"]

    monkeypatch.setattr(
        cloudflare_stream,
        "create_direct_upload",
        lambda *, max_duration_seconds: DirectUpload(
            uid="vid-abc123", upload_url="https://upload.cloudflare.test/vid-abc123"
        ),
    )

    response = client.post(f"/api/v1/lessons/{lesson_id}/video-upload", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["video_uid"] == "vid-abc123"
    assert body["upload_url"] == "https://upload.cloudflare.test/vid-abc123"
    assert body["max_duration_seconds"] == 900

    detail = client.get(f"/api/v1/lessons/{lesson_id}", headers=headers).json()
    assert detail["video_uid"] == "vid-abc123"


def test_upload_de_video_sem_configuracao_retorna_503(
    client: TestClient, monkeypatch
) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Backend")
    course_id = _create_course(client, headers, category_id, "Django")
    lesson_id = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Models"},
        headers=headers,
    ).json()["id"]

    def _raise(**_: int) -> DirectUpload:
        raise cloudflare_stream.CloudflareNotConfiguredError("sem credenciais")

    monkeypatch.setattr(cloudflare_stream, "create_direct_upload", _raise)

    response = client.post(f"/api/v1/lessons/{lesson_id}/video-upload", headers=headers)

    assert response.status_code == 503
