"""Testes do catálogo público: vitrine de cursos publicados e categorias ativas."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations import firebase
from app.integrations.firebase import FirebaseIdentity

ADMIN_EMAIL = "admin.catalogo@oestudoliberta.test"


def _admin_headers(monkeypatch) -> dict[str, str]:
    """Prepara um administrador autenticado e devolve o cabeçalho de autorização."""
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)

    def fake_verify(id_token: str) -> FirebaseIdentity:
        if id_token != "tok-admin":
            raise firebase.InvalidTokenError("token desconhecido")
        return FirebaseIdentity(
            uid="uid-admin-catalogo", email=ADMIN_EMAIL, email_verified=True, name="Admin"
        )

    monkeypatch.setattr(firebase, "verify_id_token", fake_verify)
    return {"Authorization": "Bearer tok-admin"}


def _create_category(
    client: TestClient, headers: dict[str, str], name: str, status: str = "ACTIVE"
) -> int:
    response = client.post(
        "/api/v1/categories", json={"name": name, "status": status}, headers=headers
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_course(
    client: TestClient, headers: dict[str, str], category_id: int, title: str
) -> int:
    response = client.post(
        "/api/v1/courses",
        json={"category_id": category_id, "title": title, "price": "99.90"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _publish_course(client: TestClient, headers: dict[str, str], course_id: int) -> None:
    """Cria uma aula publicada e publica o curso."""
    client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Aula publicada", "status": "PUBLISHED"},
        headers=headers,
    )
    response = client.post(f"/api/v1/courses/{course_id}/publish", headers=headers)
    assert response.status_code == 200


def test_catalogo_nao_exige_autenticacao(client: TestClient) -> None:
    response = client.get("/api/v1/catalog/courses")

    assert response.status_code == 200
    assert response.json() == []


def test_curso_rascunho_nao_aparece_no_catalogo(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Rascunhos")
    _create_course(client, headers, category_id, "Curso em rascunho")

    response = client.get("/api/v1/catalog/courses")

    assert response.status_code == 200
    assert response.json() == []


def test_catalogo_lista_curso_publicado_com_categoria_e_aulas(
    client: TestClient, monkeypatch
) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Programação")
    course_id = _create_course(client, headers, category_id, "Python Essencial")
    _publish_course(client, headers, course_id)

    response = client.get("/api/v1/catalog/courses")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Python Essencial"
    assert body[0]["category_name"] == "Programação"
    assert body[0]["lessons_count"] == 1
    assert body[0]["published_at"] is not None


def test_catalogo_filtra_por_categoria_e_titulo(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    programacao = _create_category(client, headers, "Programação")
    marketing = _create_category(client, headers, "Marketing")
    _publish_course(client, headers, _create_course(client, headers, programacao, "Python Web"))
    _publish_course(client, headers, _create_course(client, headers, programacao, "FastAPI"))
    _publish_course(client, headers, _create_course(client, headers, marketing, "Tráfego Pago"))

    por_categoria = client.get(f"/api/v1/catalog/courses?category_id={programacao}")
    por_busca = client.get("/api/v1/catalog/courses?search=fast")

    assert {c["title"] for c in por_categoria.json()} == {"Python Web", "FastAPI"}
    assert [c["title"] for c in por_busca.json()] == ["FastAPI"]


def test_detalhe_do_curso_expoe_apenas_aulas_publicadas(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Segurança")
    course_id = _create_course(client, headers, category_id, "AppSec")
    client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Rascunho interno", "lesson_order": 1},
        headers=headers,
    )
    client.post(
        "/api/v1/lessons",
        json={
            "course_id": course_id,
            "title": "Aula pública",
            "lesson_order": 2,
            "status": "PUBLISHED",
            "duration_seconds": 300,
        },
        headers=headers,
    )
    assert client.post(f"/api/v1/courses/{course_id}/publish", headers=headers).status_code == 200

    response = client.get(f"/api/v1/catalog/courses/{course_id}")

    assert response.status_code == 200
    body = response.json()
    assert [lesson["title"] for lesson in body["lessons"]] == ["Aula pública"]
    assert body["lessons"][0]["duration_seconds"] == 300
    assert "video_uid" not in body["lessons"][0]
    assert body["lessons_count"] == 1


def test_detalhe_de_curso_nao_publicado_retorna_404(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    category_id = _create_category(client, headers, "Design")
    course_id = _create_course(client, headers, category_id, "UI Kit")

    response = client.get(f"/api/v1/catalog/courses/{course_id}")

    assert response.status_code == 404


def test_catalogo_lista_apenas_categorias_ativas(client: TestClient, monkeypatch) -> None:
    headers = _admin_headers(monkeypatch)
    _create_category(client, headers, "Ativa")
    _create_category(client, headers, "Inativa", status="INACTIVE")

    response = client.get("/api/v1/catalog/categories")

    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Ativa"]
