# Script to check for network configuration issues in docker-compose.yml

Write-Host "===== Docker Network Configuration Check =====" -ForegroundColor Cyan
Write-Host ""

$dockerComposePath = "docker-compose.yml"

if (Test-Path $dockerComposePath) {
    $content = Get-Content $dockerComposePath
    $yamlLines = $content | Select-Object -Property @{Name="LineNumber";Expression={$_ -replace "^", "$($content.IndexOf($_) + 1): "}}, @{Name="Text";Expression={$_}}
    
    Write-Host "Checking for duplicate network keys..." -ForegroundColor Yellow
    
    $networkLines = @()
    for ($i = 0; $i -lt $content.Length; $i++) {
        if ($content[$i] -match "^\s*app-network\s*:") {
            $networkLines += $i + 1
        }
    }
    
    if ($networkLines.Count -gt 1) {
        Write-Host "[X] Found duplicate 'app-network' keys at lines: $($networkLines -join ', ')" -ForegroundColor Red
        Write-Host "`nFix by removing duplicate network definitions. Keep only one 'app-network' key in the networks section:" -ForegroundColor Yellow
        Write-Host @"
networks:
  app-network:
    driver: bridge
    # All network configuration should be here
"@ -ForegroundColor Green
    } else {
        Write-Host "[√] No duplicate network keys found" -ForegroundColor Green
    }
    
    # Display the networks section for reference
    Write-Host "`nCurrent networks section:" -ForegroundColor Cyan
    $inNetworksSection = $false
    for ($i = 0; $i -lt $content.Length; $i++) {
        if ($content[$i] -match "^networks\s*:") {
            $inNetworksSection = $true
            Write-Host "$($i + 1): $($content[$i])" -ForegroundColor White
        }
        elseif ($inNetworksSection) {
            if ($content[$i] -match "^\S") {
                $inNetworksSection = $false
            } else {
                Write-Host "$($i + 1): $($content[$i])" -ForegroundColor White
            }
        }
    }
} else {
    Write-Host "[X] docker-compose.yml not found" -ForegroundColor Red
}

Write-Host "`nAfter fixing the network configuration, restart your Docker containers:" -ForegroundColor Cyan
Write-Host "docker-compose down" -ForegroundColor White
Write-Host "docker-compose up -d" -ForegroundColor White
