#!/usr/bin/env python3
"""
Test script to verify Render.com port binding works correctly
Run this locally before deploying to Render to ensure port binding will work
"""
import os
import sys
import requests
import time
import subprocess
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("render-port-test")

def test_port_binding(port=5000):
    """Test if the application binds correctly to the specified port"""
    logger.info(f"Testing port binding on port {port}")
    
    # Set environment variable
    os.environ["PORT"] = str(port)
    logger.info(f"Set PORT environment variable to {port}")
    
    # Start the application using the Render Procfile configuration
    cmd = f"gunicorn app:app --config=gunicorn_render_fixed.py"
    logger.info(f"Starting application with command: {cmd}")
    
    proc = subprocess.Popen(cmd, shell=True)
    logger.info(f"Application started with PID {proc.pid}")
    
    # Wait for the application to start
    logger.info("Waiting for application to start...")
    time.sleep(3)
    
    # Test if the application is responding
    try:
        logger.info(f"Testing connection to http://localhost:{port}/health")
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Successfully connected to application on port {port}")
            logger.info(f"Response: {response.json()}")
            success = True
        else:
            logger.error(f"❌ Application responded with status code {response.status_code}")
            success = False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to connect to application: {e}")
        success = False
    
    # Terminate the application
    logger.info(f"Terminating application (PID {proc.pid})")
    proc.terminate()
    proc.wait()
    
    return success

if __name__ == "__main__":
    # Allow port to be specified as a command line argument
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    if test_port_binding(port):
        logger.info("✅ Port binding test PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Port binding test FAILED!")
        sys.exit(1)
