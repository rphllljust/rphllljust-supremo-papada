[CmdletBinding()]
param(
    [int]$Port = 8005,
    [string]$Token = "idep_sheets_bc4d78f7b1d5447ab19d537d2b985781e9a363133e574a96",
    [int]$MaxRetries = 20,
    [switch]$SkipBackendRestart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$tunnelDir = Join-Path $workspaceRoot ".tunnel"
New-Item -ItemType Directory -Path $tunnelDir -Force | Out-Null

$composeBaseFile = Join-Path $workspaceRoot "docker-compose.yml"
$composeDevFile = Join-Path $workspaceRoot "docker-compose.development.yml"
if (-not (Test-Path $composeBaseFile) -or -not (Test-Path $composeDevFile)) {
    throw "Arquivos docker compose nao encontrados no workspace."
}

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & docker compose -f $composeBaseFile -f $composeDevFile @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar docker compose: $($Args -join ' ')"
    }
}

function Test-Url200 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Retries = 10,
        [int]$DelaySeconds = 2,
        [int]$TimeoutSec = 20
    )

    for ($i = 0; $i -lt $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec $TimeoutSec
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds $DelaySeconds
            continue
        }
        Start-Sleep -Seconds $DelaySeconds
    }

    return $false
}

function Test-UrlExternally {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Retries = 6,
        [int]$DelaySeconds = 2
    )

    $externalUrl = "https://r.jina.ai/http://$($Url -replace '^https?://', '')"

    for ($i = 0; $i -lt $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $externalUrl -Method Get -UseBasicParsing -TimeoutSec 30
            if ($response.StatusCode -eq 200 -and $response.Content -match "secao,id,titulo,descricao,valor,data,status,href") {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds $DelaySeconds
            continue
        }
        Start-Sleep -Seconds $DelaySeconds
    }

    return $false
}

function Stop-ExistingTunnelProcesses {
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -eq "cloudflared.exe" -or ($_.Name -eq "node.exe" -and $_.CommandLine -match "localtunnel") } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
}

function Start-CloudflareTunnel {
    param(
        [int]$TargetPort,
        [string]$LogPath
    )

    $cf = "C:\Users\IDEP\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
    if (-not (Test-Path $cf)) {
        throw "cloudflared nao encontrado em '$cf'."
    }

    if (Test-Path $LogPath) { Remove-Item $LogPath -Force -ErrorAction SilentlyContinue }

    $args = @("tunnel", "--url", "http://127.0.0.1:$TargetPort", "--no-autoupdate", "--logfile", $LogPath)
    $proc = Start-Process -FilePath $cf -ArgumentList $args -PassThru

    $url = $null
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 1
        if (-not (Test-Path $LogPath)) { continue }
        $content = (Get-Content $LogPath -Raw -ErrorAction SilentlyContinue) -as [string]
        if (-not $content) { continue }

        $match = [regex]::Match($content, "https://[a-z0-9-]+\.trycloudflare\.com")
        if ($match.Success) {
            $url = $match.Value
            break
        }
    }

    if (-not $url) {
        try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
        return $null
    }

    return @{
        Name = "cloudflare"
        Url = $url
        Pid = $proc.Id
    }
}

function Update-ComposePublicUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PublicUrl
    )

    $content = Get-Content -Path $composeDevFile -Raw
    $updatedContent = [regex]::Replace(
        $content,
        "(?m)^\s*GOOGLE_SHEETS_PUBLIC_BASE_URL:.*$",
        "      GOOGLE_SHEETS_PUBLIC_BASE_URL: $PublicUrl"
    )

    if ($updatedContent -ne $content) {
        Set-Content -Path $composeDevFile -Value $updatedContent -Encoding UTF8
    }
}

Stop-ExistingTunnelProcesses

Write-Host "Subindo backend para integracao CSV..." -ForegroundColor Cyan
Invoke-Compose -Args @("up", "-d", "postgres", "backend")

$localCsvUrl = "http://127.0.0.1:$Port/api/v1/dashboard/overview-sheets.csv?token=$Token"
if (-not (Test-Url200 -Url $localCsvUrl -Retries $MaxRetries -DelaySeconds 2 -TimeoutSec 15)) {
    throw "Rota CSV local nao respondeu 200: $localCsvUrl"
}

$cloudflareLog = Join-Path $tunnelDir "cloudflared.log"
$tunnel = $null

Write-Host "Tentando tunnel Cloudflare..." -ForegroundColor Cyan
$tunnel = Start-CloudflareTunnel -TargetPort $Port -LogPath $cloudflareLog
if ($tunnel) {
    $candidateCsv = "$($tunnel.Url)/api/v1/dashboard/overview-sheets.csv?token=$Token"
    if (-not (Test-Url200 -Url $candidateCsv -Retries 8 -DelaySeconds 2 -TimeoutSec 20)) {
        try { Stop-Process -Id $tunnel.Pid -Force -ErrorAction SilentlyContinue } catch {}
        $tunnel = $null
    }
    elseif (-not (Test-UrlExternally -Url $candidateCsv -Retries 6 -DelaySeconds 2)) {
        try { Stop-Process -Id $tunnel.Pid -Force -ErrorAction SilentlyContinue } catch {}
        $tunnel = $null
    }
}

if (-not $tunnel) {
    throw "Nao foi possivel obter uma URL Cloudflare estavel para Google Sheets. Rode o script novamente."
}

Update-ComposePublicUrl -PublicUrl $tunnel.Url

if (-not $SkipBackendRestart) {
    Write-Host "Reiniciando backend com URL publica atualizada..." -ForegroundColor Cyan
    Invoke-Compose -Args @("up", "-d", "backend")
}

$csvUrl = "$($tunnel.Url)/api/v1/dashboard/overview-sheets.csv?token=$Token"
if (-not (Test-Url200 -Url $csvUrl -Retries $MaxRetries -DelaySeconds 3 -TimeoutSec 20)) {
    throw "Tunnel criado, mas URL publica sem 200 apos tentativas: $csvUrl"
}

Write-Output "Tunnel ativo."
Write-Output "Provedor: $($tunnel.Name)"
Write-Output "PID: $($tunnel.Pid)"
Write-Output "URL publica: $($tunnel.Url)"
Write-Output "CSV: $csvUrl"
Write-Output "Status: 200 OK"
Write-Output "Formula Google Sheets:"
Write-Output "=IMPORTDATA(\"$csvUrl\")"
