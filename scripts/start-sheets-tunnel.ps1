[CmdletBinding()]
param(
    [int]$Port = 8005,
    [string]$Subdomain = "idep-dashboard-ro-2026",
    [string]$Token = "idep_sheets_bc4d78f7b1d5447ab19d537d2b985781e9a363133e574a96"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$tunnelDir = Join-Path $workspaceRoot ".tunnel"
New-Item -ItemType Directory -Path $tunnelDir -Force | Out-Null

$outLog = Join-Path $tunnelDir "localtunnel.out.log"
$errLog = Join-Path $tunnelDir "localtunnel.err.log"

$npx = "C:\Program Files\nodejs\npx.cmd"
if (-not (Test-Path $npx)) {
    throw "npx nao encontrado em '$npx'."
}

Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "node.exe" -and $_.CommandLine -match "localtunnel" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

Start-Sleep -Milliseconds 400
if (Test-Path $outLog) { Remove-Item $outLog -Force -ErrorAction SilentlyContinue }
if (Test-Path $errLog) { Remove-Item $errLog -Force -ErrorAction SilentlyContinue }

$args = @("--yes", "localtunnel", "--port", "$Port", "--local-host", "127.0.0.1", "--subdomain", $Subdomain)
$proc = Start-Process -FilePath $npx -ArgumentList $args -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru

$url = $null
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    if (-not (Test-Path $outLog)) { continue }

    $content = (Get-Content $outLog -Raw -ErrorAction SilentlyContinue) -as [string]
    if (-not $content) { continue }
    $match = [regex]::Match($content, "https://[a-z0-9-]+\.loca\.lt")
    if ($match.Success) {
        $url = $match.Value
        break
    }
}

if (-not $url) {
    Write-Host "Nao foi possivel obter a URL do tunnel." -ForegroundColor Red
    if (Test-Path $outLog) { Get-Content $outLog -ErrorAction SilentlyContinue | Select-Object -First 60 }
    if (Test-Path $errLog) { Get-Content $errLog -ErrorAction SilentlyContinue | Select-Object -First 60 }
    exit 1
}

$csvUrl = "$url/api/v1/dashboard/overview-sheets.csv?token=$Token"

Write-Output "Tunnel ativo."
Write-Output "PID: $($proc.Id)"
Write-Output "URL Sheets: $csvUrl"
Write-Output "Formula Google Sheets:"
Write-Output "=IMPORTDATA(""$csvUrl"")"
