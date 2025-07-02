# Quick fix for the specific ESLint error at line 66 in App.js

Write-Host "===== Line 66 ESLint Error Fix =====" -ForegroundColor Cyan
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

# Look specifically around line 66
$targetLine = 66
$searchRange = 10  # Look 10 lines before and after line 66
$startLine = [Math]::Max(1, $targetLine - $searchRange)
$endLine = [Math]::Min($lines.Length, $targetLine + $searchRange)
$fixApplied = $false

Write-Host "Targeting ESLint error near line $targetLine..." -ForegroundColor Yellow

for ($i = $startLine - 1; $i -lt $endLine; $i++) {
    if ($lines[$i] -match "^\s*try\s*\{") {
        # Found a try block near the target line
        $tryLineNumber = $i + 1
        Write-Host "Found try block at line $tryLineNumber" -ForegroundColor Yellow
        
        # Look for the end of this try block
        $braceCount = 1  # Start with 1 for the opening brace of try
        $tryEndLine = -1
        
        for ($j = $i + 1; $j -lt $lines.Length; $j++) {
            # Count braces to track nested blocks
            $openBraces = ([regex]::Matches($lines[$j], "\{")).Count
            $closeBraces = ([regex]::Matches($lines[$j], "\}")).Count
            $braceCount += $openBraces - $closeBraces
            
            # If we're back to the same level, we found the end of the try block
            if ($braceCount == 0) {
                $tryEndLine = $j
                break
            }
        }
        
        if ($tryEndLine -ne -1) {
            # Check if there's already a catch block
            $hasCatch = $false
            if ($tryEndLine + 1 < $lines.Length) {
                if ($lines[$tryEndLine + 1] -match "^\s*catch" -or $lines[$tryEndLine] -match "\}\s*catch") {
                    $hasCatch = $true
                }
            }
            
            if (-not $hasCatch) {
                # Determine the indentation level
                $indent = [regex]::Match($lines[$i], "^\s*").Value
                
                # Insert a catch block after the try block
                $catchBlock = "$indent} catch (error) {`n${indent}  console.error('Error:', error);`n$indent}"
                
                # If the try block ends with a single closing brace
                if ($lines[$tryEndLine].Trim() -eq "}") {
                    $lines[$tryEndLine] = $catchBlock
                } else {
                    # If the closing brace is on the same line as other code
                    $lines[$tryEndLine] = $lines[$tryEndLine] + "`n" + $catchBlock
                }
                
                Write-Host "Added catch block after line $tryEndLine" -ForegroundColor Green
                $fixApplied = $true
                
                # If this is close to line 66, it's likely the one causing the error
                if ([Math]::Abs($tryLineNumber - $targetLine) -lt 5 || [Math]::Abs($tryEndLine - $targetLine) -lt 5) {
                    Write-Host "This appears to be the try block causing the ESLint error at line $targetLine" -ForegroundColor Magenta
                }
            }
        }
    }
}

if ($fixApplied) {
    # Save the modified content
    $fixedContent = $lines -join "`n"
    Set-Content -Path $appJsPath -Value $fixedContent
    
    Write-Host "`nFix applied to App.js" -ForegroundColor Green
    Write-Host "You can now rebuild your Docker containers with:" -ForegroundColor Cyan
    Write-Host "  docker-compose down" -ForegroundColor White
    Write-Host "  docker-compose up -d --build" -ForegroundColor White
} else {
    Write-Host "`nNo fix was applied - couldn't find an uncaught try block near line $targetLine" -ForegroundColor Yellow
    Write-Host "Alternative approach: Create a docker-compose override to bypass ESLint errors:" -ForegroundColor Cyan
    Write-Host "`n  .\fix-docker-build.ps1" -ForegroundColor White
}
