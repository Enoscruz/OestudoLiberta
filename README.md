# OestudoLiberta — Plataforma de Educação Digital

Plataforma própria de cursos online (modelo **pay-per-course**), com autenticação
Firebase, hospedagem de vídeos via Cloudflare Stream e pagamentos via Mercado Pago.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js + React + TypeScript (CSS responsivo) |
| Backend | Python + FastAPI + SQLAlchemy + Pydantic + Alembic |
| Autenticação | Firebase Authentication (Firebase Admin SDK no backend) |
| Banco de dados | PostgreSQL (local em dev / Google Cloud SQL em produção) |
| Vídeos | Cloudflare Stream |
| Pagamentos | Mercado Pago |
| Infraestrutura | Google Cloud (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager) |

Arquitetura: **monólito modular** (sem microsserviços inicialmente).

## Estrutura do monorepo

```
OestudoLiberta/
├── backend/
│   ├── app/
│   │   ├── core/          # config, segurança, dependências
│   │   ├── models/        # modelos SQLAlchemy
│   │   ├── schemas/       # schemas Pydantic
│   │   ├── api/           # rotas FastAPI
│   │   ├── services/      # regras de negócio
│   │   ├── repositories/  # acesso a dados
│   │   └── integrations/  # Firebase, Mercado Pago, Cloudflare
│   ├── tests/
│   ├── migrations/        # Alembic
│   └── requirements.txt
├── frontend/              # Next.js (SPRINT 3)
├── infrastructure/
│   ├── docker/
│   └── cloud/             # scripts gcloud/PowerShell (SPRINT 6)
└── docs/
    ├── 01-architecture.md
    ├── 04-roadmap.md
    ├── 05-project-guide.md
    ├── sprint-6-google-cloud.md
    └── assets/             # diagramas SVG da documentação
```

## Como rodar (desenvolvimento)

```powershell
# 1. Banco de dados (PostgreSQL local em D:\postgre)
#    Crie o banco oestudo_liberta e o usuário oestudo_app.
#    Modelo, constraints e migrations: docs/01-architecture.md (seção 4).

# 2. Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example ..\.env     # e preencha os valores
alembic upgrade head
uvicorn app.main:app --reload
```

## Docker local

Com Docker Desktop/WSL ativo e os arquivos `.env` e `frontend/.env.local`
configurados:

```powershell
docker compose --env-file .env --env-file frontend/.env.local run --rm backend alembic upgrade head
docker compose --env-file .env --env-file frontend/.env.local up --build -d
```

Frontend: `http://localhost:3000`. Backend: `http://localhost:8000/health`.
Para parar os containers sem apagar o volume do banco:

```powershell
docker compose down
```

## Documentação

- [Guia técnico do projeto](docs/05-project-guide.md)
- [Arquitetura](docs/01-architecture.md)
- [Roadmap e pendências](docs/04-roadmap.md)
- [SPRINT 6 — Google Cloud](docs/sprint-6-google-cloud.md)
