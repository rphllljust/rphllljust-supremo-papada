[CmdletBinding()]
param(
	[ValidateSet("development", "homolog", "production")]
	[string]$Environment,
	[string]$HostAddress = "127.0.0.1",
	[int]$Port = 8000
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

	Write-Host "Selecione o ambiente:" -ForegroundColor Yellow
	Write-Host "[1] development" -ForegroundColor Gray
	Write-Host "[2] homolog" -ForegroundColor Gray
	Write-Host "[3] production" -ForegroundColor Gray

	$choice = Read-Host "Digite 1, 2 ou 3 (Enter = development)"

	switch (($choice ?? "").Trim()) {
		"2" { return "homolog" }
		"3" { return "production" }
		default { return "development" }
	}
}

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

	$selectedEnvironment = Select-Environment -CurrentValue $Environment

	$env:APP_ENV = $selectedEnvironment
	Write-Host "Ambiente selecionado: $selectedEnvironment" -ForegroundColor Yellow

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
