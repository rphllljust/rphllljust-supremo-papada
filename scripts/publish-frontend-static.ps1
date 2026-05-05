[CmdletBinding()]
param(
    [ValidateSet("development", "homolog", "production")]
    [string]$Environment = "development"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "SUAP\frontend"
$backendStaticDir = Join-Path $repoRoot "SUAP\backend\static"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    throw "Frontend nao encontrado em: $frontendDir"
}

if (-not (Test-Path $backendStaticDir)) {
    throw "Diretorio static do backend nao encontrado em: $backendStaticDir"
}

$buildScript = switch ($Environment) {
    "development" { "build:development" }
    "homolog" { "build:homolog" }
    "production" { "build:production" }
    default { "build:development" }
}

Push-Location $frontendDir
try {
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        throw "npm.cmd nao encontrado no PATH."
    }

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "Instalando dependencias do frontend..." -ForegroundColor Cyan
        & npm.cmd install
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar dependencias do frontend."
        }
    }

    Write-Host "Gerando build do frontend ($Environment)..." -ForegroundColor Cyan
    & npm.cmd run $buildScript
    if ($LASTEXITCODE -ne 0) {
        throw "Falha no build do frontend."
    }
}
finally {
    Pop-Location
}

$frontendDistDir = Join-Path $frontendDir "dist"
if (-not (Test-Path $frontendDistDir)) {
    throw "Diretorio dist nao encontrado em: $frontendDistDir"
}

Write-Host "Sincronizando dist -> backend/static..." -ForegroundColor Cyan
robocopy $frontendDistDir $backendStaticDir /MIR /R:1 /W:1 | Out-Null

$versionStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$htmlTargets = @(
    (Join-Path $backendStaticDir "index.html"),
    (Join-Path $backendStaticDir "vue.html")
)

foreach ($htmlPath in $htmlTargets) {
    if (-not (Test-Path $htmlPath)) {
        continue
    }

    $html = Get-Content $htmlPath -Raw
    $html = $html -replace '([?&])v=[^"&'' >]+', ''
    $html = $html -replace '((?:src|href)=["'']/static/[^"'']+)(["''])', ('$1?v=' + $versionStamp + '$2')
    Set-Content -Path $htmlPath -Value $html -NoNewline
}

Write-Host "Publicacao concluida. Versao aplicada: $versionStamp" -ForegroundColor Green
