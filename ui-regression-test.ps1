#
# UI Regression Testing Helper
# This script helps document UI state before and after changes
#

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$screenshotDir = ".\ui-regression-tests\$timestamp"

# Create directory for screenshots
if (-not (Test-Path $screenshotDir)) {
    New-Item -ItemType Directory -Path $screenshotDir -Force | Out-Null
}

Write-Host "UI Regression Test Helper" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will guide you through UI regression testing."
Write-Host "Screenshots will be saved to: $screenshotDir"
Write-Host ""
Write-Host "Instructions:" -ForegroundColor Yellow
Write-Host "1. Run this script BEFORE making changes to establish baseline" -ForegroundColor Yellow
Write-Host "2. Make your changes to the system" -ForegroundColor Yellow
Write-Host "3. Run this script AFTER changes to capture comparison screenshots" -ForegroundColor Yellow
Write-Host "4. Compare the before/after screenshots to identify regressions" -ForegroundColor Yellow
Write-Host ""

# Define key UI pages to test
$pages = @(
    @{name="Home Page"; url="http://localhost:3000/"},
    @{name="Documents"; url="http://localhost:3000/documents"},
    @{name="Models"; url="http://localhost:3000/models"},
    @{name="Search"; url="http://localhost:3000/search"}
)

Write-Host "Manual testing checklist:" -ForegroundColor Green
foreach ($page in $pages) {
    Write-Host "  • $($page.name) - $($page.url)" -ForegroundColor Green
}

Write-Host "`nAPI endpoints to verify:" -ForegroundColor Green
$endpoints = @(
    "/api/info",
    "/api/greeting",
    "/api/models",
    "/api/documents",
    "/api/collections/stats",
    "/api/search/filters",
    "/api/assistants",
    "/health"
)

foreach ($endpoint in $endpoints) {
    Write-Host "  • http://localhost:10000$endpoint" -ForegroundColor Green
}

Write-Host "`nSuggested browser tools:" -ForegroundColor Magenta
Write-Host "• Chrome DevTools (F12) - Network tab to monitor API requests" -ForegroundColor Magenta
Write-Host "• React Developer Tools extension - To inspect component state" -ForegroundColor Magenta
Write-Host "• Console tab - To check for JavaScript errors" -ForegroundColor Magenta

Write-Host "`nTest results folder created at: $screenshotDir" -ForegroundColor Cyan
Write-Host "Create a text file in this folder to document your observations." -ForegroundColor Cyan

# Open the screenshot directory
explorer $screenshotDir
