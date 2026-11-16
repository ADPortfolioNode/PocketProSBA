"""Appointments (calendar) and to-dos (tasks) for the signed-in business owner.

Times are stored as the owner's local wall-clock time (naive datetimes), the
way they typed them: "Saturday 3pm" is saved as 15:00 and shown as 15:00.
Each row belongs to one user (``user_id``); the API only ever returns the
caller's own rows.
"""
from datetime import datetime

from backend.models.chat import db

TITLE_MAX = 200
CONTACT_MAX = 200
NOTES_MAX = 2000


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(TITLE_MAX), nullable=False)
    start = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    contact = db.Column(db.String(CONTACT_MAX))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.strftime("%Y-%m-%dT%H:%M") if self.start else None,
            "duration_minutes": self.duration_minutes,
            "contact": self.contact or "",
            "notes": self.notes or "",
        }


class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(TITLE_MAX), nullable=False)
    due_date = db.Column(db.Date)
    done = db.Column(db.Boolean, nullable=False, default=False)
    # Deleting the appointment keeps the task and just drops the link.
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "done": bool(self.done),
            "appointment_id": self.appointment_id,
        }
