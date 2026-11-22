[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[a-z][a-z0-9-]{4,28}[a-z0-9]$")]
    [string]$ProjectId,

    [Parameter(Mandatory)]
    [ValidatePattern("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")]
    [string]$AssetsBucket,

    [string]$Region = "southamerica-east1",
    [string]$SqlInstance = "oestudo-postgres",
    [string]$DatabaseName = "oestudo_liberta",
    [string]$ArtifactRepository = "oestudo-liberta",

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

function Test-GcloudResource {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & gcloud @Arguments *> $null
    return $LASTEXITCODE -eq 0
}

if (-not $Apply) {
    throw "Este script cria recursos GCP que podem gerar custos. Revise docs/sprint-6-google-cloud.md e execute novamente com -Apply."
}

$accounts = (& gcloud auth list --format=json | ConvertFrom-Json)
$activeAccount = $accounts | Where-Object { $_.status -eq "ACTIVE" } | Select-Object -First 1
if (-not $activeAccount) {
    throw "Nenhuma conta GCP ativa. Execute: gcloud auth login"
}

$confirmation = Read-Host "Isso criara Cloud SQL e recursos no projeto '$ProjectId' usando a conta $($activeAccount.account). Para confirmar, digite o ID do projeto"
if ($confirmation -cne $ProjectId) {
    throw "Confirmação não corresponde ao ID do projeto; nenhuma alteração foi feita."
}

$projectArgs = @("--project=$ProjectId")
$runtimeAccount = "oestudo-runtime@$ProjectId.iam.gserviceaccount.com"
$deployerAccount = "oestudo-deployer@$ProjectId.iam.gserviceaccount.com"
$secretNames = @(
    "POSTGRES_PASSWORD",
    "FIREBASE_SERVICE_ACCOUNT",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_STREAM_API_TOKEN",
    "CLOUDFLARE_STREAM_CUSTOMER_CODE",
    "MERCADO_PAGO_ACCESS_TOKEN",
    "MERCADO_PAGO_WEBHOOK_SECRET"
)

Write-Host "Habilitando APIs necessárias..."
Invoke-Gcloud (@("services", "enable", "run.googleapis.com", "sqladmin.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com", "iam.googleapis.com", "iamcredentials.googleapis.com", "sts.googleapis.com", "storage.googleapis.com") + $projectArgs)

if (-not (Test-GcloudResource (@("artifacts", "repositories", "describe", $ArtifactRepository, "--location=$Region") + $projectArgs))) {
    Invoke-Gcloud (@("artifacts", "repositories", "create", $ArtifactRepository, "--repository-format=docker", "--location=$Region", "--description=Imagens do OestudoLiberta") + $projectArgs)
}

if (-not (Test-GcloudResource (@("sql", "instances", "describe", $SqlInstance) + $projectArgs))) {
    Write-Warning "Cloud SQL usa instância dedicada e gera cobrança contínua. Verifique preços e cotas da região antes de prosseguir."
    Invoke-Gcloud (@("sql", "instances", "create", $SqlInstance, "--database-version=POSTGRES_16", "--tier=db-custom-1-3840", "--region=$Region", "--storage-type=SSD", "--storage-size=20", "--storage-auto-increase", "--availability-type=zonal", "--backup-start-time=03:00", "--enable-point-in-time-recovery") + $projectArgs)
}

if (-not (Test-GcloudResource (@("sql", "databases", "describe", $DatabaseName, "--instance=$SqlInstance") + $projectArgs))) {
    Invoke-Gcloud (@("sql", "databases", "create", $DatabaseName, "--instance=$SqlInstance") + $projectArgs)
}

$bucketUri = "gs://$AssetsBucket"
if (-not (Test-GcloudResource @("storage", "buckets", "describe", $bucketUri, "--project=$ProjectId"))) {
    Invoke-Gcloud @("storage", "buckets", "create", $bucketUri, "--project=$ProjectId", "--location=$Region", "--uniform-bucket-level-access", "--public-access-prevention=enforced")
}

foreach ($serviceAccount in @(
    @{ Name = "oestudo-runtime"; Email = $runtimeAccount; DisplayName = "OestudoLiberta Cloud Run runtime" },
    @{ Name = "oestudo-deployer"; Email = $deployerAccount; DisplayName = "OestudoLiberta GitHub deploy" }
)) {
    if (-not (Test-GcloudResource (@("iam", "service-accounts", "describe", $serviceAccount.Email) + $projectArgs))) {
        Invoke-Gcloud (@("iam", "service-accounts", "create", $serviceAccount.Name, "--display-name=$($serviceAccount.DisplayName)") + $projectArgs)
    }
}

foreach ($role in @("roles/cloudsql.client")) {
    Invoke-Gcloud (@("projects", "add-iam-policy-binding", $ProjectId, "--member=serviceAccount:$runtimeAccount", "--role=$role", "--condition=None"))
}

foreach ($role in @("roles/run.admin", "roles/artifactregistry.writer", "roles/serviceusage.serviceUsageConsumer")) {
    Invoke-Gcloud (@("projects", "add-iam-policy-binding", $ProjectId, "--member=serviceAccount:$deployerAccount", "--role=$role", "--condition=None"))
}

Invoke-Gcloud (@("iam", "service-accounts", "add-iam-policy-binding", $runtimeAccount, "--member=serviceAccount:$deployerAccount", "--role=roles/iam.serviceAccountUser") + $projectArgs)
Invoke-Gcloud @("storage", "buckets", "add-iam-policy-binding", $bucketUri, "--member=serviceAccount:$runtimeAccount", "--role=roles/storage.objectUser")

foreach ($secretName in $secretNames) {
    if (-not (Test-GcloudResource (@("secrets", "describe", $secretName) + $projectArgs))) {
        Invoke-Gcloud (@("secrets", "create", $secretName, "--replication-policy=automatic") + $projectArgs)
    }
    Invoke-Gcloud (@("secrets", "add-iam-policy-binding", $secretName, "--member=serviceAccount:$runtimeAccount", "--role=roles/secretmanager.secretAccessor") + $projectArgs)
}

Write-Host ""
Write-Host "Provisionamento concluído. A instância SQL, o bucket e as contas de serviço foram configurados."
Write-Host "Nenhum valor secreto foi criado. Siga docs/sprint-6-google-cloud.md para cadastrar as versões dos segredos e configurar Workload Identity Federation."
Write-Host "Cloud SQL connection name: $ProjectId`:$Region`:$SqlInstance"
