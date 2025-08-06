
from flask import jsonify

def register_health_routes(app):

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'healthy',
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'rag_status': 'available' if app.rag_system_available else 'unavailable',
            'document_count': app.vector_store.count()
        })

    @app.route('/startup', methods=['GET'])
    def startup_check():
        """Startup readiness check"""
        return jsonify({
            'ready': True,
            'rag_available': app.rag_system_available,
            'service': 'PocketPro SBA',
            'document_count': app.vector_store.count()
        })
