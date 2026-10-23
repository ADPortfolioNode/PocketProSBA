"""
Request-level security for the Flask app: rate limits, request size cap,
and the CORS policy helpers.

Kept separate from create_app() so the rules are easy to find and test.
"""
from __future__ import annotations

import logging

from flask import jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)

# Endpoints are Flask endpoint names (blueprint.function). Each auth action
# shares one bucket between its /api/<x> alias and /api/auth/<x>, so the
# alias can't be used to double the allowance.
AUTH_ENDPOINTS = {
    "login": ("auth.login", "api.api_login_alias"),
    "register": ("auth.register", "api.api_register_alias"),
    "forgot-password": ("auth.forgot_password", "api.api_forgot_password_alias"),
    "reset-password": ("auth.reset_password", "api.api_reset_password_alias"),
    "refresh": ("auth.refresh",),
}

# Routes that call the LLM / RAG / orchestration stack (paid and slow).
# They share one "llm" bucket per client.
LLM_ENDPOINTS = (
    "chat.post_message",
    "chat_double_api_prefix",
    "rag.rag_root_query",
    "rag.query_documents",
    "rag.query_sba_documents",
    "rag.decompose_task",
    "rag.execute_step",
    "rag.validate_step",
    "api.api_rag_alias",
    "api.query_documents",
    "api.decompose_task",
    "api.execute_step",
    "api.validate_step",
    "api.api_search",
    "orchestrator.submit_task",
    "assistants.assistants_concierge",
    "assistants.assistants_search",
    "assistants.assistants_file",
    "assistants.assistants_function",
)

# Environments where any http://localhost:* / 127.0.0.1:* origin is reflected.
DEV_CORS_ENVS = ("development", "testing")

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://frontend:80",
]


def app_env(app) -> str:
    """Active environment name: development, production or testing."""
    env = app.config.get("APP_ENV")
    if env and env != "base":
        return str(env)
    if app.config.get("TESTING"):
        return "testing"
    return str(app.config.get("FLASK_ENV") or "production")


def build_allowed_origins(app) -> list[str]:
    origins = list(DEFAULT_ALLOWED_ORIGINS)
    extra = [app.config.get("FRONTEND_URL")] + list(app.config.get("CORS_ALLOWED_ORIGINS") or [])
    for origin in extra:
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def make_origin_checker(app, allowed_origins):
    """Return origin -> bool. Localhost reflection only in development/testing."""
    allow_any_localhost = app_env(app) in DEV_CORS_ENVS

    def _allowed(origin: str | None) -> bool:
        if not origin:
            return False
        if origin in allowed_origins:
            return True
        if allow_any_localhost:
            return origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")
        return False

    return _allowed


def init_request_size_limit(app) -> None:
    """MAX_CONTENT_LENGTH (from config) plus a clean JSON 413."""
    max_len = app.config.get("MAX_CONTENT_LENGTH")
    max_mb = round(max_len / (1024 * 1024), 1) if max_len else None

    def _too_large_response():
        msg = "Request is too large."
        if max_mb:
            msg = f"Request is too large. The maximum size is {max_mb:g} MB."
        resp = jsonify({"error": msg, "success": False, "max_content_length": max_len})
        resp.status_code = 413
        return resp

    @app.before_request
    def _reject_oversized_requests():
        # Fail fast on a declared Content-Length, before any route reads the
        # body (some routes catch broad exceptions around request.files).
        limit = app.config.get("MAX_CONTENT_LENGTH")
        if limit and request.content_length is not None and request.content_length > limit:
            return _too_large_response()
        return None

    @app.errorhandler(RequestEntityTooLarge)
    def _handle_413(_error):
        return _too_large_response()


def init_rate_limiting(app):
    """Attach a per-app Flask-Limiter and apply auth + LLM limits.

    Returns the Limiter (also at app.extensions["sba_limiter"]), or None when
    disabled (RATELIMIT_ENABLED=false) or Flask-Limiter isn't installed
    (logged loudly; the app still boots).
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.errors import RateLimitExceeded
        from flask_limiter.util import get_remote_address
    except Exception as err:  # pragma: no cover - dependency is pinned
        logger.error("Flask-Limiter unavailable, rate limiting DISABLED: %s", err)
        return None

    if not app.config.get("RATELIMIT_ENABLED", True):
        logger.warning("Rate limiting disabled (RATELIMIT_ENABLED=false)")
        return None

    proxies = int(app.config.get("TRUSTED_PROXY_COUNT") or 0)
    if proxies > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=0)

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI") or "memory://",
        default_limits=[],
        headers_enabled=bool(app.config.get("RATELIMIT_HEADERS_ENABLED", True)),
        strategy="fixed-window",
    )
    # Limits hold only a weak reference to their Limiter: keep a strong one.
    app.extensions["sba_limiter"] = limiter

    auth_limit = app.config.get("RATELIMIT_AUTH") or "10 per minute"
    llm_limit = app.config.get("RATELIMIT_LLM") or "30 per minute"

    def _wrap(endpoint, rule, scope):
        view = app.view_functions.get(endpoint)
        if view is None:
            logger.debug("rate limit: endpoint %s not registered, skipped", endpoint)
            return
        app.view_functions[endpoint] = limiter.shared_limit(
            rule, scope=scope, methods=["POST"]
        )(view)

    for action, endpoints in AUTH_ENDPOINTS.items():
        for ep in endpoints:
            _wrap(ep, auth_limit, f"auth:{action}")
    for ep in LLM_ENDPOINTS:
        _wrap(ep, llm_limit, "llm")

    @app.errorhandler(RateLimitExceeded)
    def _handle_429(error):
        resp = jsonify({
            "error": "Too many requests. Please wait a moment and try again.",
            "success": False,
            "limit": str(getattr(error, "description", "") or ""),
        })
        resp.status_code = 429
        # Keep Retry-After / X-RateLimit-* headers Flask-Limiter computed.
        if getattr(error, "response", None) is not None:
            for key, value in error.response.headers.items():
                if key.lower().startswith(("retry-after", "x-ratelimit")):
                    resp.headers[key] = value
        return resp

    return limiter
