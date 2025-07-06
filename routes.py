# Central route registration for all API endpoints

def register_all_routes(app):
    # Import and register each component's routes here
    from sba_content_routes import register_sba_content_routes
    register_sba_content_routes(app)
    # Add other route registrations here as needed
