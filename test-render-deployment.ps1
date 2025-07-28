# PowerShell script to test the Render.com deployment after fixes
Write-Host "🧪 Testing PocketPro SBA Render.com Deployment" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

$backendUrl = "https://pocketprosba-backend.onrender.com"
$frontendUrl = "https://pocketprosba-frontend.onrender.com"

# Test 1: Backend Health Check
Write-Host "`n1. Testing Backend Health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$backendUrl/health" -Method GET -TimeoutSec 30
    Write-Host "   ✅ Backend health check passed" -ForegroundColor Green
    Write-Host "   Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Frontend Accessibility
Write-Host "`n2. Testing Frontend Accessibility..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method GET -TimeoutSec 30
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend is accessible" -ForegroundColor Green
        
        # Check for static assets in HTML
        $htmlContent = $frontendResponse.Content
        if ($htmlContent -match 'static/css/main\.[a-f0-9]+\.css') {
            Write-Host "   ✅ CSS asset reference found in HTML" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  CSS asset reference not found" -ForegroundColor Yellow
        }
        
        if ($htmlContent -match 'static/js/main\.[a-f0-9]+\.js') {
            Write-Host "   ✅ JS asset reference found in HTML" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  JS asset reference not found" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Frontend accessibility failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Static Assets (the main issue we're fixing)
Write-Host "`n3. Testing Static Assets..." -ForegroundColor Yellow
try {
    # Get the main page to extract asset URLs
    $mainPage = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 30
    $htmlContent = $mainPage.Content
    
    # Extract CSS file URL
    if ($htmlContent -match 'href="(/static/css/main\.[a-f0-9]+\.css)"') {
        $cssUrl = $frontendUrl + $matches[1]
        try {
            $cssResponse = Invoke-WebRequest -Uri $cssUrl -Method GET -TimeoutSec 15
            if ($cssResponse.StatusCode -eq 200) {
                Write-Host "   ✅ CSS file loads successfully: $cssUrl" -ForegroundColor Green
            }
        } catch {
            Write-Host "   ❌ CSS file failed to load: $cssUrl" -ForegroundColor Red
            Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Extract JS file URL
    if ($htmlContent -match 'src="(/static/js/main\.[a-f0-9]+\.js)"') {
        $jsUrl = $frontendUrl + $matches[1]
        try {
            $jsResponse = Invoke-WebRequest -Uri $jsUrl -Method GET -TimeoutSec 15
            if ($jsResponse.StatusCode -eq 200) {
                Write-Host "   ✅ JS file loads successfully: $jsUrl" -ForegroundColor Green
            }
        } catch {
            Write-Host "   ❌ JS file failed to load: $jsUrl" -ForegroundColor Red
            Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Test favicon
    try {
        $faviconResponse = Invoke-WebRequest -Uri "$frontendUrl/favicon.ico" -Method GET -TimeoutSec 15
        if ($faviconResponse.StatusCode -eq 200) {
            Write-Host "   ✅ Favicon loads successfully" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ❌ Favicon failed to load" -ForegroundColor Red
    }
    
} catch {
    Write-Host "   ❌ Static asset testing failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Frontend-Backend Connectivity
Write-Host "`n4. Testing Frontend-Backend Connectivity..." -ForegroundColor Yellow
try {
    # Test if frontend can reach backend API
    $apiHealthUrl = "$backendUrl/api/health"
    $apiResponse = Invoke-RestMethod -Uri $apiHealthUrl -Method GET -TimeoutSec 30
    Write-Host "   ✅ Frontend can reach backend API" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Frontend-Backend connectivity issue: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n📊 Test Summary:" -ForegroundColor Yellow
Write-Host "=================" -ForegroundColor Yellow
Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all tests pass, your 502 Bad Gateway errors should be resolved!" -ForegroundColor Green
Write-Host "If any tests fail, check the Render deployment logs and environment variables." -ForegroundColor Yellow

Write-Host "`n🔗 Quick Links:" -ForegroundColor Yellow
Write-Host "- Frontend: $frontendUrl" -ForegroundColor Cyan
Write-Host "- Backend Health: $backendUrl/health" -ForegroundColor Cyan
Write-Host "- Backend API Health: $backendUrl/api/health" -ForegroundColor Cyan
