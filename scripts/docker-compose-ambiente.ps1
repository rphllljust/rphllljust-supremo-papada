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

function Select-Environment {
    param(
        [string]$CurrentValue
    )

    if ($CurrentValue) {
        return $CurrentValue
    }

    Write-Host "Selecione o ambiente Docker Compose:" -ForegroundColor Yellow
    Write-Host "[1] development" -ForegroundColor Gray
    Write-Host "[2] homolog" -ForegroundColor Gray
    Write-Host "[3] production" -ForegroundColor Gray

    $choice = Read-Host "Digite 1, 2 ou 3 (Enter = development)"
    if ($null -eq $choice) {
        $choice = ""
    }

    switch ($choice.Trim()) {
        "2" { return "homolog" }
        "3" { return "production" }
        default { return "development" }
    }
}

function Select-Action {
    param(
        [string]$CurrentValue
    )

    if ($CurrentValue) {
        return $CurrentValue
    }

    Write-Host "Selecione a acao:" -ForegroundColor Yellow
    Write-Host "[1] up     -> sobe o ambiente" -ForegroundColor Gray
    Write-Host "[2] rerun  -> derruba e sobe novamente" -ForegroundColor Gray
    Write-Host "[3] down   -> derruba o ambiente" -ForegroundColor Gray
    Write-Host "[4] restart -> reinicia os containers" -ForegroundColor Gray
    Write-Host "[5] ps     -> mostra o estado atual" -ForegroundColor Gray

    $choice = Read-Host "Digite 1, 2, 3, 4 ou 5 (Enter = up)"
    if ($null -eq $choice) {
        $choice = ""
    }

    switch ($choice.Trim()) {
        "2" { return "rerun" }
        "3" { return "down" }
        "4" { return "restart" }
        "5" { return "ps" }
        default { return "up" }
    }
}

function Invoke-InitialAdminBootstrap {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$ComposeArgs
    )

    $maxAttempts = 12
    $delaySeconds = 5

    Write-Host "Verificando bootstrap automatico do administrador inicial..." -ForegroundColor Cyan

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        $bootstrapOutput = & docker @ComposeArgs exec -T backend python manage.py bootstrap_initial_admin 2>&1
        if ($LASTEXITCODE -eq 0) {
            return
        }

        $bootstrapMessage = ($bootstrapOutput | Out-String)
        if ($bootstrapMessage -match "Informe o CPF do administrador inicial" -or $bootstrapMessage -match "INITIAL_ADMIN_CPF") {
            throw "Falha de configuracao no bootstrap automatico do administrador inicial no container backend.`n$bootstrapMessage"
        }

        if ($attempt -eq $maxAttempts) {
            throw "Falha ao executar o bootstrap automatico do administrador inicial no container backend."
        }

        Write-Host "Backend ainda nao esta pronto para o bootstrap. Nova tentativa em $delaySeconds segundos... ($attempt/$maxAttempts)" -ForegroundColor DarkYellow
        Start-Sleep -Seconds $delaySeconds
    }
}

function Invoke-DevelopmentSeed {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$ComposeArgs,
        [Parameter(Mandatory = $true)]
        [string]$SelectedEnvironment
    )

    if ($SelectedEnvironment -ne "development") {
        return
    }

    Write-Host "Executando seed academico de desenvolvimento..." -ForegroundColor Cyan
    & docker @ComposeArgs exec -T backend python manage.py seed_development_data --reset
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar o seed academico de desenvolvimento no container backend."
    }
}

function Get-ComposeConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SelectedEnvironment,
        [Parameter(Mandatory = $true)]
        [string]$WorkspaceRoot
    )

    $overlayFile = Join-Path $WorkspaceRoot "docker-compose.$SelectedEnvironment.yml"
    if (-not (Test-Path -Path $overlayFile)) {
        throw "Arquivo de compose do ambiente nao encontrado: $overlayFile"
    }

    $projectName = switch ($SelectedEnvironment) {
        "homolog" { "suap-homolog" }
        "production" { "suap-prod" }
        default { "suap-dev" }
    }

    return @{
        ProjectName = $projectName
        BaseFile = Join-Path $WorkspaceRoot "docker-compose.yml"
        OverlayFile = $overlayFile
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker nao foi encontrado no PATH. Instale o Docker Desktop antes de continuar."
}

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$selectedEnvironment = Select-Environment -CurrentValue $Environment
$selectedAction = Select-Action -CurrentValue $Action
$composeConfig = Get-ComposeConfig -SelectedEnvironment $selectedEnvironment -WorkspaceRoot $workspaceRoot

$composeArgs = @(
    "compose",
    "-p", $composeConfig.ProjectName,
    "-f", $composeConfig.BaseFile,
    "-f", $composeConfig.OverlayFile
)

Push-Location $workspaceRoot
try {
    Write-Host "Ambiente selecionado: $selectedEnvironment" -ForegroundColor Yellow
    Write-Host "Projeto Compose: $($composeConfig.ProjectName)" -ForegroundColor Yellow
    Write-Host "Acao: $selectedAction" -ForegroundColor Yellow

    switch ($selectedAction) {
        "rerun" {
            Write-Host "Derrubando containers atuais do ambiente..." -ForegroundColor Cyan
            & docker @composeArgs down --remove-orphans
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }

            Write-Host "Subindo ambiente com Docker Compose..." -ForegroundColor Green
            $upArgs = @($composeArgs + @("up", "-d"))
            if (-not $NoBuild) {
                $upArgs += "--build"
            }

            & docker @upArgs
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }

            Invoke-InitialAdminBootstrap -ComposeArgs $composeArgs
            Invoke-DevelopmentSeed -ComposeArgs $composeArgs -SelectedEnvironment $selectedEnvironment
        }
        "up" {
            Write-Host "Subindo ambiente com Docker Compose..." -ForegroundColor Green
            $upArgs = @($composeArgs + @("up", "-d"))
            if (-not $NoBuild) {
                $upArgs += "--build"
            }

            & docker @upArgs
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }

            Invoke-InitialAdminBootstrap -ComposeArgs $composeArgs
            Invoke-DevelopmentSeed -ComposeArgs $composeArgs -SelectedEnvironment $selectedEnvironment
        }
        "down" {
            Write-Host "Derrubando ambiente..." -ForegroundColor Cyan
            & docker @composeArgs down --remove-orphans
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }
        }
        "restart" {
            Write-Host "Reiniciando containers do ambiente..." -ForegroundColor Cyan
            & docker @composeArgs restart
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }
        }
        "ps" {
            Write-Host "Estado atual dos servicos:" -ForegroundColor Cyan
        }
    }

    Write-Host "Estado final dos servicos:" -ForegroundColor Cyan
    & docker @composeArgs ps
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}