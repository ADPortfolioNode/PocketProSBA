#!/usr/bin/env python3
"""
Production deployment verification script for Render.com
Checks if the application is ready for production deployment
"""
import os
import sys
import re
import json
from pathlib import Path

def check_files_exist():
    """Check if all required files exist"""
    required_files = [
        "minimal_app.py",
        "requirements-render-production.txt",
        "Procfile.production",
        "render.production.yaml",
        "Dockerfile.production"
    ]
    
    print("🔍 Checking for required files...")
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")
    
    return len(missing_files) == 0

def check_port_binding():
    """Check if minimal_app.py binds to 0.0.0.0 and uses PORT env var"""
    print("\n🔍 Checking port binding in minimal_app.py...")
    
    try:
        with open("minimal_app.py", "r") as f:
            content = f.read()
        
        # Check for PORT environment variable
        port_env_pattern = r"PORT\s*=\s*int\(os\.environ\.get\(['\"](PORT)['\"],\s*(\d+)\)\)"
        port_env_match = re.search(port_env_pattern, content)
        
        if port_env_match:
            print(f"✅ PORT environment variable used with default {port_env_match.group(2)}")
        else:
            print("❌ PORT environment variable not properly used")
            return False
        
        # Check for 0.0.0.0 binding
        binding_pattern = r"app\.run\(host=['\"]0\.0\.0\.0['\"],\s*port"
        binding_match = re.search(binding_pattern, content)
        
        if binding_match:
            print("✅ Application binds to 0.0.0.0")
        else:
            print("❌ Application does not bind to 0.0.0.0")
            return False
        
        # Check for Gunicorn application export
        application_pattern = r"application\s*=\s*app"
        application_match = re.search(application_pattern, content)
        
        if application_match:
            print("✅ 'application = app' export for Gunicorn found")
        else:
            print("❌ 'application = app' export for Gunicorn missing")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error checking minimal_app.py: {e}")
        return False

def check_health_endpoint():
    """Check if the health endpoint is defined"""
    print("\n🔍 Checking for health endpoint...")
    
    try:
        with open("minimal_app.py", "r") as f:
            content = f.read()
        
        health_pattern = r"@app\.route\(['\"]\/health['\"]\)"
        health_match = re.search(health_pattern, content)
        
        if health_match:
            print("✅ Health endpoint defined")
            return True
        else:
            print("❌ Health endpoint not defined")
            return False
    
    except Exception as e:
        print(f"❌ Error checking for health endpoint: {e}")
        return False

def check_render_yaml():
    """Check render.production.yaml configuration"""
    print("\n🔍 Checking render.production.yaml configuration...")
    
    try:
        with open("render.production.yaml", "r") as f:
            content = f.read()
        
        # Check for critical settings
        checks = [
            ("Health check path", r"healthCheckPath:\s*/health"),
            ("Gunicorn timeout", r"--timeout\s+\d+"),
            ("Workers configuration", r"--workers\s+\d+"),
            ("Binding configuration", r"--bind\s+0\.0\.0\.0:\$PORT"),
            ("PORT environment variable", r"key:\s*PORT"),
            ("PYTHONUNBUFFERED setting", r"PYTHONUNBUFFERED"),
            ("Access logs configuration", r"--access-logfile"),
            ("Error logs configuration", r"--error-logfile")
        ]
        
        all_passed = True
        for name, pattern in checks:
            match = re.search(pattern, content)
            if match:
                print(f"✅ {name}: Configured")
            else:
                print(f"❌ {name}: Missing")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Error checking render.production.yaml: {e}")
        return False

def check_dockerfile():
    """Check Dockerfile.production configuration"""
    print("\n🔍 Checking Dockerfile.production configuration...")
    
    try:
        with open("Dockerfile.production", "r") as f:
            content = f.read()
        
        checks = [
            ("Base image", r"FROM\s+python"),
            ("Working directory", r"WORKDIR\s+/app"),
            ("Non-root user", r"useradd.*appuser"),
            ("PORT environment variable", r"ENV\s+PORT"),
            ("Port exposure", r"EXPOSE\s+\$\{PORT\}"),
            ("Health check", r"HEALTHCHECK"),
            ("Gunicorn command", r"CMD\s+gunicorn")
        ]
        
        all_passed = True
        for name, pattern in checks:
            match = re.search(pattern, content)
            if match:
                print(f"✅ {name}: Configured")
            else:
                print(f"❌ {name}: Missing")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Error checking Dockerfile.production: {e}")
        return False

def check_requirements():
    """Check production requirements"""
    print("\n🔍 Checking production requirements...")
    
    try:
        # Always ensure pip is upgraded before installing requirements in production
        # Example: pip install --upgrade pip && pip install --no-cache-dir -r requirements-render-production.txt
        with open("requirements-render-production.txt", "r") as f:
            content = f.read()
        
        required_packages = [
            "flask",
            "gunicorn",
            "flask-cors"
        ]
        
        all_passed = True
        for package in required_packages:
            if package in content.lower():
                print(f"✅ {package}: Included")
            else:
                print(f"❌ {package}: Missing")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def create_deployment_report():
    """Create a deployment readiness report"""
    report = {
        "timestamp": "__TIMESTAMP__",  # Will be replaced with actual timestamp when run
        "checks": {
            "files_exist": check_files_exist(),
            "port_binding": check_port_binding(),
            "health_endpoint": check_health_endpoint(),
            "render_yaml": check_render_yaml(),
            "dockerfile": check_dockerfile(),
            "requirements": check_requirements()
        }
    }
    
    # Calculate overall status
    report["ready_for_deployment"] = all(report["checks"].values())
    
    # Write report to file
    with open("render_production_readiness.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📝 Deployment readiness report written to render_production_readiness.json")
    
    return report

def main():
    """Main function"""
    print("🚀 Render.com Production Deployment Verification")
    print("=" * 50)
    
    report = create_deployment_report()
    
    # Print summary
    print("\n📋 Verification Summary:")
    for check, status in report["checks"].items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"   {check.replace('_', ' ').title()}: {status_str}")
    
    if report["ready_for_deployment"]:
        print("\n🎉 All checks passed! Your application is ready for production deployment on Render.com")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please address the issues before deploying to production.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
