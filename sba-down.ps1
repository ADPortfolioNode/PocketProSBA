# PocketPro:SBA local DOWN for testing (keeps volumes)
Set-Location $PSScriptRoot
Write-Host "Stopping PocketPro:SBA..." -ForegroundColor Cyan
if (Test-Path "docker-compose.dev.yml") {
    docker compose -f docker-compose.dev.yml down --timeout 30 --remove-orphans
}
if (Test-Path "docker-compose.yml") {
    docker compose -f docker-compose.yml down --timeout 30 --remove-orphans
}
if (Test-Path "docker-compose.prod.yml") {
    docker compose -f docker-compose.prod.yml down --timeout 30 --remove-orphans
}
Write-Host "[OK] PocketPro:SBA down. Data kept in uploads/ and chromadb_data/" -ForegroundColor Green
