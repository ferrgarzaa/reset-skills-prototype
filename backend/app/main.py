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


CHECKIN_LABELS = {
    "wound_up": "wound up / tense",
    "scattered": "scattered / hard to focus",
    "low": "low / heavy",
    "okay": "okay",
}


def _recent_checkin(conn, hours=3):
    """The check-in the person chose in this visit, if any. Never inferred."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    row = conn.execute("SELECT state, created_at FROM checkins WHERE created_at >= ? "
                       "ORDER BY id DESC LIMIT 1", (since,)).fetchone()
    if not row or row["state"] == "cleared":
        return None
    return row["state"]


def _profile_facts(conn):
    return {
        "name": (db.get_pref(conn, "display_name", "") or "").strip()[:40],
        "activity": (db.get_pref(conn, "favorite_activity", "") or "").strip()[:60],
        "usual": _usual(conn),
        "checkin": _recent_checkin(conn),
    }


def _journal_context(conn, current_session_id):
    """The only personal information the model sees: what the person chose to
    tell the app (name, activity, check-in) and what they already did in it."""
    facts = _profile_facts(conn)
    lines = []
    names = {"breath": "Breath reset", "ground": "Ground reset"}
    if facts["name"]:
        lines.append(f"They asked to be called: {facts['name']}.")
    if facts["activity"]:
        lines.append(f"Something they said they enjoy: {facts['activity']}.")
    if facts["checkin"]:
        lines.append(f"At the start of this visit they chose the check-in: {CHECKIN_LABELS[facts['checkin']]}. "
                     "This is their own words for right now, not a diagnosis.")
    if facts["usual"]:
        lines.append(f"Their usual reset: {names[facts['usual']]}.")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    resets = conn.execute(
        "SELECT kind, COUNT(*) n FROM sessions WHERE kind IN ('breath','ground') "
        "AND status='completed' AND started_at >= ? GROUP BY kind", (week_ago,)
    ).fetchall()
    if resets:
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


class Checkin(BaseModel):
    state: str = Field(pattern="^(wound_up|scattered|low|okay|cleared)$")


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=40)
    favorite_activity: str | None = Field(default=None, max_length=60)
    large_text: bool | None = None
    remember_journal: bool | None = None


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
        facts = _profile_facts(conn)
    # Model must see a conversation that starts with the user.
    while history and history[0]["role"] != "user":
        history.pop(0)
    system = llm.JOURNAL_SYSTEM + "\n\n" + context
    try:
        reply, source = llm.generate("journal", history, system, max_tokens=300,
                                     timeout=JOURNAL_TIMEOUT_S, ctx=facts)
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
        conn.execute("DELETE FROM checkins")
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


@app.post("/api/checkin")
def checkin(body: Checkin):
    """Optional, user-chosen check-in. It only reorders or narrows the home screen
    for this visit; the person can change or clear it any time."""
    with db.connect() as conn:
        conn.execute("INSERT INTO checkins (state, created_at) VALUES (?, ?)", (body.state, db.now()))
    return {"ok": True, "state": None if body.state == "cleared" else body.state}


@app.get("/api/profile")
def profile():
    """Everything the app keeps about the person, shown back to them."""
    with db.connect() as conn:
        facts = _profile_facts(conn)
        counts = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) n FROM sessions WHERE kind IN ('breath','ground') GROUP BY status")}
        by_skill = {r["kind"]: r["n"] for r in conn.execute(
            "SELECT kind, COUNT(*) n FROM sessions WHERE kind IN ('breath','ground') "
            "AND status='completed' GROUP BY kind")}
        journals = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM messages m JOIN sessions s ON s.id=m.session_id "
            "WHERE s.kind='journal'").fetchone()[0]
        first = conn.execute("SELECT MIN(started_at) FROM sessions").fetchone()[0]
        checkins = [dict(r) for r in conn.execute(
            "SELECT state, created_at FROM checkins WHERE state != 'cleared' ORDER BY id DESC LIMIT 5")]
        return {
            "display_name": facts["name"],
            "favorite_activity": facts["activity"],
            "usual": facts["usual"],
            "checkin": facts["checkin"],
            "recent_checkins": checkins,
            "last_sensing": db.get_pref(conn, "last_sensing", "none"),
            "large_text": db.get_pref(conn, "large_text", False),
            "remember_journal": db.get_pref(conn, "remember_journal", True),
            "resets_completed": counts.get("completed", 0),
            "resets_stopped": counts.get("stopped", 0),
            "completed_by_skill": by_skill,
            "journal_entries": journals,
            "first_seen": first,
        }


@app.put("/api/profile")
def update_profile(body: ProfileUpdate):
    with db.connect() as conn:
        for key in ("display_name", "favorite_activity", "large_text", "remember_journal"):
            val = getattr(body, key)
            if val is not None:
                db.set_pref(conn, key, val.strip() if isinstance(val, str) else val)
    return profile()


@app.get("/api/journal/context")
def journal_context(session_id: int = -1):
    """Shows the person exactly what the companion is told about them."""
    with db.connect() as conn:
        return {"context": _journal_context(conn, session_id)}


# Dev-only: load a fictional persona's history so a demo can show personalization
# without doing ten resets live. All data here is made up.
@app.post("/api/dev/seed-demo")
def dev_seed_demo():
    if os.getenv("DEV_ENDPOINTS", "0") != "1":
        raise HTTPException(404, "not found")
    now = datetime.now(timezone.utc)
    ago = lambda d, h=0: (now - timedelta(days=d, hours=h)).isoformat(timespec="seconds")  # noqa: E731
    with db.connect() as conn:
        for t in ("messages", "sessions", "checkins"):
            conn.execute(f"DELETE FROM {t}")
        db.set_pref(conn, "display_name", "Sofia")
        db.set_pref(conn, "favorite_activity", "running, training for a half marathon")
        db.set_pref(conn, "last_sensing", "hold")
        rows = [
            ("breath", ago(6), "completed", 8, 66.0, "hold", 5, "helped"),
            ("ground", ago(5), "completed", 6, 61.2, None, None, "not_sure"),
            ("breath", ago(3), "completed", 8, 66.0, "mic", 6, "helped"),
            ("breath", ago(2), "stopped", 3, 21.4, "hold", 2, None),
            ("breath", ago(1), "completed", 8, 66.0, "hold", 6, None),
        ]
        for kind, at, status, steps, dur, sensing, heard, fb in rows:
            conn.execute(
                "INSERT INTO sessions (kind, started_at, ended_at, status, steps_completed, duration_s, "
                "sensing, breaths_detected, feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (kind, at, at, status, steps, dur, sensing, heard, fb))
        sid = conn.execute("INSERT INTO sessions (kind, started_at, ended_at, status, duration_s) "
                           "VALUES ('journal', ?, ?, 'completed', 140)", (ago(2, 1), ago(2, 1))).lastrowid
        db.add_message(conn, sid, "user", "Long run went bad today. My legs felt dead and I'm annoyed at myself.", "user")
        db.add_message(conn, sid, "assistant", "That sounds frustrating after putting in the effort. Rough days happen in training too. What's bugging you most about it?", "mock")
        for d, st in ((6, "wound_up"), (5, "scattered"), (3, "wound_up"), (1, "okay")):
            conn.execute("INSERT INTO checkins (state, created_at) VALUES (?, ?)", (st, ago(d)))
    return {"ok": True}


# Dev-only switch so the demo and evidence can show what happens when the model fails.
@app.post("/api/dev/llm-mode")
def dev_llm_mode(body: ModeSwitch):
    if os.getenv("DEV_ENDPOINTS", "0") != "1":
        raise HTTPException(404, "not found")
    llm.set_mode(body.mode)
    return llm.status()
