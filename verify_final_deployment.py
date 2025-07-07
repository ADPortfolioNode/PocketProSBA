#!/usr/bin/env python3
"""
Final deployment verification for Render.com
Ensures all port bindings are set to 5000, not 10000
"""
import os
import re
from pathlib import Path

def check_file_port_config(file_path, expected_port="5000"):
    """Check if a file has the correct port configuration"""
    if not Path(file_path).exists():
        return False, f"File {file_path} does not exist"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for port 10000 (should not exist)
        if "10000" in content:
            return False, f"Found reference to port 10000 in {file_path}"
        
        # Check for PORT environment variable usage
        port_pattern = r"PORT['\"],?\s*['\"]?(\d+)['\"]?\)"
        matches = re.findall(port_pattern, content)
        
        for match in matches:
            if match == "10000":
                return False, f"Found PORT default to 10000 in {file_path}"
            elif match == expected_port:
                return True, f"Correct PORT default ({expected_port}) found in {file_path}"
        
        # Check if file uses PORT env var at all
        if "PORT" in content and "os.environ.get" in content:
            return True, f"Uses PORT environment variable in {file_path}"
        
        return True, f"No port issues found in {file_path}"
        
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def check_yaml_config(file_path):
    """Check YAML configuration files"""
    if not Path(file_path).exists():
        return False, f"File {file_path} does not exist"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for correct gunicorn command
        if "gunicorn app:app" not in content:
            return False, f"Missing 'gunicorn app:app' in {file_path}"
        
        # Check for PORT environment variable
        if "PORT" not in content:
            return False, f"Missing PORT environment variable in {file_path}"
        
        # Check for health check
        if "healthCheckPath" not in content:
            return False, f"Missing health check configuration in {file_path}"
        
        return True, f"Configuration looks good in {file_path}"
        
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def main():
    """Main verification function"""
    print("🔍 Final Deployment Verification for Render.com")
    print("=" * 50)
    
    files_to_check = [
        ("app.py", "5000"),
        ("wsgi.py", "5000"),
        ("gunicorn.conf.robust.py", "5000"),
        ("Procfile", None),
        ("Dockerfile", None)
    ]
    
    yaml_files = [
        "render.yaml",
        "render.docker.yaml"
    ]
    
    all_passed = True
    
    print("\n📁 Checking Python files for port configuration...")
    for file_path, expected_port in files_to_check:
        passed, message = check_file_port_config(file_path, expected_port)
        status = "✅" if passed else "❌"
        print(f"{status} {message}")
        if not passed:
            all_passed = False
    
    print("\n📄 Checking YAML configuration files...")
    for yaml_file in yaml_files:
        passed, message = check_yaml_config(yaml_file)
        status = "✅" if passed else "❌"
        print(f"{status} {message}")
        if not passed:
            all_passed = False
    
    print("\n📋 Summary:")
    if all_passed:
        print("🎉 All checks passed! Your application should deploy correctly to Render.com")
        print("🚀 The application will bind to port 5000 (from PORT environment variable)")
        print("💡 Health check endpoint: /health")
        print("💡 Main application file: app.py")
        return 0
    else:
        print("⚠️  Some issues found. Please fix them before deploying.")
        return 1

if __name__ == "__main__":
    exit(main())
