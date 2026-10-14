# AGENTS.md: Rules for the coding agent

Read `docs/design.md` before changing anything. If a change conflicts with it, stop and ask instead of guessing.

## What this project is
A local coursework prototype (Vue + FastAPI + SQLite + Claude API) with two skills: Breath reset (4–6 paced breathing) and Ground reset (5-4-3-2-1 grounding by taps). It is not a mental health tool.

## Never break these
1. **Need help now** is visible on every screen, in the same place, including inside exercises. Its panel is static frontend content. It must never call the backend or the model and must work with the backend stopped.
2. **Skill steps are fixed** in the `skill_steps` table / seed file. The model never generates or changes steps.
3. **Stop** is on every exercise screen. Stopping goes to a neutral screen and saves `status='stopped'`. Never use words like "fail", "quit", or "incomplete" in the UI.
4. **No timer kicks the user out.** Exercises wait if the user is slow.
5. **One action per screen** inside exercises.
6. **No scores, streaks, badges, or "personal best"**, even with the sports framing.
7. Crisis keyword check runs **before** any model call on user text. On a match: don't call the model, show the fixed message, open the crisis panel, save `crisis_flag=1`.
8. Model calls: backend only, ~3 s timeout, fixed fallback line on any error. The app must keep working with no API key when `MOCK_LLM=1`.
9. Never imply the app monitors the user or that someone will follow up. Never claim it is therapy.

## Tone of all UI text
Short, plain, calm. No exclamation marks, no emojis, no clinical terms, no coach hype. Sports words only as calm framing ("reset", "timeout").

## Timing budget
Breath reset ≈ 66 s from first instruction to final step; Ground reset under 90 s at 4 s per item. Re-check timing if you change steps or transitions.

## Testing
- Use `MOCK_LLM=1` for automated tests. Mark any live-model results separately.
- Use fictional scenarios only.
- Record test results and notable decisions in `docs/evidence-log.md`.

## Repo hygiene
Never commit `.env`, API keys, or `*.db` files.
