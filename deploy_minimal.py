#!/usr/bin/env python3
"""
Render.com deployment script for PocketPro SBA Assistant
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy_minimal():
    """Deploy the minimal version for Render.com"""
    try:
        # Copy minimal app to main app.py
        if os.path.exists('app_minimal.py'):
            logger.info("Using minimal app for deployment")
            
            # Backup original app if it exists
            if os.path.exists('app.py'):
                os.rename('app.py', 'app_full.py')
                logger.info("Backed up full app to app_full.py")
            
            # Copy minimal app
            os.rename('app_minimal.py', 'app.py')
            logger.info("Deployed minimal app as app.py")
            
        # Use minimal requirements if available
        if os.path.exists('requirements.minimal.txt'):
            logger.info("Using minimal requirements for deployment")
            
            # Backup original requirements
            if os.path.exists('requirements.txt'):
                os.rename('requirements.txt', 'requirements_full.txt')
                logger.info("Backed up full requirements")
            
            # Copy minimal requirements
            os.rename('requirements.minimal.txt', 'requirements.txt')
            logger.info("Deployed minimal requirements as requirements.txt")
        
        logger.info("Minimal deployment setup complete")
        return True
        
    except Exception as e:
        logger.error(f"Deployment setup failed: {e}")
        return False

if __name__ == '__main__':
    success = deploy_minimal()
    sys.exit(0 if success else 1)
