"""The concierge's "do something" layer, applied around the chat answer.

Before the normal concierge answer (``pre_route``):
  - "yes" right after the concierge offered a next step -> re-offers that action
  - "book a band rehearsal Saturday 3pm, 2 hours"     -> proposed appointment
  - "add call the landlord to my tasks"                -> proposed task(s)
  - a question about an uploaded document              -> grounded, cited answer

After it (``add_next_step``): one concrete next step the concierge can take,
as a question at the end of the answer plus a ``suggested_action``.

Nothing here writes to the calendar or task list. Proposals come back as
``proposed_action`` / ``suggested_action`` and the UI asks the owner to
confirm before it calls /api/appointments or /api/todos.
"""
from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from datetime import datetime

from backend.services import planner_nlp

logger = logging.getLogger(__name__)

_MAX_SESSIONS = 500
_last_offer: "OrderedDict[str, dict]" = OrderedDict()
_lock = threading.Lock()


def _remember_offer(session_id: str, action: dict | None):
    if not session_id:
        return
    with _lock:
        if action is None:
            _last_offer.pop(session_id, None)
            return
        _last_offer[session_id] = action
        _last_offer.move_to_end(session_id)
        while len(_last_offer) > _MAX_SESSIONS:
            _last_offer.popitem(last=False)


def _take_offer(session_id: str):
    with _lock:
        return _last_offer.pop(session_id, None) if session_id else None


def _fmt_when(start: str) -> str:
    try:
        dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return start or ""
    hour = dt.strftime("%I").lstrip("0") or "12"
    minute = "" if dt.minute == 0 else dt.strftime(":%M")
    return f"{dt.strftime('%A, %B')} {dt.day} at {hour}{minute} {dt.strftime('%p').lower()}"


def _fmt_minutes(m: int) -> str:
    if m % 60 == 0:
        h = m // 60
        return f"{h} hour{'s' if h != 1 else ''}"
    if m > 60:
        return f"{m // 60} h {m % 60} min"
    return f"{m} minutes"


def _reply(session_id, text, action=None, **extra):
    body = {
        "success": True,
        "response": text,
        "message": text,
        "answer": text,
        "sources": extra.pop("sources", []),
        "session_id": session_id or "default",
        "timestamp": datetime.now().isoformat(),
    }
    if action:
        body["proposed_action"] = action
    body.update(extra)
    return body


def describe_action(action: dict) -> str:
    data = action.get("data") or {}
    if action.get("type") == "appointment":
        who = f" with {data['contact']}" if data.get("contact") else ""
        return (f"**{data.get('title', 'Appointment')}**{who} on {_fmt_when(data.get('start'))} "
                f"({_fmt_minutes(int(data.get('duration_minutes') or 60))})")
    items = data.get("items") or []
    return ", ".join(f"**{i['title']}**" for i in items)


def pre_route(message: str, payload: dict, session_id: str):
    """A full chat response for action/document requests, or None to let the concierge answer."""
    now = planner_nlp.parse_client_now(payload.get("client_now"))
    workflow = payload.get("workflow") or None
    document = payload.get("document") or None

    if planner_nlp.is_yes(message):
        offer = _take_offer(session_id)
        if offer:
            where = "calendar" if offer["type"] == "appointment" else "task list"
            return _reply(session_id, f"Great! Here it is: {describe_action(offer)}. "
                                      f"Check the details and tap confirm to add it to your {where}.", offer)

    appt = planner_nlp.parse_appointment(message, now)
    if appt:
        action = {"type": "appointment", "data": appt}
        _remember_offer(session_id, None)
        return _reply(
            session_id,
            f"Happy to set that up: {describe_action(action)}. "
            "Check the details below and tap **Add to calendar**, or change anything first.",
            action,
        )

    todos = planner_nlp.parse_todos(message, now)
    if todos:
        action = {"type": "todo", "data": todos}
        n = len(todos["items"])
        _remember_offer(session_id, None)
        return _reply(
            session_id,
            (f"Got it. I'll add {describe_action(action)} to your tasks." if n == 1
             else f"Here's your list, {n} tasks: {describe_action(action)}.")
            + " Tap **Add to tasks** to confirm.",
            action,
        )

    from backend.services import doc_qa

    if doc_qa.wants_documents(message, workflow, document):
        try:
            result = doc_qa.answer(message, document=document)
        except Exception as err:
            logger.warning("document answer failed: %s", err)
            result = None
        if result:
            body = _reply(session_id, result["text"], sources=result["sources"],
                          grounded=True, document=result.get("document"), answer_mode=result.get("mode"))
            return add_next_step(body, message, workflow, session_id, now)
        if workflow == "doc_qa" or document:
            return _reply(session_id, "I don't see any uploaded documents yet. Tap the 📎 button below "
                                      "to upload a PDF, Word or text file, and I'll read it for you.")
    return None


def add_next_step(response: dict, message: str, workflow: str | None, session_id: str, now: datetime | None = None):
    """End the answer with one concrete next step and attach it as ``suggested_action``."""
    if not isinstance(response, dict) or response.get("proposed_action"):
        return response
    try:
        question, action = planner_nlp.suggest_next_step(message, workflow, now)
    except Exception as err:  # never let a suggestion break an answer
        logger.debug("next step suggestion failed: %s", err)
        return response
    text = str(response.get("response") or response.get("message") or "").rstrip()
    if question not in text:
        text = f"{text}\n\n**Next step:** {question}" if text else question
    response["response"] = response["message"] = response["answer"] = text
    response["suggested_action"] = action
    _remember_offer(session_id, action)
    return response
