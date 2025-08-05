# Central route registration for all API endpoints

def register_all_routes(app):
    """Register all API routes with the Flask application"""
    
    # Import and register SBA content routes
    try:
        from sba_content_routes import register_sba_content_routes
        register_sba_content_routes(app)
    except ImportError as e:
        print(f"Warning: Could not register SBA content routes: {e}")
    
    # Import and register core API routes
    try:
        from core_routes import register_core_routes
        register_core_routes(app)
    except ImportError as e:
        print(f"Warning: Could not register core routes: {e}")
    
    # Import and register health check routes
    try:
        from health_routes import register_health_routes
        register_health_routes(app)
    except ImportError as e:
        print(f"Warning: Could not register health routes: {e}")
    
    print("✅ All API routes registered successfully")
