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
    """Normalize multi-source client payloads into the frontend card contract."""
    if not isinstance(result, dict):
        return {
            'items': [],
            'results': [],
            'totalPages': 0,
            'currentPage': page,
            'count': 0,
            'degraded': True,
            'is_current': False,
            'freshness': 'not_current',
            'message': 'Unexpected SBA client response',
            'source': 'unknown',
            'render_policy': 'current_unless_rag',
        }

    # Hard error with no items → still try to surface message; callers may attach fallbacks
    if result.get('error') and not result.get('items') and not result.get('results'):
        logger.warning("SBA source error: %s", result.get('error'))
        return {
            'items': [],
            'results': [],
            'totalPages': 0,
            'currentPage': page,
            'count': 0,
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
        if not item:
            continue
        # Guarantee prebuilt SPA list fields (title + summary always present)
        if not item.get('summary'):
            item['summary'] = item.get('description') or item.get('title') or 'SBA resource'
        if not item.get('description'):
            item['description'] = item['summary']
        if not item.get('body'):
            desc = str(item.get('description') or '')
            safe = (
                desc.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\n', '<br/>')
            )
            item['body'] = f'<p>{safe}</p>'
        if not item.get('created'):
            item['created'] = result.get('retrieved_at') or item.get('retrieved_at')
        if not item.get('link') and item.get('url'):
            item['link'] = item['url']
        if item.get('type') == 'event' or 'event' in str(item.get('type', '')):
            item.setdefault('startDate', item.get('created') or item.get('retrieved_at'))
            item.setdefault('location', 'Online / see official page')
            item.setdefault('registrationLink', item.get('url') or item.get('link'))
        if item.get('type') in ('document', 'form') or 'document' in str(item.get('type', '')):
            item.setdefault('fileUrl', item.get('url') or item.get('link'))
        normalized.append(item)

    total_pages = result.get('totalPages', result.get('total_pages', 1 if normalized else 0))
    is_current = result.get('is_current')
    if is_current is None:
        is_current = result.get('source', '').startswith('sba_html') or result.get('source') in (
            'legacy_json', 'sbir',
        )
    return {
        'items': normalized,
        'results': normalized,  # alias for older clients
        'totalPages': total_pages,
        'currentPage': result.get('currentPage', page),
        'count': result.get('count', len(normalized)),
        'degraded': bool(result.get('degraded')),
        'is_current': bool(is_current),
        'freshness': result.get('freshness') or ('current' if is_current else 'not_current'),
        'retrieved_at': result.get('retrieved_at'),
        'source': result.get('source'),
        'message': result.get('message'),
        'render_policy': result.get('render_policy') or 'current_unless_rag',
    }


def _sba_program_cards():
    """Cards for SBA Programs tab (prebuilt SPA + SBAContent)."""
    site = 'https://www.sba.gov'
    return [
        {
            'id': 'loans',
            'name': 'SBA Loans',
            'title': 'SBA Loans',
            'description': '7(a), 504, Microloan, and Express financing options for small businesses.',
            'icon': '💰',
            'url': f'{site}/funding-programs/loans',
            'path': '/api/sba/content/loans',
            'group': 'Funding',
        },
        {
            'id': 'contracting',
            'name': 'Government Contracting',
            'title': 'Government Contracting',
            'description': 'Certifications and support to win federal contracts (8(a), HUBZone, WOSB, SDVOSB).',
            'icon': '📝',
            'url': f'{site}/federal-contracting',
            'path': '/api/sba/content/articles',
            'group': 'Growth',
        },
        {
            'id': 'disaster',
            'name': 'Disaster Assistance',
            'title': 'Disaster Assistance',
            'description': 'Low-interest disaster loans for businesses, nonprofits, homeowners, and renters.',
            'icon': '🚨',
            'url': f'{site}/funding-programs/disaster-assistance',
            'group': 'Funding',
        },
        {
            'id': 'counseling',
            'name': 'Counseling & Training',
            'title': 'Counseling & Training',
            'description': 'Free mentoring via SBDC, SCORE, WBC, and VBOC resource partners.',
            'icon': '👥',
            'url': f'{site}/local-assistance',
            'path': '/api/sba/content/offices',
            'group': 'Local',
        },
        {
            'id': 'international',
            'name': 'International Trade',
            'title': 'International Trade',
            'description': 'Export financing and market expansion support for small businesses.',
            'icon': '🌎',
            'url': f'{site}/business-guide/grow-your-business/export-products',
            'group': 'Growth',
        },
        {
            'id': 'innovation',
            'name': 'SBIR/STTR',
            'title': 'SBIR/STTR',
            'description': 'R&D grants that encourage small businesses to engage in federal research.',
            'icon': '💡',
            'url': 'https://www.sbir.gov/',
            'path': '/api/sba/content/sbir',
            'group': 'Innovation',
        },
        {
            'id': 'opportunities',
            'name': 'Opportunities for Veterans',
            'title': 'Opportunities for Veterans',
            'description': 'Training, counseling, capital access, and contracting for veteran entrepreneurs.',
            'icon': '🎖️',
            'url': f'{site}/business-guide/grow-your-business/veteran-owned-businesses',
            'group': 'Community',
        },
        {
            'id': 'women',
            'name': 'Women-Owned Businesses',
            'title': 'Women-Owned Businesses',
            'description': 'WBC network support and WOSB federal contracting opportunities.',
            'icon': '👩‍💼',
            'url': f'{site}/business-guide/grow-your-business/women-owned-businesses',
            'group': 'Community',
        },
        {
            'id': 'lenders',
            'name': 'Lender Match',
            'title': 'Lender Match',
            'description': 'Connect with SBA lenders interested in your financing needs.',
            'icon': '🏦',
            'url': f'{site}/funding-programs/loans/lender-match',
            'path': '/api/sba/content/lenders',
            'group': 'Funding',
        },
    ]


def _sba_lifecycle_cards():
    """Cards for Business Lifecycle tab."""
    site = 'https://www.sba.gov'
    return [
        {
            'id': 'plan',
            'name': 'Plan Your Business',
            'title': 'Plan Your Business',
            'description': 'Market research, business plans, and startup cost calculators.',
            'icon': '📋',
            'phase': 'Plan',
            'url': f'{site}/business-guide/plan-your-business',
            'path': '/api/sba/content/articles',
            'resources': [
                {'name': 'Write a business plan', 'url': f'{site}/business-guide/plan-your-business/write-your-business-plan'},
                {'name': 'Market research', 'url': f'{site}/business-guide/plan-your-business/market-research-competitive-analysis'},
                {'name': 'Startup costs', 'url': f'{site}/business-guide/plan-your-business/calculate-your-startup-costs'},
            ],
        },
        {
            'id': 'launch',
            'name': 'Launch Your Business',
            'title': 'Launch Your Business',
            'description': 'Structure, registration, licenses, and tax IDs to open legally.',
            'icon': '🚀',
            'phase': 'Launch',
            'url': f'{site}/business-guide/launch-your-business',
            'path': '/api/sba/content/articles',
            'resources': [
                {'name': 'Choose a structure', 'url': f'{site}/business-guide/launch-your-business/choose-business-structure'},
                {'name': 'Register your business', 'url': f'{site}/business-guide/launch-your-business/register-your-business'},
                {'name': 'Get tax IDs', 'url': f'{site}/business-guide/launch-your-business/get-federal-state-tax-id-numbers'},
            ],
        },
        {
            'id': 'manage',
            'name': 'Manage Your Business',
            'title': 'Manage Your Business',
            'description': 'Finances, employees, insurance, and day-to-day operations.',
            'icon': '⚙️',
            'phase': 'Manage',
            'url': f'{site}/business-guide/manage-your-business',
            'path': '/api/sba/content/articles',
            'resources': [
                {'name': 'Manage finances', 'url': f'{site}/business-guide/manage-your-business/manage-your-finances'},
                {'name': 'Hire employees', 'url': f'{site}/business-guide/manage-your-business/hire-manage-employees'},
                {'name': 'Business insurance', 'url': f'{site}/business-guide/manage-your-business/get-business-insurance'},
            ],
        },
        {
            'id': 'grow',
            'name': 'Grow Your Business',
            'title': 'Grow Your Business',
            'description': 'Funding, marketing, new locations, and expansion strategies.',
            'icon': '📈',
            'phase': 'Grow',
            'url': f'{site}/business-guide/grow-your-business',
            'path': '/api/sba/content/loans',
            'resources': [
                {'name': 'Get more funding', 'url': f'{site}/business-guide/grow-your-business/get-more-funding'},
                {'name': 'Marketing & sales', 'url': f'{site}/business-guide/manage-your-business/marketing-sales'},
                {'name': 'Open a new location', 'url': f'{site}/business-guide/grow-your-business/open-new-location'},
            ],
        },
        {
            'id': 'fund',
            'name': 'Fund Your Business',
            'title': 'Fund Your Business',
            'description': 'SBA loan programs and Lender Match for capital needs.',
            'icon': '💰',
            'phase': 'Fund',
            'url': f'{site}/funding-programs/loans',
            'path': '/api/sba/content/loans',
            'resources': [
                {'name': '7(a) loans', 'url': f'{site}/funding-programs/loans/7a-loans'},
                {'name': '504 loans', 'url': f'{site}/funding-programs/loans/504-loans'},
                {'name': 'Lender Match', 'url': f'{site}/funding-programs/loans/lender-match'},
            ],
        },
        {
            'id': 'exit',
            'name': 'Exit / Transition',
            'title': 'Exit / Transition',
            'description': 'Selling, succession, or closing a small business thoughtfully.',
            'icon': '🏁',
            'phase': 'Exit',
            'url': f'{site}/business-guide',
            'resources': [
                {'name': 'Business guide hub', 'url': f'{site}/business-guide'},
                {'name': 'Local counseling', 'url': f'{site}/local-assistance/find'},
            ],
        },
    ]


def _sba_local_resource_cards():
    """Cards for Local Resources tab."""
    site = 'https://www.sba.gov'
    find = f'{site}/local-assistance/find'
    return [
        {
            'id': 'sbdc',
            'name': 'Small Business Development Centers',
            'title': 'Small Business Development Centers',
            'description': 'Local centers providing free counseling and training to small business owners.',
            'icon': '🏢',
            'url': f'{find}/?type=Small%20Business%20Development%20Center&pageNumber=1',
            'path': '/api/sba/content/offices',
        },
        {
            'id': 'score',
            'name': 'SCORE Business Mentors',
            'title': 'SCORE Business Mentors',
            'description': 'Volunteer mentors offering free, confidential business advice.',
            'icon': '🤝',
            'url': 'https://www.score.org/find-mentor',
            'path': '/api/sba/content/offices',
        },
        {
            'id': 'wbc',
            'name': "Women's Business Centers",
            'title': "Women's Business Centers",
            'description': 'Training and counseling tailored for women entrepreneurs.',
            'icon': '👩‍💼',
            'url': f"{find}/?type=Women%27s%20Business%20Center&pageNumber=1",
            'path': '/api/sba/content/offices',
        },
        {
            'id': 'vboc',
            'name': 'Veterans Business Outreach Centers',
            'title': 'Veterans Business Outreach Centers',
            'description': 'Business training and counseling for veteran entrepreneurs.',
            'icon': '🎖️',
            'url': f'{find}/?type=Veterans%20Business%20Outreach%20Center&pageNumber=1',
            'path': '/api/sba/content/offices',
        },
        {
            'id': 'district',
            'name': 'SBA District Offices',
            'title': 'SBA District Offices',
            'description': 'Local SBA offices that connect owners to programs and partners.',
            'icon': '📍',
            'url': f'{find}/?type=SBA%20District%20Office&pageNumber=1',
            'path': '/api/sba/content/offices',
        },
        {
            'id': 'lender-match',
            'name': 'Lender Match',
            'title': 'Lender Match',
            'description': 'Get matched with SBA lenders in your market.',
            'icon': '🏦',
            'url': f'{site}/funding-programs/loans/lender-match',
            'path': '/api/sba/content/lenders',
        },
        {
            'id': 'events-local',
            'name': 'Local Events & Training',
            'title': 'Local Events & Training',
            'description': 'Webinars and workshops from SBA and resource partners near you.',
            'icon': '📅',
            'url': f'{site}/events',
            'path': '/api/sba/content/events',
        },
        {
            'id': 'locations',
            'name': 'SBA Locations Directory',
            'title': 'SBA Locations Directory',
            'description': 'Find headquarters, district offices, and disaster centers.',
            'icon': '🗺️',
            'url': f'{site}/about-sba/sba-locations',
            'path': '/api/sba/content/offices',
        },
    ]


@sba_bp.route('/resources', methods=['GET'])
def list_resources():
    """
    Multi-consumer SBA catalog.

    1) Browse UI: `resources[]` nav items with `path` for click-to-load content.
    2) Prebuilt SPA SBA Programs panel expects:
         sbaPrograms, businessLifecycleStages, localResourceTypes
       (fetched via GET /api/sba/resources — without these keys the cards render blank).
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

    sba_programs = _sba_program_cards()
    lifecycle = _sba_lifecycle_cards()
    local = _sba_local_resource_cards()

    # Optionally enrich program cards with live loan items when available (soft)
    try:
        loans = sba_api.search_loans(query='', page=1)
        live_items = (loans or {}).get('items') or []
        if live_items:
            # Keep catalog programs, append a few live loan cards for richness
            for item in live_items[:6]:
                if not isinstance(item, dict):
                    continue
                title = item.get('title') or item.get('name')
                if not title:
                    continue
                sba_programs.append({
                    'id': str(item.get('id') or title),
                    'name': title,
                    'title': title,
                    'description': item.get('description') or item.get('summary') or title,
                    'icon': '💵',
                    'url': item.get('url') or item.get('link') or '',
                    'path': '/api/sba/content/loans',
                    'group': 'Live loans',
                    'is_current': item.get('is_current'),
                    'source': item.get('source') or loans.get('source'),
                })
    except Exception as e:
        logger.warning('Live loan enrichment skipped: %s', e)

    return jsonify({
        # Browse / resources.html navigation
        'resources': resources,
        'count': len(resources),
        'status': 'ok',
        'navigation': {
            'source': '/api/sba/resources',
            'behavior': 'click_to_query',
            'item_open': 'detail_card',
        },
        # Prebuilt SPA + SBAContent Programs panel (CRITICAL — empty arrays = blank cards)
        'sbaPrograms': sba_programs,
        'businessLifecycleStages': lifecycle,
        'localResourceTypes': local,
        # Aliases for newer clients
        'programs': sba_programs,
        'lifecycle': lifecycle,
        'local': local,
    }), 200


@sba_bp.route('/programs', methods=['GET'])
def list_sba_program_cards():
    """Dedicated programs cards endpoint."""
    cards = _sba_program_cards()
    return jsonify({'items': cards, 'count': len(cards), 'status': 'ok'}), 200


@sba_bp.route('/lifecycle', methods=['GET'])
def list_sba_lifecycle_cards():
    """Business lifecycle cards endpoint."""
    cards = _sba_lifecycle_cards()
    return jsonify({'items': cards, 'count': len(cards), 'status': 'ok'}), 200


@sba_bp.route('/local-resources', methods=['GET'])
def list_sba_local_cards():
    """Local resource partner cards endpoint."""
    cards = _sba_local_resource_cards()
    return jsonify({'items': cards, 'count': len(cards), 'status': 'ok'}), 200


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
            # Soft-fallback card so detail pane still populates
            detail = sba_api.get_content_detail('articles', node_id)
            if detail and not detail.get('error'):
                return jsonify(detail), 200
            return jsonify({'error': result['error']}), 404
        return jsonify(result)
    except Exception as e:
        logger.error("Error getting node details: %s", e)
        return jsonify({'error': 'Failed to get node details'}), 500


@sba_bp.route('/content/<content_type>/<path:item_id>', methods=['GET'])
def get_content_item_detail(content_type, item_id):
    """
    Detail card for prebuilt SPA:
      GET /api/sba-content/{type}/{id}  (rewritten to /api/sba/content/{type}/{id})
    Always returns a populated card object when possible (200).
    """
    allowed = {
        'articles', 'blogs', 'courses', 'documents', 'events',
        'offices', 'loans', 'lenders', 'sbir', 'node',
    }
    content_type = (content_type or '').lower()
    if content_type not in allowed:
        return jsonify({'error': f'Unknown content type: {content_type}'}), 404
    try:
        detail = sba_api.get_content_detail(content_type, item_id)
        if not detail:
            return jsonify({'error': 'Not found'}), 404
        # Never 404 a resolvable soft card — UI must show content
        if detail.get('error') and not detail.get('title'):
            return jsonify(detail), 404
        return jsonify(detail), 200
    except Exception as e:
        logger.error("Error getting %s/%s: %s", content_type, item_id, e)
        return jsonify({
            'id': item_id,
            'title': f'SBA {content_type}',
            'summary': f'Unable to load detail ({e}). Visit sba.gov for official information.',
            'description': f'Unable to load detail ({e}). Visit sba.gov for official information.',
            'body': f'<p>Unable to load detail. Visit <a href="https://www.sba.gov">sba.gov</a>.</p>',
            'url': 'https://www.sba.gov',
            'success': True,
        }), 200
