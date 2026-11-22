# SPRINT 6 — Produção no Google Cloud

## Objetivo e situação

Esta sprint prepara o caminho de produção para Cloud Run, Cloud SQL, Secret
Manager e Cloud Storage. A stack Docker local foi construída, iniciada e
validada; os endpoints locais retornaram HTTP 200 e as migrations foram
aplicadas.

**Ainda não existe deploy GCP.** Não há projeto/conta GCP autenticada nesta
máquina. Os scripts abaixo não foram executados. A criação de Cloud SQL e
outros recursos pode gerar cobranças contínuas, por isso o provisionamento e o
deploy exigem `-Apply`, confirmação do ID do projeto e uma conta autenticada.
O [roadmap revisado](04-roadmap.md) registra bloqueios encontrados também nas
SPRINTS 1 a 5.

O bucket está preparado como recurso de infraestrutura, mas o código atual
não armazena arquivos nele; as aulas em vídeo continuam usando Cloudflare
Stream.

## Arquitetura preparada

- `oestudo-backend`: Cloud Run, API FastAPI pública, com autorização aplicada
  pelo backend e segredos montados do Secret Manager.
- `oestudo-frontend`: Cloud Run, Next.js standalone; `NEXT_PUBLIC_*` é
  incorporado à imagem durante o build.
- Cloud SQL PostgreSQL 16: conexão privada pelo socket Cloud SQL em
  `/cloudsql/PROJECT:REGION:INSTANCE`.
- `oestudo-migrate`: Cloud Run Job executado antes de publicar a revisão nova
  do backend. As migrations não rodam no startup da aplicação.
- Secret Manager: senha do banco, credenciais Firebase Admin e, quando
  cadastrados, tokens Cloudflare e Mercado Pago.
- Cloud Storage: bucket privado com acesso uniforme, reservado para futuros
  arquivos da plataforma.
- GitHub Actions: CI em pull requests e pushes para `main`; deploy de produção
  manual, protegido pelo Environment `production` e Workload Identity
  Federation (sem chave JSON de service account no GitHub).

## Pré-requisitos

1. Criar um projeto Google Cloud e associar uma conta de faturamento.
2. Instalar Google Cloud CLI e Docker Desktop; autenticar com
   `gcloud auth login`.
3. Configurar o projeto no Console GCP e conferir região, cotas e preços de
   Cloud SQL. A configuração inicial do script cria uma instância PostgreSQL
   `db-custom-1-3840` com backup/PITR, que gera cobrança mesmo sem tráfego.
4. Ter o Firebase Authentication habilitado e um arquivo de service account
   Firebase Admin válido, guardado fora do Git.

## Provisionamento inicial

No PowerShell, a partir da raiz do monorepo:

```powershell
.\infrastructure\cloud\provision.ps1 `
  -ProjectId "SEU_PROJECT_ID" `
  -AssetsBucket "SEU_BUCKET_GLOBALMENTE_UNICO" `
  -Region "southamerica-east1" `
  -Apply
```

O script pede que o ID do projeto seja digitado novamente. Ele habilita APIs,
cria Artifact Registry, Cloud SQL PostgreSQL, banco, bucket privado, service
accounts e recursos vazios no Secret Manager. Não cria valores de segredos nem
publica imagens.

Crie o usuário PostgreSQL da aplicação no Cloud SQL, com uma senha forte, e
cadastre a mesma senha no secret `POSTGRES_PASSWORD`. Crie versões dos segredos
necessários usando arquivos locais fora do repositório:

```powershell
gcloud secrets versions add POSTGRES_PASSWORD `
  --data-file="CAMINHO_LOCAL_SEGURO\postgres-password.txt" `
  --project="SEU_PROJECT_ID"

gcloud secrets versions add FIREBASE_SERVICE_ACCOUNT `
  --data-file="CAMINHO_LOCAL_SEGURO\firebase-service-account.json" `
  --project="SEU_PROJECT_ID"
```

O arquivo de senha deve conter exatamente a senha definida no usuário do Cloud
SQL. Restrinja o acesso a esses arquivos e remova-os do disco quando não forem
mais necessários. Não coloque valores de segredo em comandos, logs, GitHub
Variables ou no repositório.

Quando as integrações forem configuradas, cadastre versões para
`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_STREAM_API_TOKEN`,
`CLOUDFLARE_STREAM_CUSTOMER_CODE`, `MERCADO_PAGO_ACCESS_TOKEN` e
`MERCADO_PAGO_WEBHOOK_SECRET`. O deploy ignora segredos opcionais sem versão.

## GitHub Actions e identidade sem chave

Depois do provisionamento, configure a federação para o repositório:

```powershell
.\infrastructure\cloud\setup-github-identity.ps1 `
  -ProjectId "SEU_PROJECT_ID" `
  -GitHubRepository "DONO/REPOSITORIO" `
  -Apply
```

No GitHub, crie o Environment `production`, limite deployments à branch `main`
e configure aprovação manual se disponível. Cadastre como **Repository
Variables**:

| Variable | Valor |
|---|---|
| `GCP_PROJECT_ID` | ID do projeto GCP |
| `GCP_REGION` | Região dos serviços, por exemplo `southamerica-east1` |
| `GCP_SQL_INSTANCE` | Nome da instância criada |
| `GCP_DATABASE_NAME` | Nome do banco criado |
| `GCP_DATABASE_USER` | Usuário PostgreSQL criado para a aplicação |
| `GCP_ARTIFACT_REPOSITORY` | Repositório Docker criado |
| `GCP_RUNTIME_SERVICE_ACCOUNT` | E-mail `oestudo-runtime@PROJECT_ID.iam.gserviceaccount.com` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | E-mail `oestudo-deployer@PROJECT_ID.iam.gserviceaccount.com` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Recurso `projects/NUMERO/locations/global/workloadIdentityPools/github-actions/providers/github` impresso pelo script |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | API key pública do app Web Firebase |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Domínio de autenticação Firebase |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | ID do projeto Firebase |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | App ID Web Firebase |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Sender ID Firebase |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Bucket Firebase do app Web |
| `ADMIN_BOOTSTRAP_EMAIL` | E-mail do administrador inicial |

Os valores `NEXT_PUBLIC_*` são configuração pública do cliente, não segredos.
As credenciais do Firebase Admin e do PostgreSQL permanecem no Secret Manager.

O workflow `.github/workflows/ci.yml` valida backend e frontend em PR/push. Após
CI verde em `main`, execute `.github/workflows/deploy-production.yml` por
`workflow_dispatch`, selecione `deploy` e aprove o Environment. O workflow
confere a configuração necessária, autentica por OIDC/WIF, executa migrations
e publica as imagens. O script `deploy.ps1` também pode ser executado
localmente; ele solicita confirmação do ID do projeto.

## Pós-deploy

1. Confira a URL de ambos os serviços Cloud Run e os logs no Cloud Logging.
2. Verifique `GET /health` e `GET /health/db` no backend e a home do frontend.
3. Adicione o domínio do frontend em Firebase Authentication >
   Authorized domains.
4. Configure o domínio oficial e DNS. O HTTPS gerenciado é fornecido pelo
   mapeamento de domínio do Cloud Run depois da validação DNS.
5. Configure o endpoint de webhook do Mercado Pago para
   `https://SEU_BACKEND/api/v1/webhooks/mercadopago` e valide o fluxo com
   credenciais de produção apenas após homologação.
6. Revise retenção de logs, alertas, backups e orçamento no GCP. Backups/PITR
   do Cloud SQL são habilitados no provisionamento; alarmes de custo precisam
   ser configurados no projeto.

## Limites e pendências

- O script do deploy usa as URLs padrão `*.run.app`. Mapeamento de domínio
  customizado/DNS ainda é uma etapa operacional posterior.
- Carga de teste, monitoramento com alertas e restauração de backup ainda não
  foram executados.
- O workflow de deploy não foi executado porque não há projeto, conta GCP ou
  valores de configuração confirmados.
- O repositório não tem remote Git configurado, portanto os workflows ainda não
  rodaram no GitHub.
- As variáveis locais de Cloudflare Stream e Mercado Pago estão vazias. O
  handler do Mercado Pago só verifica HMAC quando o secret está preenchido;
  tornar a ausência desse secret um erro é requisito antes de produção.
- `ADMIN_BOOTSTRAP_EMAIL` está vazio e a ativação do provedor Firebase
  E-mail/senha precisa ser confirmada no Console.
- Não foi criado um usuário de administrador nem provisionados segredos reais.
