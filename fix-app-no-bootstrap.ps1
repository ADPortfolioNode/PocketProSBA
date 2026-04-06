# PowerShell script to replace App.js with version that doesn't require react-bootstrap

Write-Host "Fixing frontend App.js to work without react-bootstrap..." -ForegroundColor Cyan

# Backup original App.js
if (-not (Test-Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js.original")) {
    Copy-Item -Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js" -Destination "e:\2024 RESET\PocketProSBA\frontend\src\App.js.original" -Force
}

# Apply the no-bootstrap version
Copy-Item -Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js.no-bootstrap" -Destination "e:\2024 RESET\PocketProSBA\frontend\src\App.js" -Force

# Add CSS for loading spinner
$spinnerCSS = @"
/* Add loading spinner CSS */
.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-right: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
"@

Add-Content -Path "e:\2024 RESET\PocketProSBA\frontend\src\App.css" -Value $spinnerCSS

Write-Host "App.js has been updated to work without react-bootstrap!" -ForegroundColor Green
Write-Host "Please refresh your browser to see the changes." -ForegroundColor Cyan
