"""
Authentication routes — register, login, forgot/reset password.
Persists users via Flask-SQLAlchemy User model.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


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
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    User, db = _get_user_model()
    try:
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({"error": "An account with this email already exists"}), 409

        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        logger.info("Registered user %s", email)
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": user.to_public_dict(),
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An account with this email already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logger.exception("Register failed")
        return jsonify({"error": f"Registration failed: {e}"}), 500


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

        # Lightweight opaque token (dev-friendly; swap for JWT in production if needed)
        token = secrets.token_urlsafe(32)
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": user.to_public_dict(),
        }), 200
    except Exception as e:
        logger.exception("Login failed")
        return jsonify({"error": f"Login failed: {e}"}), 500


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Issue a password-reset token.
    Always returns 200 with a generic message to avoid email enumeration.
    In development, includes reset_token in the response when the user exists
    so the UI can complete the flow without email infrastructure.
    """
    data = _json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    User, db = _get_user_model()
    generic = {
        "success": True,
        "message": "If this email is registered, you will receive password reset instructions.",
    }
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify(generic), 200

        token = secrets.token_urlsafe(24)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=2)
        db.session.commit()

        payload = dict(generic)
        # Dev / no-mail mode: return token so the product is usable
        if current_app.config.get("DEBUG", True):
            payload["reset_token"] = token
            payload["dev_note"] = "Token returned because DEBUG is on (no email gateway configured)."
        logger.info("Password reset token issued for %s", email)
        return jsonify(payload), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Forgot password failed")
        return jsonify({"error": f"Request failed: {e}"}), 500


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
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    User, db = _get_user_model()
    try:
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return jsonify({"error": "Invalid or expired reset token"}), 400
        if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            return jsonify({"error": "Reset token has expired"}), 400

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return jsonify({"success": True, "message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Reset password failed")
        return jsonify({"error": f"Reset failed: {e}"}), 500
