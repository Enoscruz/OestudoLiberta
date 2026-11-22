[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern("^[a-z][a-z0-9-]{4,28}[a-z0-9]$")]
    [string]$ProjectId,

    [Parameter(Mandatory)]
    [ValidatePattern("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")]
    [string]$GitHubRepository,

    [string]$PoolId = "github-actions",
    [string]$ProviderId = "github",
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

if (-not $Apply) {
    throw "Este script altera IAM do GCP. Revise docs/sprint-6-google-cloud.md e execute novamente com -Apply."
}

$accounts = (& gcloud auth list --format=json | ConvertFrom-Json)
$activeAccount = $accounts | Where-Object { $_.status -eq "ACTIVE" } | Select-Object -First 1
if (-not $activeAccount) {
    throw "Nenhuma conta GCP ativa. Execute: gcloud auth login"
}

$confirmation = Read-Host "Vincular GitHub '$GitHubRepository' ao deployer do projeto '$ProjectId'. Digite o ID do projeto para confirmar"
if ($confirmation -cne $ProjectId) {
    throw "Confirmação não corresponde ao ID do projeto; nenhuma alteração foi feita."
}

$projectNumber = (& gcloud projects describe $ProjectId --format="value(projectNumber)")
if ($LASTEXITCODE -ne 0 -or -not $projectNumber) {
    throw "Não foi possível obter o número do projeto '$ProjectId'."
}

$poolArgs = @(
    "iam", "workload-identity-pools", "describe", $PoolId,
    "--location=global", "--project=$ProjectId"
)
& gcloud @poolArgs *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gcloud @(
        "iam", "workload-identity-pools", "create", $PoolId,
        "--location=global",
        "--display-name=GitHub Actions",
        "--project=$ProjectId"
    )
}

$providerArgs = @(
    "iam", "workload-identity-pools", "providers", "describe", $ProviderId,
    "--workload-identity-pool=$PoolId", "--location=global", "--project=$ProjectId"
)
& gcloud @providerArgs *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gcloud @(
        "iam", "workload-identity-pools", "providers", "create-oidc", $ProviderId,
        "--workload-identity-pool=$PoolId",
        "--location=global",
        "--issuer-uri=https://token.actions.githubusercontent.com",
        "--attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository",
        "--attribute-condition=assertion.repository=='$GitHubRepository'",
        "--project=$ProjectId"
    )
}

$deployer = "oestudo-deployer@$ProjectId.iam.gserviceaccount.com"
$principal = "principalSet://iam.googleapis.com/projects/$projectNumber/locations/global/workloadIdentityPools/$PoolId/attribute.repository/$GitHubRepository"
Invoke-Gcloud @(
    "iam", "service-accounts", "add-iam-policy-binding", $deployer,
    "--role=roles/iam.workloadIdentityUser",
    "--member=$principal",
    "--project=$ProjectId"
)

Write-Host ""
Write-Host "Workload Identity Federation configurada para $GitHubRepository."
Write-Host "Workload Identity Provider: projects/$projectNumber/locations/global/workloadIdentityPools/$PoolId/providers/$ProviderId"
Write-Host "Service account: $deployer"
