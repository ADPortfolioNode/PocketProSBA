# Script to fix missing catch/finally clauses in App.js

Write-Host "===== App.js ESLint Fixer =====" -ForegroundColor Cyan
Write-Host ""

$appJsPath = "frontend\src\App.js"

if (-not (Test-Path $appJsPath)) {
    Write-Host "Error: Cannot find App.js at $appJsPath" -ForegroundColor Red
    exit 1
}

# Create a backup
$backupPath = "$appJsPath.bak"
Copy-Item -Path $appJsPath -Destination $backupPath -Force
Write-Host "Created backup at $backupPath" -ForegroundColor Green

# Read the file content
$content = Get-Content $appJsPath -Raw
$lines = $content -split "`n"
$fixCount = 0

Write-Host "Scanning for incomplete try blocks..." -ForegroundColor Yellow

for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^\s*try\s*\{") {
        # Look ahead for a matching catch or finally
        $hasCatchOrFinally = $false
        $braceCount = 1  # Start with 1 for the opening brace of try
        $tryLineNumber = $i + 1
        $tryEndLine = -1
        
        for ($j = $i + 1; $j -lt $lines.Length; $j++) {
            # Count braces to track nested blocks
            $openBraces = ([regex]::Matches($lines[$j], "\{")).Count
            $closeBraces = ([regex]::Matches($lines[$j], "\}")).Count
            $braceCount += $openBraces - $closeBraces
            
            # If we're back to the same level, check for catch/finally
            if ($braceCount == 0) {
                $tryEndLine = $j
                if ($j + 1 < $lines.Length -and ($lines[$j + 1] -match "^\s*catch" -or $lines[$j + 1] -match "^\s*finally")) {
                    $hasCatchOrFinally = $true
                }
                break
            }
        }
        
        # If we didn't find a matching catch/finally, add one
        if (-not $hasCatchOrFinally -and $tryEndLine -ne -1) {
            Write-Host "Found incomplete try block at line $tryLineNumber" -ForegroundColor Yellow
            
            # Determine the indentation level
            $indent = [regex]::Match($lines[$i], "^\s*").Value
            
            # Insert a catch block after the try block
            $catchBlock = "$indent} catch (error) {`n${indent}  console.error('Error:', error);`n"
            
            # If the try block doesn't end with a closing brace on its own line, add one
            if (-not $lines[$tryEndLine].Trim().Equals("}")) {
                $lines[$tryEndLine] = $lines[$tryEndLine] + "`n$catchBlock"
            } else {
                $lines[$tryEndLine] = $catchBlock + $lines[$tryEndLine]
            }
            
            $fixCount++
            Write-Host "  Fixed: Added catch block after line $($tryEndLine + 1)" -ForegroundColor Green
        }
    }
}

# Save the fixed content back to the file
if ($fixCount -gt 0) {
    $fixedContent = $lines -join "`n"
    Set-Content -Path $appJsPath -Value $fixedContent
    Write-Host "`nFixed $fixCount incomplete try blocks in App.js" -ForegroundColor Green
    Write-Host "You can now rebuild your Docker containers:" -ForegroundColor Cyan
    Write-Host "  docker-compose down" -ForegroundColor White
    Write-Host "  docker-compose up -d --build" -ForegroundColor White
} else {
    Write-Host "`nNo obvious incomplete try blocks found in App.js" -ForegroundColor Yellow
    Write-Host "The ESLint error might be more complex or in a different location." -ForegroundColor Yellow
    Write-Host "Try using the docker-compose override approach instead:" -ForegroundColor Cyan
    Write-Host "  .\fix-docker-build.ps1" -ForegroundColor White
}

Write-Host "`nAlternative: Manually fix the issue around line 66 in App.js" -ForegroundColor Magenta
