# PocketPro:SBA local UP for testing (Windows)
param(
    [ValidateSet("dev","prod")]
    [string]$Mode = "dev",
    [switch]$NoBuild
)
Set-Location $PSScriptRoot
$argsList = @("-Mode", $Mode, "-OpenBrowser")
if (-not $NoBuild) { $argsList += "-Build" }
& "$PSScriptRoot\start-windows.ps1" @argsList
exit $LASTEXITCODE
