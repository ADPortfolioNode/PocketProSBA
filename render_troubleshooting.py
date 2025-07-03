#!/usr/bin/env python3
"""
Render.com Deployment Troubleshooting Guide
"""

def main():
    print("=== RENDER.COM BAD GATEWAY TROUBLESHOOTING ===")
    print()
    
    print("🔍 COMMON CAUSES OF BAD GATEWAY (502) ERRORS:")
    print()
    
    causes = [
        "1. App fails to start (dependency issues, import errors)",
        "2. App starts but crashes immediately (runtime errors)",
        "3. Health check endpoint fails or times out",
        "4. Port binding issues (not binding to $PORT)",
        "5. Startup timeout (app takes too long to start)",
        "6. Memory limits exceeded during startup",
        "7. Python version compatibility issues",
        "8. Missing environment variables",
        "9. File system permissions",
        "10. Worker process crashes"
    ]
    
    for cause in causes:
        print(f"   {cause}")
    
    print()
    print("🔧 FIXES APPLIED TO RESOLVE THESE ISSUES:")
    print()
    
    fixes = [
        "✅ Created minimal requirements-render-minimal.txt (no Rust deps)",
        "✅ Removed gevent/gevent-websocket (Python 3.13 incompatible)",
        "✅ Added wsgi.py entry point for better Gunicorn integration",
        "✅ Fixed render.yaml configuration",
        "✅ Used sync workers instead of async (more stable)",
        "✅ Set proper timeouts and worker limits",
        "✅ Added proper environment variable configuration",
        "✅ Ensured health check endpoint works",
        "✅ Added graceful error handling for missing ChromaDB",
        "✅ Fixed Python path configuration"
    ]
    
    for fix in fixes:
        print(f"   {fix}")
    
    print()
    print("📋 DEPLOYMENT CHECKLIST:")
    print()
    
    checklist = [
        "□ Check Render dashboard build logs for errors",
        "□ Verify all environment variables are set (especially GEMINI_API_KEY)",
        "□ Confirm Python 3.13 is being used",
        "□ Check that requirements install successfully",
        "□ Verify the health check endpoint /health responds",
        "□ Monitor memory usage during startup",
        "□ Check for any import errors in app startup",
        "□ Verify Gunicorn starts without errors",
        "□ Test locally with same requirements file",
        "□ Check Render service logs for runtime errors"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print()
    print("🚨 IMMEDIATE ACTION ITEMS:")
    print()
    
    actions = [
        "1. Check Render Dashboard → Your Service → Logs",
        "2. Look for build errors or startup failures",
        "3. Verify environment variables are set",
        "4. Test health endpoint manually after deployment",
        "5. Monitor resource usage (memory/CPU)",
        "6. Check if the app is binding to the correct port"
    ]
    
    for action in actions:
        print(f"   {action}")
    
    print()
    print("📂 KEY FILES FOR RENDER DEPLOYMENT:")
    print()
    
    files = [
        "render.yaml - Service configuration",
        "wsgi.py - Application entry point",
        "requirements-render-minimal.txt - Dependencies",
        "app.py - Main Flask application",
        "src/utils/config.py - Configuration management"
    ]
    
    for file in files:
        print(f"   📝 {file}")
    
    print()
    print("🔍 DEBUGGING STEPS:")
    print()
    
    debug_steps = [
        "1. Check build logs: Look for 'pip install' errors",
        "2. Check deploy logs: Look for startup errors",
        "3. Check runtime logs: Look for crash messages",
        "4. Test health endpoint: curl https://your-app.onrender.com/health",
        "5. Test minimal endpoint: curl https://your-app.onrender.com/",
        "6. Check memory usage in Render dashboard",
        "7. Verify environment variables in Render dashboard"
    ]
    
    for step in debug_steps:
        print(f"   {step}")
    
    print()
    print("⚡ QUICK FIXES TO TRY:")
    print()
    
    quick_fixes = [
        "• Redeploy with 'Clear build cache' option",
        "• Increase worker timeout in render.yaml",
        "• Verify GEMINI_API_KEY is set correctly",
        "• Check if health endpoint responds locally",
        "• Try with fewer workers (workers: 1)",
        "• Check for any missing imports in app.py"
    ]
    
    for fix in quick_fixes:
        print(f"   {fix}")
    
    print()
    print("🎯 MOST LIKELY CAUSE:")
    print("   Based on previous fixes, the most likely causes are:")
    print("   1. Missing environment variables (GEMINI_API_KEY)")
    print("   2. Import errors during app startup")
    print("   3. Health check endpoint timing out")
    print("   4. Memory limits during initialization")
    print()
    print("📞 NEXT STEPS:")
    print("   1. Check Render dashboard logs immediately")
    print("   2. Look for specific error messages")
    print("   3. Test the health endpoint locally")
    print("   4. Verify all environment variables are set")
    print("   5. Redeploy with build cache cleared")

if __name__ == "__main__":
    main()
