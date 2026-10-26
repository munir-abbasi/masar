"""Event-sourced session journal with reversible agent execution and undo/redo."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field


class SessionEvent(BaseModel):
    """An atomic agent operation in the takhrīj workspace."""

    event_id: str
    action: str = Field(description="Action type: ADD, PRUNE, SPLIT, STAGE.")
    target_id: str
    payload: dict[str, Any]
    timestamp: str
    is_undone: bool = False


class SessionJournal:
    """Event-sourced workspace journal supporting single-step rollback."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS session_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    action TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    is_undone INTEGER DEFAULT 0
                )
                """
            )
            conn.commit()

    def record(
        self,
        action: str,
        target_id: str,
        payload: dict[str, Any],
    ) -> SessionEvent:
        """Record a new action into the event stream, clearing any pending redo events."""
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Clear forward redo events
            cursor.execute("DELETE FROM session_events WHERE is_undone = 1")
            cursor.execute(
                """
                INSERT INTO session_events (event_id, action, target_id, payload, timestamp, is_undone)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (event_id, action, target_id, payload_json, now_iso),
            )
            conn.commit()

        return SessionEvent(
            event_id=event_id,
            action=action,
            target_id=target_id,
            payload=payload,
            timestamp=now_iso,
            is_undone=False,
        )

    def undo(self) -> Optional[SessionEvent]:
        """Rollback the most recent active operation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_events WHERE is_undone = 0 ORDER BY seq DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "UPDATE session_events SET is_undone = 1 WHERE event_id = ?",
                (row["event_id"],),
            )
            conn.commit()

            return SessionEvent(
                event_id=row["event_id"],
                action=row["action"],
                target_id=row["target_id"],
                payload=json.loads(row["payload"]),
                timestamp=row["timestamp"],
                is_undone=True,
            )

    def redo(self) -> Optional[SessionEvent]:
        """Reapply the most recently undone operation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_events WHERE is_undone = 1 ORDER BY seq ASC LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "UPDATE session_events SET is_undone = 0 WHERE event_id = ?",
                (row["event_id"],),
            )
            conn.commit()

            return SessionEvent(
                event_id=row["event_id"],
                action=row["action"],
                target_id=row["target_id"],
                payload=json.loads(row["payload"]),
                timestamp=row["timestamp"],
                is_undone=False,
            )

    def get_history(self) -> list[SessionEvent]:
        """Return all historical events in execution sequence."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_events ORDER BY seq ASC")
            rows = cursor.fetchall()
            return [
                SessionEvent(
                    event_id=r["event_id"],
                    action=r["action"],
                    target_id=r["target_id"],
                    payload=json.loads(r["payload"]),
                    timestamp=r["timestamp"],
                    is_undone=bool(r["is_undone"]),
                )
                for r in rows
            ]

    def get_active_events(self) -> list[SessionEvent]:
        """Return currently active events (excluding undone events)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_events WHERE is_undone = 0 ORDER BY seq ASC"
            )
            rows = cursor.fetchall()
            return [
                SessionEvent(
                    event_id=r["event_id"],
                    action=r["action"],
                    target_id=r["target_id"],
                    payload=json.loads(r["payload"]),
                    timestamp=r["timestamp"],
                    is_undone=False,
                )
                for r in rows
            ]
