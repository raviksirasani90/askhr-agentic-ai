
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "askhr.db"


def get_connection():
    """Open a SQLite connection and return rows as dictionaries."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the database tables if they do not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_requests (
                request_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                days_requested INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                manager_id TEXT,
                manager_comments TEXT,
                demo INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details_json TEXT NOT NULL
            )
            """
        )


def save_leave_request(request: dict):
    """Insert a new leave request or update its existing record."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO leave_requests (
                request_id, employee_id, days_requested, reason,
                status, manager_id, manager_comments, demo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_id) DO UPDATE SET
                status = excluded.status,
                manager_id = excluded.manager_id,
                manager_comments = excluded.manager_comments
            """,
            (
                request["request_id"],
                request["employee_id"],
                request["days_requested"],
                request["reason"],
                request["status"],
                request.get("manager_id"),
                request.get("manager_comments"),
                int(request.get("demo", True)),
            ),
        )


def get_leave_request_record(request_id: str):
    """Retrieve one leave request, or None if it does not exist."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM leave_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()

    return dict(row) if row else None


def list_leave_requests(employee_id: str | None = None):
    """Return leave requests, optionally filtered by employee."""
    with get_connection() as connection:
        if employee_id is None:
            rows = connection.execute(
                "SELECT * FROM leave_requests ORDER BY rowid DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM leave_requests
                WHERE employee_id = ?
                ORDER BY rowid DESC
                """,
                (employee_id,),
            ).fetchall()

    return [dict(row) for row in rows]


def add_audit_event(event: dict):
    """Persist an audit event with its additional details as JSON."""
    details = {
        key: value
        for key, value in event.items()
        if key not in {"event_id", "event_type", "timestamp"}
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (
                event_id, event_type, timestamp, details_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["event_type"],
                event["timestamp"],
                json.dumps(details),
            ),
        )


def list_audit_events():
    """Return audit events in reverse chronological insertion order."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM audit_events ORDER BY rowid ASC"
        ).fetchall()

    events = []
    for row in rows:
        event = {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "timestamp": row["timestamp"],
        }
        event.update(json.loads(row["details_json"]))
        events.append(event)

    return events
