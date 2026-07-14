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


def _digest_payload(normalized_items, *, route='', title='', description='', source='', degraded=False,
                    is_current=False, message='', page=1, total_pages=1, extra=None):
    """
    World-class API digestion layer.
    Turns a raw item list into a topic page model: narrative, facets, groups, next actions.
    Additive — never removes items/results contract fields.
    """
    items = list(normalized_items or [])
    type_counts = {}
    with_url = 0
    with_path = 0
    with_resources = 0
    for it in items:
        t = str((it or {}).get('type') or 'content').strip() or 'content'
        type_counts[t] = type_counts.get(t, 0) + 1
        if (it or {}).get('url') or (it or {}).get('link'):
            with_url += 1
        if str((it or {}).get('path') or '').startswith('/api/'):
            with_path += 1
        if (it or {}).get('resources'):
            with_resources += 1

    facets = [
        {'id': 'all', 'label': 'All', 'count': len(items)},
    ]
    for t, c in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        facets.append({
            'id': t,
            'label': t.replace('_', ' ').title(),
            'count': c,
        })

    # Group items by type for sectioned topic pages
    groups = []
    for t, c in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        group_items = [it for it in items if str(it.get('type') or 'content') == t]
        groups.append({
            'id': t,
            'title': t.replace('_', ' ').title(),
            'count': c,
            'item_ids': [it.get('id') for it in group_items[:50]],
            'preview': [
                {
                    'id': it.get('id'),
                    'title': it.get('title') or it.get('name'),
                    'path': it.get('path') or '',
                    'url': it.get('url') or it.get('link') or '',
                }
                for it in group_items[:5]
            ],
        })

    # Topic narrative (fully develop the subject of this route)
    top_titles = [str(it.get('title') or it.get('name') or '').strip() for it in items[:6]]
    top_titles = [t for t in top_titles if t]
    brief_bits = []
    if description:
        brief_bits.append(str(description).strip())
    elif message:
        brief_bits.append(str(message).strip())
    if items:
        brief_bits.append(
            f'This topic currently surfaces {len(items)} resource'
            f'{"s" if len(items) != 1 else ""}'
            + (f' across {len(type_counts)} types' if len(type_counts) > 1 else '')
            + '.'
        )
        if top_titles:
            brief_bits.append('Highlights include: ' + '; '.join(top_titles[:4]) + '.')
    else:
        brief_bits.append('No resources were returned for this route yet. Try refresh or another endpoint.')

    topic_title = title or (route.rsplit('/', 1)[-1].replace('-', ' ').replace('_', ' ').title() if route else 'SBA Topic')
    related_routes = []
    # Suggest natural next digests from item paths
    seen_routes = set()
    for it in items:
        p = str(it.get('path') or '').strip()
        if p.startswith('/api/') and p not in seen_routes and p != route:
            seen_routes.add(p)
            related_routes.append({
                'path': p,
                'title': it.get('title') or it.get('name') or p,
                'type': it.get('type') or 'route',
            })
        if len(related_routes) >= 8:
            break

    steps = [
        {'id': 'resolve', 'label': 'Resolve route', 'status': 'done', 'detail': route or 'catalog'},
        {'id': 'fetch', 'label': 'Fetch API', 'status': 'done' if not degraded or items else 'warn',
         'detail': source or 'multi-source'},
        {'id': 'normalize', 'label': 'Normalize cards', 'status': 'done',
         'detail': f'{len(items)} items'},
        {'id': 'facet', 'label': 'Facet & group', 'status': 'done',
         'detail': f'{len(type_counts)} types'},
        {'id': 'ready', 'label': 'Topic ready', 'status': 'done' if items else 'empty',
         'detail': 'render page'},
    ]

    digestion = {
        'version': 1,
        'pipeline': steps,
        'stats': {
            'items': len(items),
            'types': len(type_counts),
            'with_url': with_url,
            'with_path': with_path,
            'with_resources': with_resources,
            'page': page,
            'total_pages': total_pages,
        },
        'facets': facets,
        'groups': groups,
        'related_routes': related_routes,
        'quality': {
            'degraded': bool(degraded),
            'is_current': bool(is_current),
            'coverage': round((with_url / len(items)) * 100, 1) if items else 0,
            'drillable': with_path,
        },
    }
    topic = {
        'title': topic_title,
        'description': ' '.join(brief_bits),
        'summary': brief_bits[0] if brief_bits else topic_title,
        'route': route,
        'source': source,
        'sections': [
            {
                'id': 'overview',
                'title': 'Overview',
                'body': ' '.join(brief_bits),
            },
            {
                'id': 'resources',
                'title': 'Resources',
                'body': f'{len(items)} curated / live resources for this topic.',
                'count': len(items),
            },
            {
                'id': 'how_to_use',
                'title': 'How to use this page',
                'body': (
                    'Click any card with an API badge to open that route’s results. '
                    'Use type filters to focus. Open official links for full SBA.gov detail. '
                    'Use Back to return to the previous topic.'
                ),
            },
        ],
        'actions': [
            {'id': 'refresh', 'label': 'Refresh from API', 'kind': 'refresh'},
            {'id': 'browse', 'label': 'Open in Resources browser', 'kind': 'link', 'href': '/browse'},
            {'id': 'programs', 'label': 'Programs & lifecycle', 'kind': 'link', 'href': '/sba'},
        ],
    }
    if extra and isinstance(extra, dict):
        if extra.get('url'):
            topic['official_url'] = extra['url']
            topic['actions'].insert(0, {
                'id': 'official', 'label': 'Official SBA page', 'kind': 'external', 'href': extra['url'],
            })
        if extra.get('phase'):
            topic['phase'] = extra['phase']
        if extra.get('icon'):
            topic['icon'] = extra['icon']

    return topic, digestion


def _envelope(result, page=1, *, route='', title=''):
    """Normalize multi-source client payloads into the frontend card + topic contract."""
    if not route:
        try:
            route = request.path or ''
        except Exception:
            route = ''
    if not title and route:
        title = route.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').replace('_', ' ').title()
    if not isinstance(result, dict):
        topic, digestion = _digest_payload(
            [], route=route, title=title or 'SBA Topic', degraded=True,
            message='Unexpected SBA client response', page=page, total_pages=0,
        )
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
            'topic': topic,
            'digestion': digestion,
        }

    # Hard error with no items → still try to surface message; callers may attach fallbacks
    if result.get('error') and not result.get('items') and not result.get('results'):
        logger.warning("SBA source error: %s", result.get('error'))
        topic, digestion = _digest_payload(
            [], route=route, title=title, degraded=True,
            message=result.get('message') or result.get('error'),
            source=result.get('source', 'unknown'), page=page, total_pages=0,
        )
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
            'topic': topic,
            'digestion': digestion,
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
        # Digestion helpers for UI — every child that can load more content is a clickable resource
        parent_route = str(route or result.get('path') or result.get('parent_path') or '').rstrip('/')
        cid = str(item.get('id') or item.get('nid') or '').strip()
        path = str(item.get('path') or '').strip()
        itype = str(item.get('type') or '').lower()
        leaf_types = {
            'overview', 'link', 'notice', 'source_status', 'loan_section',
        }
        leaf_suffixes = ('-overview', '-official', '-about', '-how', '-sec-')
        # Stamp path under parent when missing so UI can drill parent→child→child
        if (
            not path.startswith('/api/')
            and parent_route.startswith('/api/sba/')
            and cid
            and not cid.startswith('item-')
            and itype not in leaf_types
            and not any(s in cid for s in leaf_suffixes)
        ):
            candidate = f'{parent_route}/{cid}'
            if candidate.rstrip('/') != parent_route:
                item['path'] = candidate
                path = candidate
        item['drillable'] = bool(str(item.get('path') or '').startswith('/api/'))
        # Path-backed items are parents of further API results; resources[] are local children
        item['has_children'] = bool(
            item.get('drillable')
            or (isinstance(item.get('resources'), list) and item.get('resources'))
        )
        if not item.get('parent_path') and parent_route.startswith('/api/'):
            item['parent_path'] = parent_route
        item['actions'] = []
        if item.get('drillable'):
            item['actions'].append({'id': 'open_route', 'label': 'Explore children', 'path': item.get('path')})
        # Usable content actions: forms, downloads, registration, official pages
        file_url = item.get('fileUrl') or item.get('file_url')
        if file_url:
            is_form = str(item.get('type') or '').lower() in ('form', 'document') or 'form' in str(
                item.get('title') or ''
            ).lower()
            item['actions'].append({
                'id': 'download' if not is_form else 'form',
                'label': 'Open form / document' if is_form else 'Open document',
                'href': file_url,
            })
        reg = item.get('registrationLink') or item.get('registration_link')
        if reg:
            item['actions'].append({'id': 'register', 'label': 'Register / RSVP', 'href': reg})
        if item.get('url') or item.get('link'):
            item['actions'].append({
                'id': 'official', 'label': 'Official source',
                'href': item.get('url') or item.get('link'),
            })
        if item.get('has_children') and not item.get('drillable'):
            item['actions'].append({'id': 'expand', 'label': 'Expand options'})
        normalized.append(item)

    total_pages = result.get('totalPages', result.get('total_pages', 1 if normalized else 0))
    is_current = result.get('is_current')
    if is_current is None:
        is_current = result.get('source', '').startswith('sba_html') or result.get('source') in (
            'legacy_json', 'sbir',
        )
    resolved_route = route or result.get('path') or ''
    resolved_title = title or result.get('title') or result.get('name') or ''
    topic, digestion = _digest_payload(
        normalized,
        route=resolved_route,
        title=resolved_title,
        description=result.get('description') or result.get('summary') or '',
        source=result.get('source') or '',
        degraded=bool(result.get('degraded')),
        is_current=bool(is_current),
        message=result.get('message') or '',
        page=result.get('currentPage', page) or page,
        total_pages=total_pages or 1,
        extra={
            'url': result.get('url') or result.get('official_url'),
            'phase': result.get('phase'),
            'icon': result.get('icon'),
        },
    )
    env = {
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
        # Topic page model (additive)
        'topic': topic,
        'digestion': digestion,
        'path': resolved_route,
    }
    # When parent/child API results are pulled, feed the response into RAG (soft).
    # Children explores (loans/7a, contracting/8a, …) become searchable for chat/RAG.
    try:
        from backend.services.sba_rag_ingest import schedule_sba_rag_ingest

        if normalized or (topic and (topic.get('description') or topic.get('sections'))):
            schedule_sba_rag_ingest(env, route=resolved_route, title=resolved_title)
            env['rag_ingest'] = {
                'scheduled': True,
                'route': resolved_route,
                'items': len(normalized),
                'note': 'API response queued for RAG (local KB + Chroma when available). Child digests become searchable in /api/rag and chat.',
            }
    except Exception as rag_err:
        logger.debug('SBA RAG ingest schedule soft-fail: %s', rag_err)
        env['rag_ingest'] = {'scheduled': False, 'error': str(rag_err)}
    return env


def _sba_program_cards():
    """Cards for SBA Programs tab (prebuilt SPA + SBAContent)."""
    site = 'https://www.sba.gov'
    return [
        {
            'id': 'loans',
            'name': 'SBA Loans',
            'title': 'SBA Loans',
            'description': '7(a), 504, Microloan, and Express financing options for small businesses. Click to open all loan children.',
            'icon': '💰',
            'url': f'{site}/funding-programs/loans',
            'path': '/api/sba/content/loans',
            'group': 'Funding',
            'type': 'program',
            'resources': [
                {'id': '7a', 'name': 'SBA 7(a) loans', 'title': 'SBA 7(a) loans', 'path': '/api/sba/content/loans/7a', 'url': f'{site}/funding-programs/loans/7a-loans', 'type': 'loan_program'},
                {'id': '504', 'name': 'SBA 504 loans', 'title': 'SBA 504 loans', 'path': '/api/sba/content/loans/504', 'url': f'{site}/funding-programs/loans/504-loans', 'type': 'loan_program'},
                {'id': 'microloans', 'name': 'SBA Microloans', 'title': 'SBA Microloans', 'path': '/api/sba/content/loans/microloans', 'url': f'{site}/funding-programs/loans/microloans', 'type': 'loan_program'},
                {'id': 'lender-match', 'name': 'Lender Match', 'title': 'Lender Match', 'path': '/api/sba/content/loans/lender-match', 'url': f'{site}/funding-programs/loans/lender-match', 'type': 'tool'},
            ],
        },
        {
            'id': 'contracting',
            'name': 'Government Contracting',
            'title': 'Government Contracting',
            'description': 'Certifications and support to win federal contracts (8(a), HUBZone, WOSB, SDVOSB).',
            'icon': '📝',
            'url': f'{site}/federal-contracting',
            'path': '/api/sba/content/contracting',
            'group': 'Growth',
            'type': 'program',
        },
        {
            'id': 'disaster',
            'name': 'Disaster Assistance',
            'title': 'Disaster Assistance',
            'description': 'Low-interest disaster loans for businesses, nonprofits, homeowners, and renters.',
            'icon': '🚨',
            'url': f'{site}/funding-programs/disaster-assistance',
            'path': '/api/sba/content/disaster',
            'group': 'Funding',
            'type': 'program',
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
            'path': '/api/sba/content/articles',
            'group': 'Growth',
            'type': 'program',
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
            'type': 'program',
        },
        {
            'id': 'opportunities',
            'name': 'Opportunities for Veterans',
            'title': 'Opportunities for Veterans',
            'description': 'Training, counseling, capital access, and contracting for veteran entrepreneurs.',
            'icon': '🎖️',
            'url': f'{site}/business-guide/grow-your-business/veteran-owned-businesses',
            'path': '/api/sba/content/articles',
            'group': 'Community',
            'type': 'program',
        },
        {
            'id': 'women',
            'name': 'Women-Owned Businesses',
            'title': 'Women-Owned Businesses',
            'description': 'WBC network support and WOSB federal contracting opportunities.',
            'icon': '👩‍💼',
            'url': f'{site}/business-guide/grow-your-business/women-owned-businesses',
            'path': '/api/sba/content/offices',
            'group': 'Community',
            'type': 'program',
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
            'type': 'program',
        },
    ]


def _lifecycle_option(name, description, url, opt_type='guide', path=''):
    """One assigned resource option under a lifecycle / program category."""
    return {
        'id': name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')[:64],
        'name': name,
        'title': name,
        'description': description,
        'url': url,
        'type': opt_type,
        'path': path or '',
    }


def _sba_lifecycle_cards():
    """Cards for Business Lifecycle tab. Each has assigned resources for drill-down."""
    site = 'https://www.sba.gov'
    return [
        {
            'id': 'start',
            'name': 'Start a Business',
            'title': 'Start a Business',
            'description': 'Plan and launch path: research, structure, registration, and first funding options.',
            'icon': '🏁',
            'phase': 'Start',
            'type': 'lifecycle',
            'url': f'{site}/business-guide',
            'path': '/api/sba/lifecycle/start',
            'content_path': '/api/sba/content/articles',
            'resources': [
                _lifecycle_option(
                    'Plan your business',
                    'Market research, business plans, and startup cost calculators.',
                    f'{site}/business-guide/plan-your-business',
                    'guide',
                    '/api/sba/lifecycle/plan',
                ),
                _lifecycle_option(
                    'Launch your business',
                    'Structure, registration, licenses, and tax IDs to open legally.',
                    f'{site}/business-guide/launch-your-business',
                    'guide',
                    '/api/sba/lifecycle/launch',
                ),
                _lifecycle_option(
                    'Write a business plan',
                    'Step-by-step guide to writing a plan lenders and partners understand.',
                    f'{site}/business-guide/plan-your-business/write-your-business-plan',
                ),
                _lifecycle_option(
                    'Choose a business structure',
                    'Sole prop, LLC, corporation, and other legal structures.',
                    f'{site}/business-guide/launch-your-business/choose-business-structure',
                ),
                _lifecycle_option(
                    'Register your business',
                    'State and local registration requirements to operate legally.',
                    f'{site}/business-guide/launch-your-business/register-your-business',
                ),
                _lifecycle_option(
                    'Get tax ID numbers',
                    'Federal EIN and state tax IDs for payroll and filings.',
                    f'{site}/business-guide/launch-your-business/get-federal-state-tax-id-numbers',
                ),
                _lifecycle_option(
                    'Calculate startup costs',
                    'Estimate one-time and monthly costs before you open.',
                    f'{site}/business-guide/plan-your-business/calculate-your-startup-costs',
                ),
                _lifecycle_option(
                    'Fund your startup',
                    'SBA-backed loans and Lender Match for capital.',
                    f'{site}/funding-programs/loans',
                    'funding',
                    '/api/sba/content/loans',
                ),
            ],
        },
        {
            'id': 'plan',
            'name': 'Plan Your Business',
            'title': 'Plan Your Business',
            'description': 'Market research, business plans, and startup cost calculators.',
            'icon': '📋',
            'phase': 'Plan',
            'type': 'lifecycle',
            'url': f'{site}/business-guide/plan-your-business',
            'path': '/api/sba/lifecycle/plan',
            'content_path': '/api/sba/content/articles',
            'resources': [
                _lifecycle_option('Write a business plan', 'Build a plan that covers market, operations, and finances.', f'{site}/business-guide/plan-your-business/write-your-business-plan'),
                _lifecycle_option('Market research & competitive analysis', 'Validate demand and competitors before you invest.', f'{site}/business-guide/plan-your-business/market-research-competitive-analysis'),
                _lifecycle_option('Calculate your startup costs', 'Estimate startup and operating costs.', f'{site}/business-guide/plan-your-business/calculate-your-startup-costs'),
                _lifecycle_option('Pick your business location', 'Choose a location that fits customers, zoning, and costs.', f'{site}/business-guide/launch-your-business/pick-your-business-location'),
                _lifecycle_option('Buy an existing business or franchise', 'Evaluate buying vs starting from scratch.', f'{site}/business-guide/launch-your-business/buy-existing-business'),
            ],
        },
        {
            'id': 'launch',
            'name': 'Launch Your Business',
            'title': 'Launch Your Business',
            'description': 'Structure, registration, licenses, and tax IDs to open legally.',
            'icon': '🚀',
            'phase': 'Launch',
            'type': 'lifecycle',
            'url': f'{site}/business-guide/launch-your-business',
            'path': '/api/sba/lifecycle/launch',
            'content_path': '/api/sba/content/articles',
            'resources': [
                _lifecycle_option('Choose a business structure', 'Pick the legal structure that fits liability and taxes.', f'{site}/business-guide/launch-your-business/choose-business-structure'),
                _lifecycle_option('Register your business', 'Complete state and local registration steps.', f'{site}/business-guide/launch-your-business/register-your-business'),
                _lifecycle_option('Get federal & state tax IDs', 'Apply for EIN and state tax accounts.', f'{site}/business-guide/launch-your-business/get-federal-state-tax-id-numbers'),
                _lifecycle_option('Apply for licenses and permits', 'Find required licenses for your industry and location.', f'{site}/business-guide/launch-your-business/apply-licenses-permits-regulations'),
                _lifecycle_option('Open a business bank account', 'Separate personal and business finances.', f'{site}/business-guide/launch-your-business/open-business-bank-account'),
            ],
        },
        {
            'id': 'manage',
            'name': 'Manage Your Business',
            'title': 'Manage Your Business',
            'description': 'Finances, employees, insurance, and day-to-day operations.',
            'icon': '⚙️',
            'phase': 'Manage',
            'type': 'lifecycle',
            'url': f'{site}/business-guide/manage-your-business',
            'path': '/api/sba/lifecycle/manage',
            'content_path': '/api/sba/content/articles',
            'resources': [
                _lifecycle_option('Manage your finances', 'Bookkeeping, cash flow, and financial statements.', f'{site}/business-guide/manage-your-business/manage-your-finances'),
                _lifecycle_option('Hire and manage employees', 'Hiring, payroll, and workplace basics.', f'{site}/business-guide/manage-your-business/hire-manage-employees'),
                _lifecycle_option('Get business insurance', 'Protect operations with the right coverage.', f'{site}/business-guide/manage-your-business/get-business-insurance'),
                _lifecycle_option('Pay taxes', 'Federal, state, and local tax obligations.', f'{site}/business-guide/manage-your-business/pay-taxes'),
                _lifecycle_option('Marketing & sales', 'Attract and retain customers.', f'{site}/business-guide/manage-your-business/marketing-sales'),
            ],
        },
        {
            'id': 'grow',
            'name': 'Grow Your Business',
            'title': 'Grow Your Business',
            'description': 'Funding, marketing, new locations, and expansion strategies.',
            'icon': '📈',
            'phase': 'Grow',
            'type': 'lifecycle',
            'url': f'{site}/business-guide/grow-your-business',
            'path': '/api/sba/lifecycle/grow',
            'content_path': '/api/sba/content/loans',
            'resources': [
                _lifecycle_option('Get more funding', 'Growth capital options including SBA loans.', f'{site}/business-guide/grow-your-business/get-more-funding', 'funding', '/api/sba/content/loans'),
                _lifecycle_option('Expand to a new location', 'Open additional sites or enter new markets.', f'{site}/business-guide/grow-your-business/open-new-location'),
                _lifecycle_option('Merge and acquire businesses', 'Growth through M&A.', f'{site}/business-guide/grow-your-business/merge-acquire-businesses'),
                _lifecycle_option('Become a federal contractor', 'Sell to the government.', f'{site}/federal-contracting', 'guide', '/api/sba/content/articles'),
            ],
        },
        {
            'id': 'fund',
            'name': 'Fund Your Business',
            'title': 'Fund Your Business',
            'description': 'SBA loan programs and Lender Match for capital needs.',
            'icon': '💰',
            'phase': 'Fund',
            'type': 'lifecycle',
            'url': f'{site}/funding-programs/loans',
            'path': '/api/sba/lifecycle/fund',
            'content_path': '/api/sba/content/loans',
            'resources': [
                _lifecycle_option('SBA 7(a) loans', 'Flexible financing for working capital and growth.', f'{site}/funding-programs/loans/7a-loans', 'loan_program', '/api/sba/content/loans/7a'),
                _lifecycle_option('SBA 504 loans', 'Fixed-asset financing for real estate and equipment.', f'{site}/funding-programs/loans/504-loans', 'loan_program', '/api/sba/content/loans/504'),
                _lifecycle_option('SBA Microloans', 'Smaller loans often with counseling support.', f'{site}/funding-programs/loans/microloans', 'loan_program', '/api/sba/content/loans/microloans'),
                _lifecycle_option('Lender Match', 'Connect with lenders interested in your financing needs.', f'{site}/funding-programs/loans/lender-match', 'tool', '/api/sba/content/loans/lender-match'),
                _lifecycle_option('Disaster loans', 'Recovery financing after declared disasters.', f'{site}/funding-programs/disaster-assistance', 'loan_program'),
            ],
        },
        {
            'id': 'exit',
            'name': 'Exit / Transition',
            'title': 'Exit / Transition',
            'description': 'Selling, succession, or closing a small business thoughtfully.',
            'icon': '🚪',
            'phase': 'Exit',
            'type': 'lifecycle',
            'url': f'{site}/business-guide',
            'path': '/api/sba/lifecycle/exit',
            'content_path': '/api/sba/content/articles',
            'resources': [
                _lifecycle_option('Business guide hub', 'Browse the full SBA business guide.', f'{site}/business-guide'),
                _lifecycle_option('Local counseling', 'Free local mentors and advisors for transition planning.', f'{site}/local-assistance/find', 'local', '/api/sba/content/offices'),
                _lifecycle_option('Sell your business', 'Prepare and market a business for sale.', f'{site}/business-guide/manage-your-business'),
            ],
        },
    ]


def _lifecycle_stage_by_id(stage_id):
    sid = str(stage_id or '').strip().lower()
    for card in _sba_lifecycle_cards():
        if str(card.get('id', '')).lower() == sid:
            return card
    # fuzzy: match phase or name tokens
    for card in _sba_lifecycle_cards():
        name = str(card.get('name') or '').lower()
        if sid and sid in name.replace(' ', '-'):
            return card
    return None


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


@sba_bp.route('/standard', methods=['GET'])
def sba_app_standard():
    """Return the locked app standard template (CURRENT functionality)."""
    try:
        from backend.services.app_standard import describe_standard

        return jsonify({'status': 'ok', **describe_standard()}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 200


@sba_bp.route('/rag-ingest', methods=['GET', 'POST', 'OPTIONS'])
def sba_rag_ingest():
    """
    GET  — status of SBA API → RAG ingest (live KB files + optional Chroma).
    POST — pull a parent/child API path and force-ingest the response into RAG.
           Body/query: { "path": "/api/sba/content/loans/7a" }
           Or pass { "envelope": { ... } } to ingest an already-fetched payload.
    """
    if request.method == 'OPTIONS':
        return '', 204
    if request.method == 'GET':
        try:
            from backend.services.sba_rag_ingest import ingest_status

            st = ingest_status()
            return jsonify({'status': 'ok', **st}), 200
        except Exception as e:
            logger.warning('rag-ingest status soft-fail: %s', e)
            return jsonify({'status': 'degraded', 'error': str(e)}), 200

    data = request.get_json(silent=True) or {}
    path = (data.get('path') or data.get('route') or request.args.get('path') or '').strip()
    if path and not path.startswith('/api/sba/'):
        return jsonify({'error': 'path must start with /api/sba/', 'ok': False}), 400
    try:
        from backend.services.sba_rag_ingest import ingest_sba_envelope

        envelope = data.get('envelope')
        if not isinstance(envelope, dict):
            if not path:
                return jsonify({'error': 'path or envelope required', 'ok': False}), 400
            import json as _json
            import urllib.request

            url = request.host_url.rstrip('/') + path
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=45) as resp:
                envelope = _json.loads(resp.read().decode('utf-8', errors='replace'))
        route = path or str((envelope or {}).get('path') or '')
        title = ''
        if isinstance(envelope, dict) and isinstance(envelope.get('topic'), dict):
            title = envelope['topic'].get('title') or ''
        result = ingest_sba_envelope(envelope, route=route, title=title, force=True)
        return jsonify({'ok': True, 'path': route, 'ingest': result, 'rag_ingest': result}), 200
    except Exception as e:
        logger.warning('manual SBA RAG ingest soft-fail: %s', e)
        return jsonify({'ok': False, 'error': str(e), 'path': path}), 200


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
            'name': 'SBA Loans',
            'description': 'Loan types SBA offers: 7(a), 504, Microloans, Lender Match',
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
            'id': 'contracting',
            'name': 'Government Contracting',
            'description': 'Federal contract programs and certifications',
            'path': '/api/sba/content/contracting',
            'icon': 'articles',
            'group': 'Growth',
            'queryable': True,
        },
        {
            'id': 'disaster',
            'name': 'Disaster Assistance',
            'description': 'Disaster loans and recovery resources',
            'path': '/api/sba/content/disaster',
            'icon': 'loans',
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

    # Do NOT flatten loan children into the programs catalog — parent SBA Loans
    # owns children via path=/api/sba/content/loans (parent → children navigation).

    return jsonify({
        # Browse / resources.html navigation
        'resources': resources,
        'count': len(resources),
        'status': 'ok',
        'navigation': {
            'source': '/api/sba/resources',
            'behavior': 'click_badge_opens_route_results',
            'item_open': 'route_results_page',
            'rule': 'Each badge/card with path loads GET path and renders items as the page.',
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
    """Dedicated programs cards endpoint — fully digested topic list."""
    cards = _sba_program_cards()
    raw = {
        'items': cards,
        'count': len(cards),
        'status': 'ok',
        'source': 'catalog',
        'is_current': True,
        'description': 'Official SBA program categories. Click a card to open its API route results.',
        'title': 'SBA Programs',
        'name': 'SBA Programs',
        'path': '/api/sba/programs',
    }
    env = _envelope(raw, 1, route='/api/sba/programs', title='SBA Programs')
    env['status'] = 'ok'
    return jsonify(env), 200


@sba_bp.route('/lifecycle', methods=['GET'])
def list_sba_lifecycle_cards():
    """Business lifecycle cards — digested for topic navigation."""
    cards = _sba_lifecycle_cards()
    raw = {
        'items': cards,
        'count': len(cards),
        'status': 'ok',
        'source': 'catalog',
        'is_current': True,
        'description': 'Business lifecycle stages from plan to exit. Each stage opens its assigned resource options.',
        'title': 'Business Lifecycle',
        'name': 'Business Lifecycle',
        'path': '/api/sba/lifecycle',
    }
    env = _envelope(raw, 1, route='/api/sba/lifecycle', title='Business Lifecycle')
    env['status'] = 'ok'
    return jsonify(env), 200


@sba_bp.route('/lifecycle/<stage_id>', methods=['GET'])
def get_sba_lifecycle_stage(stage_id):
    """
    Fully developed lifecycle topic page payload:
    assigned resources + related API content + topic/digestion model.
    """
    card = _lifecycle_stage_by_id(stage_id)
    route = f'/api/sba/lifecycle/{stage_id}'
    if not card:
        env = _envelope(
            {'error': f'Unknown lifecycle stage: {stage_id}', 'items': [], 'message': f'Unknown stage: {stage_id}'},
            1, route=route, title=str(stage_id),
        )
        env['status'] = 'not_found'
        env['available'] = [c['id'] for c in _sba_lifecycle_cards()]
        return jsonify(env), 404

    # Assigned resources are first-class option cards
    assigned = []
    for i, raw in enumerate(card.get('resources') or []):
        if isinstance(raw, dict):
            opt = dict(raw)
            opt.setdefault('id', f"{card['id']}-opt-{i}")
            opt.setdefault('title', opt.get('name') or f'Option {i + 1}')
            opt.setdefault('name', opt.get('title'))
            opt.setdefault('type', 'assigned_resource')
            opt['parent_id'] = card['id']
            opt['parent_name'] = card.get('name')
            assigned.append(opt)
        elif isinstance(raw, str) and raw.strip():
            assigned.append({
                'id': f"{card['id']}-opt-{i}",
                'name': raw.strip(),
                'title': raw.strip(),
                'description': raw.strip(),
                'type': 'assigned_resource',
                'parent_id': card['id'],
                'parent_name': card.get('name'),
            })

    # Optionally merge related content from content_path (or legacy path)
    related = []
    content_path = (card.get('content_path') or '').strip()
    if content_path.startswith('/api/sba/content/'):
        try:
            # Map path tail → client method when available
            tail = content_path.split('/api/sba/content/', 1)[-1].split('?')[0].strip('/')
            method_map = {
                'articles': 'search_articles',
                'loans': 'search_loans',
                'lenders': 'search_lenders',
                'courses': 'search_courses',
                'documents': 'search_documents',
                'events': 'search_events',
                'offices': 'search_offices',
                'blogs': 'search_blogs',
                'sbir': 'search_sbir',
            }
            meth_name = method_map.get(tail)
            if meth_name and hasattr(sba_api, meth_name):
                result = getattr(sba_api, meth_name)(query='', page=1, fresh=False)
                if isinstance(result, dict):
                    for j, row in enumerate((result.get('items') or result.get('results') or [])[:20]):
                        if not isinstance(row, dict):
                            continue
                        related.append({
                            'id': row.get('id') or f"{card['id']}-api-{j}",
                            'name': row.get('title') or row.get('name') or f'Item {j + 1}',
                            'title': row.get('title') or row.get('name') or f'Item {j + 1}',
                            'description': row.get('description') or row.get('summary') or '',
                            'url': row.get('url') or row.get('link') or '',
                            'type': row.get('type') or 'api_resource',
                            'source': 'content_api',
                            'parent_id': card['id'],
                            'parent_name': card.get('name'),
                            'path': row.get('path') or content_path,
                        })
        except Exception as e:
            logger.warning('lifecycle related content soft-fail for %s: %s', stage_id, e)

    # Prefer assigned options; append related that are not obvious duplicates
    assigned_titles = {str(a.get('title') or '').strip().lower() for a in assigned}
    for r in related:
        t = str(r.get('title') or '').strip().lower()
        if t and t not in assigned_titles:
            assigned.append(r)
            assigned_titles.add(t)

    raw = {
        'status': 'ok',
        'stage': card,
        'id': card.get('id'),
        'name': card.get('name'),
        'title': card.get('title') or card.get('name'),
        'description': card.get('description'),
        'phase': card.get('phase'),
        'url': card.get('url'),
        'path': route,
        'icon': card.get('icon'),
        'items': assigned,
        'results': assigned,
        'count': len(assigned),
        'assigned_count': len(card.get('resources') or []),
        'message': f'{len(assigned)} resource options for {card.get("name")}',
        'source': 'lifecycle_catalog+content',
        'is_current': True,
    }
    env = _envelope(raw, 1, route=route, title=card.get('name') or stage_id)
    env['status'] = 'ok'
    env['stage'] = card
    env['assigned_count'] = len(card.get('resources') or [])
    env['icon'] = card.get('icon')
    env['phase'] = card.get('phase')
    env['url'] = card.get('url')
    # Develop topic sections with stage-specific guidance
    if isinstance(env.get('topic'), dict):
        env['topic']['icon'] = card.get('icon')
        env['topic']['phase'] = card.get('phase')
        env['topic']['official_url'] = card.get('url')
        env['topic']['sections'] = [
            {
                'id': 'overview',
                'title': f'About {card.get("name")}',
                'body': card.get('description') or env['topic'].get('description'),
            },
            {
                'id': 'assigned',
                'title': 'Assigned resources',
                'body': f'{len(card.get("resources") or [])} curated SBA steps for this stage.',
                'count': len(card.get('resources') or []),
            },
            {
                'id': 'related',
                'title': 'Related API content',
                'body': f'Additional live content merged from {content_path or "linked content routes"}.',
                'count': max(0, len(assigned) - len(card.get('resources') or [])),
            },
            {
                'id': 'next',
                'title': 'What to do next',
                'body': (
                    'Open each assigned resource for official guidance. '
                    'Drill into API-badged cards to load that route’s results. '
                    'Use Lender Match or counseling partners when you are ready for capital or advice.'
                ),
            },
        ]
    return jsonify(env), 200


@sba_bp.route('/local-resources', methods=['GET'])
def list_sba_local_cards():
    """Local resource partner cards — digested topic list."""
    cards = _sba_local_resource_cards()
    raw = {
        'items': cards,
        'count': len(cards),
        'status': 'ok',
        'source': 'catalog',
        'is_current': True,
        'description': 'Local SBA partners and offices. Click a card to open its content route.',
        'title': 'Local Resources',
        'name': 'Local Resources',
        'path': '/api/sba/local-resources',
    }
    env = _envelope(raw, 1, route='/api/sba/local-resources', title='Local Resources')
    env['status'] = 'ok'
    return jsonify(env), 200


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


def _with_child_paths(parent_path, items):
    """Stamp recursive explore paths: parent/child_id for every child without a path."""
    parent_path = (parent_path or '').rstrip('/')
    out = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        it = dict(raw)
        cid = str(it.get('id') or '').strip()
        if not it.get('path') and cid and parent_path.startswith('/api/'):
            it['path'] = f'{parent_path}/{cid}'
        it['parent_path'] = parent_path or it.get('parent_path') or ''
        it['drillable'] = bool(str(it.get('path') or '').startswith('/api/'))
        it['has_children'] = True if it.get('drillable') else bool(it.get('resources'))
        out.append(it)
    return out


def _contracting_children():
    """Government Contracting parent → certification/program children."""
    site = 'https://www.sba.gov'
    parent = '/api/sba/content/contracting'
    items = [
        {
            'id': '8a',
            'title': '8(a) Business Development',
            'name': '8(a) Business Development',
            'description': 'Program helping small disadvantaged businesses compete for federal contracts.',
            'url': f'{site}/federal-contracting/contracting-assistance-programs/8a-business-development-program',
            'type': 'contract_program',
        },
        {
            'id': 'hubzone',
            'title': 'HUBZone program',
            'name': 'HUBZone program',
            'description': 'Contracting preference for small businesses in Historically Underutilized Business Zones.',
            'url': f'{site}/federal-contracting/contracting-assistance-programs/hubzone-program',
            'type': 'contract_program',
        },
        {
            'id': 'wosb',
            'title': 'Women-Owned Small Business (WOSB)',
            'name': 'WOSB',
            'description': 'Federal contracting program for women-owned small businesses.',
            'url': f'{site}/federal-contracting/contracting-assistance-programs/women-owned-small-business-federal-contracting-program',
            'type': 'contract_program',
        },
        {
            'id': 'sdvosb',
            'title': 'Service-Disabled Veteran-Owned (SDVOSB)',
            'name': 'SDVOSB',
            'description': 'Contracting opportunities for service-disabled veteran-owned small businesses.',
            'url': f'{site}/federal-contracting/contracting-assistance-programs/service-disabled-veteran-owned-small-businesses-program',
            'type': 'contract_program',
        },
        {
            'id': 'size-standards',
            'title': 'Size standards',
            'name': 'Size standards',
            'description': 'Determine if your business qualifies as small for federal contracting.',
            'url': f'{site}/federal-contracting/contracting-guide/size-standards',
            'type': 'guide',
        },
        {
            'id': 'contracting-guide',
            'title': 'Contracting guide',
            'name': 'Contracting guide',
            'description': 'How to get started selling to the federal government.',
            'url': f'{site}/federal-contracting/contracting-guide',
            'type': 'guide',
        },
        {
            'id': 'sam',
            'title': 'Register in SAM.gov',
            'name': 'Register in SAM.gov',
            'description': 'Required registration to bid on federal contracts.',
            'url': 'https://sam.gov/',
            'type': 'tool',
        },
        {
            'id': 'subcontracting',
            'title': 'Subcontracting',
            'name': 'Subcontracting',
            'description': 'Find subcontracting opportunities with prime contractors.',
            'url': f'{site}/federal-contracting/contracting-guide/basic-requirements',
            'type': 'guide',
        },
    ]
    return _with_child_paths(parent, items)


def _disaster_children():
    """Disaster Assistance parent → disaster resource children."""
    site = 'https://www.sba.gov'
    parent = '/api/sba/content/disaster'
    items = [
        {
            'id': 'disaster-loans',
            'title': 'SBA disaster loans',
            'name': 'SBA disaster loans',
            'description': 'Low-interest disaster loans for businesses, nonprofits, homeowners, and renters.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'loan_program',
        },
        {
            'id': 'business-physical',
            'title': 'Business physical disaster loans',
            'name': 'Business physical disaster loans',
            'description': 'Repair or replace disaster-damaged business property.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'loan_program',
        },
        {
            'id': 'eidl',
            'title': 'Economic Injury Disaster Loans (EIDL)',
            'name': 'EIDL',
            'description': 'Working capital after a declared disaster causes economic injury.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'loan_program',
        },
        {
            'id': 'homeowners',
            'title': 'Home and personal property loans',
            'name': 'Home and personal property loans',
            'description': 'Disaster loans for homeowners and renters.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'loan_program',
        },
        {
            'id': 'apply',
            'title': 'How to apply',
            'name': 'How to apply',
            'description': 'Steps and documents needed to apply for SBA disaster assistance.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'guide',
        },
        {
            'id': 'declarations',
            'title': 'Current disaster declarations',
            'name': 'Current disaster declarations',
            'description': 'Check if your area has an active SBA disaster declaration.',
            'url': f'{site}/funding-programs/disaster-assistance',
            'type': 'tool',
        },
    ]
    return _with_child_paths(parent, items)


def _catalog_for_parent(parent_key):
    """Return child list for a known parent key (recursive explore)."""
    key = (parent_key or '').lower().strip()
    if key in ('loans', 'loan', 'funding'):
        # Prefer live loan list; paths already stamped by SBA_Content
        try:
            result = sba_api.search_loans(query='', page=1, fresh=False)
            items = (result or {}).get('items') or []
            return _with_child_paths('/api/sba/content/loans', items), '/api/sba/content/loans', 'SBA Loans'
        except Exception:
            return [], '/api/sba/content/loans', 'SBA Loans'
    if key in ('contracting', 'contracts', 'government-contracting'):
        return _contracting_children(), '/api/sba/content/contracting', 'Government Contracting'
    if key in ('disaster', 'disaster-assistance'):
        return _disaster_children(), '/api/sba/content/disaster', 'Disaster Assistance'
    if key in ('lenders',):
        try:
            result = sba_api.search_lenders(query='', page=1, fresh=False)
            items = (result or {}).get('items') or []
            return _with_child_paths('/api/sba/content/lenders', items), '/api/sba/content/lenders', 'Lenders'
        except Exception:
            return [], '/api/sba/content/lenders', 'Lenders'
    if key in ('offices',):
        try:
            result = sba_api.search_offices(query='', page=1, fresh=False)
            items = (result or {}).get('items') or []
            return _with_child_paths('/api/sba/content/offices', items), '/api/sba/content/offices', 'Offices'
        except Exception:
            return [], '/api/sba/content/offices', 'Offices'
    if key in ('articles',):
        try:
            result = sba_api.search_articles(query='', page=1, fresh=False)
            items = (result or {}).get('items') or []
            return _with_child_paths('/api/sba/content/articles', items), '/api/sba/content/articles', 'Articles'
        except Exception:
            return [], '/api/sba/content/articles', 'Articles'
    if key in ('sbir',):
        try:
            result = sba_api.search_sbir_awards(query='', page=1, rows=20)
            items = (result or {}).get('items') or (result or {}).get('results') or []
            return _with_child_paths('/api/sba/content/sbir', items), '/api/sba/content/sbir', 'SBIR/STTR'
        except Exception:
            return [], '/api/sba/content/sbir', 'SBIR/STTR'
    return None, None, None


def _explore_as_parent(parent_key, child_id):
    """
    Recursive explore: treat child as the new parent and return ITS contents.
    Children = structured next steps + sibling programs (excluding self).
    """
    child_id = str(child_id or '').strip()
    siblings, parent_path, parent_title = _catalog_for_parent(parent_key)
    if siblings is None:
        return None

    # Loan program detail has richer live content
    if parent_key in ('loans', 'loan', 'funding') and child_id:
        try:
            detail = sba_api.get_loan_program(child_id, force_fresh=False)
            if detail and not detail.get('error'):
                # Filter chrome headings from scraped sections
                clean = []
                for it in detail.get('items') or []:
                    if not isinstance(it, dict):
                        continue
                    title = str(it.get('title') or it.get('name') or '')
                    low = title.lower()
                    if any(x in low for x in (
                        'navigation', 'breadcrumb', 'menu', 'footer', 'cookie', 'skip to',
                        'primary navigation', 'section navigation', 'content',
                    )):
                        continue
                    # Avoid infinite self-loop to same path
                    p = str(it.get('path') or '')
                    if p and p.rstrip('/') == f'/api/sba/content/loans/{child_id}'.rstrip('/'):
                        it = dict(it)
                        it.pop('path', None)
                        it['drillable'] = False
                    # Leaf sections stay non-recursive (no fake deep paths)
                    t = str(it.get('type') or '')
                    if t in ('overview', 'guidance', 'loan_section', 'link', 'notice'):
                        it = dict(it)
                        # Keep explicit cross-links (e.g. Next steps → lenders)
                        if t in ('overview', 'loan_section', 'link', 'notice') or not str(it.get('path') or '').startswith('/api/'):
                            if t != 'guidance' or not str(it.get('path') or '').startswith('/api/sba/content/'):
                                if t != 'guidance':
                                    it['path'] = ''
                                    it['drillable'] = False
                        if t in ('overview', 'loan_section', 'link', 'notice'):
                            it['path'] = ''
                            it['drillable'] = False
                    clean.append(it)
                route = f'/api/sba/content/loans/{child_id}'
                # Related siblings still drillable at loans/* level (real parents only)
                for sib in siblings:
                    if str(sib.get('id')) == child_id:
                        continue
                    clean.append(sib)
                detail['items'] = clean
                detail['results'] = clean
                detail['count'] = len(clean)
                detail['path'] = route
                detail['parent_path'] = parent_path
                return detail
        except Exception as e:
            logger.warning('loan explore soft-fail %s: %s', child_id, e)

    node = None
    for it in siblings:
        if str(it.get('id')) == child_id or str(it.get('title') or '').lower() == child_id.lower():
            node = dict(it)
            break
    if not node:
        return {
            'error': f'Unknown child {child_id} under {parent_key}',
            'items': [],
            'available': [str(s.get('id')) for s in siblings],
        }

    route = node.get('path') or f'{parent_path}/{child_id}'
    # Build recursive children for this node-as-parent
    children = [
        {
            'id': f'{child_id}-overview',
            'title': f"About {node.get('title') or child_id}",
            'name': f"About {node.get('title') or child_id}",
            'description': node.get('description') or node.get('summary') or '',
            'url': node.get('url') or '',
            'type': 'overview',
            'drillable': False,
        },
        {
            'id': f'{child_id}-official',
            'title': 'Official SBA source',
            'name': 'Official SBA source',
            'description': 'Open the official page for full requirements and current terms.',
            'url': node.get('url') or 'https://www.sba.gov',
            'type': 'link',
            'drillable': False,
        },
        {
            'id': f'{child_id}-next',
            'title': 'Next steps',
            'name': 'Next steps',
            'description': (
                'Review eligibility, gather documents, then contact a local SBA resource partner '
                'or use Lender Match for financing paths.'
            ),
            'url': node.get('url') or '',
            'type': 'guidance',
            'path': '/api/sba/content/offices',
            'drillable': True,
        },
    ]
    # Siblings as further recursive parents
    for sib in siblings:
        if str(sib.get('id')) == str(node.get('id')):
            continue
        children.append(sib)

    return {
        'id': node.get('id') or child_id,
        'title': node.get('title') or node.get('name') or child_id,
        'name': node.get('name') or node.get('title') or child_id,
        'description': node.get('description') or '',
        'url': node.get('url') or '',
        'path': route,
        'parent_path': parent_path,
        'parent_title': parent_title,
        'type': node.get('type') or 'resource',
        'items': children,
        'results': children,
        'count': len(children),
        'source': 'catalog',
        'is_current': True,
        'message': f'Exploring “{node.get("title") or child_id}” as parent — {len(children)} child items.',
    }


@sba_bp.route('/content/contracting', methods=['GET'])
def list_contracting():
    """Government Contracting parent → contract programs/certifications children."""
    items = _contracting_children()
    raw = {
        'items': items,
        'count': len(items),
        'title': 'Government Contracting',
        'name': 'Government Contracting',
        'description': 'Federal contracting programs and certifications. Click a child to explore it as the next parent.',
        'url': 'https://www.sba.gov/federal-contracting',
        'path': '/api/sba/content/contracting',
        'source': 'catalog',
        'is_current': True,
        'message': f'{len(items)} contracting programs under Government Contracting.',
    }
    return jsonify(_envelope(raw, 1, route='/api/sba/content/contracting', title='Government Contracting')), 200


@sba_bp.route('/content/contracting/<child_id>', methods=['GET'])
def explore_contracting_child(child_id):
    """Recursive: contracting child becomes parent and lists its contents."""
    result = _explore_as_parent('contracting', child_id)
    route = f'/api/sba/content/contracting/{child_id}'
    if result and result.get('error') and not result.get('items'):
        return jsonify(_envelope(result, 1, route=route, title=str(child_id))), 404
    env = _envelope(result, 1, route=route, title=(result or {}).get('title') or child_id)
    env['parent_path'] = '/api/sba/content/contracting'
    return jsonify(env), 200


@sba_bp.route('/content/disaster', methods=['GET'])
def list_disaster():
    """Disaster Assistance parent → disaster loan/resource children."""
    items = _disaster_children()
    raw = {
        'items': items,
        'count': len(items),
        'title': 'Disaster Assistance',
        'name': 'Disaster Assistance',
        'description': 'SBA disaster loan types and recovery resources. Click a child to explore it as the next parent.',
        'url': 'https://www.sba.gov/funding-programs/disaster-assistance',
        'path': '/api/sba/content/disaster',
        'source': 'catalog',
        'is_current': True,
        'message': f'{len(items)} disaster resources under Disaster Assistance.',
    }
    return jsonify(_envelope(raw, 1, route='/api/sba/content/disaster', title='Disaster Assistance')), 200


@sba_bp.route('/content/disaster/<child_id>', methods=['GET'])
def explore_disaster_child(child_id):
    """Recursive: disaster child becomes parent and lists its contents."""
    result = _explore_as_parent('disaster', child_id)
    route = f'/api/sba/content/disaster/{child_id}'
    if result and result.get('error') and not result.get('items'):
        return jsonify(_envelope(result, 1, route=route, title=str(child_id))), 404
    env = _envelope(result, 1, route=route, title=(result or {}).get('title') or child_id)
    env['parent_path'] = '/api/sba/content/disaster'
    return jsonify(env), 200


@sba_bp.route('/content/loans', methods=['GET'])
def search_loans():
    """
    Parent: SBA Loans — returns all loan program children.
    Clicking SBA Loans in the UI should land here and list 7(a), 504, Microloans, etc.
    """
    query, page, force_fresh = _page_args()
    try:
        result = sba_api.search_loans(query=query, page=page, fresh=force_fresh)
        env = _envelope(result, page, route='/api/sba/content/loans', title='SBA Loans')
        # Ensure parent topic narrative is explicit
        if isinstance(env.get('topic'), dict):
            env['topic']['title'] = 'SBA Loans'
            env['topic']['description'] = (
                result.get('description')
                or env['topic'].get('description')
                or 'All SBA-backed loan program children. Open a child for full program detail.'
            )
            env['topic']['official_url'] = 'https://www.sba.gov/funding-programs/loans'
            env['topic']['sections'] = [
                {
                    'id': 'overview',
                    'title': 'About SBA Loans',
                    'body': 'SBA does not lend directly for most programs — it guarantees loans made by partner lenders. Children below are the main program types.',
                },
                {
                    'id': 'children',
                    'title': 'Loan program children',
                    'body': f'{env.get("count") or len(env.get("items") or [])} programs and tools under this parent.',
                    'count': env.get('count') or len(env.get('items') or []),
                },
                {
                    'id': 'next',
                    'title': 'What to do next',
                    'body': 'Open 7(a), 504, or Microloans for full detail. Use Lender Match to connect with lenders.',
                },
            ]
        return jsonify(env), 200
    except Exception as e:
        logger.error("Error searching loans: %s", e)
        return jsonify(_envelope({'error': str(e), 'items': []}, page, route='/api/sba/content/loans', title='SBA Loans')), 200


@sba_bp.route('/content/loans/<loan_id>', methods=['GET'])
def get_loan_program(loan_id):
    """Recursive: loan child becomes parent and lists its contents / siblings."""
    route = f'/api/sba/content/loans/{loan_id}'
    try:
        result = _explore_as_parent('loans', loan_id)
        if result and result.get('error') and not result.get('items'):
            env = _envelope(result, 1, route=route, title=str(loan_id))
            env['status'] = 'not_found'
            env['available'] = result.get('available') or []
            return jsonify(env), 404
        env = _envelope(result or {}, 1, route=route, title=(result or {}).get('title') or loan_id)
        env['status'] = 'ok'
        env['parent_path'] = '/api/sba/content/loans'
        env['url'] = (result or {}).get('url')
        if isinstance(env.get('topic'), dict):
            env['topic']['official_url'] = (result or {}).get('url')
            env['topic']['sections'] = [
                {
                    'id': 'overview',
                    'title': f"About {(result or {}).get('title') or loan_id}",
                    'body': (result or {}).get('description') or '',
                },
                {
                    'id': 'children',
                    'title': 'Contents of this parent',
                    'body': f'{len((result or {}).get("items") or [])} child items — click any with a path to explore deeper.',
                    'count': len((result or {}).get('items') or []),
                },
                {
                    'id': 'siblings',
                    'title': 'Related loan programs',
                    'body': 'Sibling programs remain drillable. Back returns to SBA Loans.',
                },
            ]
            env['topic']['actions'] = [
                {'id': 'parent', 'label': '← All SBA Loans', 'kind': 'link', 'href': '/browse#r=/api/sba/content/loans&t=SBA%20Loans'},
                {'id': 'official', 'label': 'Official SBA page', 'kind': 'external', 'href': (result or {}).get('url') or 'https://www.sba.gov/funding-programs/loans'},
            ]
        return jsonify(env), 200
    except Exception as e:
        logger.error("Error getting loan program %s: %s", loan_id, e)
        return jsonify(_envelope({'error': str(e), 'items': []}, 1, route=route, title=str(loan_id))), 200


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
    Recursive explore + detail:
      GET /api/sba/content/{parent}/{child}
    Returns a topic envelope with items when the child is treated as the new parent.
    """
    content_type = (content_type or '').lower()
    # Prefer recursive parent rendering for known trees
    explored = _explore_as_parent(content_type, item_id)
    if explored is not None:
        route = f'/api/sba/content/{content_type}/{item_id}'
        if explored.get('error') and not explored.get('items'):
            env = _envelope(explored, 1, route=route, title=str(item_id))
            return jsonify(env), 404
        env = _envelope(explored, 1, route=route, title=explored.get('title') or item_id)
        env['parent_path'] = explored.get('parent_path') or f'/api/sba/content/{content_type}'
        return jsonify(env), 200

    allowed = {
        'articles', 'blogs', 'courses', 'documents', 'events',
        'offices', 'loans', 'lenders', 'sbir', 'node',
        'contracting', 'disaster',
    }
    if content_type not in allowed:
        return jsonify({'error': f'Unknown content type: {content_type}'}), 404
    try:
        detail = sba_api.get_content_detail(content_type, item_id)
        if not detail:
            return jsonify({'error': 'Not found'}), 404
        # Promote single detail into parent-style items list for recursive UI
        if isinstance(detail, dict) and not detail.get('items'):
            card = dict(detail)
            card.setdefault('id', item_id)
            detail = {
                'title': card.get('title') or card.get('name') or item_id,
                'description': card.get('description') or card.get('summary') or '',
                'url': card.get('url') or '',
                'path': f'/api/sba/content/{content_type}/{item_id}',
                'parent_path': f'/api/sba/content/{content_type}',
                'items': [card],
                'results': [card],
                'count': 1,
                'source': card.get('source') or 'detail',
                'is_current': card.get('is_current', True),
            }
        env = _envelope(detail, 1, route=f'/api/sba/content/{content_type}/{item_id}',
                        title=(detail.get('title') if isinstance(detail, dict) else None) or item_id)
        return jsonify(env), 200
    except Exception as e:
        logger.error("Error getting %s/%s: %s", content_type, item_id, e)
        return jsonify(_envelope({
            'id': item_id,
            'title': f'SBA {content_type}',
            'description': f'Unable to load detail ({e}). Visit sba.gov for official information.',
            'items': [],
            'url': 'https://www.sba.gov',
        }, 1, route=f'/api/sba/content/{content_type}/{item_id}', title=str(item_id))), 200
