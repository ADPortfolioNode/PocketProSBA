#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Reliable Windows startup for the PocketPro:SBA Docker stack.
  Duplicated from the successful PocketPro:NYL profile. Same flags, SBA resources.

.DESCRIPTION
  - Binds published ports from .env (DOCKER_BIND_HOST, FRONTEND_HOST_PORT, BACKEND_HOST_PORT)
  - Staged compose up: chroma/chromadb -> backend -> frontend
  - Verifies HTTP from the Windows host
  - POST /api/startup_init when present, else /api/health + /api/chat smoke
  - Optional -Test runs property regression if production_test.ps1 or backend/tests exist

.EXAMPLE
  .\start-windows.ps1
  .\start-windows.ps1 -Build -OpenBrowser
  .\start-windows.ps1 -Build -Test
  .\start-windows.ps1 -Recreate
#>
param(
    [switch]$Build,
    [switch]$Recreate,
    [switch]$OpenBrowser,
    [switch]$Test,
    [switch]$Reset,
    [ValidateSet("dev","prod")]
    [string]$Mode = "dev",
    [int]$MaxPortWaitSec = 120
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Monitor([string]$Level, [string]$Message) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) {
        "INFO" { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
    "[$timestamp] [$Level] $Message" | Out-File -FilePath $script:MonitorLog -Append
}

function Read-DotEnvValue([string]$Name, [string]$Default) {
    $envPath = Join-Path $PSScriptRoot ".env"
    if (-not (Test-Path $envPath)) { return $Default }
    foreach ($line in Get-Content $envPath) {
        if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.+?)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

function Ensure-EnvFiles {
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.template") { Copy-Item ".env.template" ".env" }
        elseif (Test-Path ".env.example") { Copy-Item ".env.example" ".env" }
        else { throw "Missing .env and .env.template / .env.example" }
        Write-Host "Created .env from template. Set GEMINI_API_KEY." -ForegroundColor Yellow
    }
    if ((Test-Path "backend\.env.example") -and -not (Test-Path "backend\.env")) {
        Copy-Item "backend\.env.example" "backend\.env"
    }
    $key = Read-DotEnvValue "GEMINI_API_KEY" ""
    if ([string]::IsNullOrWhiteSpace($key) -or $key -eq "your_api_key_here") {
        throw "GEMINI_API_KEY missing in .env — required for PocketPro:SBA chat."
    }
}

function Wait-DockerDaemon([int]$MaxSeconds = 180) {
    Write-Step "Waiting for Docker Desktop"
    $elapsed = 0
    while ($elapsed -lt $MaxSeconds) {
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Docker ready (${elapsed}s)" -ForegroundColor Green
            return $true
        }
        if ($elapsed -eq 30) {
            Write-Host "  Starting Docker Desktop..." -ForegroundColor Yellow
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    throw "Docker daemon not reachable after ${MaxSeconds}s. Open Docker Desktop manually."
}

function Invoke-Compose([string[]]$ComposeArgs) {
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $allArgs = $script:ComposeFileArgs + $ComposeArgs
        $output = & docker compose @allArgs 2>&1
        foreach ($line in $output) {
            if ($line -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $line.ToString()
            } else {
                Write-Host $line
            }
        }
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed ($LASTEXITCODE): $($allArgs -join ' ')"
        }
    } finally {
        $ErrorActionPreference = $prevEap
    }
}

function Get-VectorServiceName {
    $names = @("chroma", "chromadb", "chromadb_service")
    foreach ($n in $names) {
        $ErrorActionPreference = 'Continue'
        $svcs = & docker compose @script:ComposeFileArgs config --services 2>$null
        $ErrorActionPreference = "Stop"
        if ($svcs -match [regex]::Escape($n)) { return $n }
    }
    return "chroma"
}

function Repair-PortForwarding {
    Write-Step "Repairing Docker port forwarding (Windows)"
    Invoke-Compose @("restart", "backend", "frontend")
    Start-Sleep -Seconds 12
    Invoke-Compose @("up", "-d", "--force-recreate", "frontend")
    Start-Sleep -Seconds 10
}

$script:MonitorLog = "logs/startup_monitor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Ensure-EnvFiles

if ($Mode -eq "prod") {
    if (Test-Path "docker-compose.prod.yml") {
        $script:ComposeFileArgs = @("-f", "docker-compose.prod.yml")
    } else {
        $script:ComposeFileArgs = @("-f", "docker-compose.yml")
    }
} else {
    if (Test-Path "docker-compose.dev.yml") {
        $script:ComposeFileArgs = @("-f", "docker-compose.dev.yml")
    } else {
        $script:ComposeFileArgs = @("-f", "docker-compose.yml")
    }
}

$bindHost = Read-DotEnvValue "DOCKER_BIND_HOST" "127.0.0.1"
$frontendPort = [int](Read-DotEnvValue "FRONTEND_HOST_PORT" "3000")
$backendPort = [int](Read-DotEnvValue "BACKEND_HOST_PORT" "5000")
$chromaPort = [int](Read-DotEnvValue "CHROMA_HOST_PORT" "8000")
if ([string]::IsNullOrWhiteSpace($bindHost)) { $bindHost = "127.0.0.1" }

Write-Host "PocketPro:SBA Windows Start" -ForegroundColor White
Write-Host "  mode      : $Mode"
Write-Host "  compose   : $($script:ComposeFileArgs -join ' ')"
Write-Host "  bind host : $bindHost"
Write-Host "  ports     : frontend=$frontendPort backend=$backendPort chroma=$chromaPort"
Write-Host "  app URL   : http://${bindHost}:${frontendPort}/" -ForegroundColor Green

$waitScript = Join-Path $PSScriptRoot "scripts\Wait-PocketProSBAPorts.ps1"
if (-not (Test-Path $waitScript)) { throw "Missing $waitScript" }
. $waitScript

if ($Test) {
    Write-Host "REGRESSION TEST MONITORING ENABLED" -ForegroundColor Cyan
    Write-Host "Monitor log: $script:MonitorLog"
}

Wait-DockerDaemon | Out-Null
if ($Test) { Write-Monitor "SUCCESS" "Docker daemon responsive" }

if ($Reset) {
    Write-Step "Full reset"
    Invoke-Compose @("down", "-v")
    docker system prune -f
}

if ($Recreate) {
    Write-Step "Recreating stack"
    Invoke-Compose @("down", "--timeout", "15")
    Start-Sleep -Seconds 2
}

if ($Build) {
    Write-Step "Building images"
    $env:DOCKER_BUILDKIT = "0"
    $env:COMPOSE_DOCKER_CLI_BUILD = "0"
    Invoke-Compose @("build")
}

$vector = Get-VectorServiceName
Write-Step "Starting services (staged) vector=$vector"
Invoke-Compose @("up", "-d", "--force-recreate", $vector)
Start-Sleep -Seconds 8
Invoke-Compose @("up", "-d", "--force-recreate", "backend")
Start-Sleep -Seconds 15
Invoke-Compose @("up", "-d", "--force-recreate", "frontend")

Write-Step "Verifying host connectivity"
$result = Wait-PocketProSBAPorts -FrontendPort $frontendPort -BackendPort $backendPort -BindHost $bindHost -MaxWaitSec $MaxPortWaitSec

if (-not $result.Ok) {
    Repair-PortForwarding
    $result = Wait-PocketProSBAPorts -FrontendPort $frontendPort -BackendPort $backendPort -BindHost $bindHost -MaxWaitSec 60
}

if (-not $result.Ok) {
    Write-Host "`nPort forwarding still failing from Windows." -ForegroundColor Red
    Write-Host "  1. Restart Docker Desktop"
    Write-Host "  2. Re-run: .\start-windows.ps1 -Recreate"
    Write-Host "  3. Open: http://${bindHost}:${frontendPort}/"
    Invoke-Compose @("ps")
    exit 1
}

$backendUrl = "http://${bindHost}:${backendPort}"
$forcePayload = if ($Build) { '{"force": true}' } else { '{"force": false}' }
Write-Step "Triggering SBA backend startup initialization"
try {
    $init = Invoke-WebRequest -Uri "${backendUrl}/api/startup_init" -Method POST -ContentType "application/json" -Body $forcePayload -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    Write-Host "  startup_init HTTP $($init.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  /api/startup_init not present or failed — falling back to health + chat smoke" -ForegroundColor Yellow
    try {
        $h = Invoke-WebRequest -Uri "${backendUrl}/api/health" -UseBasicParsing -TimeoutSec 15
        Write-Host "  health HTTP $($h.StatusCode)" -ForegroundColor Green
    } catch {
        throw "SBA health check failed: $($_.Exception.Message)"
    }
    try {
        $c = Invoke-WebRequest -Uri "${backendUrl}/api/chat" -Method POST -ContentType "application/json" -Body '{"message":"hello"}' -UseBasicParsing -TimeoutSec 60
        Write-Host "  chat smoke HTTP $($c.StatusCode) ($($c.Content.Length) bytes)" -ForegroundColor Green
    } catch {
        Write-Host "  chat smoke failed: $($_.Exception.Message)" -ForegroundColor Yellow
        if ($Test) { throw }
    }
}

Write-Step "Stack healthy"
Invoke-Compose @("ps")
Write-Host "`nApp ready: $($result.FrontendUrl)" -ForegroundColor Green

if ($Test) {
    Write-Step "Running SBA regression"
    if (Test-Path "$PSScriptRoot\production_test.ps1") {
        & "$PSScriptRoot\production_test.ps1" -WriteFile -Verbose
    } elseif (Get-Command pytest -ErrorAction SilentlyContinue) {
        pytest "$PSScriptRoot\backend\tests" -q
    } else {
        Write-Host "No production_test.ps1 / pytest — smoke already completed." -ForegroundColor Yellow
    }
}

if ($OpenBrowser) {
    Start-Process $result.FrontendUrl
}

exit 0
