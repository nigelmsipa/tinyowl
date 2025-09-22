from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from .config import HISTORY_DB_PATH


class ChatHistory:
    def __init__(self, db_path: Path = HISTORY_DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    ai_enabled INTEGER NOT NULL,
                    ai_model TEXT
                )
                """
            )
            # Migration: ensure ai_model column exists
            cur.execute("PRAGMA table_info(sessions)")
            cols = {row[1] for row in cur.fetchall()}
            if "ai_model" not in cols:
                cur.execute("ALTER TABLE sessions ADD COLUMN ai_model TEXT")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.commit()

    def create_session(self, ai_enabled: bool, ai_model: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sessions (created_at, ai_enabled, ai_model) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat(), 1 if ai_enabled else 0, ai_model),
            )
            conn.commit()
            return cur.lastrowid

    def add_message(self, session_id: int, role: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def recent_sessions(self, limit: int = 5) -> List[Tuple[int, str, bool]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, created_at, ai_enabled FROM sessions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [(row[0], row[1], bool(row[2])) for row in cur.fetchall()]

    def get_session_messages(self, session_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            )
            return [(row[0], row[1], row[2]) for row in cur.fetchall()]

    def update_session_ai_enabled(self, session_id: int, ai_enabled: bool) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET ai_enabled = ? WHERE id = ?",
                (1 if ai_enabled else 0, session_id),
            )
            conn.commit()

    def update_session_ai_model(self, session_id: int, ai_model: Optional[str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET ai_model = ? WHERE id = ?",
                (ai_model, session_id),
            )
            conn.commit()

    def get_session_ai_model(self, session_id: int) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT ai_model FROM sessions WHERE id = ?", (session_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None
