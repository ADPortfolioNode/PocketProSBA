#!/usr/bin/env python3
"""
Render.com Environment Verification Script
This script verifies that the application is correctly configured for Render.com
"""
import os
import sys
import platform
import socket
import json

def check_environment():
    """Check the environment variables"""
    print("🔍 Checking environment variables...")
    
    # Critical environment variables
    critical_vars = ['PORT', 'FLASK_APP', 'FLASK_ENV', 'PYTHONPATH']
    env_status = {}
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✅ {var}: {value}")
            env_status[var] = value
        else:
            print(f"  ❌ {var}: Not set")
            env_status[var] = None
    
    # Check if we're running on Render.com
    render_var = os.environ.get('RENDER')
    if render_var:
        print(f"  ✅ Running on Render.com: {render_var}")
        env_status['RENDER'] = render_var
    else:
        print(f"  ℹ️ Not running on Render.com")
        env_status['RENDER'] = None
    
    return env_status

def check_networking():
    """Check networking configuration"""
    print("\n🔍 Checking networking configuration...")
    
    # Get hostname and IP
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  ✅ Hostname: {hostname}")
        print(f"  ✅ IP address: {ip}")
    except Exception as e:
        print(f"  ❌ Failed to get IP address: {e}")
        ip = None
    
    # Check if we can bind to the port
    port = int(os.environ.get('PORT', 5000))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        print(f"  ✅ Can bind to 0.0.0.0:{port}")
        sock.close()
    except Exception as e:
        print(f"  ❌ Cannot bind to 0.0.0.0:{port}: {e}")
    
    return {
        'hostname': hostname,
        'ip': ip,
        'port': port
    }

def check_system():
    """Check system information"""
    print("\n🔍 Checking system information...")
    
    # Python version
    python_version = sys.version.split()[0]
    print(f"  ✅ Python version: {python_version}")
    
    # Operating system
    os_info = platform.platform()
    print(f"  ✅ Operating system: {os_info}")
    
    # CPU architecture
    cpu_arch = platform.machine()
    print(f"  ✅ CPU architecture: {cpu_arch}")
    
    # Current working directory
    cwd = os.getcwd()
    print(f"  ✅ Working directory: {cwd}")
    
    return {
        'python_version': python_version,
        'os_info': os_info,
        'cpu_arch': cpu_arch,
        'cwd': cwd
    }

def write_report(env_status, networking, system_info):
    """Write a report file"""
    report = {
        'environment': env_status,
        'networking': networking,
        'system': system_info,
        'timestamp': '__TIMESTAMP__',  # Will be replaced in the actual code
    }
    
    report_path = 'render_environment_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report written to {report_path}")

def main():
    """Main function"""
    print("🚀 Render.com Environment Verification")
    print("=" * 50)
    
    env_status = check_environment()
    networking = check_networking()
    system_info = check_system()
    
    # Write report
    write_report(env_status, networking, system_info)
    
    print("\n📋 Verification Summary:")
    render_env = env_status.get('RENDER')
    port_env = env_status.get('PORT')
    
    if render_env:
        print("  ✅ Running on Render.com")
    else:
        print("  ℹ️ Not running on Render.com (local environment)")
    
    if port_env:
        print(f"  ✅ PORT environment variable set to {port_env}")
    else:
        print("  ❌ PORT environment variable not set")
    
    print("\n✅ Verification complete.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
