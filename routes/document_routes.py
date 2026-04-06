"""Document management routes for PocketPro SBA."""

from flask import request, jsonify
import logging
import time
from utils import ChromaDBError, ValidationError, format_error_response

# Configure logging
logger = logging.getLogger(__name__)

def register_document_routes(app, socketio, chroma_service, rag_system_available):
    """Register document management routes with the Flask app."""

    @app.route('/api/documents/<doc_id>', methods=['DELETE'])
    def delete_document(doc_id):
        """Delete a document from ChromaDB"""
        if not rag_system_available:
            return jsonify({
                'error': 'RAG system not available',
                'status_code': 503,
                'timestamp': int(time.time())
            }), 503
        
        try:
            if not doc_id:
                raise ValidationError('Document ID is required')
            
            # Update frontend about deletion process
            socketio.emit('document_status', {
                'status': 'processing',
                'message': f'Deleting document {doc_id}...'
            })
            
            try:
                # Attempt to delete from ChromaDB
                if chroma_service.delete_document(doc_id):
                    # Get updated stats
                    stats = chroma_service.get_collection_stats()
                    
                    logger.info("✅ Document deleted: %s", doc_id)
                    
                    # Update frontend about completion
                    socketio.emit('document_status', {
                        'status': 'completed',
                        'message': f'Document {doc_id} deleted successfully',
                        'stats': stats
                    })
                    
                    return jsonify({
                        'success': True,
                        'document_id': doc_id,
                        'message': 'Document deleted successfully',
                        'stats': stats,
                        'timestamp': int(time.time())
                    })
                else:
                    raise ValidationError(f'Document {doc_id} not found')
                    
            except ChromaDBError as e:
                # Update frontend about error
                socketio.emit('document_status', {
                    'status': 'error',
                    'message': str(e)
                })
                raise  # Let error handler format the response
                
        except (ValidationError, ChromaDBError) as e:
            # These are already handled by error handlers
            socketio.emit('document_status', {
                'status': 'error',
                'message': str(e)
            })
            raise
            
        except Exception as e:
            logger.error("Error deleting document: %s", str(e))
            # Update frontend about error
            socketio.emit('document_status', {
                'status': 'error',
                'message': f'Failed to delete document: {str(e)}'
            })
            return jsonify(format_error_response(e, 500)), 500