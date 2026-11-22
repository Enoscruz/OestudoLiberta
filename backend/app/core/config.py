"""Configurações da aplicação, carregadas de variáveis de ambiente (.env)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# backend/app/core/config.py -> backend/ -> raiz do monorepo
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Configurações centralizadas da plataforma."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicação ─────────────────────────────────────────
    app_name: str = "OestudoLiberta"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # ── Banco de dados ────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "oestudo_liberta"
    postgres_user: str = "oestudo_app"
    postgres_password: str = "change-me"
    database_url: str | None = None

    # ── Firebase Authentication ───────────────────────────
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None

    # ── Bootstrap de administrador ────────────────────────
    # E-mail promovido a ADMIN na primeira sincronização (procedimento seguro).
    admin_bootstrap_email: str | None = None

    # ── Cloudflare Stream (vídeos) ────────────────────────
    cloudflare_account_id: str | None = None
    cloudflare_stream_api_token: str | None = None
    # Subdomínio da conta (``customer-<CODE>.cloudflarestream.com``), usado para
    # montar as URLs assinadas de reprodução.
    cloudflare_stream_customer_code: str | None = None

    # ── Mercado Pago (pagamentos) ─────────────────────────
    mercado_pago_access_token: str | None = None
    # Chave usada para validar a assinatura (``x-signature``) dos webhooks.
    mercado_pago_webhook_secret: str | None = None
    # URL pública que o Mercado Pago chama ao mudar o status de um pagamento.
    # Em desenvolvimento costuma apontar para um túnel (ex.: ngrok).
    mercado_pago_notification_url: str | None = None

    # ── Frontend ──────────────────────────────────────────
    # Base usada nos ``back_urls`` do checkout (retorno do aluno).
    frontend_base_url: str = "http://localhost:3000"

    # ── CORS ──────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """URL de conexão usada pelo SQLAlchemy/Alembic."""
        if self.database_url:
            return self.database_url
        is_cloud_sql_socket = self.postgres_host.startswith("/cloudsql/")
        url = URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=None if is_cloud_sql_socket else self.postgres_host,
            port=None if is_cloud_sql_socket else self.postgres_port,
            database=self.postgres_db,
            query={"host": self.postgres_host} if is_cloud_sql_socket else {},
        )
        return url.render_as_string(hide_password=False)

    @property
    def cors_origin_list(self) -> list[str]:
        """Origens permitidas de CORS como lista."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) das configurações."""
    return Settings()
