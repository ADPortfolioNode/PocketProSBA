function Wait-PocketProSBAPorts {
    param(
        [int]$FrontendPort = 3000,
        [int]$BackendPort = 5000,
        [string]$BindHost = "127.0.0.1",
        [int]$MaxWaitSec = 120,
        [int]$IntervalSec = 3
    )

    function Test-PocketProSBAHttp {
        param(
            [string]$Label,
            [string]$Url,
            [int]$TimeoutSec = 8
        )
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
            return @{ Ok = $true; Label = $Label; Status = $resp.StatusCode }
        } catch {
            return @{ Ok = $false; Label = $Label; Error = $_.Exception.Message }
        }
    }

    $deadline = (Get-Date).AddSeconds($MaxWaitSec)
    $frontendHealth = "http://${BindHost}:${FrontendPort}/api/health"
    $backendHealth = "http://${BindHost}:${BackendPort}/api/health"

    while ((Get-Date) -lt $deadline) {
        $frontend = Test-PocketProSBAHttp "frontend" $frontendHealth
        $backend = Test-PocketProSBAHttp "backend_direct" $backendHealth

        if ($frontend.Ok -or $backend.Ok) {
            return @{
                Ok = $true
                FrontendUrl = "http://${BindHost}:${FrontendPort}/"
                BackendUrl = "http://${BindHost}:${BackendPort}/"
                Frontend = $frontend
                Backend = $backend
            }
        }

        if ($backend.Ok -and -not $frontend.Ok) {
            Write-Host "  backend up on ${BindHost}:${BackendPort}, waiting for frontend proxy..." -ForegroundColor Yellow
        } else {
            $msg = if ($frontend.Error) { $frontend.Error } else { "waiting" }
            Write-Host "  waiting for SBA app on ${BindHost}:${FrontendPort} ($msg)..." -ForegroundColor Gray
        }

        Start-Sleep -Seconds $IntervalSec
    }

    return @{
        Ok = $false
        FrontendUrl = "http://${BindHost}:${FrontendPort}/"
        BackendUrl = "http://${BindHost}:${BackendPort}/"
    }
}
