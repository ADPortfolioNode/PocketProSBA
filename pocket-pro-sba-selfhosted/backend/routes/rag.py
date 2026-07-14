from flask import Blueprint, request, jsonify
import logging
import os
import re
from pathlib import Path
from backend.services.api_service import (
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
)
from backend.services.rag import get_rag_manager

logger = logging.getLogger(__name__)

try:
    from backend.enhanced_gemini_rag_service import enhanced_rag_service
except Exception as e:
    logger.warning(f"Enhanced Gemini RAG service is unavailable: {e}")
    class _FallbackEnhancedRAGService:
        is_initialized = False

        def get_sba_overview(self):
            return _static_sba_overview()

        def query_sba_loans(self, question: str):
            return _local_kb_sba_answer(question)
    enhanced_rag_service = _FallbackEnhancedRAGService()
rag_bp = Blueprint('rag', __name__)


def _knowledge_base_roots():
    """Candidate knowledge-base paths (host bind-mount and container layouts)."""
    here = Path(__file__).resolve()
    return [
        here.parents[1] / "knowledge_base",  # backend/knowledge_base
        Path("./backend/knowledge_base"),
        Path("/app/backend/knowledge_base"),
        Path("./knowledge_base"),
    ]


def _static_sba_overview():
    """Static overview so /sba-overview stays available without Gemini embeddings."""
    if hasattr(enhanced_rag_service, "get_sba_overview") and type(enhanced_rag_service).__name__ != "_FallbackEnhancedRAGService":
        try:
            return enhanced_rag_service.get_sba_overview()
        except Exception:
            pass
    return {
        "available_loan_types": [
            {
                "type": "SBA 7(a) Loans",
                "max_amount": "$5 million",
                "use_cases": ["working capital", "equipment", "real estate", "business acquisition"],
                "terms": "7-25 years",
                "rates": "Prime + 2.25% to 4.75%",
            },
            {
                "type": "SBA 504 Loans",
                "max_amount": "$5.5 million per project",
                "use_cases": ["real estate", "major equipment", "construction"],
                "terms": "10-25 years",
                "rates": "Fixed, below market",
            },
            {
                "type": "SBA Microloans",
                "max_amount": "$50,000",
                "use_cases": ["working capital", "inventory", "supplies", "equipment"],
                "terms": "Up to 6 years",
                "rates": "8-13% (varies by lender)",
            },
            {
                "type": "SBA Express Loans",
                "max_amount": "$500,000",
                "use_cases": ["same as 7(a) but faster"],
                "terms": "7-25 years",
                "rates": "Prime + 4.5% to 6.5%",
            },
        ],
        "topics_covered": [
            "Loan eligibility requirements",
            "Application process steps",
            "Required documentation",
            "Current interest rates and terms",
            "Collateral requirements",
            "Timeline expectations",
            "Fee structures",
            "Prepayment penalties",
            "Down payment requirements",
        ],
        "sample_questions": [
            "What are the eligibility requirements for an SBA 7(a) loan?",
            "How long does the SBA loan application process take?",
            "What documents do I need to apply for an SBA loan?",
            "What can SBA loans be used for?",
            "What are the current SBA loan interest rates?",
        ],
        "mode": "static_fallback",
        "note": "Served from static knowledge summary (Gemini RAG not fully initialized).",
    }


def _normalize_kb_text(value: str) -> str:
    """Compact alphanumerics only so 7(a)/7-a/7A all match token 7a."""
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _local_kb_sba_answer(question: str, max_chunks: int = 4):
    """
    Lightweight keyword retrieval over local knowledge_base text files.
    Used when Gemini embeddings / enhanced RAG are unavailable — no new deps.
    """
    q_spaced = re.sub(r"[^a-z0-9\s]", " ", (question or "").lower())
    q_compact = _normalize_kb_text(question)
    tokens = [t for t in re.findall(r"[a-z0-9]{3,}", q_spaced) if t not in {
        "the", "and", "for", "what", "how", "are", "with", "from", "this", "that",
        "can", "does", "about", "loan", "loans", "sba",  # too common in all docs
    }]
    # High-signal SBA terms (including short codes like 7a / 504)
    for keep in ("7a", "504", "microloan", "express", "eligibility", "rate", "rates"):
        if keep in q_compact and keep not in tokens:
            tokens.append(keep)

    scored = []
    seen_paths = set()
    for root in _knowledge_base_roots():
        if not root.exists():
            continue
        for path in root.rglob("*.txt"):
            key = str(path.resolve())
            if key in seen_paths:
                continue
            # Skip ingest manifests (metadata only)
            if path.name.endswith("__manifest.txt"):
                continue
            seen_paths.add(key)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            lower = text.lower()
            compact = _normalize_kb_text(text)
            score = sum(compact.count(tok) for tok in tokens) if tokens else 1
            if score <= 0:
                continue
            # Boost live API digests written when browsing parent→children
            path_str = str(path).replace("\\", "/")
            if "sba_api_live" in path_str or path.name.startswith("api_sba_"):
                score += 12
                if "combined" in path.name:
                    score += 4
                if "overview" in path.name:
                    score += 2
            # Prefer a relevant paragraph/snippet from original text
            snippet = text.strip()
            if tokens:
                idx_candidates = []
                for tok in tokens:
                    pos = lower.find(tok)
                    if pos >= 0:
                        idx_candidates.append(pos)
                    else:
                        # Map compact match approx onto original via digit/letter run
                        cpos = compact.find(tok)
                        if cpos >= 0 and tok[:1].isdigit():
                            m = re.search(r"7\s*[\(\-]?\s*a", lower)
                            if m:
                                idx_candidates.append(m.start())
                idx = min(idx_candidates) if idx_candidates else 0
                start = max(0, idx - 120)
                end = min(len(text), start + 600)
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
            scored.append((score, path.name, snippet, str(path)))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_chunks]

    if not top:
        overview = _static_sba_overview()
        types = overview.get("available_loan_types", [])
        lines = [
            "I don't have live Gemini RAG embeddings right now, but here is a brief SBA overview:",
        ]
        for item in types[:4]:
            lines.append(
                f"- {item.get('type')}: up to {item.get('max_amount')} "
                f"({item.get('terms')}; {item.get('rates')})"
            )
        answer = "\n".join(lines)
        return {
            "question": question,
            "answer": answer,
            "source_documents": [],
            "mode": "static_fallback",
        }

    live_hits = sum(
        1
        for _, name, _, p in top
        if "sba_api_live" in str(p).replace("\\", "/")
        or "sba_api" in str(name)
        or str(name).startswith("api_sba_")
    )
    if live_hits:
        answer_parts = [
            "Based on live SBA API digests (from parent/child explore) plus the local knowledge base:",
            "",
        ]
        kb_mode = "sba_api_live"
    else:
        answer_parts = [
            "Based on the local SBA knowledge base (keyword match; Gemini embeddings unavailable):",
            "",
        ]
        kb_mode = "local_kb_fallback"
    sources = []
    for score, name, snippet, full in top:
        answer_parts.append(snippet)
        answer_parts.append("")
        sources.append({
            "content": snippet[:200] + ("..." if len(snippet) > 200 else ""),
            "metadata": {"source": name, "path": full, "score": score},
        })

    return {
        "question": question,
        "answer": "\n".join(answer_parts).strip(),
        "source_documents": sources,
        "mode": kb_mode,
    }

@rag_bp.route('', methods=['POST', 'OPTIONS'])
@rag_bp.route('/', methods=['POST', 'OPTIONS'])
def rag_root_query():
    """
    Prebuilt App.js:
      POST {base}/api/rag  with body {query}
    where base is often http://localhost:5000/api → /api/api/rag → rewritten to /api/rag.

    Expects JSON response with answer/response and optional sources.
    """
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.get_json(silent=True) or {}
        query = (data.get('query') or data.get('message') or data.get('question') or '').strip()
        if not query:
            return jsonify({'error': 'query is required', 'answer': '', 'sources': []}), 400

        answer = ''
        sources = []

        mode = 'none'
        # 1) Local SBA knowledge base (static + live API ingest files)
        try:
            kb = _local_kb_sba_answer(query)
            if isinstance(kb, dict):
                answer = kb.get('answer') or kb.get('response') or ''
                # local helper returns source_documents; normalize for clients
                raw_src = kb.get('sources') or kb.get('source_documents') or []
                sources = []
                for s in raw_src:
                    if not isinstance(s, dict):
                        continue
                    meta = s.get('metadata') or {}
                    sources.append({
                        'title': meta.get('source') or meta.get('title') or s.get('title') or 'SBA KB',
                        'snippet': s.get('content') or s.get('snippet') or '',
                        'path': meta.get('path') or s.get('path') or '',
                        'score': meta.get('score'),
                        'source': meta.get('source') or 'local_kb',
                    })
                mode = kb.get('mode') or 'local_kb'
        except Exception as e:
            logger.warning('local KB soft-fail on /api/rag: %s', e)

        # 2) Chroma / RAGManager — includes SBA API child digests when ingested
        if not answer:
            try:
                from backend.services.rag import get_rag_manager
                rag_mgr = get_rag_manager()
                if rag_mgr and rag_mgr.is_available():
                    results = rag_mgr.query_documents(query, n_results=5)
                    rows = []
                    if isinstance(results, dict):
                        # chroma_fixed may return documents/metadatas lists
                        docs = results.get('documents') or results.get('results') or []
                        if docs and isinstance(docs[0], list):
                            docs = docs[0]
                        metas = results.get('metadatas') or []
                        if metas and isinstance(metas[0], list):
                            metas = metas[0]
                        for i, doc in enumerate(docs or []):
                            meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
                            rows.append({'content': doc, 'metadata': meta})
                        if not rows and isinstance(results.get('results'), list):
                            rows = results.get('results')
                    if rows:
                        parts = []
                        sources = []
                        for r in rows[:5]:
                            if not isinstance(r, dict):
                                parts.append(str(r)[:400])
                                continue
                            content = str(r.get('content') or r.get('text') or '')
                            meta = r.get('metadata') or {}
                            parts.append(content[:500])
                            sources.append({
                                'title': meta.get('title') or meta.get('route') or meta.get('source') or 'SBA API',
                                'snippet': content[:200],
                                'route': meta.get('route') or meta.get('child_path') or '',
                                'source': meta.get('source') or 'chroma',
                            })
                        answer = '\n\n'.join(p for p in parts if p)
                        mode = 'chroma_sba_api' if any(
                            (s.get('source') == 'sba_api') for s in sources
                        ) else 'chroma'
            except Exception as e:
                logger.warning('RAGManager query soft-fail on /api/rag: %s', e)

        # 3) Vector / enhanced Gemini store
        if not answer:
            try:
                if getattr(enhanced_rag_service, 'is_initialized', False):
                    results = enhanced_rag_service.search_documents(query, limit=5)
                    if isinstance(results, list) and results:
                        parts = []
                        for r in results[:5]:
                            if isinstance(r, dict):
                                parts.append(r.get('content') or r.get('text') or str(r))
                                sources.append({
                                    'title': r.get('title') or r.get('source') or 'Document',
                                    'snippet': (r.get('content') or r.get('text') or '')[:200],
                                })
                            else:
                                parts.append(str(r))
                        answer = '\n\n'.join(parts)
                        mode = 'enhanced_rag'
            except Exception as e:
                logger.warning('Enhanced RAG soft-fail on /api/rag: %s', e)

        if not answer:
            try:
                from backend.services.api_service import query_documents_service
                results = query_documents_service(query, 5)
                rows = results.get('results') if isinstance(results, dict) else []
                if rows:
                    answer = '\n\n'.join(
                        str(r.get('content') or r.get('text') or '')[:400] for r in rows if r
                    )
                    sources = [
                        {
                            'title': (r.get('metadata') or {}).get('filename') or r.get('id') or 'Doc',
                            'snippet': str(r.get('content') or '')[:200],
                        }
                        for r in rows
                    ]
                    mode = 'query_documents_service'
            except Exception as e:
                logger.warning('query_documents_service soft-fail: %s', e)

        if not answer:
            try:
                from backend.services.chat_processing_service import process_chat_message
                chat = process_chat_message(1, query, session_id=None)
                answer = chat.get('response') or chat.get('text') or ''
                sources = chat.get('sources') or []
            except Exception as e:
                logger.warning('chat fallback soft-fail: %s', e)
                answer = (
                    f"I received your question about “{query}”. "
                    "Upload documents in the RAG workflow or browse SBA Resources for live program content."
                )

        # Prefer live API digests when sources came from sba_api_live
        is_live = any(
            'sba_api' in str(s.get('source') or s.get('path') or '').lower()
            or 'sba_api_live' in str(s.get('path') or '').lower()
            for s in (sources or [])
            if isinstance(s, dict)
        )
        # Always attach markdown hyperlinks + usable forms/docs/tools
        try:
            from backend.services.link_enrichment import enrich_answer_with_links
            from backend.services.actionable_content import attach_actionable_section

            answer = enrich_answer_with_links(answer, sources)
            answer = attach_actionable_section(answer, query=query)
        except Exception as link_err:
            logger.warning('link enrichment soft-fail: %s', link_err)

        return jsonify({
            'success': True,
            'query': query,
            'answer': answer,
            'response': answer,
            'message': answer,
            'sources': sources or [],
            'context': sources or [],
            'mode': mode,
            'is_current': bool(is_live),
            'freshness': 'current' if is_live else 'not_current',
        }), 200
    except Exception as e:
        logger.exception('POST /api/rag failed')
        return jsonify({
            'error': str(e),
            'answer': 'RAG query failed. Please try again.',
            'sources': [],
        }), 500


@rag_bp.route('/health', methods=['GET'])
def rag_health():
    """RAG service health check"""
    try:
        rag_manager = get_rag_manager()
        if rag_manager.is_available():
            stats = rag_manager.get_collection_stats()
            document_count = stats.get('count', 0) if isinstance(stats, dict) else 0
            return jsonify({
                'status': 'ok',
                'message': 'RAG system is available and connected',
                'document_count': document_count
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'RAG system is not available'
            }), 503
    except Exception as e:
        logger.error(f"Error checking RAG health: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to check RAG health: {str(e)}'
        }), 500

@rag_bp.route('/decompose', methods=['POST'])
def decompose_task():
    """Decompose a user task into steps"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for decompose task")
            return jsonify({'error': 'No JSON data provided'}), 400

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

@rag_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for execute step")
            return jsonify({'error': 'No JSON data provided'}), 400

        task = data.get('task', {})
        result = execute_step_service(task)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        return jsonify({'error': f'Failed to execute step: {str(e)}'}), 500

@rag_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for validate step")
            return jsonify({'error': 'No JSON data provided'}), 400

        result = data.get('result', '')
        task = data.get('task', {})
        validation = validate_step_service(result, task)
        return jsonify(validation)

    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

@rag_bp.route('/query', methods=['POST'])
def query_documents():
    """Query documents"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for query documents")
            return jsonify({'error': 'No JSON data provided'}), 400

        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)

        if not query:
            logger.warning("Query is required for querying documents")
            return jsonify({'error': 'Query is required'}), 400

        # Use enhanced Gemini RAG service if available and initialized
        if enhanced_rag_service.is_initialized:
            results = enhanced_rag_service.search_documents(query, limit=top_k)
            return jsonify({
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            })
        else:
            results = query_documents_service(query, top_k)
            return jsonify(results)

    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return jsonify({'error': 'Failed to query documents'}), 500

@rag_bp.route('/sba-query', methods=['POST'])
def query_sba_documents():
    """Query SBA documents using Gemini RAG, with local KB fallback."""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for SBA query")
            return jsonify({'error': 'No JSON data provided'}), 400

        # Accept both "query" and "question" for client compatibility
        query = (data.get('query') or data.get('question') or '').strip()

        if not query:
            logger.warning("Query is required for SBA query")
            return jsonify({'error': 'Query is required'}), 400

        def _mark_rag(payload: dict, mode: str) -> dict:
            """RAG / KB answers are intentionally not claimed as live SBA.gov current."""
            if not isinstance(payload, dict):
                payload = {'answer': str(payload)}
            payload['is_current'] = False
            payload['freshness'] = 'not_current'
            payload['source'] = mode
            payload['render_policy'] = 'current_unless_rag'
            payload.setdefault('mode', mode)
            payload.setdefault(
                'message',
                'Answer from RAG/knowledge base — may not reflect the latest sba.gov content. '
                'Use /api/sba/content/* for current official pages.',
            )
            return payload

        # Prefer enhanced Gemini RAG when fully initialized
        if getattr(enhanced_rag_service, 'is_initialized', False):
            try:
                result = enhanced_rag_service.query_sba_loans(query)
                # If the service returns a soft error, fall back to local KB
                if isinstance(result, dict) and result.get('error') and not result.get('answer'):
                    logger.warning("Enhanced RAG returned error; using local KB fallback: %s", result.get('error'))
                    return jsonify(_mark_rag(_local_kb_sba_answer(query), 'local_kb_fallback'))
                return jsonify(_mark_rag(result if isinstance(result, dict) else {'answer': result}, 'gemini_rag'))
            except Exception as rag_err:
                logger.warning("Enhanced RAG query failed; using local KB fallback: %s", rag_err)

        # Soft degrade: keyword search over on-disk knowledge base (no Gemini required)
        return jsonify(_mark_rag(_local_kb_sba_answer(query), 'local_kb_fallback'))

    except Exception as e:
        logger.error(f"Error querying SBA documents: {str(e)}")
        return jsonify({'error': 'Failed to query SBA documents'}), 500

@rag_bp.route('/sba-overview', methods=['GET'])
def get_sba_overview():
    """
    SBA loan overview for UI.

    Prefer *current* live loan content from /sba content client.
    RAG/static catalog is only used when live fetch fails (and is marked not current).
    """
    try:
        # 1) Current official loan content (non-RAG)
        try:
            from backend.services.SBA_Content import SBAContentAPI, clear_sba_cache
            if (request.args.get('fresh') or '').lower() in ('1', 'true', 'yes'):
                clear_sba_cache()
            live = SBAContentAPI().search_loans(page=1, fresh=bool(request.args.get('fresh')))
            if isinstance(live, dict) and live.get('is_current') and live.get('items'):
                return jsonify({
                    'available_loan_types': [
                        {
                            'type': item.get('title') or item.get('name'),
                            'description': item.get('description') or item.get('summary'),
                            'url': item.get('url'),
                            'is_current': True,
                            'retrieved_at': item.get('retrieved_at'),
                        }
                        for item in live.get('items', [])[:8]
                        if item.get('type') in (None, 'loan_program', 'loan') or 'loan' in (item.get('title') or '').lower()
                    ] or [
                        {
                            'type': i.get('title'),
                            'description': i.get('description'),
                            'url': i.get('url'),
                            'is_current': True,
                            'retrieved_at': i.get('retrieved_at'),
                        }
                        for i in live.get('items', [])[:6]
                    ],
                    'source': live.get('source'),
                    'is_current': True,
                    'freshness': 'current',
                    'retrieved_at': live.get('retrieved_at'),
                    'mode': 'live_sba',
                    'message': live.get('message') or 'Current loan overview from official sba.gov pages.',
                    'render_policy': 'current_unless_rag',
                })
        except Exception as live_err:
            logger.warning("Live SBA overview failed; falling back to RAG/static: %s", live_err)

        # 2) RAG/static — explicitly not current
        if getattr(enhanced_rag_service, 'is_initialized', False) and hasattr(enhanced_rag_service, 'get_sba_overview'):
            try:
                overview = enhanced_rag_service.get_sba_overview()
                if isinstance(overview, dict):
                    overview['mode'] = 'gemini_rag'
                    overview['is_current'] = False
                    overview['freshness'] = 'not_current'
                    overview['message'] = (
                        'RAG overview (not live sba.gov). Prefer /api/sba/content/loans for current content.'
                    )
                return jsonify(overview)
            except Exception as ov_err:
                logger.warning("Enhanced overview failed; static fallback: %s", ov_err)
        static = _static_sba_overview()
        if isinstance(static, dict):
            static['is_current'] = False
            static['freshness'] = 'not_current'
            static['mode'] = static.get('mode') or 'static_fallback'
            static['message'] = (
                'Offline/static overview only — not current sba.gov content. '
                'Retry /api/sba/content/loans?fresh=1 when network is available.'
            )
        return jsonify(static)

    except Exception as e:
        logger.error(f"Error getting SBA overview: {str(e)}")
        return jsonify({'error': 'Failed to get SBA overview'}), 500
