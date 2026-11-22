# syntax=docker/dockerfile:1
# =========================================================================
# OestudoLiberta — imagem do backend (FastAPI + Uvicorn)
#
# Build (contexto = ./backend):
#   docker build -t oestudo-backend ./backend
# =========================================================================

# ── Estágio 1: dependências em um virtualenv isolado ──────
# Compila/instala os pacotes aqui; apenas o venv resultante vai para o runtime.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt ./
RUN pip install -r requirements.txt

# ── Estágio 2: runtime enxuto ─────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Usuário sem privilégios.
RUN groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid app --create-home app

# O código fica em /app/backend para que a raiz do monorepo — calculada em
# config.py como parents[2] de app/core/config.py — seja /app, preservando a
# mesma semântica do repositório local (onde .env e secrets/ ficam na raiz).
WORKDIR /app/backend

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app

# Cloud Run injeta a porta via $PORT (padrão 8080).
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health').status == 200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
