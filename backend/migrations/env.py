"""Ambiente de execução das migrações Alembic."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.models import Base

# Objeto de configuração do Alembic (alembic.ini).
config = context.config

# Injeta a URL do banco vinda das configurações da aplicação (.env),
# evitando credenciais versionadas no alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().sqlalchemy_database_uri)

# Configuração de logging a partir do alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata usada pelo autogenerate para comparar modelos x banco.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações em modo 'offline' (gera SQL sem conectar)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações em modo 'online' (com conexão ativa)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
