"""
Safe error responses for route handlers.

Route handlers must never send raw exception text (``str(e)``) to clients:
it can leak stack details, file paths, SQL, or upstream API messages.
``internal_error_message`` logs the full exception server-side (with
traceback) and returns a short, generic message for the response body.
"""
from __future__ import annotations

import logging
import sys

from werkzeug.exceptions import HTTPException

logger = logging.getLogger("backend.routes.errors")

GENERIC_ERROR = "An internal error occurred. Please try again later."


def internal_error_message(exc: BaseException, public: str = GENERIC_ERROR, context: str | None = None) -> str:
    """Log ``exc`` with its traceback and return a client-safe message.

    HTTP errors raised by Flask/Werkzeug (for example 413 Request Entity Too
    Large while reading an upload) are re-raised so their own handlers answer
    with the right status code instead of a generic 500.
    """
    if isinstance(exc, HTTPException):
        raise exc
    if context is None:
        try:
            context = sys._getframe(1).f_code.co_name  # calling route function
        except Exception:  # pragma: no cover - CPython always has frames
            context = "request"
    logger.error("%s failed: %s", context, exc, exc_info=(type(exc), exc, exc.__traceback__))
    return public
