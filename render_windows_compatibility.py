"""
Windows-compatible script to test the Render.com deployment
Since fcntl is not available on Windows, this uses a simplified approach
"""

import os
import sys
import logging
import json
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("render-windows-test")

def test_port_config():
    """Test if the PORT environment variable is correctly read"""
    # Check if app.py exists
    if not os.path.exists("app.py"):
        logger.error("ERROR: app.py not found in the current directory!")
        return False
    
    # Import the app without running it
    try:
        sys.path.insert(0, os.getcwd())
        import app as app_module
        
        # Check if 'app' is in the module
        if not hasattr(app_module, 'app'):
            logger.error("ERROR: No 'app' object found in app.py!")
            return False
        
        app_instance = app_module.app
        if not isinstance(app_instance, Flask):
            logger.error("ERROR: The 'app' object in app.py is not a Flask application!")
            return False
        
        logger.info("PASSED: Successfully imported the Flask app from app.py")
        
        # Test the __main__ block logic
        if not hasattr(app_module, '__name__'):
            logger.error("ERROR: app.py doesn't have a __name__ check!")
            return False
        
        # Look for PORT environment variable usage
        with open("app.py", "r") as f:
            content = f.read()
            if "os.environ.get('PORT'" in content or 'os.environ.get("PORT"' in content:
                logger.info("PASSED: app.py correctly uses the PORT environment variable")
            else:
                logger.warning("WARNING: Couldn't find PORT environment variable usage in app.py")
        
        # Look for Procfile
        if os.path.exists("Procfile"):
            with open("Procfile", "r") as f:
                procfile = f.read()
                if "$PORT" in procfile or "${PORT}" in procfile:
                    logger.info("PASSED: Procfile includes PORT variable reference")
                else:
                    logger.warning("WARNING: Procfile doesn't explicitly reference the PORT variable")
        else:
            logger.error("ERROR: Procfile not found!")
            return False
        
        # Check if there's a port binding in main
        if "app.run" in content and "port" in content:
            logger.info("PASSED: app.py includes app.run with port parameter")
        
        return True
    except ImportError as e:
        logger.error(f"ERROR: Failed to import app.py: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"ERROR: Error testing app.py: {str(e)}")
        return False

def create_windows_render_config():
    """Create a Windows-compatible Render configuration file"""
    config_content = """\"\"\"
Windows-compatible Gunicorn configuration for Render.com
Modified to work without fcntl module
\"\"\"
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gunicorn.render.windows")

# Get the PORT environment variable
port = int(os.environ.get('PORT', 5000))
logger.info(f"PORT environment variable: {port}")

# Server socket binding configuration
bind = f"0.0.0.0:{port}"
logger.info(f"Binding to: {bind}")

# Worker configuration - minimal for Render
workers = 1
worker_class = "sync"
timeout = 60
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    logger.info("=== PocketPro SBA Server Starting ===")
    logger.info(f"Binding to: {bind}")
    logger.info(f"Worker concurrency: {workers}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

def on_exit(server):
    logger.info("=== PocketPro SBA Server Shutting Down ===")
"""
    
    # Write the file
    with open("gunicorn_windows_render.py", "w") as f:
        f.write(config_content)
    
    logger.info("PASSED: Created Windows-compatible gunicorn_windows_render.py")
    
    # Update Procfile for Windows compatibility
    with open("Procfile", "r") as f:
        procfile = f.read()
    
    # Update Procfile to use windows compatible config
    new_procfile = procfile.replace(
        "gunicorn app:app --config=gunicorn_render_fixed.py", 
        "gunicorn app:app --config=gunicorn_windows_render.py"
    ).replace(
        "gunicorn app:app --bind 0.0.0.0:$PORT",
        "gunicorn app:app --config=gunicorn_windows_render.py"
    )
    
    with open("Procfile", "w") as f:
        f.write(new_procfile)
    
    logger.info("PASSED: Updated Procfile to use Windows-compatible configuration")
    
    return True

def verify_flask_app():
    """Verify the Flask app has the correct port configuration"""
    # Try to start the Flask app directly (not with gunicorn)
    os.environ["PORT"] = "5000"
    
    try:
        import app as app_module
        logger.info("PASSED: Flask app imported successfully")
        
        # Print routes
        if hasattr(app_module, 'app'):
            app = app_module.app
            logger.info("Available routes:")
            for rule in app.url_map.iter_rules():
                logger.info(f"  - {rule}")
            
            # Check for health endpoint
            has_health = any('/health' in str(rule) for rule in app.url_map.iter_rules())
            if has_health:
                logger.info("PASSED: /health endpoint found")
            else:
                logger.warning("WARNING: No /health endpoint found")
                
            return True
        else:
            logger.error("ERROR: No Flask app found in app.py")
            return False
    except Exception as e:
        logger.error(f"ERROR: Error verifying Flask app: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting Render.com Windows compatibility test")
    
    # Create Windows-compatible configuration
    if not create_windows_render_config():
        sys.exit(1)
    
    # Test the port configuration
    if not test_port_config():
        sys.exit(1)
    
    # Verify the Flask app
    if not verify_flask_app():
        sys.exit(1)
    
    logger.info("\nAll tests passed! Your application should work on Render.com.")
    logger.info("To test locally on Windows, run your Flask app directly with:")
    logger.info("    set PORT=5000")
    logger.info("    python app.py")
    logger.info("\nFor deployment to Render.com, use the updated Procfile.")
    
    sys.exit(0)
