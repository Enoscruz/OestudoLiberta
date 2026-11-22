"""Testes da área do aluno: meus cursos e reprodução de aulas."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import PurchaseStatus
from app.integrations import cloudflare_stream, firebase
from app.integrations.cloudflare_stream import DirectUpload, Playback
from app.integrations.firebase import FirebaseIdentity
from app.models.commerce import Enrollment, Purchase

ADMIN_EMAIL = "admin.aprendizado@oestudoliberta.test"
ADMIN_TOKEN = "tok-admin-aprendizado"
STUDENT_EMAIL = "aluno.aprendizado@oestudoliberta.test"
STUDENT_TOKEN = "tok-aluno-aprendizado"


def _identity(uid: str, email: str) -> FirebaseIdentity:
    return FirebaseIdentity(uid=uid, email=email, email_verified=True, name="Nome Teste")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_tokens(monkeypatch) -> None:
    """Registra o administrador de bootstrap e o aluno no verificador de tokens."""
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    tokens = {
        ADMIN_TOKEN: _identity("uid-admin-aprendizado", ADMIN_EMAIL),
        STUDENT_TOKEN: _identity("uid-aluno-aprendizado", STUDENT_EMAIL),
    }

    def fake_verify(id_token: str) -> FirebaseIdentity:
        if id_token not in tokens:
            raise firebase.InvalidTokenError("token desconhecido")
        return tokens[id_token]

    monkeypatch.setattr(firebase, "verify_id_token", fake_verify)


def _published_course(
    client: TestClient,
    admin: dict[str, str],
    *,
    title: str = "Python",
    extra_lesson_status: str | None = None,
) -> tuple[int, int, int | None]:
    """Cria um curso publicado com uma aula publicada (e, opcionalmente, uma extra)."""
    category = client.post(
        "/api/v1/categories", json={"name": f"Categoria {title}"}, headers=admin
    )
    assert category.status_code == 201
    course = client.post(
        "/api/v1/courses",
        json={"category_id": category.json()["id"], "title": title, "price": "199.90"},
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

    extra_lesson_id = None
    if extra_lesson_status is not None:
        extra = client.post(
            "/api/v1/lessons",
            json={"course_id": course_id, "title": "Extra", "status": extra_lesson_status},
            headers=admin,
        )
        assert extra.status_code == 201
        extra_lesson_id = extra.json()["id"]

    published = client.post(f"/api/v1/courses/{course_id}/publish", headers=admin)
    assert published.status_code == 200

    return course_id, lesson.json()["id"], extra_lesson_id


def _attach_video(
    client: TestClient,
    monkeypatch,
    admin: dict[str, str],
    lesson_id: int,
    *,
    uid: str,
) -> None:
    """Associa um vídeo à aula (a Cloudflare só devolve o ``uid`` no upload direto)."""
    monkeypatch.setattr(
        cloudflare_stream,
        "create_direct_upload",
        lambda *, max_duration_seconds: DirectUpload(
            uid=uid, upload_url=f"https://upload.cloudflare.test/{uid}"
        ),
    )
    response = client.post(f"/api/v1/lessons/{lesson_id}/video-upload", headers=admin)
    assert response.status_code == 200


def _fake_playback(*, video_uid: str) -> Playback:
    return Playback(
        token="tok-assinado",
        iframe_url="https://customer-demo.cloudflarestream.com/tok-assinado/iframe",
        hls_url="https://customer-demo.cloudflarestream.com/tok-assinado/manifest/video.m3u8",
        expires_at=datetime(2030, 1, 1, tzinfo=UTC),
    )


def _enroll(db_session: Session, *, user_id: int, course_id: int) -> None:
    """Libera o acesso de um aluno a um curso (simula o efeito de uma compra paga)."""
    purchase = Purchase(
        user_id=user_id,
        course_id=course_id,
        total_amount=Decimal("199.90"),
        status=PurchaseStatus.PAID,
    )
    db_session.add(purchase)
    db_session.flush()
    db_session.add(Enrollment(user_id=user_id, course_id=course_id, purchase_id=purchase.id))
    db_session.flush()


def _student_id(client: TestClient, student: dict[str, str]) -> int:
    response = client.get("/api/v1/auth/me", headers=student)
    assert response.status_code == 200
    return response.json()["id"]


def test_me_courses_sem_matricula_retorna_vazio(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)

    response = client.get("/api/v1/me/courses", headers=_auth(STUDENT_TOKEN))

    assert response.status_code == 200
    assert response.json() == []


def test_me_courses_exige_autenticacao(client: TestClient) -> None:
    response = client.get("/api/v1/me/courses")

    assert response.status_code == 401


def test_me_courses_lista_matriculas_ativas(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, _, _ = _published_course(client, admin, title="Python")
    user_id = _student_id(client, student)

    _enroll(db_session, user_id=user_id, course_id=course_id)

    response = client.get("/api/v1/me/courses", headers=student)
    assert response.status_code == 200
    body = response.json()
    assert [course["id"] for course in body] == [course_id]
    assert body[0]["title"] == "Python"
    assert body[0]["lessons_count"] == 1
    assert body[0]["granted_at"] is not None


def test_me_course_sem_matricula_retorna_403(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    course_id, _, _ = _published_course(client, admin, title="Django")

    response = client.get(f"/api/v1/me/courses/{course_id}", headers=_auth(STUDENT_TOKEN))

    assert response.status_code == 403


def test_me_course_detalha_somente_aulas_publicadas(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id, draft_id = _published_course(
        client, admin, title="FastAPI", extra_lesson_status="DRAFT"
    )
    user_id = _student_id(client, student)
    _enroll(db_session, user_id=user_id, course_id=course_id)

    response = client.get(f"/api/v1/me/courses/{course_id}", headers=student)

    assert response.status_code == 200
    body = response.json()
    lesson_ids = [lesson["id"] for lesson in body["lessons"]]
    assert lesson_ids == [lesson_id]
    assert draft_id not in lesson_ids
    assert body["lessons_count"] == 1
    assert "video_uid" not in body["lessons"][0]


def test_playback_sem_matricula_retorna_403(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    _, lesson_id, _ = _published_course(client, admin, title="Cloud")

    response = client.get(
        f"/api/v1/me/lessons/{lesson_id}/playback", headers=_auth(STUDENT_TOKEN)
    )

    assert response.status_code == 403


def test_playback_de_aula_sem_video_retorna_422(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id, _ = _published_course(client, admin, title="React")
    user_id = _student_id(client, student)
    _enroll(db_session, user_id=user_id, course_id=course_id)

    response = client.get(f"/api/v1/me/lessons/{lesson_id}/playback", headers=student)

    assert response.status_code == 422


def test_playback_emite_urls_assinadas(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id, _ = _published_course(client, admin, title="Dados")

    monkeypatch.setattr(cloudflare_stream, "create_playback", _fake_playback)
    _attach_video(client, monkeypatch, admin, lesson_id, uid="vid-aprendizado")

    user_id = _student_id(client, student)
    _enroll(db_session, user_id=user_id, course_id=course_id)

    response = client.get(f"/api/v1/me/lessons/{lesson_id}/playback", headers=student)

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"] == lesson_id
    assert body["iframe_url"].endswith("/tok-assinado/iframe")
    assert body["hls_url"].endswith("/tok-assinado/manifest/video.m3u8")
    assert "video_uid" not in body


def test_playback_sem_configuracao_retorna_503(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id, _ = _published_course(client, admin, title="Mobile")

    _attach_video(client, monkeypatch, admin, lesson_id, uid="vid-mobile")

    def _raise(*, video_uid: str) -> Playback:
        raise cloudflare_stream.CloudflareNotConfiguredError("sem credenciais")

    monkeypatch.setattr(cloudflare_stream, "create_playback", _raise)

    user_id = _student_id(client, student)
    _enroll(db_session, user_id=user_id, course_id=course_id)

    response = client.get(f"/api/v1/me/lessons/{lesson_id}/playback", headers=student)

    assert response.status_code == 503
