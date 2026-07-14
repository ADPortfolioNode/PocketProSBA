from flask import Blueprint, request, jsonify
import logging
import time

logger = logging.getLogger(__name__)
from backend.services.api_service import (
    get_system_info_service,
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
)
from backend.services.rag import get_rag_manager

api_bp = Blueprint('api', __name__)


def _get_json_payload():
    """Parse JSON body; return 400 for malformed JSON."""
    data = request.get_json(silent=True)
    if data is not None:
        return data, None
    if request.data:
        return None, (jsonify({'error': 'Bad Request'}), 400)
    return None, (jsonify({'error': 'No JSON data provided'}), 400)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    server_info = {'self': request.host_url.rstrip('/')}
    return jsonify({'status': 'healthy', 'server': server_info}), 200


@api_bp.route('/programs', methods=['GET'])
def list_sba_programs():
    """
    SBA program cards for the Programs tab.
    Delegates to sba routes helper so fields stay in sync with /api/sba/resources.
    """
    try:
        from backend.routes.sba import _sba_program_cards
        programs = _sba_program_cards()
    except Exception:
        programs = [
            {
                'id': 'loans',
                'name': 'SBA Loans',
                'description': '7(a), 504, Microloan, and Express financing options',
                'icon': '💰',
                'url': 'https://www.sba.gov/funding-programs/loans',
            },
            {
                'id': 'contracting',
                'name': 'Government Contracting',
                'description': 'Certifications and support to win federal contracts',
                'icon': '📝',
                'url': 'https://www.sba.gov/federal-contracting',
            },
            {
                'id': 'disaster',
                'name': 'Disaster Assistance',
                'description': 'Recovery loans after declared disasters',
                'icon': '🚨',
                'url': 'https://www.sba.gov/funding-programs/disaster-assistance',
            },
            {
                'id': 'counseling',
                'name': 'Counseling & Training',
                'description': 'SBDC, SCORE, WBC, and VBOC mentoring',
                'icon': '👥',
                'url': 'https://www.sba.gov/local-assistance',
            },
            {
                'id': 'international',
                'name': 'International Trade',
                'description': 'Export financing and market expansion support',
                'icon': '🌎',
                'url': 'https://www.sba.gov/business-guide/grow-your-business/export-products',
            },
            {
                'id': 'innovation',
                'name': 'SBIR/STTR',
                'description': 'R&D grants for innovative small businesses',
                'icon': '💡',
                'url': 'https://www.sbir.gov/',
            },
        ]
    return jsonify(programs), 200

@api_bp.route('/chromadb_health', methods=['GET'])
def chromadb_health_check():
    """ChromaDB health check endpoint"""
    server_info = {'self': request.host_url.rstrip('/')}
    try:
        rag_manager = get_rag_manager()
        if rag_manager.is_available():
            return jsonify({
                'status': 'ok',
                'server': server_info,
                'message': 'ChromaDB is available and connected',
                'document_count': rag_manager.get_document_count()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'server': server_info,
                'message': 'ChromaDB is not available',
                'document_count': 0
            }), 200
    except Exception as e:
        logger.error(f"Error checking ChromaDB health: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to check ChromaDB health: {str(e)}'
        }), 500

@api_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        info = get_system_info_service()
        info['server'] = {
            'self': request.host_url.rstrip('/'),
            'host': request.host,
            'scheme': request.scheme
        }
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system information'}), 500

@api_bp.route('/diagnostics', methods=['GET'])
def get_diagnostics():
    """Get diagnostics information"""
    try:
        diagnostics_info = {
            'status': 'operational',
            'message': 'All systems functional',
            'timestamp': time.time()
        }
        return jsonify(diagnostics_info), 200
    except Exception as e:
        logger.error(f"Error getting diagnostics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve diagnostics'}), 500

@api_bp.route('/decompose', methods=['POST'])
def decompose_task():
    """Decompose a user task into steps"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        message = data.get('message', '')
        session_id = data.get('session_id')

        if not message:
            logger.warning("Message is required for decompose task")
            return jsonify({'error': 'Message is required'}), 400

        response = decompose_task_service(message, session_id)
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@api_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        task = data.get('task', {})
        result = execute_step_service(task)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        return jsonify({'error': f'Failed to execute step: {str(e)}'}), 500

@api_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        result = data.get('result', '')
        task = data.get('task', {})
        validation = validate_step_service(result, task)
        return jsonify(validation)

    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

@api_bp.route('/query', methods=['POST'])
def query_documents():
    """Query documents"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)

        if not query:
            logger.warning("Query is required for querying documents")
            return jsonify({'error': 'Query is required'}), 400

        results = query_documents_service(query, top_k)
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return jsonify({'error': 'Failed to query documents'}), 500


@api_bp.route('/search', methods=['GET', 'POST', 'OPTIONS'])
def api_search():
    """
    Prebuilt App.js:
      GET {base}/api/search?query=...
    with base http://localhost:5000/api → /api/api/search → /api/search.
    Expects { results: [...] }.
    """
    if request.method == 'OPTIONS':
        return '', 204
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            query = (data.get('query') or data.get('q') or data.get('message') or '').strip()
            top_k = min(int(data.get('top_k', 10)), 20)
        else:
            query = (request.args.get('query') or request.args.get('q') or '').strip()
            try:
                top_k = min(int(request.args.get('top_k', 10)), 20)
            except ValueError:
                top_k = 10

        if not query:
            return jsonify({'results': [], 'count': 0, 'query': '', 'success': True}), 200

        results = []
        try:
            payload = query_documents_service(query, top_k)
            rows = payload.get('results') if isinstance(payload, dict) else []
            for r in rows or []:
                if not isinstance(r, dict):
                    continue
                results.append({
                    'id': r.get('id'),
                    'title': (r.get('metadata') or {}).get('filename') or r.get('id') or 'Document',
                    'content': r.get('content') or r.get('text') or '',
                    'snippet': str(r.get('content') or r.get('text') or '')[:240],
                    'score': r.get('relevance_score') or r.get('distance'),
                    'metadata': r.get('metadata') or {},
                })
        except Exception as e:
            logger.warning('api_search document query soft-fail: %s', e)

        # Soft SBA catalog match so search is never totally empty
        if not results:
            try:
                from backend.routes.sba import _sba_program_cards, _sba_lifecycle_cards, _sba_local_resource_cards
                qlow = query.lower()
                for card in (_sba_program_cards() + _sba_lifecycle_cards() + _sba_local_resource_cards()):
                    blob = f"{card.get('name','')} {card.get('description','')}".lower()
                    if any(tok in blob for tok in qlow.split() if len(tok) > 2):
                        results.append({
                            'id': card.get('id'),
                            'title': card.get('name') or card.get('title'),
                            'content': card.get('description'),
                            'snippet': (card.get('description') or '')[:240],
                            'url': card.get('url'),
                            'source': 'sba_catalog',
                        })
            except Exception as e:
                logger.warning('api_search catalog soft-fail: %s', e)

        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results),
        }), 200
    except Exception as e:
        logger.exception('GET/POST /api/search failed')
        return jsonify({'error': str(e), 'results': [], 'count': 0}), 500


@api_bp.route('/rag', methods=['POST', 'OPTIONS'])
def api_rag_alias():
    """Alias so /api/rag works even if only api_bp is mounted without rewrite quirks."""
    if request.method == 'OPTIONS':
        return '', 204
    from backend.routes.rag import rag_root_query
    return rag_root_query()


# ---- Auth aliases (frontend uses /api/login, /api/register, …) ----
@api_bp.route('/login', methods=['POST'])
def api_login_alias():
    from backend.routes.auth import login as auth_login
    return auth_login()


@api_bp.route('/register', methods=['POST'])
def api_register_alias():
    from backend.routes.auth import register as auth_register
    return auth_register()


@api_bp.route('/forgot-password', methods=['POST'])
def api_forgot_password_alias():
    from backend.routes.auth import forgot_password as auth_forgot
    return auth_forgot()


@api_bp.route('/reset-password', methods=['POST'])
def api_reset_password_alias():
    from backend.routes.auth import reset_password as auth_reset
    return auth_reset()
