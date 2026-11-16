"""Calendar (appointments) + Tasks (to-dos) API and the chat action parser."""
from datetime import datetime

import pytest

from backend.app import create_app
from backend.models.chat import db
from backend.services.planner_nlp import parse_appointment, parse_todos, suggest_next_step, is_yes
from backend.tests.auth_helpers import auth_header

NOW = datetime(2026, 10, 24, 18, 12)  # a Saturday evening


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'planner.db'}")
    app = create_app("testing")
    app.config.update(TESTING=True, AUTH_REQUIRED=True, SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'planner.db'}")
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def owner(app):
    return auth_header(app)


@pytest.fixture
def other(app):
    return auth_header(app, email="someone-else@example.com")


def _appt(client, headers, **kw):
    body = {"title": "Band rehearsal", "start": "2026-10-31T15:00", "duration_minutes": 120,
            "contact": "The Night Owls", "notes": "Room 2"}
    body.update(kw)
    return client.post("/api/appointments", json=body, headers=headers)


# --- auth ------------------------------------------------------------------

@pytest.mark.parametrize("method,url", [
    ("get", "/api/appointments"), ("post", "/api/appointments"),
    ("put", "/api/appointments/1"), ("delete", "/api/appointments/1"),
    ("get", "/api/todos"), ("post", "/api/todos"), ("put", "/api/todos/1"),
    ("delete", "/api/todos/1"), ("get", "/api/planner/summary"),
])
def test_routes_need_sign_in(client, method, url):
    resp = getattr(client, method)(url, json={})
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "token_missing"


# --- appointments ------------------------------------------------------------

def test_appointment_crud(client, owner):
    resp = _appt(client, owner)
    assert resp.status_code == 201
    appt = resp.get_json()["appointment"]
    assert appt["title"] == "Band rehearsal"
    assert appt["start"] == "2026-10-31T15:00"
    assert appt["duration_minutes"] == 120
    assert appt["contact"] == "The Night Owls"

    listed = client.get("/api/appointments", headers=owner).get_json()
    assert [a["id"] for a in listed["appointments"]] == [appt["id"]]

    upd = client.put(f"/api/appointments/{appt['id']}", json={"start": "2026-10-31T16:30", "notes": ""}, headers=owner)
    assert upd.status_code == 200
    assert upd.get_json()["appointment"]["start"] == "2026-10-31T16:30"
    assert upd.get_json()["appointment"]["title"] == "Band rehearsal"  # partial update keeps the rest

    assert client.get(f"/api/appointments/{appt['id']}", headers=owner).status_code == 200
    assert client.delete(f"/api/appointments/{appt['id']}", headers=owner).status_code == 200
    assert client.get(f"/api/appointments/{appt['id']}", headers=owner).status_code == 404


def test_appointment_range_filter_and_order(client, owner):
    _appt(client, owner, title="Later", start="2026-11-05T10:00")
    _appt(client, owner, title="Sooner", start="2026-10-26T09:00")
    _appt(client, owner, title="Out of range", start="2026-12-01T09:00")
    got = client.get("/api/appointments?from=2026-10-26&to=2026-11-05", headers=owner).get_json()
    assert [a["title"] for a in got["appointments"]] == ["Sooner", "Later"]


@pytest.mark.parametrize("body,field", [
    ({"title": "", "start": "2026-10-31T15:00"}, "title"),
    ({"title": "x", "start": "next week"}, "start"),
    ({"title": "x", "start": "2026-10-31T15:00", "duration_minutes": 0}, "duration_minutes"),
    ({"title": "x" * 201, "start": "2026-10-31T15:00"}, "title"),
])
def test_appointment_validation(client, owner, body, field):
    resp = client.post("/api/appointments", json=body, headers=owner)
    assert resp.status_code == 400
    assert resp.get_json()["field"] == field


def test_users_only_see_their_own_rows(client, owner, other):
    appt = _appt(client, owner).get_json()["appointment"]
    todo = client.post("/api/todos", json={"title": "Mine"}, headers=owner).get_json()["todo"]
    assert client.get("/api/appointments", headers=other).get_json()["appointments"] == []
    assert client.get("/api/todos", headers=other).get_json()["todos"] == []
    assert client.put(f"/api/appointments/{appt['id']}", json={"title": "x"}, headers=other).status_code == 404
    assert client.delete(f"/api/appointments/{appt['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/todos/{todo['id']}", headers=other).status_code == 404
    # and can't link a task to someone else's appointment
    resp = client.post("/api/todos", json={"title": "x", "appointment_id": appt["id"]}, headers=other)
    assert resp.status_code == 400


# --- todos ---------------------------------------------------------------------

def test_todo_crud_and_link(client, owner):
    appt = _appt(client, owner).get_json()["appointment"]
    resp = client.post("/api/todos", json={"title": "Restring house guitar", "due_date": "2026-10-30",
                                           "appointment_id": appt["id"]}, headers=owner)
    assert resp.status_code == 201
    todo = resp.get_json()["todo"]
    assert todo == {"id": todo["id"], "title": "Restring house guitar", "due_date": "2026-10-30",
                    "done": False, "appointment_id": appt["id"]}

    done = client.patch(f"/api/todos/{todo['id']}", json={"done": True}, headers=owner).get_json()["todo"]
    assert done["done"] is True and done["title"] == "Restring house guitar"
    assert client.get("/api/todos?done=false", headers=owner).get_json()["todos"] == []

    # deleting the appointment keeps the task, unlinked
    client.delete(f"/api/appointments/{appt['id']}", headers=owner)
    left = client.get("/api/todos", headers=owner).get_json()["todos"]
    assert left[0]["appointment_id"] is None

    assert client.delete(f"/api/todos/{todo['id']}", headers=owner).status_code == 200
    assert client.get("/api/todos", headers=owner).get_json()["todos"] == []


def test_todo_validation(client, owner):
    assert client.post("/api/todos", json={"title": "  "}, headers=owner).status_code == 400
    assert client.post("/api/todos", json={"title": "x", "due_date": "soon"}, headers=owner).status_code == 400
    assert client.post("/api/todos", data="nope", headers=owner).status_code == 400


def test_todos_sort_open_first_then_due(client, owner):
    for title, due in [("No date", None), ("Late", "2026-11-09"), ("Early", "2026-10-26")]:
        client.post("/api/todos", json={"title": title, "due_date": due}, headers=owner)
    finished = client.post("/api/todos", json={"title": "Finished", "due_date": "2026-10-01"}, headers=owner).get_json()["todo"]
    client.patch(f"/api/todos/{finished['id']}", json={"done": True}, headers=owner)
    titles = [t["title"] for t in client.get("/api/todos", headers=owner).get_json()["todos"]]
    assert titles == ["Early", "Late", "No date", "Finished"]


def test_summary_upcoming_and_overdue(client, owner):
    _appt(client, owner, title="Tomorrow's lockout", start="2026-10-25T12:00")
    _appt(client, owner, title="Next month", start="2026-11-20T12:00")
    client.post("/api/todos", json={"title": "Pay PA rental", "due_date": "2026-10-20"}, headers=owner)
    client.post("/api/todos", json={"title": "Future", "due_date": "2026-11-20"}, headers=owner)
    s = client.get("/api/planner/summary?now=2026-10-24T18:12", headers=owner).get_json()
    assert [a["title"] for a in s["upcoming"]] == ["Tomorrow's lockout"]
    assert [t["title"] for t in s["overdue"]] == ["Pay PA rental"]


def test_demo_mode_without_auth_still_works(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'demo.db'}")
    app = create_app("testing")
    app.config.update(AUTH_REQUIRED=False, SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'demo.db'}")
    c = app.test_client()
    assert c.post("/api/todos", json={"title": "Demo task"}).status_code == 201
    assert len(c.get("/api/todos").get_json()["todos"]) >= 1


# --- parser ------------------------------------------------------------------

def test_parse_band_rehearsal():
    got = parse_appointment("book a band rehearsal Saturday 3pm, 2 hours", NOW)
    # It's already past 3pm on Saturday, so this means next Saturday.
    assert got == {"title": "Band rehearsal", "start": "2026-10-31T15:00", "duration_minutes": 120,
                   "contact": "", "notes": ""}


@pytest.mark.parametrize("msg,title,start,minutes,contact", [
    ("Book band rehearsal with Mike Saturday at 3pm for 2 hours", "Band rehearsal", "2026-10-31T15:00", 120, "Mike"),
    ("schedule a call with the SBDC tomorrow at 10am", "Call with the SBDC", "2026-10-25T10:00", 60, "the SBDC"),
    ("Book Studio B tour with Jazz Collective next Friday 7:30pm for 90 minutes", "Studio B tour", "2026-10-30T19:30", 90, "Jazz Collective"),
    ("put drum tech visit on my calendar Oct 30 at noon", "Drum tech visit", "2026-10-30T12:00", 60, ""),
    ("book vocal session today at 8pm for an hour and a half", "Vocal session", "2026-10-24T20:00", 90, ""),
    ("Schedule an appointment for lender meeting 11/2 at 2pm 45 min", "Lender meeting", "2026-11-02T14:00", 45, ""),
])
def test_parse_appointment_variants(msg, title, start, minutes, contact):
    got = parse_appointment(msg, NOW)
    assert (got["title"], got["start"], got["duration_minutes"], got["contact"]) == (title, start, minutes, contact)


@pytest.mark.parametrize("msg", ["What is an SBA 7(a) loan?", "book a meeting", "How do I write a business plan?"])
def test_non_bookings_are_not_parsed(msg):
    assert parse_appointment(msg, NOW) is None


def test_parse_todos():
    assert parse_todos("remind me to call the bank on Monday", NOW) == {
        "items": [{"title": "Call the bank", "due_date": "2026-10-26"}]}
    assert parse_todos("add gather tax returns to my tasks", NOW) == {
        "items": [{"title": "Gather tax returns", "due_date": None}]}
    many = parse_todos("Help me plan these tasks: fix the PA in room 2, order cables, call the landlord by Wednesday", NOW)
    assert [i["title"] for i in many["items"]] == ["Fix the PA in room 2", "Order cables", "Call the landlord"]
    assert many["items"][2]["due_date"] == "2026-10-28"
    assert parse_todos("What is a microloan?", NOW) is None


def test_next_step_suggestions():
    q, action = suggest_next_step("How do I prepare a loan application?", None, NOW)
    assert "tax returns" in q and action["type"] == "todo"
    q, action = suggest_next_step("anything", "local_help", NOW)
    assert action["type"] == "appointment" and action["data"]["start"] == "2026-10-26T10:00"  # Monday, not Sunday
    assert is_yes("Yes please") and is_yes("sure") and not is_yes("yes but what about grants?")
