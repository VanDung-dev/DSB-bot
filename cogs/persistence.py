import sqlite3
from pathlib import Path
from typing import Optional

from cogs.config import Config

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "conversations.db"

MessageList = list[dict[str, str]]


class HistoryStore:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db = str(db_path or DB_PATH)
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("DROP TABLE IF EXISTS messages")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discord_user (
                    id         INTEGER PRIMARY KEY,
                    username   TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL,
                    content    TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES discord_user(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL UNIQUE,
                    content     TEXT NOT NULL,
                    created_at  TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_questions_user
                ON questions(user_id, created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_answers_question
                ON answers(question_id)
            """)

    def _ensure_user(self, user_id: int, username: str) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO discord_user (id, username) VALUES (?, ?)",
                (user_id, username),
            )
            conn.execute(
                "UPDATE discord_user SET username = ? WHERE id = ?",
                (username, user_id),
            )

    def load_history(self, user_id: int) -> MessageList:
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute("""
                SELECT q.content, a.content
                FROM questions q
                JOIN answers a ON a.question_id = q.id
                WHERE q.user_id = ?
                ORDER BY q.created_at
            """, (user_id,)).fetchall()

        history = []
        for q_content, a_content in rows:
            history.append({"role": "user", "content": q_content})
            history.append({"role": "assistant", "content": a_content})
        return history

    def save_turn(self, user_id: int, username: str, user_msg: str, assistant_msg: str) -> None:
        self._ensure_user(user_id, username)
        pair_limit = Config.MEMORY_LIMIT // 2

        with sqlite3.connect(self._db) as conn:
            cur = conn.execute(
                "INSERT INTO questions (user_id, content) VALUES (?, ?)",
                (user_id, user_msg),
            )
            question_id = cur.lastrowid
            conn.execute(
                "INSERT INTO answers (question_id, content) VALUES (?, ?)",
                (question_id, assistant_msg),
            )

            conn.execute("""
                DELETE FROM answers WHERE question_id IN (
                    SELECT id FROM questions
                    WHERE user_id = ?
                    AND id NOT IN (
                        SELECT id FROM questions
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                )
            """, (user_id, user_id, pair_limit))
            conn.execute("""
                DELETE FROM questions
                WHERE user_id = ?
                AND id NOT IN (
                    SELECT id FROM questions
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            """, (user_id, user_id, pair_limit))

    def clear_history(self, user_id: int) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                DELETE FROM answers WHERE question_id IN (
                    SELECT id FROM questions WHERE user_id = ?
                )
            """, (user_id,))
            conn.execute("DELETE FROM questions WHERE user_id = ?", (user_id,))
