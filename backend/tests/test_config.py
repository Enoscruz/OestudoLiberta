"""Testes das configurações de conexão."""

from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_cloud_sql_socket_uri_uses_unix_socket_and_escapes_credentials() -> None:
    settings = Settings(
        database_url=None,
        postgres_host="/cloudsql/project:region:instance",
        postgres_db="oestudo_liberta",
        postgres_user="oestudo_app",
        postgres_password="senha:/@segura",
    )

    url = make_url(settings.sqlalchemy_database_uri)

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "oestudo_app"
    assert url.password == "senha:/@segura"
    assert url.host is None
    assert url.database == "oestudo_liberta"
    assert url.query["host"] == "/cloudsql/project:region:instance"
