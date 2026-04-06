# Script to fix network configuration issues in docker-compose.yml

Write-Host "===== Fixing Docker Network Configuration =====" -ForegroundColor Cyan
Write-Host ""

$dockerComposePath = "docker-compose.yml"

if (Test-Path $dockerComposePath) {
    # Create a backup
    $backupPath = "${dockerComposePath}.bak"
    Copy-Item -Path $dockerComposePath -Destination $backupPath -Force
    Write-Host "Created backup at $backupPath" -ForegroundColor Green
    
    # Read the file content
    $content = Get-Content $dockerComposePath
    
    # Find all network sections
    $networkSectionStart = -1
    $networkLines = @()
    $appNetworkLines = @()
    
    for ($i = 0; $i -lt $content.Length; $i++) {
        if ($content[$i] -match "^networks\s*:") {
            $networkSectionStart = $i
        }
        
        if ($networkSectionStart -ne -1 -and $i -gt $networkSectionStart) {
            if ($content[$i] -match "^\S" -and $content[$i] -notmatch "^networks") {
                # Reached the end of the networks section
                break
            }
            
            $networkLines += $i
            
            if ($content[$i] -match "^\s*app-network\s*:") {
                $appNetworkLines += $i
            }
        }
    }
    
    if ($appNetworkLines.Count -gt 1) {
        Write-Host "Found duplicate 'app-network' keys at lines: $($appNetworkLines -join ', ')" -ForegroundColor Yellow
        
        # Keep only the first app-network section and its indented configurations
        $firstAppNetworkLine = $appNetworkLines[0]
        $linesToRemove = @()
        
        for ($i = 1; $i -lt $appNetworkLines.Count; $i++) {
            $startLine = $appNetworkLines[$i]
            $endLine = $startLine
            
            # Find how far this network section extends (all indented lines)
            for ($j = $startLine + 1; $j -lt $content.Length; $j++) {
                if ($content[$j] -match "^\s+") {
                    $endLine = $j
                } else {
                    break
                }
            }
            
            # Mark these lines for removal
            for ($j = $startLine; $j -le $endLine; $j++) {
                $linesToRemove += $j
            }
        }
        
        # Create new content without the duplicate sections
        $newContent = @()
        for ($i = 0; $i -lt $content.Length; $i++) {
            if ($linesToRemove -notcontains $i) {
                $newContent += $content[$i]
            }
        }
        
        # Save the updated content
        Set-Content -Path $dockerComposePath -Value $newContent
        
        Write-Host "Fixed docker-compose.yml by removing duplicate 'app-network' definitions" -ForegroundColor Green
    } else {
        Write-Host "No duplicate 'app-network' keys found in docker-compose.yml" -ForegroundColor Green
    }
} else {
    Write-Host "Error: docker-compose.yml not found" -ForegroundColor Red
}

Write-Host "`nRestart your Docker containers to apply changes:" -ForegroundColor Cyan
Write-Host "docker-compose down" -ForegroundColor White
Write-Host "docker-compose up -d" -ForegroundColor White
