# AGENTS.md: Rules for the coding agent

Read `docs/design.md` (especially section 12, the 3.2 changes) before changing anything. If a change conflicts with it, stop and ask instead of guessing.

## What this project is
A local coursework prototype (Vue 3 + FastAPI + SQLite + Claude API) with two skills, Breath reset (4–6 paced breathing, optional mic or press-and-hold sensing) and Ground reset (5-4-3-2-1 grounding by taps), plus a Journal chat. It is not a mental health tool.

## Layout
- `backend/app/main.py`: API routes. `db.py`: schema and fixed skill steps. `llm.py`: model access and mock/fail modes. `safety.py`: crisis check and reply filter. `prompts/`: system prompts. `mock_responses.json`: saved replies.
- `frontend/src/App.vue`: header with Need help now, view switching. `components/`: one file per screen. `lib/api.js`: backend calls. `lib/crisis.js`: frontend copy of the crisis phrase list. `lib/breathSensor.js`: mic sensing. `lib/demoApi.js`: in-browser mock, used only by the preview build.
- `docs/evidence/<part>/`: screenshots, DB inspection, test output.

## Never break these
1. **Need help now** is visible on every screen, in the same place, including inside exercises. Its panel is static frontend content. It must never call the backend or the model and must work with the backend stopped.
2. **Skill steps are fixed** in `SKILL_STEPS` in `db.py`. The model never generates or changes steps.
3. **Stop** is on every exercise screen. Stopping goes to a neutral screen and saves `status='stopped'`. Never use words like "fail", "quit", or "incomplete" in the UI.
4. **No timer kicks the user out.** Exercises pause while the crisis panel is open, and paused time is not counted.
5. **One action per screen** inside exercises.
6. **No scores, streaks, badges, or "personal best"**, even with the sports framing. Breath sensing results are saved but never shown as a score.
7. Crisis phrase check runs **before** any model call on user text, in the frontend and the backend. On a match: don't call the model, show the fixed message, open the crisis panel, save `crisis_flag=1`. Never put crisis-flagged messages into model context.
8. Model calls happen in the backend only. Short lines time out at 3 s, journal replies at 12 s. Any error or filtered reply uses a fixed fallback line. The app must work with no API key (`LLM_MODE=mock`).
9. Microphone audio is analyzed in the browser only. Never record, store, or send it.
10. Never imply the app monitors the user or that someone will follow up. Never claim it is therapy.

## Tone of all UI text and model output
Short, plain, calm. No exclamation marks, no emojis, no clinical terms, no coach hype. Sports words only as calm framing ("reset"). Any new mock line must pass `clean_reply()` (there is a test for this).

## Timing budget
Breath reset is 66 s from first instruction to final step; Ground reset is planned at 55.5 s and must stay under 90 s at 4 s per item. Re-check timing if you change steps or transitions.

## Testing
- `cd backend && python -m pytest -q` (all mocked, no API calls).
- Use `LLM_MODE=mock` for automated tests. Mark any live-model results separately. Live calls are capped by `LLM_CALL_LIMIT` (default 50), then the app switches to mock.
- Use fictional scenarios only.
- Record test results and notable decisions in `docs/evidence-log.md`.

## Repo hygiene
Never commit `.env`, API keys, or `*.db` files.
