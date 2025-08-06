# Central route registration for all API endpoints

def register_all_routes(app):
    """Register all API routes with the Flask application"""
    
    from sba_content_routes import register_sba_content_routes
from core_routes import register_core_routes
from health_routes import register_health_routes
    
    print("✅ All API routes registered successfully")
