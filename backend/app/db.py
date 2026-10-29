"""SQLite storage. One local user, no accounts."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def db_path() -> Path:
    p = Path(os.getenv("DB_PATH", "data/reset.db"))
    return p if p.is_absolute() else BASE_DIR / p


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('breath', 'ground', 'journal')),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'stopped')),
    steps_completed INTEGER DEFAULT 0,
    duration_s REAL,
    sensing TEXT CHECK (sensing IN ('mic', 'hold', 'none') OR sensing IS NULL),
    breaths_detected INTEGER,
    feedback TEXT CHECK (feedback IN ('helped', 'not_sure', 'not_today') OR feedback IS NULL),
    was_usual INTEGER DEFAULT 0,
    timing_json TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('user', 'model', 'mock', 'fallback', 'static')),
    purpose TEXT NOT NULL DEFAULT 'chat',
    crisis_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_steps (
    skill TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    count INTEGER,
    duration_s REAL NOT NULL,
    PRIMARY KEY (skill, step_order)
);

CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL CHECK (state IN ('wound_up', 'scattered', 'low', 'okay', 'cleared')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prefs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    purpose TEXT NOT NULL,
    mode TEXT NOT NULL,
    ok INTEGER NOT NULL,
    latency_ms INTEGER,
    error TEXT
);
"""

# The fixed skill scripts. The model never writes here.
SKILL_STEPS = [
    # skill, order, kind, text, count, duration_s
    ("breath", 1, "intro", "Follow the circle. In for 4, out for 6.", None, 3),
    *[("breath", 1 + i, "cycle", "In for 4, out for 6.", None, 10) for i in range(1, 7)],
    ("breath", 8, "close", "Last breath out. That's it.", None, 3),
    ("ground", 1, "intro", "Look around. One sense at a time, no need to type anything.", None, 3),
    ("ground", 2, "sense", "Notice 5 things you can see.", 5, 15.5),
    ("ground", 3, "sense", "Notice 4 things you can feel.", 4, 13),
    ("ground", 4, "sense", "Notice 3 things you can hear.", 3, 10.5),
    ("ground", 5, "sense", "Notice 2 things you can smell.", 2, 8),
    ("ground", 6, "sense", "Notice 1 thing you can taste.", 1, 5.5),
]


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR REPLACE INTO skill_steps VALUES (?, ?, ?, ?, ?, ?)", SKILL_STEPS
        )
        conn.execute(
            "INSERT OR IGNORE INTO prefs VALUES ('remember_journal', 'true')"
        )


def get_pref(conn, key, default=None):
    row = conn.execute("SELECT value FROM prefs WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def set_pref(conn, key, value):
    conn.execute(
        "INSERT INTO prefs VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, json.dumps(value)),
    )


def add_message(conn, session_id, role, content, source, purpose="chat", crisis=False):
    cur = conn.execute(
        "INSERT INTO messages (session_id, role, content, source, purpose, crisis_flag, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, role, content, source, purpose, int(crisis), now()),
    )
    return cur.lastrowid


def log_llm_call(purpose, mode, ok, latency_ms, error=None):
    with connect() as conn:
        conn.execute(
            "INSERT INTO llm_calls (created_at, purpose, mode, ok, latency_ms, error) VALUES (?, ?, ?, ?, ?, ?)",
            (now(), purpose, mode, int(ok), latency_ms, error),
        )
