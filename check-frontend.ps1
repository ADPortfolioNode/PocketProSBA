Write-Host "Checking React setup in frontend folder..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\frontend"
npm list react
if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend setup looks good! Ready to run with npm start" -ForegroundColor Green
} else {
    Write-Host "There might be issues with the React setup. Please check package.json" -ForegroundColor Yellow
}
