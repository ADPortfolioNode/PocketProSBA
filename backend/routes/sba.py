"""SBA content routes — multi-source public API consumption."""

from flask import Blueprint, request, jsonify
import logging
from backend.services.SBA_Content import SBAContentAPI

logger = logging.getLogger(__name__)

sba_bp = Blueprint('sba', __name__)
sba_api = SBAContentAPI()


def _page_args():
    query = request.args.get('query') or request.args.get('q') or ''
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    fresh_raw = (request.args.get('fresh') or request.args.get('force_fresh') or '').lower()
    force_fresh = fresh_raw in ('1', 'true', 'yes')
    if force_fresh:
        from backend.services.SBA_Content import clear_sba_cache
        clear_sba_cache()
    return query, max(1, page), force_fresh


def _normalize_item(raw, index=0):
    """Ensure every card has title + body text + optional url (no empty cards)."""
    if not isinstance(raw, dict):
        text = str(raw).strip()
        if not text:
            return None
        return {
            'id': f'item-{index}',
            'title': text[:120],
            'description': text,
            'summary': text,
            'url': '',
            'type': 'content',
        }

    title = (
        raw.get('title')
        or raw.get('name')
        or raw.get('label')
        or raw.get('award_title')
        or raw.get('firm')
        or ''
    )
    title = str(title).strip()
    description = (
        raw.get('description')
        or raw.get('summary')
        or raw.get('teaser')
        or raw.get('body')
        or raw.get('abstract')
        or raw.get('message')
        or ''
    )
    description = str(description).strip()
    url = str(raw.get('url') or raw.get('link') or raw.get('href') or raw.get('award_link') or '').strip()

    # If only URL is present, still render a card from it
    if not title and url:
        title = url.rstrip('/').split('/')[-1].replace('-', ' ').title() or 'SBA resource'
    if not title and description:
        title = description[:80] + ('…' if len(description) > 80 else '')
    if not description and title:
        description = f'Official SBA resource: {title}'
        if url:
            description += f' — {url}'

    # Drop pure-empty records
    if not title and not description and not url:
        return None

    # Skip obvious nav chrome titles with no useful body
    low = title.lower()
    if low in {'home', 'menu', 'search', 'login', 'sign in', 'share', 'print'} and len(description) < 40:
        return None

    item = dict(raw)
    item['id'] = raw.get('id') or raw.get('nid') or f'item-{index}'
    item['title'] = title
    item['name'] = raw.get('name') or title
    item['description'] = description
    item['summary'] = raw.get('summary') or description
    item['url'] = url
    item['type'] = raw.get('type') or 'content'
    # Surface extra reference fields for the UI
    extras = {}
    for key in (
        'agency', 'firm', 'phase', 'program', 'award_amount', 'award_year',
        'phone', 'email', 'address', 'location', 'source_page', 'retrieved_at',
        'is_current', 'freshness', 'source',
    ):
        if raw.get(key) not in (None, ''):
            extras[key] = raw.get(key)
    if extras:
        item['meta'] = extras
    return item


def _envelope(result, page=1):
    """Normalize multi-source client payloads into the frontend contract."""
    if not isinstance(result, dict):
        return {
            'items': [],
            'totalPages': 0,
            'currentPage': page,
            'degraded': True,
            'is_current': False,
            'freshness': 'not_current',
            'message': 'Unexpected SBA client response',
            'source': 'unknown',
            'render_policy': 'current_unless_rag',
        }

    # Hard error with no items
    if result.get('error') and not result.get('items') and not result.get('results'):
        logger.warning("SBA source error: %s", result.get('error'))
        return {
            'items': [],
            'totalPages': 0,
            'currentPage': page,
            'degraded': True,
            'is_current': False,
            'freshness': 'not_current',
            'message': result.get('message') or result.get('error'),
            'source': result.get('source', 'unknown'),
            'render_policy': 'current_unless_rag',
        }

    items = result.get('items')
    if items is None:
        items = result.get('results', [])
    if not isinstance(items, list):
        items = []

    normalized = []
    for i, raw in enumerate(items):
        item = _normalize_item(raw, i)
        if item:
            normalized.append(item)

    total_pages = result.get('totalPages', result.get('total_pages', 1 if normalized else 0))
    is_current = result.get('is_current')
    if is_current is None:
        is_current = result.get('source', '').startswith('sba_html') or result.get('source') in (
            'legacy_json', 'sbir',
        )
    return {
        'items': normalized,
        'totalPages': total_pages,
        'currentPage': result.get('currentPage', page),
        'count': len(normalized),
        'degraded': bool(result.get('degraded')),
        'is_current': bool(is_current),
        'freshness': result.get('freshness') or ('current' if is_current else 'not_current'),
        'retrieved_at': result.get('retrieved_at'),
        'source': result.get('source'),
        'message': result.get('message'),
        'render_policy': result.get('render_policy') or 'current_unless_rag',
    }


@sba_bp.route('/resources', methods=['GET'])
def list_resources():
    """
    Resource catalog used to build the Browse/Resources page navigation.

    Each entry is a nav item: {id, name, description, path, icon, group, queryable}.
    Frontend should load this once, render nav from it, and query `path` when clicked.
    """
    resources = [
        {
            'id': 'loans',
            'name': 'Loan Programs',
            'description': '7(a), 504, Microloan and related financing from sba.gov',
            'path': '/api/sba/content/loans',
            'icon': 'loans',
            'group': 'Funding',
            'queryable': True,
        },
        {
            'id': 'loan_types',
            'name': 'Loan Types Overview',
            'description': 'Live loan overview (prefers current sba.gov content)',
            'path': '/api/rag/sba-overview',
            'icon': 'loan_types',
            'group': 'Funding',
            'queryable': True,
        },
        {
            'id': 'lenders',
            'name': 'Lenders',
            'description': 'Lender Match and financing partners',
            'path': '/api/sba/content/lenders',
            'icon': 'lenders',
            'group': 'Funding',
            'queryable': True,
        },
        {
            'id': 'articles',
            'name': 'Articles & Guides',
            'description': 'SBA business guides and learning content',
            'path': '/api/sba/content/articles',
            'icon': 'articles',
            'group': 'Learn',
            'queryable': True,
        },
        {
            'id': 'blogs',
            'name': 'Blogs & News',
            'description': 'SBA blog and newsroom content',
            'path': '/api/sba/content/blogs',
            'icon': 'blogs',
            'group': 'Learn',
            'queryable': True,
        },
        {
            'id': 'courses',
            'name': 'Courses',
            'description': 'SBA learning resources',
            'path': '/api/sba/content/courses',
            'icon': 'courses',
            'group': 'Learn',
            'queryable': True,
        },
        {
            'id': 'documents',
            'name': 'Documents',
            'description': 'SBA forms and documents',
            'path': '/api/sba/content/documents',
            'icon': 'documents',
            'group': 'Learn',
            'queryable': True,
        },
        {
            'id': 'events',
            'name': 'Events',
            'description': 'SBA events and webinars',
            'path': '/api/sba/content/events',
            'icon': 'events',
            'group': 'Connect',
            'queryable': True,
        },
        {
            'id': 'offices',
            'name': 'Offices & Local Help',
            'description': 'District offices and local assistance finders',
            'path': '/api/sba/content/offices',
            'icon': 'offices',
            'group': 'Connect',
            'queryable': True,
        },
        {
            'id': 'sbir',
            'name': 'SBIR/STTR Awards',
            'description': 'Public SBIR.gov awards API (when available)',
            'path': '/api/sba/content/sbir',
            'icon': 'sbir',
            'group': 'Innovation',
            'queryable': True,
        },
        {
            'id': 'sources',
            'name': 'API Source Status',
            'description': 'Health of public SBA data sources',
            'path': '/api/sba/sources',
            'icon': 'sources',
            'group': 'System',
            'queryable': True,
        },
    ]
    return jsonify({
        'resources': resources,
        'count': len(resources),
        'status': 'ok',
        'navigation': {
            'source': '/api/sba/resources',
            'behavior': 'click_to_query',
            'item_open': 'detail_card',
        },
    }), 200


@sba_bp.route('/sources', methods=['GET'])
def source_status():
    """Probe public SBA-related APIs / pages."""
    try:
        return jsonify(sba_api.get_source_status()), 200
    except Exception as e:
        logger.error("SBA source status failed: %s", e)
        return jsonify({'error': str(e)}), 500


@sba_bp.route('/content/articles', methods=['GET'])
def search_articles():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_articles(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching articles: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    try:
        result = sba_api.get_article(article_id)
        if isinstance(result, dict) and result.get('error'):
            return jsonify({'error': result['error']}), 404
        return jsonify(result)
    except Exception as e:
        logger.error("Error getting article details: %s", e)
        return jsonify({'error': 'Failed to get article details'}), 500


@sba_bp.route('/content/blogs', methods=['GET'])
def search_blogs():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_blogs(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching blogs: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/courses', methods=['GET'])
def search_courses():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_courses(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching courses: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/documents', methods=['GET'])
def search_documents():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_documents(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching documents: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/events', methods=['GET'])
def search_events():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_events(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching events: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/offices', methods=['GET'])
def search_offices():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_offices(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching offices: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/loans', methods=['GET'])
def search_loans():
    """Official SBA loan program content — current live page text when available."""
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_loans(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching loans: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/sbir', methods=['GET'])
def search_sbir():
    """
    SBIR/STTR public awards API.
    Docs: https://www.sbir.gov/api
    Query params: query/firm, agency, year, page, rows, fresh
    """
    query, page, force_fresh = _page_args()
    agency = request.args.get('agency')
    firm = request.args.get('firm') or (query if query else None)
    year = request.args.get('year')
    try:
        year_i = int(year) if year else None
    except ValueError:
        year_i = None
    try:
        rows = int(request.args.get('rows', 20))
    except ValueError:
        rows = 20

    try:
        result = sba_api.search_sbir_awards(
            query=query,
            agency=agency,
            year=year_i,
            firm=firm,
            rows=rows,
            page=page,
        )
        env = _envelope(result, page)
        return jsonify(env), 200
    except Exception as e:
        logger.error("Error searching SBIR awards: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': [], 'source': 'sbir'}, page)), 200


@sba_bp.route('/content/lenders', methods=['GET'])
def search_lenders():
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_lenders(query=query, page=page, fresh=force_fresh)
        return jsonify(_envelope(result, page)), 200
    except Exception as e:
        logger.error("Error searching lenders: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page)), 200


@sba_bp.route('/content/node/<int:node_id>', methods=['GET'])
def get_node_details(node_id):
    try:
        result = sba_api.get_node(node_id)
        if isinstance(result, dict) and result.get('error'):
            return jsonify({'error': result['error']}), 404
        return jsonify(result)
    except Exception as e:
        logger.error("Error getting node details: %s", e)
        return jsonify({'error': 'Failed to get node details'}), 500
