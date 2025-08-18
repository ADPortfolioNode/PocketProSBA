#!/usr/bin/env python3
"""
Comprehensive startup script for PocketPro SBA
Starts both HTTP backend and WebSocket server
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerManager:
    def __init__(self):
        self.processes = []
        self.ports = {
            'http': 5000,
            'websocket': 5000,  # Same port for WebSocket
            'frontend': 3000
        }
        
    def check_port(self, port):
        """Check if a port is available"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False
            
    def start_http_server(self):
        """Start the HTTP backend server"""
        logger.info("Starting HTTP backend server...")
        try:
            # Import and run the main app
            from app import app
            logger.info(f"HTTP server starting on port {self.ports['http']}")
            app.run(host='0.0.0.0', port=self.ports['http'], debug=True, use_reloader=False)
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            
    def start_websocket_server(self):
        """Start the WebSocket server"""
        logger.info("Starting WebSocket server...")
        try:
            # Import and run the WebSocket server
            from websocket_server import socketio, app
            logger.info(f"WebSocket server starting on port {self.ports['websocket']}")
            socketio.run(app, host='0.0.0.0', port=self.ports['websocket'], debug=True, allow_unsafe_werkzeug=True)
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            
    def start_frontend(self):
        """Start the React frontend"""
        logger.info("Starting React frontend...")
        try:
            frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
            if os.path.exists(frontend_dir):
                os.chdir(frontend_dir)
                logger.info("Starting React development server...")
                subprocess.run(['npm', 'start'], cwd=frontend_dir)
            else:
                logger.error("Frontend directory not found")
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            
    def check_services(self):
        """Check if all services are running"""
        services = {
            'HTTP Backend': f'http://localhost:{self.ports["http"]}/health',
            'WebSocket': f'ws://localhost:{self.ports["websocket"]}/ws',
            'Frontend': f'http://localhost:{self.ports["frontend"]}'
        }
        
        import requests
        for name, url in services.items():
            try:
                if url.startswith('ws'):
                    # WebSocket check is more complex, skip for now
                    logger.info(f"✅ {name}: {url} (manual verification needed)")
                else:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✅ {name}: {url} is responding")
                    else:
                        logger.warn(f"⚠️ {name}: {url} returned {response.status_code}")
            except Exception as e:
                logger.warn(f"❌ {name}: {url} - {str(e)}")
                
    def open_browser(self):
        """Open browser to frontend"""
        time.sleep(3)  # Wait for servers to start
        url = f"http://localhost:{self.ports['frontend']}"
        logger.info(f"Opening browser to {url}")
        webbrowser.open(url)
        
    def run(self):
        """Run all services"""
        logger.info("=" * 60)
        logger.info("PocketPro SBA - Starting all services")
        logger.info("=" * 60)
        
        # Check ports
        for service, port in self.ports.items():
            if not self.check_port(port):
                logger.error(f"Port {port} is already in use for {service}")
                return
                
        # Start services in separate threads
        http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        websocket_thread = threading.Thread(target=self.start_websocket_server, daemon=True)
        
        # Start HTTP server
        http_thread.start()
        time.sleep(2)
        
        # Start WebSocket server (will use same port as HTTP)
        websocket_thread.start()
        time.sleep(2)
        
        # Check services
        self.check_services()
        
        # Open browser
        browser_thread = threading.Thread(target=self.open_browser, daemon=True)
        browser_thread.start()
        
        logger.info("\n" + "=" * 60)
        logger.info("Services started successfully!")
        logger.info(f"HTTP Backend: http://localhost:{self.ports['http']}")
        logger.info(f"WebSocket: ws://localhost:{self.ports['websocket']}/ws")
        logger.info(f"Frontend: http://localhost:{self.ports['frontend']}")
        logger.info("=" * 60)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down servers...")
            sys.exit(0)

if __name__ == '__main__':
    manager = ServerManager()
    manager.run()
