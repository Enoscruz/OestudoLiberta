[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[a-z][a-z0-9-]{4,28}[a-z0-9]$")]
    [string]$ProjectId,

    [Parameter(Mandatory)]
    [string]$DatabaseUser,

    [string]$Region = "southamerica-east1",
    [string]$SqlInstance = "oestudo-postgres",
    [string]$DatabaseName = "oestudo_liberta",
    [string]$ArtifactRepository = "oestudo-liberta",
    [string]$RuntimeServiceAccount = "",
    [string]$AdminBootstrapEmail = "",
    [string]$ConfirmProjectId = "",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

function Invoke-Gcloud {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud falhou (exit code $LASTEXITCODE): gcloud $($Arguments -join ' ')"
    }
}

function Get-GcloudValue {
    param([Parameter(Mandatory)][string[]]$Arguments)

    $value = & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud falhou (exit code $LASTEXITCODE): gcloud $($Arguments -join ' ')"
    }
    return ($value | Out-String).Trim()
}

function Assert-SecretVersion {
    param([Parameter(Mandatory)][string]$Name)

    Invoke-Gcloud @("secrets", "versions", "describe", "latest", "--secret=$Name", "--project=$ProjectId")
}

function Publish-Image {
    param(
        [Parameter(Mandatory)][string]$Context,
        [Parameter(Mandatory)][string]$Image,
        [string[]]$BuildArguments = @()
    )

    & docker build @BuildArguments --tag $Image $Context
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao construir a imagem '$Image'."
    }
    & docker push $Image
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao enviar a imagem '$Image'."
    }
}

if (-not $Apply) {
    throw "Este script publica serviços Cloud Run. Revise docs/sprint-6-google-cloud.md e execute novamente com -Apply."
}

foreach ($command in @("gcloud", "docker")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $command"
    }
}

$activeAccounts = (& gcloud auth list --format=json | ConvertFrom-Json)
$activeAccount = $activeAccounts | Where-Object { $_.status -eq "ACTIVE" } | Select-Object -First 1
if (-not $activeAccount) {
    throw "Nenhuma conta GCP ativa. Execute: gcloud auth login"
}

$confirmation = $ConfirmProjectId
if (-not $confirmation) {
    $confirmation = Read-Host "O deploy publicara backend e frontend no projeto '$ProjectId' e executara migrations. Digite o ID do projeto para confirmar"
}
if ($confirmation -cne $ProjectId) {
    throw "Confirmação não corresponde ao ID do projeto; nenhum deploy foi iniciado."
}

$publicFirebaseVariables = @(
    "NEXT_PUBLIC_FIREBASE_API_KEY",
    "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN",
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID",
    "NEXT_PUBLIC_FIREBASE_APP_ID",
    "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID",
    "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET"
)
foreach ($name in $publicFirebaseVariables) {
    if (-not [Environment]::GetEnvironmentVariable($name)) {
        throw "Variável pública do Firebase não definida: $name"
    }
}

Assert-SecretVersion -Name "POSTGRES_PASSWORD"
Assert-SecretVersion -Name "FIREBASE_SERVICE_ACCOUNT"

$registry = "$Region-docker.pkg.dev"
$imagePrefix = "$registry/$ProjectId/$ArtifactRepository"
$tag = (Get-Date -Format "yyyyMMddHHmmss")
$backendImage = "$imagePrefix/backend:$tag"
$frontendImage = "$imagePrefix/frontend:$tag"
$connectionName = "$ProjectId`:$Region`:$SqlInstance"
$runtimeServiceAccount = if ($RuntimeServiceAccount) {
    $RuntimeServiceAccount
} else {
    "oestudo-runtime@$ProjectId.iam.gserviceaccount.com"
}

Invoke-Gcloud @("auth", "configure-docker", $registry, "--quiet")

Write-Host "Construindo e enviando a imagem do backend..."
Publish-Image -Context "backend" -Image $backendImage

$secretMappings = @(
    "POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest",
    "/secrets/firebase-service-account.json=FIREBASE_SERVICE_ACCOUNT:latest"
)
foreach ($optionalSecret in @(
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_STREAM_API_TOKEN",
    "CLOUDFLARE_STREAM_CUSTOMER_CODE",
    "MERCADO_PAGO_ACCESS_TOKEN",
    "MERCADO_PAGO_WEBHOOK_SECRET"
)) {
    & gcloud secrets versions describe latest "--secret=$optionalSecret" "--project=$ProjectId" *> $null
    if ($LASTEXITCODE -eq 0) {
        $secretMappings += "$optionalSecret=$optionalSecret`:latest"
    }
}
$secretArgument = "--set-secrets=" + ($secretMappings -join ",")
$databaseEnvironment = "ENVIRONMENT=production,DEBUG=false,POSTGRES_HOST=/cloudsql/$connectionName,POSTGRES_PORT=5432,POSTGRES_DB=$DatabaseName,POSTGRES_USER=$DatabaseUser,FIREBASE_PROJECT_ID=$($env:NEXT_PUBLIC_FIREBASE_PROJECT_ID),FIREBASE_CREDENTIALS_PATH=/secrets/firebase-service-account.json,ADMIN_BOOTSTRAP_EMAIL=$AdminBootstrapEmail"
$runtimeArguments = @(
    "--project=$ProjectId",
    "--region=$Region",
    "--platform=managed",
    "--service-account=$runtimeServiceAccount",
    "--add-cloudsql-instances=$connectionName",
    "--set-env-vars=$databaseEnvironment",
    $secretArgument,
    "--memory=512Mi",
    "--cpu=1",
    "--max=5",
    "--timeout=300",
    "--allow-unauthenticated"
)

Write-Host "Aplicando migrations como etapa explícita do deploy..."
Invoke-Gcloud @(
    "run", "jobs", "deploy", "oestudo-migrate",
    "--image=$backendImage",
    "--region=$Region",
    "--project=$ProjectId",
    "--service-account=$runtimeServiceAccount",
    "--set-cloudsql-instances=$connectionName",
    "--set-env-vars=ENVIRONMENT=production,DEBUG=false,POSTGRES_HOST=/cloudsql/$connectionName,POSTGRES_PORT=5432,POSTGRES_DB=$DatabaseName,POSTGRES_USER=$DatabaseUser",
    "--set-secrets=POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest",
    "--command=alembic",
    "--args=upgrade,head",
    "--max-retries=0",
    "--task-timeout=600"
)
Invoke-Gcloud @("run", "jobs", "execute", "oestudo-migrate", "--region=$Region", "--project=$ProjectId", "--wait")

Write-Host "Publicando o backend..."
Invoke-Gcloud (@("run", "deploy", "oestudo-backend", "--image=$backendImage") + $runtimeArguments)
$backendUrl = Get-GcloudValue @("run", "services", "describe", "oestudo-backend", "--region=$Region", "--project=$ProjectId", "--format=value(status.url)")
if (-not $backendUrl) {
    throw "Cloud Run não retornou a URL do backend."
}

$frontendBuildArguments = @(
    "--build-arg", "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"
)
foreach ($name in $publicFirebaseVariables) {
    $frontendBuildArguments += @("--build-arg", "$name=$([Environment]::GetEnvironmentVariable($name))")
}
Write-Host "Construindo e enviando a imagem do frontend..."
Publish-Image -Context "frontend" -Image $frontendImage -BuildArguments $frontendBuildArguments

Write-Host "Publicando o frontend..."
Invoke-Gcloud @(
    "run", "deploy", "oestudo-frontend",
    "--image=$frontendImage",
    "--project=$ProjectId",
    "--region=$Region",
    "--platform=managed",
    "--service-account=$runtimeServiceAccount",
    "--memory=512Mi",
    "--cpu=1",
    "--max=5",
    "--allow-unauthenticated"
)
$frontendUrl = Get-GcloudValue @("run", "services", "describe", "oestudo-frontend", "--region=$Region", "--project=$ProjectId", "--format=value(status.url)")
if (-not $frontendUrl) {
    throw "Cloud Run não retornou a URL do frontend."
}

$finalBackendEnvironment = "$databaseEnvironment,CORS_ORIGINS=$frontendUrl,FRONTEND_BASE_URL=$frontendUrl,MERCADO_PAGO_NOTIFICATION_URL=$backendUrl/api/v1/webhooks/mercadopago"
Write-Host "Restringindo CORS e configurando URLs públicas no backend..."
Invoke-Gcloud (@("run", "services", "update", "oestudo-backend", "--project=$ProjectId", "--region=$Region", "--set-env-vars=$finalBackendEnvironment") + @($secretArgument, "--service-account=$runtimeServiceAccount", "--add-cloudsql-instances=$connectionName"))

Write-Host ""
Write-Host "Deploy concluído."
Write-Host "Frontend: $frontendUrl"
Write-Host "Backend:  $backendUrl"
Write-Host "API docs desabilitadas em produção; health check: $backendUrl/health"
Write-Host "Adicione os domínios do frontend em Firebase Authentication > Authorized domains."
