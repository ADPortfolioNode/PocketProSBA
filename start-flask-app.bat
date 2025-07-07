@echo off
echo Starting Flask application...
set PORT=5000
set FLASK_ENV=development
set FLASK_APP=minimal_app.py
python minimal_app.py
