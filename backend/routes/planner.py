"""Calendar (appointments) and Tasks (to-dos) API.

    GET    /api/appointments?from=YYYY-MM-DD&to=YYYY-MM-DD
    POST   /api/appointments            {title, start "YYYY-MM-DDTHH:MM", duration_minutes, contact, notes}
    GET    /api/appointments/<id>
    PUT    /api/appointments/<id>       (PATCH too; any subset of the fields)
    DELETE /api/appointments/<id>

    GET    /api/todos                   ?done=true|false
    POST   /api/todos                   {title, due_date "YYYY-MM-DD"|null, done, appointment_id}
    PUT    /api/todos/<id>              (PATCH too)
    DELETE /api/todos/<id>

    GET    /api/planner/summary?now=YYYY-MM-DDTHH:MM   upcoming (next 48h) + overdue, for chat nudges

All routes need a signed-in user (``auth_required``) and only see that user's
rows. Validation errors answer 400 {"error": "...", "field": "..."}; another
user's id answers 404.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from flask import Blueprint, g, jsonify, request

from backend.app.auth import AuthError, auth_required, authenticate_request
from backend.models.chat import db
from backend.models.planner import CONTACT_MAX, NOTES_MAX, TITLE_MAX, Appointment, Todo
from backend.routes._errors import internal_error_message
from backend.services.planner_nlp import parse_client_now

logger = logging.getLogger(__name__)
planner_bp = Blueprint("planner", __name__)

# AUTH_REQUIRED=false (local demo) with no token: rows belong to this shared id.
DEMO_USER_ID = 0


class ValidationError(Exception):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


def current_user_id() -> int:
    user = getattr(g, "current_user", None)
    if user is not None:
        return int(user.id)
    # Auth enforcement is off: still honour a valid token if one was sent.
    try:
        return int(authenticate_request().id)
    except AuthError:
        return DEMO_USER_ID
    except Exception:  # pragma: no cover - defensive
        return DEMO_USER_ID


def _bad(err: ValidationError):
    body = {"error": err.message, "success": False}
    if err.field:
        body["field"] = err.field
    return jsonify(body), 400


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Please send the details as JSON.")
    return data


def _text(data, key, max_len, required=False, label=None):
    label = label or key
    val = data.get(key)
    if val is None:
        if required:
            raise ValidationError(f"Please add a {label}.", key)
        return None
    if not isinstance(val, str):
        raise ValidationError(f"The {label} should be text.", key)
    val = val.strip()
    if required and not val:
        raise ValidationError(f"Please add a {label}.", key)
    if len(val) > max_len:
        raise ValidationError(f"The {label} is too long (max {max_len} characters).", key)
    return val


def _parse_start(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Please pick a date and time.", "start")
    txt = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(txt[:19] if "S" in fmt else txt[:16], fmt)
        except ValueError:
            continue
    raise ValidationError("That date and time doesn't look right (use YYYY-MM-DDTHH:MM).", "start")


def _parse_date(value, field="due_date"):
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError("That date doesn't look right (use YYYY-MM-DD).", field)
    try:
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("That date doesn't look right (use YYYY-MM-DD).", field)


def _parse_duration(value):
    if value in (None, ""):
        return 60
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Duration should be a number of minutes.", "duration_minutes")
    if minutes < 5 or minutes > 24 * 60:
        raise ValidationError("Duration should be between 5 minutes and 24 hours.", "duration_minutes")
    return minutes


def _apply_appointment(appt: Appointment, data: dict, partial: bool):
    if not partial or "title" in data:
        appt.title = _text(data, "title", TITLE_MAX, required=True, label="title")
    if not partial or "start" in data:
        appt.start = _parse_start(data.get("start"))
    if not partial or "duration_minutes" in data:
        appt.duration_minutes = _parse_duration(data.get("duration_minutes"))
    if "contact" in data or not partial:
        appt.contact = _text(data, "contact", CONTACT_MAX, label="client or contact") or None
    if "notes" in data or not partial:
        appt.notes = _text(data, "notes", NOTES_MAX, label="notes") or None


def _own_appointment(appt_id: int, uid: int):
    appt = db.session.get(Appointment, appt_id)
    if appt is None or appt.user_id != uid:
        return None
    return appt


def _own_todo(todo_id: int, uid: int):
    todo = db.session.get(Todo, todo_id)
    if todo is None or todo.user_id != uid:
        return None
    return todo


def _not_found(what):
    return jsonify({"error": f"That {what} wasn't found.", "success": False}), 404


def _server_error(e, context):
    db.session.rollback()
    return jsonify({"error": internal_error_message(e, context=context), "success": False}), 500


# --- appointments ---------------------------------------------------------

@planner_bp.route("/appointments", methods=["GET"])
@auth_required
def list_appointments():
    uid = current_user_id()
    try:
        q = Appointment.query.filter_by(user_id=uid)
        start = _parse_date(request.args.get("from"), "from")
        end = _parse_date(request.args.get("to"), "to")
        if start:
            q = q.filter(Appointment.start >= datetime.combine(start, datetime.min.time()))
        if end:
            q = q.filter(Appointment.start < datetime.combine(end + timedelta(days=1), datetime.min.time()))
        items = [a.to_dict() for a in q.order_by(Appointment.start.asc()).all()]
        return jsonify({"success": True, "appointments": items, "count": len(items)}), 200
    except ValidationError as err:
        return _bad(err)
    except Exception as e:
        return _server_error(e, "list appointments")


@planner_bp.route("/appointments", methods=["POST"])
@auth_required
def create_appointment():
    uid = current_user_id()
    try:
        data = _json_body()
        appt = Appointment(user_id=uid)
        _apply_appointment(appt, data, partial=False)
        db.session.add(appt)
        db.session.commit()
        return jsonify({"success": True, "appointment": appt.to_dict()}), 201
    except ValidationError as err:
        return _bad(err)
    except Exception as e:
        return _server_error(e, "create appointment")


@planner_bp.route("/appointments/<int:appt_id>", methods=["GET"])
@auth_required
def get_appointment(appt_id):
    appt = _own_appointment(appt_id, current_user_id())
    if appt is None:
        return _not_found("appointment")
    return jsonify({"success": True, "appointment": appt.to_dict()}), 200


@planner_bp.route("/appointments/<int:appt_id>", methods=["PUT", "PATCH"])
@auth_required
def update_appointment(appt_id):
    appt = _own_appointment(appt_id, current_user_id())
    if appt is None:
        return _not_found("appointment")
    try:
        data = _json_body()
        _apply_appointment(appt, data, partial=True)
        db.session.commit()
        return jsonify({"success": True, "appointment": appt.to_dict()}), 200
    except ValidationError as err:
        db.session.rollback()
        return _bad(err)
    except Exception as e:
        return _server_error(e, "update appointment")


@planner_bp.route("/appointments/<int:appt_id>", methods=["DELETE"])
@auth_required
def delete_appointment(appt_id):
    uid = current_user_id()
    appt = _own_appointment(appt_id, uid)
    if appt is None:
        return _not_found("appointment")
    try:
        # SQLite doesn't enforce ON DELETE SET NULL by default: unlink by hand.
        Todo.query.filter_by(user_id=uid, appointment_id=appt.id).update({"appointment_id": None})
        db.session.delete(appt)
        db.session.commit()
        return jsonify({"success": True, "deleted": appt_id}), 200
    except Exception as e:
        return _server_error(e, "delete appointment")


# --- todos ----------------------------------------------------------------

def _apply_todo(todo: Todo, data: dict, partial: bool, uid: int):
    if not partial or "title" in data:
        todo.title = _text(data, "title", TITLE_MAX, required=True, label="task")
    if not partial or "due_date" in data:
        todo.due_date = _parse_date(data.get("due_date"))
    if "done" in data:
        if not isinstance(data.get("done"), bool):
            raise ValidationError("Done should be true or false.", "done")
        todo.done = data["done"]
    elif not partial:
        todo.done = False
    if "appointment_id" in data:
        aid = data.get("appointment_id")
        if aid in (None, ""):
            todo.appointment_id = None
        else:
            try:
                aid = int(aid)
            except (TypeError, ValueError):
                raise ValidationError("That appointment wasn't found.", "appointment_id")
            if _own_appointment(aid, uid) is None:
                raise ValidationError("That appointment wasn't found.", "appointment_id")
            todo.appointment_id = aid


def _todo_sort_key(t: Todo):
    return (bool(t.done), t.due_date is None, t.due_date or date.max, t.id)


@planner_bp.route("/todos", methods=["GET"])
@auth_required
def list_todos():
    uid = current_user_id()
    try:
        q = Todo.query.filter_by(user_id=uid)
        done = (request.args.get("done") or "").lower()
        if done in ("true", "1", "yes"):
            q = q.filter_by(done=True)
        elif done in ("false", "0", "no"):
            q = q.filter_by(done=False)
        items = [t.to_dict() for t in sorted(q.all(), key=_todo_sort_key)]
        return jsonify({"success": True, "todos": items, "count": len(items)}), 200
    except Exception as e:
        return _server_error(e, "list tasks")


@planner_bp.route("/todos", methods=["POST"])
@auth_required
def create_todo():
    uid = current_user_id()
    try:
        data = _json_body()
        todo = Todo(user_id=uid)
        _apply_todo(todo, data, partial=False, uid=uid)
        db.session.add(todo)
        db.session.commit()
        return jsonify({"success": True, "todo": todo.to_dict()}), 201
    except ValidationError as err:
        db.session.rollback()
        return _bad(err)
    except Exception as e:
        return _server_error(e, "create task")


@planner_bp.route("/todos/<int:todo_id>", methods=["PUT", "PATCH"])
@auth_required
def update_todo(todo_id):
    uid = current_user_id()
    todo = _own_todo(todo_id, uid)
    if todo is None:
        return _not_found("task")
    try:
        data = _json_body()
        _apply_todo(todo, data, partial=True, uid=uid)
        db.session.commit()
        return jsonify({"success": True, "todo": todo.to_dict()}), 200
    except ValidationError as err:
        db.session.rollback()
        return _bad(err)
    except Exception as e:
        return _server_error(e, "update task")


@planner_bp.route("/todos/<int:todo_id>", methods=["DELETE"])
@auth_required
def delete_todo(todo_id):
    todo = _own_todo(todo_id, current_user_id())
    if todo is None:
        return _not_found("task")
    try:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({"success": True, "deleted": todo_id}), 200
    except Exception as e:
        return _server_error(e, "delete task")


# --- summary for chat nudges ---------------------------------------------

@planner_bp.route("/planner/summary", methods=["GET"])
@auth_required
def planner_summary():
    """Next 48 hours of appointments and overdue open tasks (client local time)."""
    uid = current_user_id()
    try:
        now = parse_client_now(request.args.get("now"))
        horizon = now + timedelta(hours=48)
        upcoming = (
            Appointment.query.filter_by(user_id=uid)
            .filter(Appointment.start >= now - timedelta(minutes=30), Appointment.start <= horizon)
            .order_by(Appointment.start.asc())
            .limit(5)
            .all()
        )
        overdue = (
            Todo.query.filter_by(user_id=uid, done=False)
            .filter(Todo.due_date.isnot(None), Todo.due_date < now.date())
            .order_by(Todo.due_date.asc())
            .limit(5)
            .all()
        )
        due_today = (
            Todo.query.filter_by(user_id=uid, done=False)
            .filter(Todo.due_date == now.date())
            .count()
        )
        return jsonify({
            "success": True,
            "now": now.strftime("%Y-%m-%dT%H:%M"),
            "upcoming": [a.to_dict() for a in upcoming],
            "overdue": [t.to_dict() for t in overdue],
            "due_today": due_today,
        }), 200
    except Exception as e:
        return _server_error(e, "planner summary")
