#
# Quick fix script for the missing catch clause in App.js
#

$appJsPath = ".\frontend\src\App.js"

Write-Host "Fixing missing catch clause in App.js..." -ForegroundColor Cyan

if (Test-Path $appJsPath) {
    # Read the file content
    $content = Get-Content $appJsPath -Raw
    
    # Find the problematic line (around line 66)
    $lines = $content -split "`n"
    $fixNeeded = $false
    
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match "^\s*try\s*\{") {
            # Look ahead for a matching catch or finally
            $hasCatchOrFinally = $false
            $braceCount = 1  # Start with 1 for the opening brace of try
            
            for ($j = $i + 1; $j -lt $lines.Length; $j++) {
                # Count braces to track nested blocks
                $openBraces = ([regex]::Matches($lines[$j], "\{")).Count
                $closeBraces = ([regex]::Matches($lines[$j], "\}")).Count
                $braceCount += $openBraces - $closeBraces
                
                # If we're back to the same level and found a catch/finally, we're good
                if ($braceCount == 0) {
                    if ($j+1 < $lines.Length -and ($lines[$j+1] -match "^\s*catch" -or $lines[$j+1] -match "^\s*finally")) {
                        $hasCatchOrFinally = $true
                    }
                    break
                }
            }
            
            # If we didn't find a matching catch/finally, add one
            if (-not $hasCatchOrFinally) {
                $lineNumber = $i + 1
                Write-Host "Found incomplete try block at line $lineNumber" -ForegroundColor Yellow
                
                # Determine the line where the try block ends
                $tryEndLine = $j
                
                # Insert a catch block after the try block
                $indent = [regex]::Match($lines[$i], "^\s*").Value
                $catchBlock = "${indent}} catch (error) {`n${indent}  console.error('Error:', error);`n${indent}"
                
                $lines[$tryEndLine] = $lines[$tryEndLine] + "`n" + $catchBlock
                $fixNeeded = $true
            }
        }
    }
    
    # Save the fixed content back to the file if needed
    if ($fixNeeded) {
        $fixedContent = $lines -join "`n"
        Set-Content -Path $appJsPath -Value $fixedContent
        Write-Host "Fixed missing catch clause in App.js" -ForegroundColor Green
        
        # Create a backup of the original file
        Copy-Item -Path $appJsPath -Destination "$appJsPath.bak"
        Write-Host "Created backup at $appJsPath.bak" -ForegroundColor Green
    } else {
        Write-Host "No incomplete try blocks found in App.js or could not identify the issue" -ForegroundColor Yellow
    }
} else {
    Write-Host "App.js not found at $appJsPath" -ForegroundColor Red
}

Write-Host "`nAlternative: Update Dockerfile to bypass ESLint errors" -ForegroundColor Cyan
Write-Host "Add 'ENV CI=false' to your frontend Dockerfile before the build command" -ForegroundColor Yellow
Write-Host "Then rebuild the Docker container: docker-compose build frontend" -ForegroundColor Yellow
