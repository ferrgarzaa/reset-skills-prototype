"""Browser evidence for Part 3.2 (Playwright, Python).

Runs against the local dev servers: backend on :8000 with LLM_MODE=mock DEV_ENDPOINTS=1,
frontend on :5173. Pass a folder that contains backend.pid (the backend's process id);
step 10 stops the backend to show the app without a server.

    python docs/evidence/3.2/browser_evidence.py /path/to/folder-with-backend.pid
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/claude/reset-skills-prototype")
OUT = ROOT / "docs/evidence/3.2"
OUT.mkdir(parents=True, exist_ok=True)
SCRATCH = Path(sys.argv[1])
URL = "http://localhost:5173/"
LOG = []


def note(msg):
    print(msg, flush=True)
    LOG.append(msg)


def shot(page, name):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    note(f"screenshot {name}.png")


def console_collector(page, sink):
    page.on("console", lambda m: sink.append(m.text) if "[Reset]" in m.text else None)


def run_breath_hold(page):
    """Full Breath reset with press-and-hold, following the circle."""
    page.click("[data-testid=start-breath]")
    page.check("[data-testid=sense-hold]")
    shot(page, "02-breath-setup-hold")
    page.click("[data-testid=begin]")
    box = page.locator(".circle-wrap").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    for k in range(6):
        page.wait_for_function("document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe in')", timeout=20000)
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.wait_for_timeout(2500)
        if k == 1:
            shot(page, "03-breath-inhale-holding")
        page.mouse.up()
        page.wait_for_function("document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe out')", timeout=20000)
        page.wait_for_timeout(2500)
        if k == 1:
            shot(page, "04-breath-exhale-heard")
    page.wait_for_selector("[data-testid=done]", timeout=20000)
    page.wait_for_function("document.querySelector('[data-testid=closing-line]')?.dataset.source", timeout=10000)


with sync_playwright() as p:
    browser = p.chromium.launch(args=[
        "--use-fake-ui-for-media-stream",
        "--autoplay-policy=no-user-gesture-required",
    ])
    ctx = browser.new_context(viewport={"width": 480, "height": 900}, permissions=["microphone"])
    # Simulated microphone: replaces getUserMedia with generated noise whose volume the test
    # controls, so "breath out" sounds can be lined up with the exhale phase deterministically.
    ctx.add_init_script("""
      navigator.mediaDevices.getUserMedia = async () => {
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
    """)
    page = ctx.new_page()
    timings = []
    console_collector(page, timings)

    # 1. Home, first visit
    page.goto(URL)
    page.wait_for_function("document.querySelector('[data-testid=opening-line]')?.dataset.source !== 'static'")
    shot(page, "01-home-first-visit")

    # 2. Full breath reset with press-and-hold
    t = time.time()
    run_breath_hold(page)
    note(f"breath (hold) wall clock in browser test: {time.time() - t:.1f}s including setup")
    shot(page, "05-done-closing-line")
    page.click("[data-testid=fb-helped]")
    page.click("[data-testid=back-home]")

    # 3. Breath reset with simulated microphone breathing
    page.click("[data-testid=start-breath]")
    page.check("[data-testid=sense-mic]")
    page.click("[data-testid=begin]")
    for k in range(6):
        page.wait_for_function("document.querySelector('[data-testid=cue]')?.textContent.startsWith('Breathe out')", timeout=20000)
        page.wait_for_timeout(500)
        page.evaluate("window.__breath(true)")
        page.wait_for_timeout(3000)
        if k == 2:
            shot(page, "06-breath-mic-heard")
        page.evaluate("window.__breath(false)")
        page.wait_for_function("!document.querySelector('[data-testid=cue]') || !document.querySelector('[data-testid=cue]').textContent.startsWith('Breathe out')", timeout=20000)
    page.wait_for_selector("[data-testid=done]", timeout=20000)
    page.click("[data-testid=back-home]")

    # 4. Crisis panel during an exercise pauses it; then Stop
    page.click("[data-testid=start-breath]")
    page.check("text=Just the circle")
    page.click("[data-testid=begin]")
    page.wait_for_timeout(6000)
    page.click("[data-testid=need-help]")
    page.wait_for_timeout(3000)
    shot(page, "07-crisis-panel-during-exercise")
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.wait_for_timeout(800)
    shot(page, "08-exercise-after-crisis-panel")
    page.click("[data-testid=stop]")
    page.wait_for_selector("[data-testid=stopped]")
    shot(page, "09-stopped")
    page.click("[data-testid=back-home]")

    # 5. Ground reset by taps
    page.click("[data-testid=start-ground]")
    page.wait_for_selector("text=Begin")
    page.wait_for_selector("[data-testid=ground-pad]", timeout=8000)  # intro auto-advances after 3 s
    for i, n in enumerate([5, 4, 3, 2, 1]):
        page.wait_for_selector(f"[data-testid=ground-pad] .dot:nth-child({n})")
        for j in range(n):
            if i == 1 and j == 2:
                shot(page, "10-ground-feel-2-of-4")
            page.click("[data-testid=ground-pad]")
            page.wait_for_timeout(900)
        page.wait_for_timeout(700)
    page.wait_for_selector("[data-testid=done]", timeout=10000)
    page.click("[data-testid=back-home]")
    page.wait_for_selector("[data-testid=start-usual]")
    shot(page, "11-home-your-usual")

    # 6. Journal: ordinary conversation, sports slang not flagged
    page.click("[data-testid=open-journal]")
    shot(page, "12-journal-empty")
    for text in ["Long run went bad today. My legs are dead and I'm annoyed at myself.",
                 "Honestly this training block is killing me, I'm so tired."]:
        page.fill("[data-testid=journal-input]", text)
        page.click("[data-testid=journal-send]")
        page.wait_for_function(f"document.querySelectorAll('[data-testid=journal-msg]').length >= {2 if 'Long' in text else 4}")
    assert page.locator("[data-testid=crisis-panel]").count() == 0
    shot(page, "13-journal-conversation")
    page.click("[data-testid=journal-done]")

    # 7. Journal: crisis-related input
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "I don't want to be alive anymore")
    page.click("[data-testid=journal-send]")
    page.wait_for_selector("[data-testid=crisis-panel]")
    page.wait_for_function("[...document.querySelectorAll('[data-testid=journal-msg]')].some(e => e.dataset.source === 'static')")
    shot(page, "14-journal-crisis-input-panel")
    page.click("[data-testid=crisis-panel] >> text=Close")
    shot(page, "15-journal-crisis-message")
    page.click("[data-testid=journal-done]")

    # 8. Model failure: switch to fail mode
    page.click("text=History")
    page.click("text=Prototype tools")
    page.click("[data-testid=mode-fail]")
    page.wait_for_function("document.querySelector('[data-testid=llm-mode]').textContent === 'fail'")
    page.click("text=Back to home")
    page.wait_for_function("document.querySelector('[data-testid=opening-line]')?.dataset.source === 'fallback'")
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "Rough day at practice.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("[...document.querySelectorAll('[data-testid=journal-msg]')].some(e => e.dataset.source === 'fallback')")
    page.click("[data-testid=need-help]")
    shot(page, "16-model-failed-fallback-and-crisis-panel")
    page.click("[data-testid=crisis-panel] >> text=Close")
    shot(page, "17-model-failed-fallback-reply")
    page.click("[data-testid=journal-done]")
    page.click("text=History")
    page.click("text=Prototype tools")
    page.click("text=mock")

    # 9. History and a saved journal entry
    page.wait_for_selector("[data-testid=history-item]")
    shot(page, "18-history")
    page.click("text=Long run went bad")
    shot(page, "19-history-journal-entry")

    # 10. Backend stopped
    subprocess.run(["kill", (SCRATCH / "backend.pid").read_text().strip()])
    time.sleep(1.5)
    page.goto(URL)
    page.wait_for_selector("[data-testid=offline-note]")
    page.click("[data-testid=need-help]")
    shot(page, "20-backend-down-crisis-panel-works")
    page.click("[data-testid=crisis-panel] >> text=Close")
    page.click("[data-testid=start-breath]")
    page.check("text=Just the circle")
    page.click("[data-testid=begin]")
    page.wait_for_timeout(5000)
    shot(page, "21-backend-down-exercise-still-runs")
    page.click("[data-testid=stop]")

    browser.close()

(OUT / "browser-run-log.txt").write_text("\n".join(LOG) + "\n\nConsole timing logs from the browser:\n" + "\n".join(timings) + "\n")
print("\n".join(timings))
