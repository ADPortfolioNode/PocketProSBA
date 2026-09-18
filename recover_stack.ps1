# PocketPro:SBA recover — same role as NYL recover_stack.ps1
param([switch]$Build)
Set-Location $PSScriptRoot
Write-Host "Recovering PocketPro:SBA stack..." -ForegroundColor Cyan
& "$PSScriptRoot\start-windows.ps1" -Recreate -OpenBrowser @PSBoundParameters
exit $LASTEXITCODE
