param(
    [ValidateSet("development", "homolog", "production")]
    [string]$Environment,
    [int]$Port = 5173,
    [switch]$HostPublica
)

$ErrorActionPreference = "Stop"

function Select-Environment {
    param(
        [string]$CurrentValue
    )

    if ($CurrentValue) {
        return $CurrentValue
    }

    Write-Host "Selecione o ambiente:" -ForegroundColor Yellow
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

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendRoot = Resolve-Path (Join-Path $scriptDir "..")

Push-Location $frontendRoot
try {
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        throw "npm.cmd nao foi encontrado no PATH. Instale o Node.js/NPM antes de rodar o frontend."
    }

    if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
        Write-Host "node_modules nao encontrado. Instalando dependencias..."
        & npm.cmd install
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    $selectedEnvironment = Select-Environment -CurrentValue $Environment

    $scriptName = switch ($selectedEnvironment) {
        "homolog" { "dev:homolog" }
        "production" { "dev:production" }
        default { "dev" }
    }

    Write-Host "Ambiente selecionado: $selectedEnvironment"

    $viteArgs = @("run", $scriptName, "--", "--port", $Port)

    if ($HostPublica) {
        $viteArgs += "--host"
    }

    & npm.cmd @viteArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}