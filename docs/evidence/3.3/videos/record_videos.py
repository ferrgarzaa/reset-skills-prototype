"""Records the two Part 3.3 videos with Playwright, using the real app on localhost.

1. demo.mp4: walkthrough of the finished app with a fictional user.
2. process.mp4: one failure, the evidence used to understand it, the decision,
   and an explanation of a piece of generated code.

Captions are drawn in a side panel next to the app, so nothing in the app is covered.
Run from the repo root with the frontend dev server on :5173. The script starts and stops
the backend itself (port 8000, LLM_MODE=mock, DEV_ENDPOINTS=1).

    python docs/evidence/3.3/videos/record_videos.py
"""
import html
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
MOCKS = BACKEND / "app/mock_responses.json"
DB = BACKEND / "data/reset.db"
URL = "http://localhost:5173/"
W, H = 1280, 720
proc = None


def start_backend(fresh=True):
    global proc
    subprocess.run("fuser -k 8000/tcp", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(1)
    if fresh and DB.exists():
        DB.unlink()
    env = dict(os.environ, LLM_MODE="mock", DEV_ENDPOINTS="1")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
                            cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)


def stop_backend():
    if proc:
        proc.terminate()
        proc.wait()


PANEL_JS = """([section, text]) => {
  let p = document.getElementById('__cap');
  if (!p) {
    p = document.createElement('div'); p.id = '__cap';
    p.style.cssText = 'position:fixed;left:24px;top:96px;width:330px;z-index:99999;font-family:system-ui,sans-serif;' +
      'background:#22292b;color:#f1efe9;border-radius:14px;padding:18px 20px;box-shadow:0 4px 18px rgba(0,0,0,.18);';
    document.documentElement.appendChild(p);
  }
  p.innerHTML = '<div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#9fc0b5;margin-bottom:8px">' +
    section + '</div><div style="font-size:18px;line-height:1.45">' + text + '</div>';
}"""


def cap(page, section, text, ms=3500):
    page.evaluate(PANEL_JS, [section, text])
    page.wait_for_timeout(ms)


def keep_caption(page):
    # Re-add the panel after a full page load.
    page.on("load", lambda: None)


def doc_page(page, section, title, body_html, caption, ms):
    """Shows an evidence or code page (real data/code, rendered as HTML) in the same browser."""
    page.set_content(f"""<!doctype html><html><head><meta charset=utf-8><style>
      body{{margin:0;background:#f3f1ec;color:#2c3134;font-family:system-ui,sans-serif}}
      main{{margin-left:400px;margin-right:40px;padding-top:40px}}
      h1{{font-size:24px;margin:0 0 16px}} pre{{background:#fbfaf7;border:1px solid #dcd8cf;border-radius:10px;
      padding:14px 16px;font-size:13px;line-height:1.5;white-space:pre-wrap;overflow:hidden}}
      .hl{{background:#f3e4df;color:#8c4a3c;font-weight:700}} .ok{{color:#3e6b5d;font-weight:700}}
      p{{font-size:16px;line-height:1.5;max-width:760px}}
    </style></head><body><main><h1>{title}</h1>{body_html}</main></body></html>""")
    cap(page, section, caption, ms)


def new_context(p, name):
    browser = p.chromium.launch(args=["--use-fake-ui-for-media-stream"])
    ctx = browser.new_context(viewport={"width": W, "height": H}, permissions=["microphone"],
                              record_video_dir=str(OUT / f"_raw_{name}"),
                              record_video_size={"width": W, "height": H})
    return browser, ctx


def finish_video(ctx, browser, page, name):
    raw = page.video.path()
    ctx.close()
    browser.close()
    tmp = OUT / f"{name}.tmp.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-vf", "fps=30,format=yuv420p",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-movflags", "+faststart",
                        str(tmp)])
    if r.returncode == 0:
        tmp.rename(OUT / f"{name}.mp4")
    shutil.rmtree(OUT / f"_raw_{name}", ignore_errors=True)


# ---------------------------------------------------------------- demo

def demo(p):
    start_backend(fresh=True)
    browser, ctx = new_context(p, "demo")
    page = ctx.new_page()
    S = "Reset demo"
    page.goto(URL)
    page.wait_for_timeout(1200)
    cap(page, S, "Reset is a coursework skills prototype by Fernanda Garza. It is not therapy. "
        "Everything here uses a fictional user and mocked model replies (no API key).", 6000)

    # load fictional persona
    page.click("[data-testid=open-profile]")
    page.click("text=Prototype tools")
    cap(page, "Setup", "To show personalization over time, I load a made-up user, Sofia, "
        "with a week of example resets, check-ins and one journal entry.", 4500)
    page.click("[data-testid=seed-demo]")
    page.wait_for_function("document.querySelector('[data-testid=profile-name]').value === 'Sofia'")
    page.click("text=Back to home")
    page.wait_for_selector("[data-testid=hello]")
    cap(page, "1 · Returning user", "Home greets her by name and offers 'Your usual: Breath reset', "
        "learned from what she finished most. No setup needed (D5).", 6000)

    # check-in
    cap(page, "2 · User state", "The only information about how she feels right now is this optional one-tap "
        "check-in. The app never guesses (D1 does not tell us how to detect distress).", 6000)
    page.click("[data-testid=checkin-wound_up]")
    cap(page, "2 · User state", "'Wound up' makes the screen contract to one suggestion: Breath reset (D1: show less "
        "when things are harder).", 6000)
    page.click("[data-testid=show-all]")
    cap(page, "2 · User state", "She can always override it: 'Show all options' brings everything back (R4).", 4500)
    page.click("[data-testid=checkin-change]")
    page.click("[data-testid=checkin-scattered]")
    cap(page, "2 · User state", "'Scattered' moves Ground reset to the top. These mappings are my assumptions, "
        "so 'Change' and 'Clear' are always there.", 6000)

    # breath
    page.click("[data-testid=start-breath]")
    cap(page, "3 · Breath reset", "Setup (entry time, measured separately). She chooses how to follow along: "
        "just the circle, the microphone, or press and hold.", 6000)
    page.check("[data-testid=sense-hold]")
    page.click("[data-testid=begin]")
    cap(page, "3 · Breath reset", "One action per screen (D2). In for 4, out for 6, six times: 66 s planned, "
        "under the 90 s limit (R1).", 3000)
    box = page.locator(".circle-wrap").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    notes = [
        "She holds the circle while breathing in and lets go while breathing out.",
        "'with you' shows the breath matched. There is never a score afterward (D3).",
        "Need help now stays in the header during the exercise (D4).",
    ]
    for k in range(3):
        page.wait_for_function("document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe in')", timeout=25000)
        page.evaluate(PANEL_JS, ["3 · Breath reset", notes[k]])
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.wait_for_timeout(3000)
        page.mouse.up()
        page.wait_for_function("document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe out')", timeout=25000)
        page.wait_for_timeout(4500)
    page.click("[data-testid=need-help]")
    cap(page, "4 · Support", "The crisis panel is static content in the page. It works even if the model or the "
        "server is down (R2), and the exercise pauses while it is open.", 6500)
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.wait_for_timeout(1500)
    page.click("[data-testid=stop]")
    cap(page, "4 · Stopping", "Stop is on every exercise screen. Leaving costs nothing: 'You stopped. That's fine.' (R3)", 5000)
    page.click("[data-testid=back-home]")

    # ground
    page.click("[data-testid=start-ground]")
    page.wait_for_selector("[data-testid=ground-pad]", timeout=8000)
    cap(page, "5 · Ground reset", "5-4-3-2-1 grounding, one sense per screen. She taps a dot for each thing she "
        "notices, so there is nothing to type (D3).", 3000)
    for _ in range(5):
        page.click("[data-testid=ground-pad]")
        page.wait_for_timeout(900)
    page.wait_for_timeout(1200)
    cap(page, "5 · Ground reset", "The next sense appears on its own when all dots are filled.", 3500)
    page.click("[data-testid=stop]")
    page.click("[data-testid=back-home]")

    # journal
    page.click("[data-testid=open-journal]")
    cap(page, "6 · Journal", "An optional journaling space, kept outside the exercises. It says it is not a "
        "therapist and that nobody else reads it.", 5000)
    page.fill("[data-testid=journal-input]", "I feel overwhelmed about my race on Saturday.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("document.querySelectorAll('[data-testid=journal-msg]').length >= 2")
    cap(page, "6 · Journal", "The reply uses her name once and offers her usual reset as an option. Short, calm, "
        "no 'you should', no clinical words (D6). This is a mocked reply.", 7000)
    page.click("[data-testid=journal-context]")
    page.wait_for_function("document.querySelector('[data-testid=journal-context-text]')?.textContent.includes('CONTEXT')")
    page.locator("[data-testid=journal-context-text]").scroll_into_view_if_needed()
    cap(page, "6 · Journal", "This is exactly what the model is told: name, activity, today's check-in, usual "
        "reset, recent resets and how her last entry began. Nothing else.", 7500)

    page.fill("[data-testid=journal-input]", "Honestly I don't want to be alive anymore")
    page.click("[data-testid=journal-send]")
    page.wait_for_selector("[data-testid=crisis-panel]")
    cap(page, "7 · Crisis input (fictional)", "A crisis phrase is caught in code before any model call. The panel "
        "opens right away, a fixed message is saved, and the model is never called.", 7000)
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.wait_for_timeout(1200)
    page.click("[data-testid=journal-done]")

    # failure mode
    page.click("text=History")
    page.click("text=Prototype tools")
    page.click("[data-testid=mode-fail]")
    cap(page, "8 · Model failure", "Here I switch the model to 'fail' to show what happens when a request fails.", 4000)
    page.click("text=Back to home")
    page.wait_for_function("document.querySelector('[data-testid=opening-line]')?.dataset.source === 'fallback'")
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "Rough day at practice.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("[...document.querySelectorAll('[data-testid=journal-msg]')].some(e => e.dataset.source === 'fallback')")
    cap(page, "8 · Model failure", "The app shows a fixed fallback line and still saves her words. Need help now "
        "keeps working.", 6000)
    page.click("[data-testid=journal-done]")
    page.click("text=History")
    page.click("text=Prototype tools")
    page.click("text=mock")
    page.wait_for_selector("[data-testid=history-item]")
    cap(page, "9 · History", "History shows every reset (Done or Stopped, with length) and every journal entry. "
        "All of it is stored in SQLite and can be cleared.", 6000)

    page.click("text=Back to home")
    page.click("[data-testid=open-profile]")
    page.wait_for_selector("[data-testid=profile-facts]")
    cap(page, "10 · Profile", "'You' shows everything the app keeps: what she typed, and what it learned from use. "
        "It updates after every session.", 5500)
    page.click("[data-testid=large-text]")
    cap(page, "10 · Accessibility", "Larger text, taps instead of typing, press and hold instead of the mic, "
        "voice input in the Journal, 44 px targets, dark mode.", 6000)
    page.click("[data-testid=large-text]")
    cap(page, "End", "Mocked: all model replies. Not tested: the live model, a real microphone, other browsers. "
        "Thank you.", 6000)
    finish_video(ctx, browser, page, "demo")
    stop_backend()


# ---------------------------------------------------------------- process screencast

def code_lines(path, start_text, n, highlight=()):
    lines = (ROOT / path).read_text().splitlines()
    i = next(k for k, line in enumerate(lines) if start_text in line)
    out = []
    for k in range(i, min(i + n, len(lines))):
        t = html.escape(lines[k])
        if any(h in lines[k] for h in highlight):
            t = f'<span class="hl">{t}</span>'
        out.append(f"{k + 1:>4}  {t}")
    return f"<p><code>{path}</code></p><pre>" + "\n".join(out) + "</pre>"


def process(p):
    original = MOCKS.read_text()
    bad = json.loads(original)
    bad["closing"] = ["That was your reset. Nothing else you need to do."]
    MOCKS.write_text(json.dumps(bad, indent=2))
    try:
        start_backend(fresh=True)
        browser, ctx = new_context(p, "process")
        page = ctx.new_page()
        S = "Process screencast"
        page.goto(URL)
        page.wait_for_timeout(1000)
        cap(page, S, "This shows one real failure from Part 3.2: what I saw, the evidence I used, and what I "
            "decided. I recreated it by putting the old mock line back.", 7000)

        page.click("[data-testid=start-ground]")
        page.wait_for_selector("[data-testid=ground-pad]", timeout=8000)
        cap(page, "1 · The failure", "I finish a reset in mock mode, where nothing should fail.", 2500)
        page.click("[data-testid=next-sense]")
        for _ in range(4):
            page.click("[data-testid=next-sense]")
            page.wait_for_timeout(300)
        page.wait_for_selector("[data-testid=done]")
        page.wait_for_function("document.querySelector('[data-testid=closing-line]')?.dataset.source")
        src = page.locator("[data-testid=closing-line]").get_attribute("data-source")
        cap(page, "1 · The failure", f"The closing line is the fixed fallback ('That's the reset. Take your time.'). "
            f"The page marks its source as <b>{src}</b>, but the model was never asked to fail.", 8000)

        conn = sqlite3.connect(DB)
        msg = conn.execute("SELECT id, role, source, purpose, content FROM messages ORDER BY id DESC LIMIT 1").fetchone()
        calls = conn.execute("SELECT id, purpose, mode, ok, error FROM llm_calls WHERE purpose='closing' ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        body = ("<p>sqlite&gt; SELECT id, role, source, purpose, content FROM messages ORDER BY id DESC LIMIT 1;</p>"
                f"<pre>{msg[0]} | {msg[1]} | <span class='hl'>{msg[2]}</span> | {msg[3]} | {html.escape(msg[4])}</pre>"
                "<p>sqlite&gt; SELECT id, purpose, mode, ok, error FROM llm_calls WHERE purpose='closing' ORDER BY id DESC LIMIT 1;</p>"
                f"<pre>{calls[0]} | {calls[1]} | {calls[2]} | <span class='ok'>ok={calls[3]}</span> | error={calls[4]}</pre>")
        doc_page(page, "2 · Evidence", "Database after the reset", body,
                 "The saved message says source = fallback, but llm_calls says the mock call succeeded (ok = 1). "
                 "So the call worked and the reply was thrown away afterward.", 10000)
        doc_page(page, "2 · Evidence", "Where replies get thrown away",
                 code_lines("backend/app/safety.py", "BLOCKED_SHORT =", 1, ("you need to",)) +
                 "<p>The mock line being used:</p><pre><span class='hl'>\"That was your reset. Nothing else you need to do.\"</span></pre>",
                 "After a successful call, clean_reply() checks the text. Short lines may not contain "
                 "'you need to'. My own mock line did, so the filter replaced it with the fallback.", 10000)
        doc_page(page, "3 · Decision", "Keep the filter, fix the line, add a test",
                 "<p>The filter did its job, so I kept it. I changed the line to "
                 "<b>\"That was your reset. Nothing else to do right now.\"</b> and added a test so every saved "
                 "line must pass the filter:</p>" +
                 code_lines("backend/tests/test_safety.py", "def test_every_mock_line_passes_the_output_filter", 12),
                 "Decision: fix the content, not the safety rule. The new test fails if any future mock line "
                 "breaks the tone rules.", 10000)
        MOCKS.write_text(original)
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_safety.py"], cwd=BACKEND,
                             capture_output=True, text=True).stdout.strip().splitlines()[-1]
        doc_page(page, "3 · Decision", "Test result after the fix",
                 f"<pre>$ python -m pytest -q tests/test_safety.py\n<span class='ok'>{html.escape(res)}</span></pre>",
                 "With the fixed line back in place, the tests pass.", 5000)

        doc_page(page, "4 · Generated code", "Crisis input never reaches the model",
                 code_lines("backend/app/main.py", "crisis = safety.crisis_match(text)", 7,
                            ("crisis_match", "if crisis", "return")),
                 "This code was generated with Claude, and I checked it with tests. It runs before any model call: "
                 "if the text matches a crisis phrase, it saves both messages with a flag and returns a fixed "
                 "message, so the function ends before the model is ever called.", 12000)
        doc_page(page, "4 · Generated code", "Its limit",
                 code_lines("backend/tests/test_safety.py", "def test_known_miss_is_documented", 4,
                            ("disappear",)),
                 "It is a phrase list, so it misses indirect wording like this. That is why the Need help now "
                 "button never depends on it, and the system prompt also tells the model what to do.", 9000)
        finish_video(ctx, browser, page, "process")
    finally:
        MOCKS.write_text(original)
        stop_backend()


if __name__ == "__main__":
    which = sys.argv[1:] or ["demo", "process"]
    with sync_playwright() as pw:
        if "demo" in which:
            demo(pw)
        if "process" in which:
            process(pw)
