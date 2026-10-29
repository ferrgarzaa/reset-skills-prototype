"""Automated checks. All use mocked model responses (no API calls)."""
import sqlite3

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("DEV_ENDPOINTS", "1")
    from app import llm, main
    llm._State.mode = None
    with TestClient(main.app) as c:
        yield c
    llm._State.mode = None


def db_rows(tmp_path, sql, args=()):
    conn = sqlite3.connect(tmp_path / "test.db")
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, args)]
    conn.close()
    return rows


def test_breath_steps_are_fixed_and_fit_90s(client):
    r = client.post("/api/sessions", json={"skill": "breath", "sensing": "hold"}).json()
    steps = r["steps"]
    assert [s["kind"] for s in steps] == ["intro"] + ["cycle"] * 6 + ["close"]
    assert sum(s["duration_s"] for s in steps) == 66


def test_ground_planned_time_under_90s(client):
    steps = client.post("/api/sessions", json={"skill": "ground"}).json()["steps"]
    assert [s["count"] for s in steps if s["kind"] == "sense"] == [5, 4, 3, 2, 1]
    assert sum(s["duration_s"] for s in steps) < 90


def test_completed_session_persists(client, tmp_path):
    sid = client.post("/api/sessions", json={"skill": "breath", "sensing": "mic"}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/finish", json={
        "status": "completed", "steps_completed": 8, "duration_s": 66.2, "breaths_detected": 5})
    line = client.post(f"/api/sessions/{sid}/closing").json()
    assert line["source"] == "mock"
    row = db_rows(tmp_path, "SELECT * FROM sessions WHERE id=?", (sid,))[0]
    assert row["status"] == "completed" and row["duration_s"] == 66.2 and row["breaths_detected"] == 5
    msgs = db_rows(tmp_path, "SELECT * FROM messages WHERE session_id=?", (sid,))
    assert msgs[0]["purpose"] == "closing"


def test_stopped_session_is_saved_as_stopped(client, tmp_path):
    sid = client.post("/api/sessions", json={"skill": "breath", "sensing": "none"}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/finish", json={"status": "stopped", "steps_completed": 3})
    row = db_rows(tmp_path, "SELECT status FROM sessions WHERE id=?", (sid,))[0]
    assert row["status"] == "stopped"


def test_usual_appears_after_one_completed(client):
    assert client.get("/api/home").json()["usual"] is None
    sid = client.post("/api/sessions", json={"skill": "ground"}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/finish", json={"status": "completed", "steps_completed": 6})
    assert client.get("/api/home").json()["usual"] == "ground"


def test_not_today_twice_hides_usual(client):
    for _ in range(2):
        sid = client.post("/api/sessions", json={"skill": "breath"}).json()["session_id"]
        client.post(f"/api/sessions/{sid}/finish", json={"status": "completed"})
        client.post(f"/api/sessions/{sid}/feedback", json={"feedback": "not_today"})
    assert client.get("/api/home").json()["usual"] is None


def test_journal_conversation_persists(client, tmp_path):
    r1 = client.post("/api/journal/message", json={"text": "I'm so tired today"}).json()
    assert r1["source"] == "mock" and not r1["crisis"]
    r2 = client.post("/api/journal/message",
                     json={"session_id": r1["session_id"], "text": "I have an exam tomorrow"}).json()
    assert r2["session_id"] == r1["session_id"]
    msgs = db_rows(tmp_path, "SELECT role FROM messages WHERE session_id=? ORDER BY id", (r1["session_id"],))
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]


def test_crisis_text_never_reaches_model(client, tmp_path):
    r = client.post("/api/journal/message", json={"text": "I want to die"}).json()
    assert r["crisis"] is True and r["source"] == "static"
    assert db_rows(tmp_path, "SELECT * FROM llm_calls") == []
    flagged = db_rows(tmp_path, "SELECT crisis_flag FROM messages")
    assert all(m["crisis_flag"] == 1 for m in flagged)


@pytest.mark.parametrize("text", [
    "this workout is killing me",
    "my legs are dead after that long run",
    "I could die of embarrassment lol",
])
def test_sports_slang_not_flagged(client, text):
    assert client.post("/api/journal/message", json={"text": text}).json()["crisis"] is False


def test_model_failure_uses_fallback(client, tmp_path):
    client.post("/api/dev/llm-mode", json={"mode": "fail"})
    r = client.post("/api/journal/message", json={"text": "hello"}).json()
    assert r["source"] == "fallback" and "saved" in r["reply"]
    home = client.get("/api/home").json()
    assert home["opening_source"] == "fallback"
    calls = db_rows(tmp_path, "SELECT ok, error FROM llm_calls")
    assert calls and all(c["ok"] == 0 for c in calls)


def test_journal_context_respects_memory_off(client):
    from app import db, main
    client.post("/api/journal/message", json={"text": "First entry about my race"})
    with db.connect() as conn:
        assert "First entry about my race" in main._journal_context(conn, -1)
    client.put("/api/prefs", json={"remember_journal": False})
    with db.connect() as conn:
        ctx = main._journal_context(conn, -1)
    assert "race" not in ctx and "turned off" in ctx


def test_clear_history(client, tmp_path):
    client.post("/api/journal/message", json={"text": "hi"})
    client.delete("/api/history")
    assert db_rows(tmp_path, "SELECT * FROM sessions") == []
    assert db_rows(tmp_path, "SELECT * FROM messages") == []


def test_checkin_and_profile_are_saved_and_shown(client):
    client.put("/api/profile", json={"display_name": "Sofia", "favorite_activity": "running"})
    client.post("/api/checkin", json={"state": "wound_up"})
    p = client.get("/api/profile").json()
    assert p["display_name"] == "Sofia" and p["checkin"] == "wound_up"
    ctx = client.get("/api/journal/context").json()["context"]
    assert "Sofia" in ctx and "running" in ctx and "wound up" in ctx
    client.post("/api/checkin", json={"state": "cleared"})
    assert client.get("/api/profile").json()["checkin"] is None


def test_mock_journal_reply_uses_profile(client):
    client.put("/api/profile", json={"display_name": "Sofia"})
    sid = client.post("/api/sessions", json={"skill": "ground"}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/finish", json={"status": "completed"})
    r = client.post("/api/journal/message", json={"text": "I feel overwhelmed before my race"}).json()
    assert r["reply"].startswith("Thanks for writing, Sofia.")
    assert "usual Ground reset" in r["reply"]
