"""Turn plain-English chat requests into *proposed* calendar/task actions.

Nothing here writes to the database. The chat answer carries a proposal
(``proposed_action``) and the UI asks the owner to confirm before it calls the
appointments/todos API.

    parse_appointment("book a band rehearsal Saturday 3pm, 2 hours", now)
    -> {"title": "Band rehearsal", "start": "2026-10-31T15:00", "duration_minutes": 120, ...}

Dates resolve against ``now``: the client's local time when it sends one
(``client_now``), otherwise the server clock.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_ABBR = {d[:3]: i for i, d in enumerate(WEEKDAYS)}
WEEKDAY_ABBR.update({"tues": 1, "thur": 3, "thurs": 3})
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}
MONTH_ABBR = {m[:3]: n for m, n in MONTHS.items()}
MONTH_ABBR["sept"] = 9

_DAY_NAME = r"(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day|nesday|sday|urday|rsday)?"
_MONTH_NAME = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

APPOINTMENT_VERBS = re.compile(
    r"\b(book|schedule|reschedule|set up|setup|put|add|create|make|plan)\b.*"
    r"|\b(appointment|meeting|rehearsal|session|call|consultation|calendar)\b",
    re.I,
)
TODO_PATTERNS = [
    re.compile(r"^\s*(?:please\s+)?(?:can you\s+|could you\s+)?add\s+(?:a\s+)?(?:task|to-?do)\s*(?:to|:|-|for)?\s*(?P<t>.+)$", re.I),
    re.compile(r"^\s*(?:please\s+)?(?:can you\s+|could you\s+)?add\s+(?P<t>.+?)\s+to\s+(?:my\s+)?(?:tasks?|to-?dos?|to-?do list|task list|list)\b(?P<rest>.*)$", re.I),
    re.compile(r"^\s*(?:please\s+)?remind me to\s+(?P<t>.+)$", re.I),
    re.compile(r"^\s*(?:new\s+)?(?:task|to-?do)\s*:\s*(?P<t>.+)$", re.I),
]
PLAN_TASKS = re.compile(r"^\s*help me plan (?:these|my) tasks\s*:?\s*(?P<t>.+)$", re.I | re.S)
YES = re.compile(r"^\s*(yes|yep|yeah|sure|ok|okay|please|please do|do it|go ahead|sounds good|yes please)[.! ]*$", re.I)


def parse_client_now(value) -> datetime:
    """Client local time ("2026-10-24T18:12[:ss][+/-hh:mm]") as a naive datetime."""
    if isinstance(value, str) and value.strip():
        txt = value.strip().replace("Z", "")
        txt = re.sub(r"[+-]\d{2}:?\d{2}$", "", txt)
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(txt, fmt)
            except ValueError:
                continue
    return datetime.now()


def is_yes(message: str) -> bool:
    return bool(YES.match(message or ""))


# --- pieces ---------------------------------------------------------------

def _find_time(text: str):
    """Return ((hour, minute), span) or (None, None)."""
    m = re.search(r"\b(noon|midday)\b", text, re.I)
    if m:
        return (12, 0), m.span()
    m = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)(?![a-z])", text, re.I)
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        ap = m.group(3).lower().replace(".", "")
        if 1 <= h <= 12 and mi < 60:
            if ap == "pm" and h != 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            return (h, mi), m.span()
    m = re.search(r"\bat\s+(\d{1,2}):(\d{2})\b", text, re.I) or re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if h < 24 and mi < 60:
            # "at 3:00" with no am/pm: business hours read as afternoon.
            if 1 <= h <= 7:
                h += 12
            return (h, mi), m.span()
    m = re.search(r"\bat\s+(\d{1,2})\b(?!\s*(?:hours?|hrs?|minutes?|mins?|/|-))", text, re.I)
    if m:
        h = int(m.group(1))
        if 1 <= h <= 12:
            if 1 <= h <= 7:
                h += 12
            return (h, 0), m.span()
    return None, None


def _find_date(text: str, now: datetime):
    """Return (date, span) or (None, None)."""
    today = now.date()
    m = re.search(r"\b(today|tonight|this evening)\b", text, re.I)
    if m:
        return today, m.span()
    m = re.search(r"\b(?:the\s+)?day after tomorrow\b", text, re.I)
    if m:
        return today + timedelta(days=2), m.span()
    m = re.search(r"\b(tomorrow|tmrw|tmr)\b", text, re.I)
    if m:
        return today + timedelta(days=1), m.span()
    m = re.search(r"\b(?:in\s+)?(\d{1,2})\s+days?\b", text, re.I)
    if m and text[m.start():m.start() + 2].lower() == "in":
        return today + timedelta(days=int(m.group(1))), m.span()
    m = re.search(r"\b(?:(next|this|on)\s+)?(" + _DAY_NAME + r")\b", text, re.I)
    if m:
        word = m.group(2).lower()
        idx = None
        for name, i in [(d, n) for n, d in enumerate(WEEKDAYS)]:
            if word == name:
                idx = i
        if idx is None:
            idx = WEEKDAY_ABBR.get(word[:5]) if word[:5] in WEEKDAY_ABBR else WEEKDAY_ABBR.get(word[:4], WEEKDAY_ABBR.get(word[:3]))
        if idx is not None:
            ahead = (idx - today.weekday()) % 7
            if (m.group(1) or "").lower() == "next" and ahead == 0:
                ahead = 7
            return today + timedelta(days=ahead), m.span()
    m = re.search(r"\b(" + _MONTH_NAME + r")\s+(\d{1,2})(?:st|nd|rd|th)?\b", text, re.I)
    if m:
        mon = MONTH_ABBR.get(m.group(1).lower().rstrip(".")[:4]) or MONTH_ABBR.get(m.group(1).lower()[:3])
        if mon:
            return _roll_year(today, mon, int(m.group(2))), m.span()
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
    if m:
        mon, day = int(m.group(1)), int(m.group(2))
        if m.group(3):
            year = int(m.group(3))
            year = year + 2000 if year < 100 else year
            try:
                return date(year, mon, day), m.span()
            except ValueError:
                return None, None
        return _roll_year(today, mon, day), m.span()
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))), m.span()
        except ValueError:
            return None, None
    return None, None


def _roll_year(today: date, month: int, day: int):
    try:
        d = date(today.year, month, day)
    except ValueError:
        return None
    if d < today:
        try:
            d = date(today.year + 1, month, day)
        except ValueError:
            return None
    return d


def _find_duration(text: str):
    """Return (minutes, span) or (None, None)."""
    m = re.search(r"\b(?:for\s+)?(?:an?|one)\s+hour\s+and\s+a\s+half\b", text, re.I) or \
        re.search(r"\b(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:-|\s)?(?:hours?|hrs?|h)\b(?!\w)", text, re.I)
    if m:
        if m.lastindex:
            return int(round(float(m.group(1)) * 60)), m.span()
        return 90, m.span()
    m = re.search(r"\b(?:for\s+)?(\d+)\s*(?:-|\s)?(?:minutes?|mins?|m)\b", text, re.I)
    if m:
        return int(m.group(1)), m.span()
    m = re.search(r"\b(?:for\s+)?(?:an?|one)\s+hour\b", text, re.I)
    if m:
        return 60, m.span()
    m = re.search(r"\b(?:for\s+)?(?:a\s+)?half(?:\s+an)?\s+hour\b", text, re.I)
    if m:
        return 30, m.span()
    return None, None


def _cut(text: str, spans):
    for start, end in sorted([s for s in spans if s], reverse=True):
        text = text[:start] + " " + text[end:]
    return text


def _blank(text: str, spans):
    chars = list(text)
    for span in spans:
        if span:
            for i in range(span[0], span[1]):
                chars[i] = " "
    return "".join(chars)


def _clean_title(text: str) -> str:
    t = re.sub(r"^\s*(?:please\s+)?(?:can you\s+|could you\s+|i need to\s+|i want to\s+|i'd like to\s+)?", "", text, flags=re.I)
    t = re.sub(r"^\s*(?:book|schedule|set up|setup|put|add|create|make|plan)\b\s*(?:me\s+)?(?:in\s+)?", "", t, flags=re.I)
    t = re.sub(r"\b(?:on|to|in)\s+(?:my|the)\s+calendar\b", " ", t, flags=re.I)
    t = re.sub(r"\b(?:an?\s+)?appointment\s+for\b", " ", t, flags=re.I)
    t = re.sub(r"^\s*(?:an?|the)\s+", "", t, flags=re.I)
    t = re.sub(r"\b(?:at|on|for|from|this|next)\s*([,.;]|$)", r"\1", t, flags=re.I)
    t = re.sub(r"\s+(?:at|on|for|from|this|next)\s*$", "", t, flags=re.I)
    t = re.sub(r"[\s,;.:-]+$", "", t)
    t = re.sub(r"^[\s,;.:-]+", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if t.lower() in ("", "an appointment", "appointment", "a meeting", "meeting"):
        t = "Appointment"
    return t[:1].upper() + t[1:200]


# --- public parsers -------------------------------------------------------

def parse_appointment(message: str, now: datetime | None = None):
    """A proposed appointment, or None when the message isn't a booking with a day or time."""
    if not message or not APPOINTMENT_VERBS.search(message):
        return None
    if not re.search(r"\b(book|schedule|reschedule|set up|setup|calendar|appointment|put .* on)\b", message, re.I):
        return None
    now = now or datetime.now()
    text = message.strip()
    tm, t_span = _find_time(text)
    dt, d_span = _find_date(text, now)
    if tm is None and dt is None:
        return None
    dur, dur_span = _find_duration(text)
    # Look for "with <who>" only in what is left once day/time/length are cut
    # out (same length, so spans still line up with ``text``).
    rest = _blank(text, [t_span, d_span, dur_span])
    contact = None
    m = re.search(r"\bwith\s+([A-Z][\w'.-]*(?:\s+[A-Z][\w'.-]*){0,3}|my\s+[a-z]+(?:\s+[a-z]+)?|the\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)", rest)
    c_span = None
    if m:
        contact = re.sub(r"[\s,;.]+$", "", m.group(1)).strip()
        c_span = m.span()
    said_today = bool(re.search(r"\b(today|tonight|this evening)\b", text, re.I))
    if dt is None:
        dt = now.date()
        if tm and (tm[0], tm[1]) <= (now.hour, now.minute):
            dt = dt + timedelta(days=1)
    elif dt == now.date() and not said_today and tm and (tm[0], tm[1]) <= (now.hour, now.minute):
        # "Saturday 3pm" said on Saturday evening means next Saturday.
        dt = dt + timedelta(days=7)
    if tm is None:
        tm = (10, 0)
    start = datetime(dt.year, dt.month, dt.day, tm[0], tm[1])
    title = _clean_title(_cut(text, [t_span, d_span, dur_span, c_span]))
    if contact and title.lower() in ("call", "meeting", "appointment", "session", "consultation"):
        title = f"{title} with {contact}"
    return {
        "title": title,
        "start": start.strftime("%Y-%m-%dT%H:%M"),
        "duration_minutes": max(5, min(dur or 60, 24 * 60)),
        "contact": contact or "",
        "notes": "",
    }


def _todo_from(text: str, now: datetime):
    dt, d_span = _find_date(text, now)
    title = text
    if d_span:
        title = _cut(text, [d_span])
        title = re.sub(r"\b(?:by|on|due|before)\s*$", "", title.strip(), flags=re.I)
        title = re.sub(r"\b(?:by|on|due|before)\s+([,.;]|$)", r"\1", title, flags=re.I)
    title = re.sub(r"[\s,;.:-]+$", "", title).strip().strip("'\"“”‘’")
    title = re.sub(r"\s{2,}", " ", title)
    if not title:
        return None
    return {"title": title[:1].upper() + title[1:200], "due_date": dt.isoformat() if dt else None}


def parse_todos(message: str, now: datetime | None = None):
    """A proposed list of to-dos ({"items": [...]}) or None."""
    if not message:
        return None
    now = now or datetime.now()
    m = PLAN_TASKS.match(message)
    if m:
        raw = m.group("t")
        parts = [p for p in re.split(r"\n|;|,|\band then\b|\band\b|•|\s-\s", raw) if p.strip()]
        items = [it for it in (_todo_from(p.strip(" -*•\t"), now) for p in parts) if it]
        return {"items": items[:10]} if items else None
    for pat in TODO_PATTERNS:
        m = pat.match(message.strip())
        if m:
            text = m.group("t")
            rest = (m.groupdict().get("rest") or "").strip()
            if rest:
                text = f"{text} {rest}"
            item = _todo_from(text.strip(), now)
            return {"items": [item]} if item else None
    return None


# --- next-step suggestions ------------------------------------------------

_SUGGESTIONS = [
    (re.compile(r"\b(sbdc|score|mentor|counsel|local help|free help|advisor)\b", re.I), "appointment",
     {"title": "Call with my local SBDC advisor", "duration_minutes": 30, "contact": "Local SBDC"},
     "Shall I book a call with your local SBDC on your calendar?"),
    (re.compile(r"\b(loan application|apply for (?:a|an|the)? ?loan|loan prep|prepare (?:a|my) loan|lender)\b", re.I), "todo",
     {"title": "Gather last 2 years of business tax returns"},
     "Want me to add “Gather last 2 years of business tax returns” to your tasks?"),
    (re.compile(r"\b(business plan|executive summary|plan for my business)\b", re.I), "todo",
     {"title": "Draft a one-page business plan summary"},
     "Want me to add “Draft a one-page business plan summary” to your tasks?"),
    (re.compile(r"\b(fund|funding|loan|7\(a\)|7a|504|microloan|grant|capital|financ)", re.I), "todo",
     {"title": "Check my eligibility on SBA Lender Match"},
     "Want me to add “Check my eligibility on SBA Lender Match” to your tasks?"),
]
_DEFAULT_SUGGESTION = ("todo", {"title": "Follow up on today's SBA question"},
                       "Want me to add a follow-up to your tasks so this doesn't slip?")
WORKFLOW_HINTS = {
    "funding": "funding",
    "loan": "loan application",
    "plan": "business plan",
    "local_help": "sbdc",
}


def suggest_next_step(message: str, workflow: str | None = None, now: datetime | None = None):
    """One concrete next step the concierge can do: (question, proposed_action)."""
    now = now or datetime.now()
    haystack = f"{WORKFLOW_HINTS.get(workflow or '', '')} {message or ''}"
    kind, data, question = _DEFAULT_SUGGESTION
    for pat, k, d, q in _SUGGESTIONS:
        if pat.search(haystack):
            kind, data, question = k, d, q
            break
    if kind == "appointment":
        when = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        if when.weekday() >= 5:  # weekend -> next Monday
            when += timedelta(days=7 - when.weekday())
        action = {"type": "appointment", "data": {**data, "start": when.strftime("%Y-%m-%dT%H:%M"), "notes": ""}}
    else:
        due = (now + timedelta(days=7)).date().isoformat()
        action = {"type": "todo", "data": {"items": [{"title": data["title"], "due_date": due}]}}
    return question, action
