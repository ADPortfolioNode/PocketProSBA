"""
Access tokens and the ``auth_required`` decorator.

Login issues a signed, expiring access token (JWT, HS256). Protected routes
(chat/LLM, RAG, document upload/list, orchestrator, assistants) require it as
``Authorization: Bearer <token>``; a missing, expired or tampered token gets a
401 JSON answer. Health, info, the auth endpoints and public SBA content stay
open.

Strategy: short-lived access tokens (JWT_ACCESS_TTL_SECONDS, default 1 hour).
A client with a still-valid token can call POST /api/auth/refresh for a fresh
one (sliding session); once it has expired the user logs in again. Tokens are
bound to the user's current password hash, so a password reset ends every
session issued before it, and a disabled account is rejected immediately.

AUTH_REQUIRED (default true) turns enforcement off for local demos only:
``AUTH_REQUIRED=false``. Login still issues real tokens either way.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

logger = logging.getLogger(__name__)

TOKEN_ALGORITHM = "HS256"
TOKEN_ISSUER = "pocketpro-sba"
TOKEN_TYPE = "access"
DEFAULT_ACCESS_TTL_SECONDS = 3600

# Machine-readable reasons, returned as "code" in 401 bodies.
TOKEN_MISSING = "token_missing"
TOKEN_EXPIRED = "token_expired"
TOKEN_INVALID = "token_invalid"

UNAUTHORIZED_MESSAGES = {
    TOKEN_MISSING: "Please log in to continue.",
    TOKEN_EXPIRED: "Your session has expired. Please log in again.",
    TOKEN_INVALID: "Your session is no longer valid. Please log in again.",
}


class AuthError(Exception):
    """A request could not be authenticated; ``code`` is one of TOKEN_*."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def auth_enabled(app=None) -> bool:
    app = app or current_app
    return bool(app.config.get("AUTH_REQUIRED", True))


def _signing_key(app=None) -> bytes:
    """Derive the token key from SECRET_KEY (or JWT_SECRET_KEY if set).

    HMAC-SHA256 derivation gives a full 32-byte key whatever the length of the
    configured secret, and keeps token signatures separate from Flask's own
    session signing.
    """
    app = app or current_app
    secret = app.config.get("JWT_SECRET_KEY") or app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY must be set to issue or verify access tokens")
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    return hmac.new(secret, b"pocketpro-sba access token v1", hashlib.sha256).digest()


def _access_ttl(app=None) -> int:
    app = app or current_app
    try:
        ttl = int(app.config.get("JWT_ACCESS_TTL_SECONDS") or DEFAULT_ACCESS_TTL_SECONDS)
    except (TypeError, ValueError):
        ttl = DEFAULT_ACCESS_TTL_SECONDS
    return max(ttl, 1)


def password_version(user) -> str:
    """Short fingerprint of the stored password hash.

    Changing the password changes this, which invalidates older tokens.
    """
    return hashlib.sha256((user.password_hash or "").encode("utf-8")).hexdigest()[:16]


def create_access_token(user, app=None, ttl_seconds: int | None = None) -> dict:
    """Sign an access token for ``user``.

    Returns {"token", "token_type", "expires_in", "expires_at"} (expires_at is
    a Unix timestamp in seconds).
    """
    app = app or current_app
    now = int(time.time())
    ttl = int(ttl_seconds) if ttl_seconds is not None else _access_ttl(app)
    payload = {
        "sub": str(user.id),
        "iss": TOKEN_ISSUER,
        "typ": TOKEN_TYPE,
        "iat": now,
        "nbf": now,
        "exp": now + ttl,
        "pv": password_version(user),
        "jti": secrets.token_urlsafe(8),
    }
    token = jwt.encode(payload, _signing_key(app), algorithm=TOKEN_ALGORITHM)
    return {
        "token": token,
        "token_type": "Bearer",
        "expires_in": ttl,
        "expires_at": now + ttl,
    }


def decode_access_token(token: str, app=None) -> dict:
    """Verify signature, expiry, issuer and type. Raises AuthError."""
    app = app or current_app
    try:
        claims = jwt.decode(
            token,
            _signing_key(app),
            algorithms=[TOKEN_ALGORITHM],
            issuer=TOKEN_ISSUER,
            options={"require": ["exp", "iat", "sub", "iss"]},
            leeway=5,
        )
    except jwt.ExpiredSignatureError:
        raise AuthError(TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise AuthError(TOKEN_INVALID)
    if claims.get("typ") != TOKEN_TYPE:
        raise AuthError(TOKEN_INVALID)
    return claims


def bearer_token_from_request() -> str | None:
    header = request.headers.get("Authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer":
        return None
    value = value.strip()
    return value or None


def authenticate_request():
    """Return the User for the request's bearer token. Raises AuthError."""
    token = bearer_token_from_request()
    if not token:
        raise AuthError(TOKEN_MISSING)
    claims = decode_access_token(token)

    from backend.models.chat import db
    from backend.models.user import User

    try:
        user = db.session.get(User, int(claims["sub"]))
    except (TypeError, ValueError):
        raise AuthError(TOKEN_INVALID)
    if user is None or not user.is_active:
        raise AuthError(TOKEN_INVALID)
    if not hmac.compare_digest(str(claims.get("pv") or ""), password_version(user)):
        # Password changed (e.g. reset) after this token was issued.
        raise AuthError(TOKEN_INVALID)
    return user


def unauthorized_response(code: str):
    resp = jsonify({
        "error": UNAUTHORIZED_MESSAGES.get(code, UNAUTHORIZED_MESSAGES[TOKEN_MISSING]),
        "code": code,
        "success": False,
    })
    resp.status_code = 401
    if code == TOKEN_MISSING:
        resp.headers["WWW-Authenticate"] = 'Bearer realm="pocketpro-sba"'
    else:
        resp.headers["WWW-Authenticate"] = 'Bearer realm="pocketpro-sba", error="invalid_token"'
    return resp


def get_current_user():
    """The authenticated User for this request, or None."""
    return getattr(g, "current_user", None)


def _guard(view, always: bool):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.method == "OPTIONS":
            return view(*args, **kwargs)
        if not always and not auth_enabled():
            return view(*args, **kwargs)
        try:
            g.current_user = authenticate_request()
        except AuthError as err:
            return unauthorized_response(err.code)
        return view(*args, **kwargs)

    wrapper.auth_required = True
    return wrapper


def auth_required(view):
    """Require a valid bearer token (skipped when AUTH_REQUIRED is false)."""
    return _guard(view, always=False)


def token_required(view):
    """Require a valid bearer token even when AUTH_REQUIRED is false.

    For endpoints that only make sense for a signed-in user (/api/auth/me,
    /api/auth/refresh).
    """
    return _guard(view, always=True)
