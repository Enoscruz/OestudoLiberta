# Roadmap e Pendências do Projeto

**Revisão:** 14/11/2026  
**Escopo:** SPRINTS 1 a 6, comparando o planejamento com o código, testes,
configuração local e pré-requisitos externos encontrados no workspace.

## Resumo Executivo

As SPRINTS 1 a 5 têm suas funcionalidades principais implementadas e cobertas
por 72 testes de backend (última execução local: todos passaram). Lint/build
do frontend também passaram localmente. Isso não significa que todos os fluxos
estejam operacionais com provedores reais: Cloudflare Stream e Mercado Pago
não têm credenciais configuradas, e a ativação do provedor Firebase
E-mail/senha ainda precisa ser confirmada no Console.

A SPRINT 6 está **em andamento**. Docker/Compose foi validado localmente; os
workflows e scripts GCP existem, mas não foram executados. Não há remote Git,
conta GCP ativa nem projeto GCP configurado. Nenhum recurso pago foi criado.

**Não há uma SPRINT 7 definida no planejamento atual.**

## Estado por Sprint

| Sprint | Estado | Evidência e pendências |
|---|---|---|
| **1 — Fundação e segurança** | Código concluído | Monorepo, PostgreSQL, SQLAlchemy, Alembic, Firebase Admin, papéis e testes implementados. Há credencial Firebase Admin no caminho configurado, mas o bootstrap de administrador está sem `ADMIN_BOOTSTRAP_EMAIL`. A autenticação real ainda depende de confirmar E-mail/senha habilitado no Firebase. |
| **2 — Gestão de conteúdo** | Código concluído; integração real pendente | CRUD de categorias, cursos e aulas, publicação e fluxo de upload Cloudflare implementados e testados com mocks. `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_STREAM_API_TOKEN` e `CLOUDFLARE_STREAM_CUSTOMER_CODE` estão vazios; upload e reprodução reais não foram homologados. |
| **3 — Frontend** | Código concluído; validação de autenticação pendente | Layout, catálogo, login/cadastro, dashboard, player e administração implementados. As seis variáveis públicas Firebase Web estão configuradas localmente. Falta confirmar o provedor E-mail/senha, testar cadastro/verificação/recuperação com usuário real e garantir domínio autorizado em produção. Não há suíte automatizada de testes E2E/UI. |
| **4 — Pagamentos** | Código implementado; bloqueado para homologação e hardening | Checkout, consulta do pagamento na origem, idempotência, divergência de valor, estorno e matrícula estão implementados e cobertos por testes. `MERCADO_PAGO_ACCESS_TOKEN`, `MERCADO_PAGO_WEBHOOK_SECRET` e `MERCADO_PAGO_NOTIFICATION_URL` estão vazios. **A validação HMAC é condicional:** sem o secret, o código não verifica a assinatura e segue para a consulta do pagamento na API do Mercado Pago. Tornar a ausência do secret um erro em produção é requisito antes do deploy. |
| **5 — Aprendizagem e progresso** | Código concluído; aceite ponta a ponta pendente | Heartbeat, progresso monotônico, conclusão, resumo e histórico estão implementados e testados. Falta validar com usuário real matriculado e aula real na Cloudflare, incluindo retomada, conclusão e permissões. |
| **6 — Produção no Google Cloud** | Em andamento; sem ambiente GCP | Dockerfiles, Compose, migrations em etapa explícita, scripts de provisionamento/deploy, CI e workflow manual foram preparados. Docker local foi validado. Os workflows ainda não foram executados pelo GitHub; os scripts GCP não foram executados. Falta remote Git, projeto/faturamento GCP, identidade WIF, segredos, deploy, domínio, monitoramento e testes operacionais. |

## Pendências Priorizadas

### P0 — Antes de qualquer produção

1. **Falhar fechado na assinatura do Mercado Pago.** Se `MERCADO_PAGO_WEBHOOK_SECRET` não estiver configurado em produção, rejeitar o webhook em vez de simplesmente omitir a validação HMAC. Manter também a consulta do pagamento na API do Mercado Pago.
2. **Configurar integrações externas.** Definir credenciais Cloudflare Stream e Mercado Pago; manter os valores reais fora do código e do Git. Validar as credenciais com os respectivos ambientes de teste antes de usar produção.
3. **Confirmar autenticação e administrador.** Ativar E-mail/senha no Firebase Authentication, validar o fluxo de verificação e configurar `ADMIN_BOOTSTRAP_EMAIL` com o e-mail que deve receber o papel ADMIN.

### P1 — Entrega e deploy

4. **Conectar um remote GitHub.** O repositório local não tem remote configurado. Criar/vincular o repositório remoto e publicar os workflows para que o CI possa rodar.
5. **Executar o CI no GitHub.** Confirmar migrations + 72 testes backend, Ruff, lint e build do frontend em pull request/push; proteger `main` para exigir CI verde.
6. **Preparar GCP com aprovação de custo.** Criar/selecionar projeto, associar billing, conferir região/cotas/preços e só então executar `provision.ps1`. Cloud SQL tem custo contínuo.
7. **Completar identidade e segredos.** Configurar Workload Identity Federation, GitHub Environment `production`, service accounts e versões de Secret Manager (`POSTGRES_PASSWORD`, `FIREBASE_SERVICE_ACCOUNT` e segredos das integrações habilitadas).
8. **Executar deploy e migrations.** Rodar o workflow manual em `main` após CI verde; validar Cloud Run, `/health`, `/health/db`, frontend e logs.
9. **Executar aceite funcional ponta a ponta:** cadastro/verificação, promoção ADMIN, criação/publicação de curso, upload/reprodução de vídeo, checkout sandbox, webhook aprovado/rejeitado/duplicado/estornado, matrícula e persistência/retomada do progresso.

### P2 — Operação e qualidade contínua

10. Configurar domínio e DNS; ajustar domínios autorizados no Firebase, CORS e URL de notificação do Mercado Pago.
11. Configurar alertas de orçamento, política/retenção de logs e alertas operacionais. Backups/PITR são previstos no script, mas ainda falta testar uma restauração.
12. Executar teste de carga compatível com limites do Cloud Run/Cloud SQL e registrar os resultados.
13. Decidir se a plataforma precisa de Cloud Storage para arquivos. O bucket de infraestrutura é privado, mas a aplicação ainda não o utiliza; vídeos continuam no Cloudflare Stream.
14. Adicionar testes E2E/UI para os fluxos críticos e uma checagem de acessibilidade/responsividade automatizada.

## Ordem Recomendada

1. Corrigir o comportamento HMAC fail-closed e preencher/validar as integrações Firebase, Cloudflare e Mercado Pago em sandbox.
2. Definir `ADMIN_BOOTSTRAP_EMAIL`, testar o fluxo administrativo e fechar o aceite das SPRINTS 2–5 com serviços reais.
3. Configurar remote GitHub, executar CI e exigir checks em `main`.
4. Confirmar projeto GCP, faturamento e orçamento; provisionar infraestrutura e segredos.
5. Executar deploy protegido, configurar domínio/webhook e concluir o aceite ponta a ponta.
6. Validar backup/restore, alertas, logs e carga antes de declarar a SPRINT 6 concluída.

## Critério para Encerrar a SPRINT 6

- CI verde no GitHub e branch principal protegida.
- Backend e frontend publicados em Cloud Run; Cloud SQL conectado; migrations
  executadas como job antes da revisão do backend.
- Firebase, Cloudflare Stream e Mercado Pago configurados, com HMAC obrigatório
  em produção e domínio/webhook validados.
- Fluxo de aluno testado da criação de conta ao consumo do curso comprado.
- Alertas básicos de orçamento/serviço configurados e restauração de backup
  demonstrada.
- Pendências de carga e domínio customizado resolvidas ou aceitas explicitamente
  como fora do lançamento inicial.
