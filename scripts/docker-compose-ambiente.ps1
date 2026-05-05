[CmdletBinding()]
param(
    [ValidateSet("development", "homolog", "production")]
    [string]$Environment,

    [ValidateSet("up", "rerun", "down", "restart", "ps")]
    [string]$Action,

    [switch]$NoBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Credenciais de dev — sobrescreviveis por variavel de ambiente
$DevAdminCpf      = if ($env:DEV_ADMIN_CPF)      { $env:DEV_ADMIN_CPF }      else { "90000010057" }
$DevAdminPassword = if ($env:DEV_ADMIN_PASSWORD)  { $env:DEV_ADMIN_PASSWORD }  else { "admin" }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Assert-DockerSuccess {
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Select-Environment {
    param([string]$CurrentValue)

    if ($CurrentValue) { return $CurrentValue }

    Write-Host "Selecione o ambiente Docker Compose:" -ForegroundColor Yellow
    Write-Host "[1] development" -ForegroundColor Gray
    Write-Host "[2] homolog"     -ForegroundColor Gray
    Write-Host "[3] production"  -ForegroundColor Gray

    $choice = (Read-Host "Digite 1, 2 ou 3 (Enter = development)").Trim()
    switch ($choice) {
        "2" { return "homolog" }
        "3" { return "production" }
        default { return "development" }
    }
}

function Select-Action {
    param([string]$CurrentValue)

    if ($CurrentValue) { return $CurrentValue }

    Write-Host "Selecione a acao:" -ForegroundColor Yellow
    Write-Host "[1] up      -> sobe o ambiente"             -ForegroundColor Gray
    Write-Host "[2] rerun   -> derruba e sobe novamente"    -ForegroundColor Gray
    Write-Host "[3] down    -> derruba o ambiente"          -ForegroundColor Gray
    Write-Host "[4] restart -> reinicia os containers"      -ForegroundColor Gray
    Write-Host "[5] ps      -> mostra o estado atual"       -ForegroundColor Gray

    $choice = (Read-Host "Digite 1, 2, 3, 4 ou 5 (Enter = up)").Trim()
    switch ($choice) {
        "2" { return "rerun" }
        "3" { return "down" }
        "4" { return "restart" }
        "5" { return "ps" }
        default { return "up" }
    }
}

function Get-ComposeConfig {
    param(
        [Parameter(Mandatory)] [string]$SelectedEnvironment,
        [Parameter(Mandatory)] [string]$WorkspaceRoot
    )

    $baseFile    = Join-Path $WorkspaceRoot "docker-compose.yml"
    $overlayFile = Join-Path $WorkspaceRoot "docker-compose.$SelectedEnvironment.yml"

    if (-not (Test-Path $baseFile)) {
        throw "Arquivo base nao encontrado: $baseFile"
    }
    if (-not (Test-Path $overlayFile)) {
        throw "Arquivo de compose do ambiente nao encontrado: $overlayFile"
    }

    $projectName = switch ($SelectedEnvironment) {
        "homolog"    { "suap-homolog" }
        "production" { "suap-prod" }
        default      { "suap-dev" }
    }

    return @{
        ProjectName = $projectName
        BaseFile    = $baseFile
        OverlayFile = $overlayFile
    }
}

function Invoke-DockerUp {
    param(
        [Parameter(Mandatory)] [string[]]$ComposeArgs,
        [Parameter(Mandatory)] [string]$SelectedEnvironment,
        [bool]$NoBuild = $false
    )

    Write-Host "Subindo ambiente com Docker Compose..." -ForegroundColor Green

    $upArgs = $ComposeArgs + @("up", "-d")
    if (-not $NoBuild) { $upArgs += "--build" }

    & docker @upArgs
    Assert-DockerSuccess

    Invoke-InitialAdminBootstrap -ComposeArgs $ComposeArgs -SelectedEnvironment $SelectedEnvironment
    Invoke-DevelopmentSeed       -ComposeArgs $ComposeArgs -SelectedEnvironment $SelectedEnvironment
}

function Invoke-InitialAdminBootstrap {
    param(
        [Parameter(Mandatory)] [string[]]$ComposeArgs,
        [Parameter(Mandatory)] [string]$SelectedEnvironment
    )

    $maxAttempts  = 12
    $delaySeconds = 5

    Write-Host "Verificando bootstrap automatico do administrador inicial..." -ForegroundColor Cyan

    $bootstrapArgs = $ComposeArgs + @("exec", "-T", "backend", "python", "manage.py", "bootstrap_initial_admin")
    if ($SelectedEnvironment -eq "development") {
        $bootstrapArgs += @("--cpf", $DevAdminCpf, "--password", $DevAdminPassword, "--force", "--no-force-password-change")
    }

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        $output = & docker @bootstrapArgs 2>&1

        if ($LASTEXITCODE -eq 0) {
            $msg = ($output | Out-String).Trim()
            if ($msg) { Write-Host $msg -ForegroundColor Green }
            return
        }

        $outputStr = $output | Out-String
        if ($outputStr -match "Informe o CPF do administrador inicial" -or $outputStr -match "INITIAL_ADMIN_CPF") {
            throw "Falha de configuracao no bootstrap automatico do administrador inicial no container backend.`n$outputStr"
        }

        if ($attempt -eq $maxAttempts) {
            throw "Falha ao executar o bootstrap automatico do administrador inicial no container backend."
        }

        Write-Host "Backend ainda nao esta pronto. Nova tentativa em $delaySeconds segundos... ($attempt/$maxAttempts)" -ForegroundColor DarkYellow
        Start-Sleep -Seconds $delaySeconds
    }
}

function Invoke-DevelopmentSeed {
    param(
        [Parameter(Mandatory)] [string[]]$ComposeArgs,
        [Parameter(Mandatory)] [string]$SelectedEnvironment
    )

    if ($SelectedEnvironment -ne "development") { return }

    Write-Host "Executando seed academico de desenvolvimento..." -ForegroundColor Cyan
    & docker @ComposeArgs exec -T backend python manage.py seed_development_data --reset
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar o seed academico de desenvolvimento no container backend."
    }
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker nao foi encontrado no PATH. Instale o Docker Desktop antes de continuar."
}

$workspaceRoot       = Split-Path -Parent $PSScriptRoot
$selectedEnvironment = Select-Environment -CurrentValue $Environment
$selectedAction      = Select-Action      -CurrentValue $Action
$composeConfig       = Get-ComposeConfig  -SelectedEnvironment $selectedEnvironment -WorkspaceRoot $workspaceRoot

$composeArgs = @(
    "compose",
    "-p", $composeConfig.ProjectName,
    "-f", $composeConfig.BaseFile,
    "-f", $composeConfig.OverlayFile
)

Push-Location $workspaceRoot
try {
    Write-Host "Ambiente : $selectedEnvironment"          -ForegroundColor Yellow
    Write-Host "Projeto  : $($composeConfig.ProjectName)" -ForegroundColor Yellow
    Write-Host "Acao     : $selectedAction"               -ForegroundColor Yellow

    switch ($selectedAction) {
        "up" {
            Invoke-DockerUp -ComposeArgs $composeArgs -SelectedEnvironment $selectedEnvironment -NoBuild $NoBuild
        }
        "rerun" {
            Write-Host "Derrubando containers atuais do ambiente..." -ForegroundColor Cyan
            & docker @composeArgs down --remove-orphans
            Assert-DockerSuccess
            Invoke-DockerUp -ComposeArgs $composeArgs -SelectedEnvironment $selectedEnvironment -NoBuild $NoBuild
        }
        "down" {
            Write-Host "Derrubando ambiente..." -ForegroundColor Cyan
            & docker @composeArgs down --remove-orphans
            Assert-DockerSuccess
        }
        "restart" {
            Write-Host "Reiniciando containers do ambiente..." -ForegroundColor Cyan
            & docker @composeArgs restart
            Assert-DockerSuccess
        }
        "ps" {
            # sem acao previa — cai direto no bloco final
        }
    }

    Write-Host "Estado final dos servicos:" -ForegroundColor Cyan
    & docker @composeArgs ps
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
