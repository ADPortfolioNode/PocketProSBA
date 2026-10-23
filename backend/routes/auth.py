"""
Authentication routes — register, login, forgot/reset password.
Persists users via Flask-SQLAlchemy User model.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from backend.app.auth import create_access_token, get_current_user, token_required
from backend.routes._errors import internal_error_message

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8
PASSWORD_TOO_SHORT = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
RESET_TOKEN_TTL = timedelta(hours=1)
INVALID_RESET_TOKEN = "Invalid or expired reset token"
# Same body whether or not the email already has an account (no enumeration).
REGISTER_RESPONSE = {
    "success": True,
    "message": "Registration received. Please log in to continue.",
}
FORGOT_RESPONSE = {
    "success": True,
    "message": "If this email is registered, you will receive password reset instructions.",
}


def hash_reset_token(token: str) -> str:
    """Reset tokens are stored as SHA-256 digests, never in plaintext.

    The token is 32 random bytes, so a fast hash is enough (no brute-force
    risk); a DB leak alone can no longer be used to reset passwords.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _password_ok(password) -> bool:
    return isinstance(password, str) and len(password) >= MIN_PASSWORD_LENGTH


def deliver_reset_token(email: str, token: str) -> None:
    """Hand a reset token to the user out of band (never in the HTTP response).

    Set ``app.config["PASSWORD_RESET_DELIVERY"]`` to a callable
    ``(email, token) -> None`` to send it (email gateway, queue, ...).
    Without one, the token is only written to the server log when the app is
    running with DEBUG explicitly enabled, so local development still works.
    """
    sender = current_app.config.get("PASSWORD_RESET_DELIVERY")
    if callable(sender):
        sender(email, token)
        return
    if current_app.debug:
        logger.warning(
            "DEV ONLY (DEBUG on, no PASSWORD_RESET_DELIVERY configured): reset token for %s: %s",
            email, token,
        )
    else:
        logger.warning(
            "Password reset requested but no PASSWORD_RESET_DELIVERY is configured; token not delivered."
        )


def _get_user_model():
    from backend.models.user import User
    from backend.models.chat import db
    return User, db


def _json():
    data = request.get_json(silent=True)
    if data is None:
        return None
    return data if isinstance(data, dict) else None


@auth_bp.route("/auth-health", methods=["GET"])
@auth_bp.route("/health", methods=["GET"])
def auth_health():
    """Health for auth service. Prefer /api/auth/health to avoid clashing with /api/health."""
    return jsonify({
        "service": "auth",
        "status": "healthy",
        "message": "Auth service is operational",
        "endpoints": [
            "POST /api/login",
            "POST /api/register",
            "POST /api/forgot-password",
            "POST /api/reset-password",
            "GET /api/auth/me",
            "POST /api/auth/refresh",
            "GET /api/auth/health",
            "GET /api/auth-health",
        ],
    }), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account."""
    data = _json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip() or None

    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if not _password_ok(password):
        return jsonify({"error": PASSWORD_TOO_SHORT}), 400

    User, db = _get_user_model()
    try:
        existing = User.query.filter_by(email=email).first()
        if existing:
            # Do the same hashing work as a real signup so timing doesn't leak
            # which emails exist, and answer exactly like a successful signup.
            generate_password_hash(password)
            logger.info("Register attempted for an existing account")
            return jsonify(REGISTER_RESPONSE), 201

        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        logger.info("Registered user id=%s", user.id)
        return jsonify(REGISTER_RESPONSE), 201
    except IntegrityError:
        # Concurrent signup for the same email: same generic answer.
        db.session.rollback()
        return jsonify(REGISTER_RESPONSE), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": internal_error_message(e, public="Registration failed. Please try again.")}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return public profile + session token."""
    data = _json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    User, db = _get_user_model()
    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401
        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403

        user.last_login = datetime.utcnow()
        db.session.commit()

        # Signed, expiring access token (HS256 JWT); send it as
        # "Authorization: Bearer <token>" to protected routes.
        issued = create_access_token(user)
        return jsonify({
            "success": True,
            "message": "Login successful",
            **issued,
            "user": user.to_public_dict(),
        }), 200
    except Exception as e:
        return jsonify({"error": internal_error_message(e, public="Login failed. Please try again.")}), 500


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    """Profile of the user the bearer token belongs to (401 if none/invalid)."""
    return jsonify({"success": True, "user": get_current_user().to_public_dict()}), 200


@auth_bp.route("/refresh", methods=["POST"])
@token_required
def refresh():
    """Swap a still-valid access token for a fresh one (sliding session).

    Expired tokens get a 401: the user logs in again.
    """
    issued = create_access_token(get_current_user())
    return jsonify({"success": True, **issued}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Issue a password-reset token.
    Always returns 200 with the same generic message (no email enumeration).
    The token is NEVER included in the HTTP response, in any configuration:
    it is stored hashed and handed to deliver_reset_token().
    """
    data = _json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    User, db = _get_user_model()
    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.is_active:
            return jsonify(FORGOT_RESPONSE), 200

        token = secrets.token_urlsafe(32)
        user.reset_token = hash_reset_token(token)
        user.reset_token_expires = datetime.utcnow() + RESET_TOKEN_TTL
        db.session.commit()

        try:
            deliver_reset_token(user.email, token)
        except Exception:
            logger.exception("Password reset delivery failed")
        logger.info("Password reset token issued for user id=%s", user.id)
        return jsonify(FORGOT_RESPONSE), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": internal_error_message(e, public="Request failed. Please try again.")}), 500


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset password using a token from forgot-password."""
    data = _json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    token = (data.get("token") or data.get("reset_token") or "").strip()
    password = data.get("password") or data.get("new_password") or ""
    if not token:
        return jsonify({"error": "Reset token is required"}), 400
    if not _password_ok(password):
        return jsonify({"error": PASSWORD_TOO_SHORT}), 400

    User, db = _get_user_model()
    try:
        token_hash = hash_reset_token(token)
        user = User.query.filter_by(reset_token=token_hash).first()
        if not user or not user.reset_token or not hmac.compare_digest(user.reset_token, token_hash):
            return jsonify({"error": INVALID_RESET_TOKEN}), 400
        # Tokens without an expiry (legacy rows) or past it are rejected and cleared.
        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            return jsonify({"error": INVALID_RESET_TOKEN}), 400

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return jsonify({"success": True, "message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": internal_error_message(e, public="Reset failed. Please try again.")}), 500
