"""Print the main tables of the Reset database, for verification evidence.

Usage (from backend/):  python tools/inspect_db.py [path/to/reset.db]
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "data/reset.db"

QUERIES = [
    "SELECT id, kind, status, steps_completed AS steps, duration_s, sensing, "
    "breaths_detected AS heard, feedback, was_usual FROM sessions",
    "SELECT id, session_id, role, source, purpose, crisis_flag, substr(content, 1, 60) AS content FROM messages",
    "SELECT id, purpose, mode, ok, latency_ms, error FROM llm_calls",
    "SELECT skill, SUM(duration_s) AS planned_seconds FROM skill_steps GROUP BY skill",
    "SELECT id, kind, json_extract(timing_json, '$.wall_ms') AS wall_ms, "
    "json_extract(timing_json, '$.active_ms') AS active_ms, "
    "json_extract(timing_json, '$.paused_ms') AS paused_ms FROM sessions WHERE timing_json IS NOT NULL",
    "SELECT * FROM prefs",
]


def table(cur):
    cols = [d[0] for d in cur.description]
    rows = [["" if v is None else str(v) for v in r] for r in cur.fetchall()]
    widths = [max(len(c), *(len(r[i]) for r in rows)) if rows else len(c) for i, c in enumerate(cols)]
    line = "  ".join(c.ljust(w) for c, w in zip(cols, widths))
    out = [line, "  ".join("-" * w for w in widths)]
    out += ["  ".join(v.ljust(w) for v, w in zip(r, widths)) for r in rows]
    return "\n".join(out)


conn = sqlite3.connect(DB)
print(f"# Database: {DB.name}")
for q in QUERIES:
    print(f"\nsqlite> {q};")
    print(table(conn.execute(q)))
