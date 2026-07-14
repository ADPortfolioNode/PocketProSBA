#
# Script to help identify and fix ESLint errors in React code
#

$appJsPath = ".\src\App.js"

Write-Host "Checking for incomplete try/catch blocks in App.js..." -ForegroundColor Cyan

if (Test-Path $appJsPath) {
    $content = Get-Content $appJsPath -Raw
    
    # Look for try blocks without catch
    $tryBlockPattern = "try\s*\{[^}]*\}(?!\s*catch|\s*finally)"
    
    if ($content -match $tryBlockPattern) {
        Write-Host "Found incomplete try block(s) in App.js!" -ForegroundColor Red
        Write-Host "Line numbers with potential issues:" -ForegroundColor Yellow
        
        $lines = $content -split "`n"
        for ($i = 0; $i -lt $lines.Length; $i++) {
            if ($lines[$i] -match "^\s*try\s*\{") {
                # Check if there's a matching catch within the next few lines
                $hasCatch = $false
                for ($j = $i + 1; $j -lt [Math]::Min($i + 10, $lines.Length); $j++) {
                    if ($lines[$j] -match "^\s*\}\s*catch") {
                        $hasCatch = $true
                        break
                    }
                }
                
                if (-not $hasCatch) {
                    $lineNumber = $i + 1
                    Write-Host "  Line $lineNumber: $($lines[$i].Trim())" -ForegroundColor Red
                    Write-Host "  --- Missing catch or finally clause" -ForegroundColor Yellow
                }
            }
        }
        
        Write-Host "`nFix by adding catch blocks to all try statements:" -ForegroundColor Green
        Write-Host "try {" -ForegroundColor Cyan
        Write-Host "  // your code" -ForegroundColor Cyan
        Write-Host "} catch (error) {" -ForegroundColor Cyan
        Write-Host "  console.error('Error:', error);" -ForegroundColor Cyan
        Write-Host "}" -ForegroundColor Cyan
    } else {
        Write-Host "No incomplete try/catch blocks found in App.js." -ForegroundColor Green
    }
    
    # Run ESLint to find other issues
    Write-Host "`nRunning ESLint to identify other issues..." -ForegroundColor Cyan
    Write-Host "cd frontend && npx eslint src/App.js"
} else {
    Write-Host "App.js not found at $appJsPath" -ForegroundColor Red
}
