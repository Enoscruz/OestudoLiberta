"""Testes do progresso de aprendizagem: registro, indicadores e histórico."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import PurchaseStatus
from app.integrations import firebase
from app.integrations.firebase import FirebaseIdentity
from app.models.commerce import Enrollment, Purchase
from app.models.learning import LessonProgress

ADMIN_EMAIL = "admin.progresso@oestudoliberta.test"
ADMIN_TOKEN = "tok-admin-progresso"
STUDENT_EMAIL = "aluno.progresso@oestudoliberta.test"
STUDENT_TOKEN = "tok-aluno-progresso"
OTHER_EMAIL = "outro.progresso@oestudoliberta.test"
OTHER_TOKEN = "tok-outro-progresso"

LESSON_SECONDS = 600


def _identity(uid: str, email: str) -> FirebaseIdentity:
    return FirebaseIdentity(uid=uid, email=email, email_verified=True, name="Nome Teste")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_tokens(monkeypatch) -> None:
    """Registra o administrador de bootstrap e dois alunos no verificador."""
    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", ADMIN_EMAIL)
    tokens = {
        ADMIN_TOKEN: _identity("uid-admin-progresso", ADMIN_EMAIL),
        STUDENT_TOKEN: _identity("uid-aluno-progresso", STUDENT_EMAIL),
        OTHER_TOKEN: _identity("uid-outro-progresso", OTHER_EMAIL),
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
    lesson_seconds: int | None = LESSON_SECONDS,
) -> tuple[int, int]:
    """Cria um curso publicado com uma aula publicada e devolve os ids."""
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

    lesson_body: dict[str, object] = {
        "course_id": course_id,
        "title": "Introdução",
        "status": "PUBLISHED",
    }
    if lesson_seconds is not None:
        lesson_body["duration_seconds"] = lesson_seconds
    lesson = client.post("/api/v1/lessons", json=lesson_body, headers=admin)
    assert lesson.status_code == 201

    published = client.post(f"/api/v1/courses/{course_id}/publish", headers=admin)
    assert published.status_code == 200

    return course_id, lesson.json()["id"]


def _draft_lesson(client: TestClient, admin: dict[str, str], course_id: int) -> int:
    """Cria uma aula em rascunho no curso informado e devolve o id."""
    lesson = client.post(
        "/api/v1/lessons",
        json={"course_id": course_id, "title": "Rascunho", "status": "DRAFT"},
        headers=admin,
    )
    assert lesson.status_code == 201
    return lesson.json()["id"]


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


def _user_id(client: TestClient, student: dict[str, str]) -> int:
    response = client.get("/api/v1/auth/me", headers=student)
    assert response.status_code == 200
    return response.json()["id"]


def _save_progress(
    client: TestClient,
    headers: dict[str, str],
    lesson_id: int,
    *,
    seconds: int,
    completed: bool = False,
):
    return client.put(
        f"/api/v1/me/lessons/{lesson_id}/progress",
        json={"progress_seconds": seconds, "completed": completed},
        headers=headers,
    )


def _progress_rows(db_session: Session) -> list[LessonProgress]:
    return list(db_session.execute(select(LessonProgress)).scalars())


def test_progresso_exige_autenticacao(client: TestClient) -> None:
    response = client.put(
        "/api/v1/me/lessons/1/progress",
        json={"progress_seconds": 10, "completed": False},
    )

    assert response.status_code == 401


def test_progresso_recusa_valor_negativo(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)

    response = _save_progress(client, _auth(STUDENT_TOKEN), 1, seconds=-5)

    assert response.status_code == 422


def test_progresso_aula_inexistente_retorna_404(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)

    response = _save_progress(client, _auth(STUDENT_TOKEN), 999999, seconds=10)

    assert response.status_code == 404


def test_progresso_aula_nao_publicada_retorna_404(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, _ = _published_course(client, admin)
    draft_id = _draft_lesson(client, admin, course_id)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    response = _save_progress(client, student, draft_id, seconds=10)

    assert response.status_code == 404


def test_progresso_sem_matricula_retorna_403(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    _, lesson_id = _published_course(client, admin)

    response = _save_progress(client, _auth(STUDENT_TOKEN), lesson_id, seconds=10)

    assert response.status_code == 403


def test_registra_progresso_parcial(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    response = _save_progress(client, student, lesson_id, seconds=120)

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"] == lesson_id
    assert body["progress_seconds"] == 120
    assert body["completed"] is False
    assert body["completed_at"] is None
    assert body["updated_at"] is not None


def test_progresso_nao_duplica_linha(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    _save_progress(client, student, lesson_id, seconds=60)
    _save_progress(client, student, lesson_id, seconds=180)

    rows = _progress_rows(db_session)
    assert len(rows) == 1
    assert rows[0].progress_seconds == 180


def test_progresso_nao_regride(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    _save_progress(client, student, lesson_id, seconds=300)
    response = _save_progress(client, student, lesson_id, seconds=90)

    assert response.status_code == 200
    assert response.json()["progress_seconds"] == 300


def test_progresso_limitado_a_duracao_da_aula(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    response = _save_progress(client, student, lesson_id, seconds=4_000)

    assert response.status_code == 200
    assert response.json()["progress_seconds"] == LESSON_SECONDS


def test_conclusao_automatica_ao_atingir_o_fim(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    response = _save_progress(client, student, lesson_id, seconds=LESSON_SECONDS)

    body = response.json()
    assert body["completed"] is True
    assert body["completed_at"] is not None


def test_conclusao_manual_em_aula_sem_duracao(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin, lesson_seconds=None)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    response = _save_progress(client, student, lesson_id, seconds=0, completed=True)

    body = response.json()
    assert body["completed"] is True
    assert body["progress_seconds"] == 0


def test_conclusao_nao_e_perdida_ao_regravar(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)

    _save_progress(client, student, lesson_id, seconds=LESSON_SECONDS)
    response = _save_progress(client, student, lesson_id, seconds=30, completed=False)

    assert response.json()["completed"] is True


def test_me_course_traz_progresso_por_aula_e_percentual(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)
    _save_progress(client, student, lesson_id, seconds=120)

    response = client.get(f"/api/v1/me/courses/{course_id}", headers=student)

    assert response.status_code == 200
    body = response.json()
    assert body["completed_lessons"] == 0
    assert body["progress_percent"] == 0
    assert body["lessons"][0]["progress_seconds"] == 120
    assert body["lessons"][0]["completed"] is False


def test_me_courses_indica_curso_concluido(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)
    _save_progress(client, student, lesson_id, seconds=LESSON_SECONDS)

    response = client.get("/api/v1/me/courses", headers=student)

    body = response.json()
    assert body[0]["completed_lessons"] == 1
    assert body[0]["progress_percent"] == 100


def test_historico_consolida_indicadores(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)
    _save_progress(client, student, lesson_id, seconds=300)

    response = client.get("/api/v1/me/history", headers=student)

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "courses_owned": 1,
        "courses_completed": 0,
        "lessons_completed": 0,
        "lessons_available": 1,
        "watched_seconds": 300,
    }
    assert body["courses"][0]["id"] == course_id
    assert body["courses"][0]["progress_percent"] == 0
    assert body["courses"][0]["last_activity_at"] is not None

    _save_progress(client, student, lesson_id, seconds=LESSON_SECONDS)
    finished = client.get("/api/v1/me/history", headers=student).json()

    assert finished["summary"]["courses_completed"] == 1
    assert finished["summary"]["lessons_completed"] == 1
    assert finished["courses"][0]["completed"] is True
    assert finished["courses"][0]["progress_percent"] == 100


def test_historico_ordena_por_ultima_atividade(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    first_course, first_lesson = _published_course(client, admin, title="Primeiro")
    second_course, second_lesson = _published_course(client, admin, title="Segundo")
    user_id = _user_id(client, student)
    _enroll(db_session, user_id=user_id, course_id=first_course)
    _enroll(db_session, user_id=user_id, course_id=second_course)

    _save_progress(client, student, first_lesson, seconds=60)
    _save_progress(client, student, second_lesson, seconds=60)

    # Dentro de uma única transação os dois registros recebem o mesmo `now()`:
    # as datas são fixadas para que a ordenação seja realmente exercitada.
    rows = {row.lesson_id: row for row in _progress_rows(db_session)}
    rows[first_lesson].updated_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    rows[second_lesson].updated_at = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
    db_session.flush()

    response = client.get("/api/v1/me/history", headers=student)

    assert [course["id"] for course in response.json()["courses"]] == [
        second_course,
        first_course,
    ]


def test_historico_de_outro_aluno_vazio(client: TestClient, monkeypatch) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    _published_course(client, admin)

    response = client.get("/api/v1/me/history", headers=_auth(OTHER_TOKEN))

    assert response.status_code == 200
    body = response.json()
    assert body["courses"] == []
    assert body["summary"]["courses_owned"] == 0
    assert body["summary"]["watched_seconds"] == 0


def test_progresso_de_um_aluno_nao_aparece_para_outro(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _setup_tokens(monkeypatch)
    admin = _auth(ADMIN_TOKEN)
    student = _auth(STUDENT_TOKEN)
    other = _auth(OTHER_TOKEN)
    course_id, lesson_id = _published_course(client, admin)
    _enroll(db_session, user_id=_user_id(client, student), course_id=course_id)
    _enroll(db_session, user_id=_user_id(client, other), course_id=course_id)
    _save_progress(client, student, lesson_id, seconds=300)

    response = client.get(f"/api/v1/me/courses/{course_id}", headers=other)

    body = response.json()
    assert body["completed_lessons"] == 0
    assert body["lessons"][0]["progress_seconds"] == 0
