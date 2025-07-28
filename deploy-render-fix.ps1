# PowerShell script to deploy the 502 fix to Render.com
Write-Host "🚀 Deploying PocketPro SBA 502 Fix to Render.com" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Step 1: Clean and rebuild frontend locally to verify
Write-Host "`n1. Cleaning and rebuilding frontend locally..." -ForegroundColor Yellow
Set-Location frontend
if (Test-Path "build") {
    Remove-Item -Recurse -Force build
    Write-Host "   ✓ Cleaned existing build directory" -ForegroundColor Green
}

Write-Host "   Installing dependencies..." -ForegroundColor Cyan
npm install --legacy-peer-deps

Write-Host "   Building React app..." -ForegroundColor Cyan
$env:REACT_APP_BACKEND_URL = "https://pocketprosba-backend.onrender.com"
npm run build

if (Test-Path "build/index.html") {
    Write-Host "   ✓ Frontend build successful" -ForegroundColor Green
} else {
    Write-Host "   ❌ Frontend build failed" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Step 2: Commit changes
Write-Host "`n2. Committing changes to Git..." -ForegroundColor Yellow
git add render.yaml
git add frontend/build/
git commit -m "fix: Update render.yaml to use static site deployment for frontend

- Changed frontend from Node.js service to static site
- Fixed 502 Bad Gateway errors for static assets
- Updated build configuration for proper asset serving
- Removed unnecessary PORT and startCommand for static site"

Write-Host "   ✓ Changes committed" -ForegroundColor Green

# Step 3: Push to trigger deployment
Write-Host "`n3. Pushing to trigger Render deployment..." -ForegroundColor Yellow
git push origin main
Write-Host "   ✓ Pushed to main branch" -ForegroundColor Green

# Step 4: Instructions for Render.com
Write-Host "`n4. Next Steps in Render.com Dashboard:" -ForegroundColor Yellow
Write-Host "   📋 BACKEND SERVICE (pocketprosba-backend):" -ForegroundColor Cyan
Write-Host "      - Should auto-deploy from the push" -ForegroundColor White
Write-Host "      - Verify GEMINI_API_KEY is set in environment variables" -ForegroundColor White
Write-Host "      - Check deployment logs for any errors" -ForegroundColor White
Write-Host "      - Test health endpoint: https://pocketprosba-backend.onrender.com/health" -ForegroundColor White

Write-Host "`n   📋 FRONTEND SERVICE (pocketprosba-frontend):" -ForegroundColor Cyan
Write-Host "      - Should auto-deploy as static site now" -ForegroundColor White
Write-Host "      - Verify REACT_APP_BACKEND_URL = https://pocketprosba-backend.onrender.com" -ForegroundColor White
Write-Host "      - Check that build command succeeded" -ForegroundColor White
Write-Host "      - Test frontend: https://pocketprosba-frontend.onrender.com" -ForegroundColor White

# Step 5: Testing instructions
Write-Host "`n5. Testing the Fix:" -ForegroundColor Yellow
Write-Host "   🧪 After deployment completes:" -ForegroundColor Cyan
Write-Host "      1. Open: https://pocketprosba-frontend.onrender.com" -ForegroundColor White
Write-Host "      2. Check browser console - should see no 502 errors" -ForegroundColor White
Write-Host "      3. Verify CSS and JS files load correctly" -ForegroundColor White
Write-Host "      4. Test frontend-backend connectivity" -ForegroundColor White

Write-Host "`n6. If Issues Persist:" -ForegroundColor Yellow
Write-Host "   🔧 Troubleshooting:" -ForegroundColor Cyan
Write-Host "      - Check Render build logs for both services" -ForegroundColor White
Write-Host "      - Verify environment variables are set correctly" -ForegroundColor White
Write-Host "      - Ensure both services are using the same branch (main)" -ForegroundColor White
Write-Host "      - Clear browser cache and test again" -ForegroundColor White

Write-Host "`n✅ Deployment script completed!" -ForegroundColor Green
Write-Host "Monitor your Render dashboard for deployment progress." -ForegroundColor Cyan
