<<<<<<< HEAD
from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

=======
# Central route registration for all API endpoints

def register_all_routes(app):
    # Import and register each component's routes here
    from sba_content_routes import register_sba_content_routes
    register_sba_content_routes(app)
    # Add other route registrations here as needed
>>>>>>> 92e99b6 (production ready- fires out)
