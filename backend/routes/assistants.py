"""
REST endpoints for specialized assistants (Search, File, Function).
Used by TaskAssistant step execution and direct API clients.
"""
from __future__ import annotations

import logging
import os

from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
assistants_bp = Blueprint("assistants", __name__)


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def _message_from(data: dict) -> str:
    return (
        data.get("message")
        or data.get("query")
        or data.get("instruction")
        or data.get("text")
        or ""
    ).strip()


@assistants_bp.route("/health", methods=["GET"])
def assistants_health():
    return jsonify({
        "service": "assistants",
        "status": "healthy",
        "agents": ["search", "file", "function", "concierge"],
    }), 200


@assistants_bp.route("/search", methods=["POST"])
def assistants_search():
    data = _payload()
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    message = _message_from(data)
    if not message:
        return jsonify({"error": "message/query is required"}), 400

    try:
        # Prefer Google SearchAgent when keys exist; else Concierge document/SBA path
        try:
            from backend.assistants.search import SearchAgent
            agent = SearchAgent()
            result = agent.handle_message(message, session_id=data.get("session_id"))
        except (ValueError, Exception) as search_err:
            logger.warning("SearchAgent unavailable (%s); using Concierge", search_err)
            from backend.assistants.concierge import Concierge
            result = Concierge().handle_message(message, session_id=data.get("session_id"))
        return jsonify(result), 200 if not result.get("error") else 200
    except Exception as e:
        logger.exception("assistants/search failed")
        return jsonify({"error": str(e), "success": False, "text": str(e)}), 500


@assistants_bp.route("/file", methods=["POST"])
def assistants_file():
    data = _payload()
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    message = _message_from(data) or "list files"
    try:
        from backend.assistants.file import FileAgent
        agent = FileAgent()
        result = agent.handle_message(message, session_id=data.get("session_id"))
        return jsonify(result), 200
    except Exception as e:
        logger.exception("assistants/file failed")
        return jsonify({"error": str(e), "success": False, "text": str(e)}), 500


@assistants_bp.route("/function", methods=["POST"])
def assistants_function():
    data = _payload()
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    message = _message_from(data)
    if not message:
        return jsonify({"error": "message/instruction is required"}), 400
    try:
        from backend.assistants.function import FunctionAgent
        agent = FunctionAgent()
        result = agent.handle_message(message, session_id=data.get("session_id"))
        return jsonify(result), 200
    except Exception as e:
        logger.exception("assistants/function failed")
        return jsonify({"error": str(e), "success": False, "text": str(e)}), 500


@assistants_bp.route("/concierge", methods=["POST"])
def assistants_concierge():
    data = _payload()
    if data is None:
        return jsonify({"error": "JSON body required"}), 400
    message = _message_from(data)
    if not message:
        return jsonify({"error": "message is required"}), 400
    try:
        from backend.assistants.concierge import Concierge
        result = Concierge().handle_message(message, session_id=data.get("session_id"))
        return jsonify(result), 200
    except Exception as e:
        logger.exception("assistants/concierge failed")
        return jsonify({"error": str(e), "success": False, "text": str(e)}), 500
