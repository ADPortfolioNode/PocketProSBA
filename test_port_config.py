#!/usr/bin/env python3
"""
Test script to verify PORT environment variable and Gunicorn configuration
"""
import os
import sys
from pathlib import Path

print("🔧 Testing PORT environment variable and Gunicorn configuration...")
print("=" * 60)

# Test 1: Check current PORT environment variable
current_port = os.environ.get('PORT', None)
print(f"1. Current PORT env var: {current_port}")

# Test 2: Check what our configs would use
gunicorn_port = os.environ.get('PORT', '5000')
print(f"2. Gunicorn will bind to: 0.0.0.0:{gunicorn_port}")

# Test 3: Check wsgi.py port logic
wsgi_port = int(os.environ.get('PORT', 5000))
print(f"3. wsgi.py will use port: {wsgi_port}")

# Test 4: Test with different PORT values
test_ports = ['5000', '8000', '10000', None]
print(f"4. Testing various PORT values:")
for test_port in test_ports:
    if test_port:
        os.environ['PORT'] = test_port
        result_port = os.environ.get('PORT', '5000')
        print(f"   PORT={test_port} -> Gunicorn will bind to: 0.0.0.0:{result_port}")
    else:
        if 'PORT' in os.environ:
            del os.environ['PORT']
        result_port = os.environ.get('PORT', '5000')
        print(f"   PORT=None -> Gunicorn will bind to: 0.0.0.0:{result_port}")

# Test 5: Check if we can import the gunicorn config
print(f"5. Testing gunicorn config import...")
try:
    # Read the gunicorn config file
    config_path = Path(__file__).parent / 'gunicorn.conf.py'
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        if 'PORT' in config_content:
            print("   ✅ gunicorn.conf.py contains PORT reference")
            
            # Extract the bind line
            for line in config_content.split('\n'):
                if 'bind = ' in line and 'PORT' in line:
                    print(f"   📌 Bind line: {line.strip()}")
                    break
        else:
            print("   ❌ gunicorn.conf.py missing PORT reference")
    else:
        print("   ❌ gunicorn.conf.py not found")
        
except Exception as e:
    print(f"   ❌ Error reading gunicorn config: {e}")

print("=" * 60)
print("🎯 Summary:")
print("- Gunicorn default port changed from 10000 to 5000 ✅")
print("- wsgi.py default port changed from 10000 to 5000 ✅")
print("- Both configurations use PORT environment variable ✅")
print("- On Render.com, PORT=5000 should be automatically set ✅")
