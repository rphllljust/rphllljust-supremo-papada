[CmdletBinding()]
param(
	[ValidateSet("development", "homolog", "production")]
	[string]$Environment = "development",
	[string]$HostAddress = "127.0.0.1",
	[int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# scripts/rodar.ps1 -> volta para a raiz do projeto (pasta pai de scripts)
$projectRoot = Split-Path -Parent $PSScriptRoot
$activateScript = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
$managePy = Join-Path $projectRoot "manage.py"

if (-not (Test-Path -Path $managePy)) {
	Write-Error "Arquivo manage.py não encontrado em: $managePy"
}

if (-not (Test-Path -Path $activateScript)) {
	Write-Error "Virtual environment não encontrado em: $activateScript"
}

Push-Location $projectRoot
$previousAppEnv = $env:APP_ENV
try {
	Write-Host "Ativando ambiente virtual..." -ForegroundColor Cyan
	. $activateScript

	$env:APP_ENV = $Environment
	Write-Host "Ambiente selecionado: $Environment" -ForegroundColor Yellow

	Write-Host "Iniciando servidor Django em $HostAddress`:$Port..." -ForegroundColor Green
	python manage.py runserver "$HostAddress`:$Port"
}
finally {
	if ($null -ne $previousAppEnv) {
		$env:APP_ENV = $previousAppEnv
	} else {
		Remove-Item Env:APP_ENV -ErrorAction SilentlyContinue
	}
	Pop-Location
}
