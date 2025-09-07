from flask import Blueprint, request, jsonify
import logging
from services.SBA_Content import SBAContentAPI

logger = logging.getLogger(__name__)

sba_bp = Blueprint('sba', __name__)
sba_api = SBAContentAPI()

@sba_bp.route('/content/articles', methods=['GET'])
def search_articles():
    """Search SBA articles"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_articles(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        return jsonify({'error': 'Failed to search articles'}), 500

@sba_bp.route('/content/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    """Get article details"""
    try:
        result = sba_api.get_article(article_id)

        if 'error' in result:
            return jsonify({'error': result['error']}), 404

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting article details: {str(e)}")
        return jsonify({'error': 'Failed to get article details'}), 500

@sba_bp.route('/content/blogs', methods=['GET'])
def search_blogs():
    """Search SBA blog posts"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_blogs(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching blogs: {str(e)}")
        return jsonify({'error': 'Failed to search blogs'}), 500

@sba_bp.route('/content/courses', methods=['GET'])
def search_courses():
    """Search SBA courses"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_courses(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching courses: {str(e)}")
        return jsonify({'error': 'Failed to search courses'}), 500

@sba_bp.route('/content/documents', methods=['GET'])
def search_documents():
    """Search SBA documents"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_documents(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return jsonify({'error': 'Failed to search documents'}), 500

@sba_bp.route('/content/events', methods=['GET'])
def search_events():
    """Search SBA events"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_events(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching events: {str(e)}")
        return jsonify({'error': 'Failed to search events'}), 500

@sba_bp.route('/content/offices', methods=['GET'])
def search_offices():
    """Search SBA offices"""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))

        params = {'query': query, 'page': page} if query else {'page': page}
        result = sba_api.search_offices(**params)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify({
            'items': result.get('results', []),
            'totalPages': result.get('total_pages', 1),
            'currentPage': page
        })

    except Exception as e:
        logger.error(f"Error searching offices: {str(e)}")
        return jsonify({'error': 'Failed to search offices'}), 500

@sba_bp.route('/content/node/<int:node_id>', methods=['GET'])
def get_node_details(node_id):
    """Get node details by ID"""
    try:
        result = sba_api.get_node(node_id)

        if 'error' in result:
            return jsonify({'error': result['error']}), 404

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting node details: {str(e)}")
        return jsonify({'error': 'Failed to get node details'}), 500
