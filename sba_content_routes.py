from flask import request, jsonify
import math
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize SBA Content API client
try:
from services.SBA_Content import SBAContentAPI
    logger.info("Using backend.services.SBA_Content")
except ImportError:
    try:
        # Fallback to local copy if backend module is not available
        from sba_content import SBAContentAPI
        logger.info("Using local sba_content module as fallback")
    except ImportError:
        logger.error("Failed to import SBA_Content from any location")
        # Define a stub API class as a last resort
        class SBAContentAPI:
            def __init__(self, *args, **kwargs):
                pass
                
            def _get(self, *args, **kwargs):
                return {"error": "SBA Content API not available", "success": False}
                
            def __getattr__(self, name):
                return lambda *args, **kwargs: self._get()

sba_content_api = SBAContentAPI()

def register_sba_content_routes(app):
    """Register SBA content routes with the Flask app"""

    @app.route('/api/sba-content/<content_type>', methods=['GET'])
    def get_sba_content(content_type):
        """Get SBA content by type with optional search query"""
        try:
            query = request.args.get('query', '')
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 10))
            
            # Set up parameters for the API call
            params = {
                'page': page,
                'limit': limit
            }
            
            # Add search parameters if provided
            if query:
                params['search'] = query
            
            # Call the appropriate method based on content type
            results = None
            if content_type == 'articles':
                results = sba_content_api.search_articles(**params)
            elif content_type == 'blogs':
                results = sba_content_api.search_blogs(**params)
            elif content_type == 'courses':
                results = sba_content_api.search_courses(**params)
            elif content_type == 'events':
                results = sba_content_api.search_events(**params)
            elif content_type == 'documents':
                results = sba_content_api.search_documents(**params)
            elif content_type == 'offices':
                results = sba_content_api.search_contacts(**params)
            else:
                return jsonify({'error': 'Invalid content type', 'success': False}), 400
            
            return jsonify({'items': results.get('items', []), 'totalPages': results.get('totalPages', 1), 'success': True})
        except Exception as e:
            logger.error(f"Error in get_sba_content: {e}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/api/sba-content/<content_type>/<int:item_id>', methods=['GET'])
    def get_sba_content_item(content_type, item_id):
        """Get a single SBA content item by ID"""
        try:
            if content_type == 'articles':
                result = sba_content_api.get_article(item_id)
            elif content_type == 'blogs':
                result = sba_content_api.get_blog(item_id)
            elif content_type == 'courses':
                result = sba_content_api.get_course(str(item_id))  # Course uses pathname
            elif content_type == 'events':
                # For events, we need to first get all events and filter by ID
                events = sba_content_api.search_events()
                if events.get('items'):
                    event_list = events.get('items', [])
                    result = next((event for event in event_list if event.get('id') == item_id), None)
                    if result:
                        return jsonify(result)
                    else:
                        return jsonify({'error': f'Event with ID {item_id} not found'}), 404
            elif content_type == 'documents':
                # For documents, we need to first get all documents and filter by ID
                documents = sba_content_api.search_documents()
                if documents.get('items'):
                    doc_list = documents.get('items', [])
                    result = next((doc for doc in doc_list if doc.get('id') == item_id), None)
                    if result:
                        return jsonify(result)
                    else:
                        return jsonify({'error': f'Document with ID {item_id} not found'}), 404
            elif content_type == 'offices':
                # For offices, we need to first get all offices and filter by ID
                offices = sba_content_api.search_offices()
                if offices.get('items'):
                    office_list = offices.get('items', [])
                    result = next((office for office in office_list if office.get('id') == item_id), None)
                    if result:
                        return jsonify(result)
                    else:
                        return jsonify({'error': f'Office with ID {item_id} not found'}), 404
            else:
                return jsonify({'error': f'Invalid content type: {content_type}'}), 400
            
            # Check for API errors
            if result and result.get('error'):
                return jsonify({'error': result['error']}), 500
            
            # Return the result
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"SBA content item error: {str(e)}")
            return jsonify({'error': f'Failed to fetch SBA content item: {str(e)}'}), 500

    @app.route('/api/sba-content/health', methods=['GET'])
    def sba_content_health():
        """Check if SBA content API is available"""
        try:
            # Try to make a simple query to test the API
            test_result = sba_content_api.search_articles(limit=1)
            if test_result.get('error'):
                return jsonify({
                    'status': 'degraded',
                    'message': f"SBA Content API returned an error: {test_result.get('error')}",
                    'available': False
                }), 200
            
            return jsonify({
                'status': 'ok',
                'message': 'SBA Content API is available',
                'available': True
            }), 200
        except Exception as e:
            logger.error(f"SBA content health check error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'SBA Content API health check failed: {str(e)}',
                'available': False
            }), 200  # Still return 200 for health checks
