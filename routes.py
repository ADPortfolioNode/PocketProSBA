# Central route registration for all API endpoints

def register_all_routes(app):
    """Register all API routes with the Flask app."""
    global socketio, chroma_service, rag_system_available
    
    # Import and register component routes
    from sba_content_routes import register_sba_content_routes
    register_sba_content_routes(app)
    
    # Import and register document management routes
    from routes.document_routes import register_document_routes
    register_document_routes(app, socketio, chroma_service, rag_system_available)
    
    # Add other route registrations here as needed
