"""Reset backend: FastAPI + SQLite. Coursework prototype, not a mental health tool."""
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import db, llm, safety  # noqa: E402

@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(title="Reset prototype API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SHORT_TIMEOUT_S = 3.0
JOURNAL_TIMEOUT_S = 12.0

FALLBACK_OPENING = "Take a short reset. Stop whenever you want."
FALLBACK_CLOSING = "That's the reset. Take your time."
FALLBACK_JOURNAL = (
    "I'm having trouble replying right now. Your words are saved here. "
    "You can keep writing, try a Breath reset, or come back later."
)

JOURNAL_STARTERS = [
    "What's taking up the most space in my head",
    "Something that went okay today",
    "Something I'm carrying",
]


# ---------- helpers ----------

def _usual(conn):
    """Skill the person finished most in their last 10 resets, unless they said
    'not today' to it the last two times. Only after at least one completed."""
    rows = conn.execute(
        "SELECT kind, status, feedback FROM sessions WHERE kind IN ('breath', 'ground') "
        "ORDER BY id DESC LIMIT 10"
    ).fetchall()
    counts = {}
    for r in rows:
        if r["status"] == "completed":
            counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    if not counts:
        return None
    best = max(counts, key=lambda k: (counts[k], k == "breath"))
    recent = [r["feedback"] for r in rows if r["kind"] == best][:2]
    if len(recent) == 2 and all(f == "not_today" for f in recent):
        return None
    return best


def _short_line(purpose, prompt, usual=False):
    try:
        text, source = llm.generate(
            purpose, [{"role": "user", "content": prompt}], llm.SHORT_SYSTEM,
            max_tokens=60, timeout=SHORT_TIMEOUT_S, usual=usual,
        )
        cleaned = safety.clean_reply(text, max_words=25, short=True)
        if cleaned:
            return cleaned, source
    except llm.LLMError:
        pass
    return (FALLBACK_CLOSING if purpose == "closing" else FALLBACK_OPENING), "fallback"


def _journal_context(conn, current_session_id):
    """The only personal information the model sees. Built from what the person
    already did in the app. No profile, no settings."""
    lines = []
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    resets = conn.execute(
        "SELECT kind, COUNT(*) n FROM sessions WHERE kind IN ('breath','ground') "
        "AND status='completed' AND started_at >= ? GROUP BY kind", (week_ago,)
    ).fetchall()
    if resets:
        names = {"breath": "Breath reset", "ground": "Ground reset"}
        lines.append("Resets completed in the last 7 days: " +
                     ", ".join(f"{names[r['kind']]} x{r['n']}" for r in resets) + ".")
    if db.get_pref(conn, "remember_journal", True):
        prev = conn.execute(
            "SELECT s.started_at, m.content FROM sessions s JOIN messages m ON m.session_id = s.id "
            "WHERE s.kind='journal' AND s.id != ? AND m.role='user' AND m.crisis_flag=0 "
            "AND m.id = (SELECT MIN(id) FROM messages WHERE session_id = s.id AND role='user') "
            "ORDER BY s.id DESC LIMIT 3", (current_session_id,)
        ).fetchall()
        for p in prev:
            snippet = p["content"][:120].replace("\n", " ")
            lines.append(f"Earlier journal entry ({p['started_at'][:10]}) began: \"{snippet}\"")
    else:
        lines.append("Memory of past journal entries is turned off. Do not refer to past entries.")
    return "CONTEXT\n" + ("\n".join(lines) if lines else "No earlier activity in the app.")


def _get_session(conn, sid):
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
    if not row:
        raise HTTPException(404, "session not found")
    return row


# ---------- models ----------

class StartSession(BaseModel):
    skill: str = Field(pattern="^(breath|ground)$")
    sensing: str | None = Field(default=None, pattern="^(mic|hold|none)$")
    from_usual: bool = False


class FinishSession(BaseModel):
    status: str = Field(pattern="^(completed|stopped)$")
    steps_completed: int = 0
    duration_s: float | None = None
    breaths_detected: int | None = None
    timing: dict | None = None


class Feedback(BaseModel):
    feedback: str = Field(pattern="^(helped|not_sure|not_today)$")


class JournalMessage(BaseModel):
    session_id: int | None = None
    text: str = Field(min_length=1, max_length=4000)


class Prefs(BaseModel):
    remember_journal: bool


class ModeSwitch(BaseModel):
    mode: str = Field(pattern="^(mock|live|fail)$")


# ---------- routes ----------

@app.get("/api/health")
def health():
    return {"ok": True, "llm": llm.status()}


@app.get("/api/home")
def home():
    with db.connect() as conn:
        usual = _usual(conn)
        last_sensing = db.get_pref(conn, "last_sensing", "none")
    line, source = _short_line("opening", "Write a short welcome line for the home screen.")
    return {"usual": usual, "last_sensing": last_sensing, "opening_line": line,
            "opening_source": source, "journal_starters": JOURNAL_STARTERS}


@app.post("/api/sessions")
def start_session(body: StartSession):
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (kind, started_at, sensing, was_usual) VALUES (?, ?, ?, ?)",
            (body.skill, db.now(), body.sensing if body.skill == "breath" else None,
             int(body.from_usual)),
        )
        if body.skill == "breath" and body.sensing:
            db.set_pref(conn, "last_sensing", body.sensing)
        steps = [dict(r) for r in conn.execute(
            "SELECT step_order, kind, text, count, duration_s FROM skill_steps "
            "WHERE skill = ? ORDER BY step_order", (body.skill,))]
    return {"session_id": cur.lastrowid, "steps": steps}


@app.post("/api/sessions/{sid}/finish")
def finish_session(sid: int, body: FinishSession):
    with db.connect() as conn:
        _get_session(conn, sid)
        conn.execute(
            "UPDATE sessions SET status=?, ended_at=?, steps_completed=?, duration_s=?, "
            "breaths_detected=?, timing_json=? WHERE id=?",
            (body.status, db.now(), body.steps_completed, body.duration_s,
             body.breaths_detected, json.dumps(body.timing) if body.timing else None, sid),
        )
    return {"ok": True}


@app.post("/api/sessions/{sid}/closing")
def closing_line(sid: int):
    with db.connect() as conn:
        s = _get_session(conn, sid)
        done_before = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE kind=? AND status='completed' AND id<?",
            (s["kind"], sid)).fetchone()[0]
    name = "Breath reset" if s["kind"] == "breath" else "Ground reset"
    prompt = (f"The person just finished a {name}. "
              f"{'It is their usual reset. ' if s['was_usual'] else ''}"
              f"They have finished it {done_before} time(s) before. Write a short closing line.")
    line, source = _short_line("closing", prompt, usual=bool(s["was_usual"]))
    with db.connect() as conn:
        db.add_message(conn, sid, "assistant", line, source, purpose="closing")
    return {"line": line, "source": source}


@app.post("/api/sessions/{sid}/feedback")
def feedback(sid: int, body: Feedback):
    with db.connect() as conn:
        _get_session(conn, sid)
        conn.execute("UPDATE sessions SET feedback=? WHERE id=?", (body.feedback, sid))
    return {"ok": True}


@app.post("/api/journal/message")
def journal_message(body: JournalMessage):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "empty message")
    with db.connect() as conn:
        if body.session_id is None:
            sid = conn.execute(
                "INSERT INTO sessions (kind, started_at) VALUES ('journal', ?)", (db.now(),)
            ).lastrowid
        else:
            s = _get_session(conn, body.session_id)
            if s["kind"] != "journal":
                raise HTTPException(400, "not a journal session")
            sid = s["id"]
        crisis = safety.crisis_match(text)
        db.add_message(conn, sid, "user", text, "user", crisis=crisis)
        if crisis:
            # Decision: never send crisis-related text to the model.
            db.add_message(conn, sid, "assistant", safety.CRISIS_MESSAGE, "static", crisis=True)
            return {"session_id": sid, "reply": safety.CRISIS_MESSAGE, "source": "static",
                    "crisis": True}
        history = [
            {"role": r["role"], "content": r["content"]}
            for r in conn.execute(
                "SELECT role, content FROM messages WHERE session_id=? AND purpose='chat' "
                "AND crisis_flag=0 ORDER BY id DESC LIMIT 20", (sid,))
        ][::-1]
        context = _journal_context(conn, sid)
    # Model must see a conversation that starts with the user.
    while history and history[0]["role"] != "user":
        history.pop(0)
    system = llm.JOURNAL_SYSTEM + "\n\n" + context
    try:
        reply, source = llm.generate("journal", history, system, max_tokens=300,
                                     timeout=JOURNAL_TIMEOUT_S)
        cleaned = safety.clean_reply(reply, max_words=110)
        if not cleaned:
            reply, source = FALLBACK_JOURNAL, "fallback"
        else:
            reply = cleaned
    except llm.LLMError:
        reply, source = FALLBACK_JOURNAL, "fallback"
    with db.connect() as conn:
        db.add_message(conn, sid, "assistant", reply, source)
    return {"session_id": sid, "reply": reply, "source": source, "crisis": False}


@app.post("/api/journal/{sid}/end")
def journal_end(sid: int):
    with db.connect() as conn:
        s = _get_session(conn, sid)
        if s["status"] == "in_progress":
            started = datetime.fromisoformat(s["started_at"])
            dur = (datetime.now(timezone.utc) - started).total_seconds()
            conn.execute("UPDATE sessions SET status='completed', ended_at=?, duration_s=? "
                         "WHERE id=?", (db.now(), dur, sid))
    return {"ok": True}


@app.get("/api/history")
def history():
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT s.id, s.kind, s.started_at, s.status, s.duration_s, s.feedback, "
            "(SELECT content FROM messages WHERE session_id=s.id AND role='user' ORDER BY id LIMIT 1) first_text, "
            "(SELECT COUNT(*) FROM messages WHERE session_id=s.id) n_messages "
            "FROM sessions s WHERE NOT (s.kind='journal' AND NOT EXISTS "
            "(SELECT 1 FROM messages WHERE session_id=s.id)) ORDER BY s.id DESC LIMIT 100"
        ).fetchall()
    return {"sessions": [dict(r) for r in rows]}


@app.get("/api/sessions/{sid}")
def session_detail(sid: int):
    with db.connect() as conn:
        s = dict(_get_session(conn, sid))
        msgs = [dict(r) for r in conn.execute(
            "SELECT role, content, source, purpose, crisis_flag, created_at FROM messages "
            "WHERE session_id=? ORDER BY id", (sid,))]
    s.pop("timing_json", None)
    return {"session": s, "messages": msgs}


@app.delete("/api/history")
def clear_history():
    with db.connect() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM sessions")
    return {"ok": True}


@app.get("/api/prefs")
def get_prefs():
    with db.connect() as conn:
        return {"remember_journal": db.get_pref(conn, "remember_journal", True)}


@app.put("/api/prefs")
def put_prefs(body: Prefs):
    with db.connect() as conn:
        db.set_pref(conn, "remember_journal", body.remember_journal)
    return {"ok": True}


# Dev-only switch so the demo and evidence can show what happens when the model fails.
@app.post("/api/dev/llm-mode")
def dev_llm_mode(body: ModeSwitch):
    if os.getenv("DEV_ENDPOINTS", "0") != "1":
        raise HTTPException(404, "not found")
    llm.set_mode(body.mode)
    return llm.status()
