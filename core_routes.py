from flask import request, jsonify
import time
import logging

logger = logging.getLogger(__name__)

# This function will be called by app.py to register the routes
def register_core_routes(app):

    # In a real application, you would have a more sophisticated way of handling
    # the vector_store, but for this example, we'll just pass it in.
    vector_store = app.vector_store

    @app.route('/api/info', methods=['GET'])
    def get_system_info():
        """Get system information"""
        return jsonify({
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'status': 'operational',
            'rag_status': 'available' if app.rag_system_available else 'unavailable',
            'vector_store': 'simple-memory',
            'document_count': vector_store.count()
        })

    @app.route('/api/models', methods=['GET'])
    def get_available_models():
        """Get available AI models"""
        return jsonify({'models': ['simple-rag']})

    @app.route('/api/documents', methods=['GET'])
    def get_documents():
        """Get all documents"""
        try:
            documents = vector_store.get_all_documents()
            return jsonify({
                'documents': documents,
                'count': len(documents),
                'rag_status': 'available'
            })
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return jsonify({
                'documents': [],
                'count': 0,
                'rag_status': 'unavailable'
            })

    @app.route('/api/documents/add', methods=['POST'])
    def add_document():
        """Add a new document to the vector database"""
        if not app.rag_system_available:
            return jsonify({'error': 'RAG system not available'}), 503
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
                
            document_text = data.get('text', '')
            document_id = data.get('id')
            metadata = data.get('metadata', {})
            
            if not document_text:
                return jsonify({'error': 'Document text is required'}), 400
            
            if not document_id:
                document_id = f'doc_{int(time.time() * 1000)}'
            
            metadata.update({
                'added_at': int(time.time()),
                'content_length': len(document_text),
                'source': 'api_upload'
            })
            
            vector_store.add_document(document_id, document_text, metadata)
            
            logger.info(f"Document added: {document_id}")
            return jsonify({
                'success': True,
                'document_id': document_id,
                'message': 'Document added successfully',
                'metadata': metadata
            })
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return jsonify({'error': f'Failed to add document: {str(e)}'}), 500

    @app.route('/api/search', methods=['POST'])
    def semantic_search():
        """Perform semantic search on documents"""
        if not app.rag_system_available:
            return jsonify({'error': 'RAG system not available'}), 503
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
                
            query = data.get('query', '')
            n_results = min(int(data.get('n_results', 5)), 20)
            
            if not query:
                return jsonify({'error': 'Query is required'}), 400
            
            results = vector_store.search(query, n_results=n_results)
            
            formatted_results = []
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'relevance_score': 1 - results['distances'][0][i]
                    })
            
            return jsonify({
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results),
                'search_time': time.time()
            })
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return jsonify({'error': f'Search failed: {str(e)}'}), 500

    @app.route('/api/chat', methods=['POST'])
    def rag_chat():
        """RAG-powered chat endpoint"""
        if not app.rag_system_available:
            return jsonify({'error': 'RAG system not available'}), 503
        
        try:
            data = request.get_json()
            user_query = data.get('message', '')
            
            if not user_query:
                return jsonify({'error': 'Message is required'}), 400
            
            search_results = vector_store.search(user_query, n_results=3)
            
            context_parts = []
            sources = []
            
            if search_results['documents'][0]:
                for i, doc in enumerate(search_results['documents'][0]):
                    context_parts.append(f"Source {i+1}: {doc}")
                    sources.append({
                        'id': search_results['ids'][0][i],
                        'content': doc[:200] + "..." if len(doc) > 200 else doc,
                        'metadata': search_results['metadatas'][0][i],
                        'relevance': 1 - search_results['distances'][0][i]
                    })
            
            context = "\n\n".join(context_parts)
            
            if context:
                response = f"Based on my knowledge base, here's what I found regarding '{user_query}':\n\n{context}"
            else:
                response = f"I don't have specific information about '{user_query}' in my current knowledge base. Please add relevant documents to help me provide better answers."
            
            return jsonify({
                'query': user_query,
                'response': response,
                'sources': sources,
                'context_used': bool(context),
                'response_time': time.time()
            })
            
        except Exception as e:
            logger.error(f"RAG chat error: {str(e)}")
            return jsonify({'error': f'Chat failed: {str(e)}'}), 500

    @app.route('/api/collections/stats', methods=['GET'])
    def get_collection_stats():
        """Get collection statistics"""
        return jsonify({
            'total_documents': vector_store.count(),
            'collection_name': 'simple_vector_store',
            'rag_status': 'available' if app.rag_system_available else 'unavailable'
        })
