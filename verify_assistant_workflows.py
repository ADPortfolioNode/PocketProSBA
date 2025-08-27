#!/usr/bin/env python3
"""
Verification script for PocketPro:SBA Assistant and User Experience Workflows
"""

import subprocess
import sys
import os
import json
import requests
import time

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_backend_assistants():
    """Test backend assistant functionality"""
    print("🧪 Testing Backend Assistants...")
    
    tests = [
        ("Concierge Assistant", "cd backend && python test_concierge_workflows.py"),
        ("All Assistants", "cd backend && python test_all_assistants.py"),
        ("Search Agent", "cd backend && python test_search_assistant.py"),
        ("File Agent", "cd backend && python test_file_agent.py"),
        ("Function Agent", "cd backend && python test_function_agent.py")
    ]
    
    results = []
    for test_name, command in tests:
        print(f"  Running {test_name}...")
        success, stdout, stderr = run_command(command)
        results.append((test_name, success))
        if success:
            print(f"  ✅ {test_name}: PASSED")
        else:
            print(f"  ❌ {test_name}: FAILED")
            print(f"    Error: {stderr}")
    
    return results

def test_backend_health():
    """Test backend health endpoint"""
    print("🧪 Testing Backend Health...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Backend Health: PASSED")
            return True
        else:
            print(f"  ❌ Backend Health: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"  ❌ Backend Health: FAILED (Error: {e})")
        return False

def test_frontend_build():
    """Test if frontend can build successfully"""
    print("🧪 Testing Frontend Build...")
    success, stdout, stderr = run_command("npm run build", cwd="frontend")
    if success:
        print("  ✅ Frontend Build: PASSED")
    else:
        print("  ❌ Frontend Build: FAILED")
        print(f"    Error: {stderr}")
    return success

def test_api_endpoints():
    """Test API endpoints"""
    print("🧪 Testing API Endpoints...")
    
    endpoints = [
        ("Health", "/api/health"),
        ("Info", "/api/info"),
        ("Decompose", "/api/decompose"),
        ("Execute", "/api/execute"),
        ("Validate", "/api/validate"),
        ("Query", "/api/query"),
        ("Chat", "/api/chat")
    ]
    
    results = []
    for endpoint_name, endpoint_path in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint_path}", timeout=5)
            if response.status_code in [200, 201]:
                print(f"  ✅ {endpoint_name}: PASSED (Status: {response.status_code})")
                results.append((endpoint_name, True))
            else:
                print(f"  ⚠️  {endpoint_name}: PARTIAL (Status: {response.status_code})")
                results.append((endpoint_name, False))
        except Exception as e:
            print(f"  ❌ {endpoint_name}: FAILED (Error: {e})")
            results.append((endpoint_name, False))
    
    return results

def main():
    """Main verification function"""
    print("=" * 60)
    print("PocketPro:SBA Assistant & User Experience Workflow Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test backend assistants
    assistant_results = test_backend_assistants()
    assistant_passed = all(result[1] for result in assistant_results)
    if not assistant_passed:
        all_passed = False
    
    # Test backend health
    health_passed = test_backend_health()
    if not health_passed:
        all_passed = False
    
    # Test API endpoints
    api_results = test_api_endpoints()
    api_passed = all(result[1] for result in api_results)
    if not api_passed:
        all_passed = False
    
    # Test frontend build
    build_passed = test_frontend_build()
    if not build_passed:
        all_passed = False
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"Backend Assistants: {'✅ PASSED' if assistant_passed else '❌ FAILED'}")
    print(f"Backend Health: {'✅ PASSED' if health_passed else '❌ FAILED'}")
    print(f"API Endpoints: {'✅ PASSED' if api_passed else '❌ PARTIAL/FAILED'}")
    print(f"Frontend Build: {'✅ PASSED' if build_passed else '❌ FAILED'}")
    
    if all_passed:
        print("\n🎉 ALL WORKFLOWS VERIFIED SUCCESSFULLY!")
        return 0
    else:
        print("\n⚠️  SOME WORKFLOWS NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
