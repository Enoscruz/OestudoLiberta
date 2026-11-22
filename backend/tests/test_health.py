"""Testes dos endpoints de saúde."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "OestudoLiberta"


def test_health_db_ok() -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["database"] == "reachable"
