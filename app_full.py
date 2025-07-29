import os
import time
from flask import Flask, jsonify
import logging

# Basic setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
start_time = time.time()

app = Flask(__name__)

# Gunicorn-compatible logging integration
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Startup info endpoint
@app.route('/startup', methods=['GET'])
def startup_info():
    return jsonify({
        "environment": os.getenv("FLASK_ENV", "production"),
        "host": "0.0.0.0",
        "message": "🚀 PocketPro:SBA is running!",
        "port": int(os.getenv("PORT", 5000)),
        "service": "PocketPro Small Business Assistant",
        "status": "success",
        "version": "1.0.0",
        "uptime": round(time.time() - start_time, 2)
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
