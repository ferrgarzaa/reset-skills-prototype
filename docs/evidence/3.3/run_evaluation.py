"""Part 3.3 evaluation: fictional scenarios and behavior checks, run in the real browser
against the real backend (FastAPI + SQLite) with mocked model replies.

Start the servers first:
    backend:  LLM_MODE=mock DEV_ENDPOINTS=1 uvicorn app.main:app --port 8000   (from backend/)
    frontend: npm run dev                                                     (from frontend/)
Then:  python docs/evidence/3.3/run_evaluation.py <folder with backend.pid>

Writes results.json, evaluation.md and screenshots into this folder.
All people and situations here are made up.
"""
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DB = ROOT / "backend/data/reset.db"
PID_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
URL = "http://localhost:5173/"
API = "http://localhost:8000/api"

results = []
behavior = {"B1": [], "B2": None, "B3": None, "B4": None}


def q(sql, args=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, args)]
    conn.close()
    return rows


def record(sid, kind, does, expected, observed, ok, shot=None):
    results.append({"id": sid, "type": kind, "user_does": does, "expected": expected,
                    "observed": observed, "pass": bool(ok), "screenshot": shot})
    print(("PASS" if ok else "FAIL"), sid, "-", observed[:110], flush=True)


def snap(page, name):
    page.screenshot(path=str(HERE / f"{name}.png"), full_page=True)
    return f"{name}.png"


def help_visible(page, where):
    vis = page.locator("[data-testid=need-help]").is_visible()
    behavior["B1"].append({"screen": where, "visible": vis})
    return vis


def wait_cue(page, prefix):
    page.wait_for_function(
        f"document.querySelector('[data-testid=cue]')?.textContent.startsWith('{prefix}')", timeout=25000)


def home(page):
    page.goto(URL)
    page.wait_for_function("document.querySelector('[data-testid=opening-line]')?.dataset.source !== 'static'")


httpx.delete(f"{API}/history")
httpx.put(f"{API}/profile", json={"display_name": "", "favorite_activity": "", "large_text": False,
                                  "remember_journal": True})

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--use-fake-ui-for-media-stream"])
    ctx = browser.new_context(viewport={"width": 480, "height": 900}, permissions=["microphone"])
    ctx.add_init_script("""
      if (!window.__denyMic) {
        navigator.mediaDevices.getUserMedia = async () => {
          if (window.localStorage.getItem('denyMic') === '1') { const e = new Error('denied'); e.name = 'NotAllowedError'; throw e; }
          const ac = new AudioContext();
          const buf = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate);
          const d = buf.getChannelData(0);
          for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
          const src = ac.createBufferSource(); src.buffer = buf; src.loop = true;
          const g = ac.createGain(); g.gain.value = 0.003;
          const dest = ac.createMediaStreamDestination();
          src.connect(g); g.connect(dest); src.start();
          window.__breath = (on) => { g.gain.value = on ? 0.15 : 0.003; };
          return dest.stream;
        };
      }
    """)
    page = ctx.new_page()

    # S01 first visit
    home(page)
    help_visible(page, "home")
    has_usual = page.locator("[data-testid=start-usual]").count()
    chips = page.locator("[data-testid^=checkin-]").count()
    record("S01", "ordinary", "Opens the app for the first time.",
           "Home shows Breath, Ground, Journal and an optional check-in. No 'Your usual' yet.",
           f"{chips} check-in choices shown, 'Your usual' shown: {bool(has_usual)}.",
           chips == 4 and not has_usual, snap(page, "s01-first-visit"))

    # S02 wound up -> contracted
    page.click("[data-testid=checkin-wound_up]")
    page.wait_for_selector("[data-testid=show-all]")
    n_buttons = page.locator("[data-testid=start-breath], [data-testid=start-ground], [data-testid=open-journal], [data-testid=start-journal]").count()
    record("S02", "ordinary", "Taps the check-in 'Wound up'.",
           "Screen shrinks to one suggestion (Breath reset) plus 'Show all options'.",
           f"{n_buttons} activity button visible; suggestion is Breath reset: {page.locator('[data-testid=suggested] [data-testid=start-breath]').count() == 1}.",
           n_buttons == 1, snap(page, "s02-wound-up"))

    # S03 override
    page.click("[data-testid=show-all]")
    n_buttons = page.locator("[data-testid=start-breath], [data-testid=start-ground], [data-testid=open-journal], [data-testid=start-journal]").count()
    record("S03", "ordinary", "Taps 'Show all options' after choosing 'Wound up'.",
           "All three activities come back. The person can override the app's narrowing.",
           f"{n_buttons} activity buttons visible.", n_buttons == 3)

    # S04 scattered
    page.click("[data-testid=checkin-change]")
    page.click("[data-testid=checkin-scattered]")
    first = page.locator("[data-testid=suggested] button").first.inner_text()
    record("S04", "ordinary", "Changes the check-in to 'Scattered'.",
           "Ground reset becomes the suggestion at the top; the others stay available.",
           f"Suggested: {first.split(chr(10))[0].split(' ·')[0]}.", first.startswith("Ground reset"),
           snap(page, "s04-scattered"))

    # S05 low
    page.click("[data-testid=checkin-change]")
    page.click("[data-testid=checkin-low]")
    first = page.locator("[data-testid=suggested] button").first.inner_text()
    record("S05", "ordinary", "Changes the check-in to 'Low'.",
           "Journal becomes the suggestion at the top.", f"Suggested: {first.strip()}.",
           first.strip().startswith("Journal"))

    # S06 clear
    page.click("[data-testid=checkin-clear]")
    page.wait_for_selector("[data-testid=checkin-wound_up]")
    prof = httpx.get(f"{API}/profile").json()
    record("S06", "ordinary", "Taps 'Clear' on the check-in.",
           "Normal home screen; the profile shows no current check-in.",
           f"Check-in choices back on screen; profile check-in = {prof['checkin']}.", prof["checkin"] is None)

    # S07 breath hold full run
    page.click("[data-testid=start-breath]")
    help_visible(page, "breath setup")
    page.check("[data-testid=sense-hold]")
    page.click("[data-testid=begin]")
    box = page.locator(".circle-wrap").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    for k in range(6):
        wait_cue(page, "Breathe in")
        if k == 0:
            help_visible(page, "breath exercise")
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.wait_for_timeout(2500)
        page.mouse.up()
        wait_cue(page, "Breathe out")
        page.wait_for_timeout(2000)
    page.wait_for_selector("[data-testid=done]", timeout=20000)
    page.wait_for_function("document.querySelector('[data-testid=closing-line]')?.dataset.source")
    help_visible(page, "done")
    s = q("SELECT * FROM sessions WHERE kind='breath' ORDER BY id DESC LIMIT 1")[0]
    record("S07", "ordinary", "Does a full Breath reset with press and hold.",
           "Completes in about 66 s (plan), saved as completed with breaths followed.",
           f"status={s['status']}, duration={s['duration_s']} s, breaths_detected={s['breaths_detected']}.",
           s["status"] == "completed" and abs(s["duration_s"] - 66) < 0.5, snap(page, "s07-done"))
    page.click("[data-testid=back-home]")

    # S08 mic simulated, no score on Done
    page.click("[data-testid=start-breath]")
    page.check("[data-testid=sense-mic]")
    page.click("[data-testid=begin]")
    for k in range(6):
        wait_cue(page, "Breathe out")
        page.wait_for_timeout(400)
        page.evaluate("window.__breath(true)")
        page.wait_for_timeout(2500)
        page.evaluate("window.__breath(false)")
        page.wait_for_function("!document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe out')", timeout=20000)
    page.wait_for_selector("[data-testid=done]", timeout=20000)
    done_text = page.locator("[data-testid=done]").inner_text()
    s = q("SELECT * FROM sessions WHERE kind='breath' ORDER BY id DESC LIMIT 1")[0]
    record("S08", "ordinary", "Does a Breath reset with the microphone (simulated breath-out sound).",
           "Breaths are noticed and saved, but the Done screen shows no count or score.",
           f"breaths_detected={s['breaths_detected']} saved; Done screen mentions a count: {'of 6' in done_text}.",
           (s["breaths_detected"] or 0) >= 5 and "of 6" not in done_text)
    page.click("[data-testid=back-home]")

    # S09 mic denied
    page.evaluate("localStorage.setItem('denyMic','1')")
    page.click("[data-testid=start-breath]")
    page.check("[data-testid=sense-mic]")
    page.click("[data-testid=begin]")
    page.wait_for_selector("[data-testid=setup-note]")
    hold_checked = page.locator("[data-testid=sense-hold]").is_checked()
    record("S09", "failure", "Chooses Microphone but the browser denies microphone access.",
           "Stays on setup, explains it, and switches to press and hold.",
           f"Note shown: '{page.locator('[data-testid=setup-note]').inner_text()}'. Hold selected: {hold_checked}.",
           hold_checked, snap(page, "s09-mic-denied"))
    page.evaluate("localStorage.removeItem('denyMic')")

    # S10 + S11 crisis panel pause then stop
    page.check("text=Just the circle")
    page.click("[data-testid=begin]")
    page.wait_for_timeout(5000)
    page.click("[data-testid=need-help]")
    page.wait_for_timeout(4000)
    paused_label = page.locator("text=paused").count() > 0
    snap(page, "s10-crisis-during-exercise")
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.wait_for_timeout(1500)
    page.click("[data-testid=stop]")
    page.wait_for_selector("[data-testid=stopped]")
    help_visible(page, "stopped")
    s = q("SELECT * FROM sessions WHERE kind='breath' ORDER BY id DESC LIMIT 1")[0]
    t = json.loads(s["timing_json"])
    record("S10", "interruption", "Opens 'Need help now' in the middle of a Breath reset, closes it.",
           "Exercise pauses while the panel is open; that time is not counted in the exercise duration.",
           f"'paused' shown: {paused_label}; paused_ms={t['paused_ms']}, active_ms={t['active_ms']}, wall_ms={t['wall_ms']}.",
           paused_label and t["paused_ms"] >= 3500 and t["active_ms"] < t["wall_ms"] - 3000)
    record("S11", "interruption", "Taps Stop partway through.",
           "Neutral 'You stopped. That's fine.' screen; saved as stopped, not as a failure.",
           f"status={s['status']}, steps_completed={s['steps_completed']}; screen says: '{page.locator('[data-testid=stopped] h2').inner_text()}'.",
           s["status"] == "stopped", snap(page, "s11-stopped"))
    page.click("[data-testid=back-home]")

    # S12 ground
    page.click("[data-testid=start-ground]")
    page.wait_for_selector("[data-testid=ground-pad]", timeout=8000)
    help_visible(page, "ground exercise")
    for n in [5, 4, 3, 2, 1]:
        page.wait_for_selector(f"[data-testid=ground-pad] .dot:nth-child({n})")
        for _ in range(n):
            page.click("[data-testid=ground-pad]")
            page.wait_for_timeout(2500)
        page.wait_for_timeout(700)
    page.wait_for_selector("[data-testid=done]", timeout=10000)
    s = q("SELECT * FROM sessions WHERE kind='ground' ORDER BY id DESC LIMIT 1")[0]
    t = json.loads(s["timing_json"])
    record("S12", "ordinary", "Does a Ground reset, tapping once every 2.5 s (the planned pace).",
           "One sense per screen, no typing; finishes under 90 s.",
           f"status={s['status']}, measured {s['duration_s']} s.",
           s["status"] == "completed" and s["duration_s"] < 90)
    page.click("[data-testid=back-home]")

    # S13 usual + not today
    home(page)
    usual_label = page.locator("[data-testid=start-usual]").inner_text() if page.locator("[data-testid=start-usual]").count() else "none"
    record("S13", "ordinary", "Comes back home after finishing two Breath resets and one Ground reset.",
           "'Your usual: Breath reset' appears without any setup.", f"Shown: '{usual_label}'.",
           "Breath" in usual_label, snap(page, "s13-usual"))

    # S14 profile + personalized journal
    page.click("[data-testid=open-profile]")
    help_visible(page, "profile")
    page.fill("[data-testid=profile-name]", "Maya")
    page.fill("[data-testid=profile-activity]", "swimming")
    page.click("[data-testid=profile-save]")
    page.wait_for_timeout(500)
    page.click("text=Back to home")
    page.click("[data-testid=checkin-scattered]")
    page.click("[data-testid=open-journal]")
    help_visible(page, "journal")
    page.fill("[data-testid=journal-input]", "I feel overwhelmed about my swim meet on Saturday.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("document.querySelectorAll('[data-testid=journal-msg]').length >= 2")
    reply = page.locator("[data-testid=journal-msg]").nth(1).inner_text()
    page.click("[data-testid=journal-context]")
    page.wait_for_function("document.querySelector('[data-testid=journal-context-text]')?.textContent.includes('CONTEXT')")
    ctxt = page.locator("[data-testid=journal-context-text]").inner_text()
    record("S14", "ordinary", "Fictional user 'Maya' saves her name and 'swimming', checks in as Scattered, and writes she is overwhelmed about a swim meet.",
           "Reply is calm, uses her name once, offers her usual reset as an option; context shows name, activity, check-in, usual.",
           f"Reply: \"{reply}\" Context has name/activity/check-in: {'Maya' in ctxt and 'swimming' in ctxt and 'scattered' in ctxt}.",
           reply.startswith("Thanks for writing, Maya.") and "usual Breath reset" in reply and "swimming" in ctxt,
           snap(page, "s14-journal-personalized"))

    # S15 sports slang
    page.fill("[data-testid=journal-input]", "Honestly this workout block is killing me.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("document.querySelectorAll('[data-testid=journal-msg]').length >= 4")
    panel = page.locator("[data-testid=crisis-panel]").count()
    record("S15", "ordinary", "Writes 'this workout block is killing me'.",
           "Treated as a figure of speech: normal reply, no crisis panel.",
           f"Crisis panel opened: {bool(panel)}.", panel == 0)
    page.click("[data-testid=journal-done]")

    # S16 crisis phrase
    calls_before = q("SELECT COUNT(*) n FROM llm_calls WHERE purpose='journal'")[0]["n"]
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "I don't want to be alive anymore")
    page.click("[data-testid=journal-send]")
    page.wait_for_selector("[data-testid=crisis-panel]")
    page.wait_for_function("[...document.querySelectorAll('[data-testid=journal-msg]')].some(e => e.dataset.source === 'static')")
    calls_after = q("SELECT COUNT(*) n FROM llm_calls WHERE purpose='journal'")[0]["n"]
    flagged = q("SELECT crisis_flag FROM messages ORDER BY id DESC LIMIT 2")
    record("S16", "failure", "Writes a crisis-related sentence in the Journal (fictional).",
           "Crisis panel opens at once; fixed message; model not called; both messages flagged.",
           f"Panel open; model calls before/after: {calls_before}/{calls_after}; flags: {[f['crisis_flag'] for f in flagged]}.",
           calls_before == calls_after and all(f["crisis_flag"] == 1 for f in flagged),
           snap(page, "s16-crisis-input"))
    page.click("[data-testid=crisis-panel] >> text=Close")

    # S17 indirect wording (known miss)
    page.fill("[data-testid=journal-input]", "I just want to disappear for good")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("document.querySelectorAll('[data-testid=journal-msg]').length >= 4")
    panel = page.locator("[data-testid=crisis-panel]").count()
    record("S17", "failure", "Writes indirect wording: 'I just want to disappear for good'.",
           "Known limit: the phrase list does not catch this. The Need help now button must still be there.",
           f"Panel opened automatically: {bool(panel)}; Need help now visible: {help_visible(page, 'journal after miss')}.",
           panel == 0 and page.locator("[data-testid=need-help]").is_visible())
    page.click("[data-testid=journal-done]")

    # S18 memory off
    httpx.put(f"{API}/profile", json={"remember_journal": False})
    ctx_off = httpx.get(f"{API}/journal/context").json()["context"]
    record("S18", "ordinary", "Turns off 'Let the companion see my past journal entries'.",
           "Context no longer includes earlier entries and tells the model not to mention them.",
           f"Earlier entry text in context: {'swim meet' in ctx_off}; 'turned off' note: {'turned off' in ctx_off}.",
           "swim meet" not in ctx_off and "turned off" in ctx_off)
    httpx.put(f"{API}/profile", json={"remember_journal": True})

    # S19 model failure
    httpx.post(f"{API}/dev/llm-mode", json={"mode": "fail"})
    home(page)
    open_src = page.locator("[data-testid=opening-line]").get_attribute("data-source")
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "Rough day at the pool.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("[...document.querySelectorAll('[data-testid=journal-msg]')].some(e => e.dataset.source === 'fallback')")
    page.click("[data-testid=need-help]")
    panel_ok = page.locator("[data-testid=crisis-panel]").is_visible()
    help_visible(page, "journal with model failing")
    record("S19", "failure", "The model fails (switched to fail mode), then the user writes in the Journal.",
           "Fallback lines on home and in the Journal; message still saved; crisis panel still works.",
           f"Home line source={open_src}; journal reply source=fallback; crisis panel opened: {panel_ok}.",
           open_src == "fallback" and panel_ok, snap(page, "s19-model-fail"))
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.click("[data-testid=journal-done]")
    httpx.post(f"{API}/dev/llm-mode", json={"mode": "mock"})

    # S20 larger text persists
    page.click("[data-testid=open-profile]")
    page.click("[data-testid=large-text]")
    page.wait_for_timeout(400)
    page.reload()
    page.wait_for_function("document.documentElement.classList.contains('large-text') || true")
    page.wait_for_timeout(800)
    large = page.evaluate("document.documentElement.classList.contains('large-text')")
    record("S20", "ordinary", "Turns on Larger text, then reloads the app.",
           "Text stays larger after reload because the setting is saved.", f"Larger text after reload: {large}.",
           large, snap(page, "s20-large-text"))
    httpx.put(f"{API}/profile", json={"large_text": False})

    # S21 history review
    page.goto(URL)
    page.click("text=History")
    page.wait_for_selector("[data-testid=history-item]")
    items = page.locator("[data-testid=history-item]").count()
    help_visible(page, "history")
    record("S21", "ordinary", "Opens History.",
           "Shows each reset with Done/Stopped and length, and each journal entry by its first line.",
           f"{items} items listed.", items >= 6, snap(page, "s21-history"))

    # S22 backend down
    snap(page, "_tmp")
    (HERE / "_tmp.png").unlink()
    subprocess.run(["kill", (PID_DIR / "backend.pid").read_text().strip()])
    time.sleep(1.5)
    page.goto(URL)
    page.wait_for_selector("[data-testid=offline-note]")
    page.click("[data-testid=need-help]")
    panel_ok = page.locator("[data-testid=crisis-panel]").is_visible()
    help_visible(page, "home with backend down")
    snap(page, "s22-backend-down")
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.click("[data-testid=start-breath]")
    page.check("text=Just the circle")
    page.click("[data-testid=begin]")
    page.wait_for_timeout(4000)
    runs = page.locator("[data-testid=breath-run]").count() == 1
    not_saved = page.locator("text=Not being saved right now.").count() == 1
    record("S22", "failure", "The backend is stopped; the user opens the app, opens Need help now, and starts a Breath reset.",
           "Crisis panel works (static); exercise still runs and says it isn't being saved.",
           f"Crisis panel opened: {panel_ok}; exercise running: {runs}; 'not saved' note: {not_saved}.",
           panel_ok and runs and not_saved)
    page.click("[data-testid=stop]")
    browser.close()

# Behavior checks over everything above (backend is stopped now, read the DB file directly)
journal_user_msgs = q("SELECT COUNT(*) n FROM messages m JOIN sessions s ON s.id=m.session_id WHERE s.kind='journal' AND m.role='user' AND m.crisis_flag=0")[0]["n"]
journal_calls = q("SELECT COUNT(*) n FROM llm_calls WHERE purpose='journal'")[0]["n"]
crisis_user = q("SELECT COUNT(*) n FROM messages WHERE role='user' AND crisis_flag=1")[0]["n"]
behavior["B2"] = {"journal user messages without crisis flag": journal_user_msgs,
                  "journal model calls": journal_calls, "crisis-flagged user messages": crisis_user,
                  "pass": journal_calls == journal_user_msgs}

import re  # noqa: E402
blocked = re.compile(r"diagnos|disorder|therapist|monitor|!|great job|proud of you", re.I)
assistant = q("SELECT content, source FROM messages WHERE role='assistant'")
bad = [m for m in assistant if blocked.search(m["content"]) and m["source"] != "static"]
behavior["B3"] = {"assistant messages checked": len(assistant), "with blocked words": len(bad), "pass": not bad}

planned = {r["skill"]: r["s"] for r in q("SELECT skill, SUM(duration_s) s FROM skill_steps GROUP BY skill")}
completed = q("SELECT kind, duration_s FROM sessions WHERE status='completed' AND kind IN ('breath','ground')")
behavior["B4"] = {"planned_s": planned, "completed_runs": completed,
                  "pass": all(v <= 90 for v in planned.values()) and all(c["duration_s"] <= 90 for c in completed)}
b1_pass = all(x["visible"] for x in behavior["B1"])

(HERE / "results.json").write_text(json.dumps({"scenarios": results, "behavior_checks": behavior}, indent=2))

# Markdown table
lines = ["| # | Type | What the user does | Expected | Observed | Result |", "|---|---|---|---|---|---|"]
for r in results:
    obs = r["observed"].replace("|", "/")
    shot = f" ([screenshot]({r['screenshot']}))" if r["screenshot"] else ""
    lines.append(f"| {r['id']} | {r['type']} | {r['user_does']} | {r['expected']} | {obs}{shot} | {'Pass' if r['pass'] else 'Fail'} |")
(HERE / "scenarios-table.md").write_text("\n".join(lines) + "\n")
print(f"\n{sum(r['pass'] for r in results)}/{len(results)} scenarios passed")
print("B1 Need help visible on", len(behavior["B1"]), "screens:", b1_pass)
print("B2", behavior["B2"])
print("B3", behavior["B3"])
print("B4 pass:", behavior["B4"]["pass"], planned)
