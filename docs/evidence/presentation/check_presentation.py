"""Screenshots of the features added for the in-class presentation (Oct 29).
Runs against the local dev servers with LLM_MODE=mock DEV_ENDPOINTS=1. Fictional persona only."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
URL = "http://localhost:5173/"


def shot(page, name):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print("screenshot", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 480, "height": 900})
    page.goto(URL)
    page.click("[data-testid=open-profile]")
    page.click("text=Prototype tools")
    page.click("[data-testid=seed-demo]")
    page.wait_for_function("document.querySelector('[data-testid=profile-name]').value === 'Sofia'")
    page.click("text=Back to home")
    page.wait_for_selector("[data-testid=hello]")
    page.wait_for_selector("[data-testid=start-usual]")
    shot(page, "p01-home-returning-user")

    page.click("[data-testid=checkin-wound_up]")
    page.wait_for_selector("[data-testid=show-all]")
    assert page.locator("[data-testid=open-journal]").count() == 0
    shot(page, "p02-checkin-wound-up-contracted")
    page.click("[data-testid=show-all]")
    shot(page, "p03-show-all-override")

    page.click("[data-testid=checkin-change]")
    page.click("[data-testid=checkin-scattered]")
    page.wait_for_selector("[data-testid=suggested] [data-testid=start-ground]")
    shot(page, "p04-checkin-scattered-ground-first")

    page.click("[data-testid=open-profile]")
    page.wait_for_selector("[data-testid=profile-facts]")
    page.click("[data-testid=show-context]")
    page.wait_for_selector("[data-testid=context]")
    shot(page, "p05-profile-what-is-saved")
    page.click("[data-testid=large-text]")
    page.wait_for_function("document.documentElement.classList.contains('large-text')")
    shot(page, "p06-larger-text")
    page.click("[data-testid=large-text]")

    page.click("text=Back to home")
    page.click("[data-testid=open-journal]")
    page.fill("[data-testid=journal-input]", "I feel overwhelmed about my race on Saturday.")
    page.click("[data-testid=journal-send]")
    page.wait_for_function("document.querySelectorAll('[data-testid=journal-msg]').length >= 2")
    page.click("[data-testid=journal-context]")
    page.wait_for_selector("[data-testid=journal-context-text]")
    shot(page, "p07-journal-personalized-reply-and-context")
    print("reply:", page.locator("[data-testid=journal-msg]").nth(1).inner_text())
    print("voice button:", page.locator("[data-testid=voice]").count())
    b.close()
