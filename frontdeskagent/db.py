from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    urgency TEXT NOT NULL DEFAULT 'normal',
    preferred_time TEXT NOT NULL DEFAULT '',
    postcode TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    transcript TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'web'
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    lead_id INTEGER,
    requested_time TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'requested',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT ''
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def stats(self) -> dict:
        with self.connect() as conn:
            return {
                "leads": conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
                "open_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE status != 'closed'").fetchone()[0],
                "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
                "knowledge": conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0],
            }

    def create_lead(self, data: dict) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO leads
                (created_at, name, phone, email, company, reason, urgency, preferred_time, postcode, status, transcript, summary, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now(),
                    data.get("name", ""),
                    data.get("phone", ""),
                    data.get("email", ""),
                    data.get("company", ""),
                    data.get("reason", ""),
                    data.get("urgency", "normal"),
                    data.get("preferred_time", ""),
                    data.get("postcode", ""),
                    data.get("status", "new"),
                    data.get("transcript", ""),
                    data.get("summary", ""),
                    data.get("source", "web"),
                ),
            )
            return int(cur.lastrowid)

    def update_lead_status(self, lead_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))

    def list_leads(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_lead(self, lead_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return dict(row) if row else None

    def create_appointment(self, lead_id: int | None, requested_time: str, notes: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO appointments (created_at, lead_id, requested_time, status, notes) VALUES (?, ?, ?, ?, ?)",
                (utc_now(), lead_id, requested_time, "requested", notes),
            )
            return int(cur.lastrowid)

    def list_appointments(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT appointments.*, leads.name AS lead_name, leads.phone AS lead_phone
                FROM appointments
                LEFT JOIN leads ON leads.id = appointments.lead_id
                ORDER BY appointments.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def add_knowledge(self, title: str, body: str, tags: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO knowledge_items (created_at, title, body, tags) VALUES (?, ?, ?, ?)",
                (utc_now(), title.strip(), body.strip(), tags.strip()),
            )
            return int(cur.lastrowid)

    def list_knowledge(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM knowledge_items ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def search_knowledge(self, query: str, limit: int = 5) -> list[dict]:
        terms = [term.lower() for term in query.split() if len(term) > 2]
        items = self.list_knowledge(limit=200)
        scored: list[tuple[int, dict]] = []
        for item in items:
            haystack = f"{item['title']} {item['body']} {item['tags']}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def add_event(self, event_type: str, payload: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO events (created_at, event_type, payload) VALUES (?, ?, ?)",
                (utc_now(), event_type, payload),
            )
            return int(cur.lastrowid)

    def list_events(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]
