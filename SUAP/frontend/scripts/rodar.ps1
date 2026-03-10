param(
    [int]$Port = 5173,
    [switch]$HostPublica
)

$ErrorActionPreference = "Stop"

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

    $viteArgs = @("run", "dev", "--", "--port", $Port)

    if ($HostPublica) {
        $viteArgs += "--host"
    }

    & npm.cmd @viteArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}