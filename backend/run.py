import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'services'))
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Disable reloader in Docker — file-change restarts cause browser
    # net::ERR_EMPTY_RESPONSE / intermittent 404 on /api/api/* during reload.
    debug = os.environ.get('FLASK_DEBUG', '0') in ('1', 'true', 'True')
    use_reloader = os.environ.get('FLASK_RELOAD', '0') in ('1', 'true', 'True')
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=use_reloader, threaded=True)