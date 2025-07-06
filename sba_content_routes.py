from backend.services.SBA_Content import SBAContentAPI

# Initialize SBA Content API client
sba_content_api = SBAContentAPI()

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
            results = sba_content_api.search_offices(**params)
        else:
            return jsonify({'error': f'Invalid content type: {content_type}'}), 400
        
        # Check for API errors
        if results.get('error'):
            return jsonify({'error': results['error']}), 500
        
        # Process and return results
        items = results.get('items', [])
        total = results.get('total', 0)
        total_pages = math.ceil(total / limit) if total > 0 else 1
        
        return jsonify({
            'items': items,
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': total_pages
        })
        
    except Exception as e:
        logger.error(f"SBA content error: {str(e)}")
        return jsonify({'error': f'Failed to fetch SBA content: {str(e)}'}), 500

@app.route('/api/sba-content/<content_type>/<int:item_id>', methods=['GET'])
def get_sba_content_item(content_type, item_id):
    """Get a specific SBA content item by type and ID"""
    try:
        # Call the appropriate method based on content type
        result = None
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
