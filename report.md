# Assignment 3.1: Research and Design Report

**Student:** Fernanda Garza
**Repository:** https://github.com/ferrgarzaa/reset-skills-prototype
**Submitted commit:** see the copy of this report submitted on Canvas

> Coursework prototype only. Not a mental health tool, not therapy, no monitoring. Fictional scenarios only.

## Links
- Design notes (flow diagram, screen sketches, decisions, model role, data, timing, open questions): [`docs/design.md`](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md)
- Evidence log: [`docs/evidence-log.md`](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md)
- README: [`README.md`](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md) · Agent rules: [`AGENTS.md`](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md) · AI use: [`AI-USE.md`](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)
- Recordings: none for this milestone

## The idea
**Reset** is a short-skills app framed like the quick reset athletes take between plays. It offers two skills: **Breath reset** (paced breathing 4 in / 6 out) and **Ground reset** (5-4-3-2-1 grounding, done with taps instead of typing). The sports part is just framing, which is my own interest. I kept it calm on purpose: no scores, streaks, or coach-style hype, because D6 says cheerful phrasing felt condescending and D3 counts "having to perform" as an emotional cost.

## Main design choices
- **Two low-effort skills** (D3, R1). I dropped the reframe because it needs typing and thinking that don't fit D3 or 90 seconds.
- **One action per screen** (D2). Grounding shows one sense at a time, and you tap a dot each time you notice something.
- **The user picks.** Home has Breath, Ground, and "Your usual" once you've done one (R4, D5). Personalization comes from history, with no settings to fill out.
- **Stop is always there**, and stopping goes to a neutral screen with no penalty (R3).
- **Need help now** is fixed on every screen and is static content (988, Crisis Text Line, 911). It works even if the model or the backend is down (R2, D4).
- **D1 without a detector:** the screen gets simpler as you go deeper (home > exercise > done), not based on guessing how someone feels. I decided against inferring distress from clicks because it could be wrong and feel like monitoring.

## Role of the model
Claude only writes short opening/closing lines and replies once to an optional note. The skill steps, timing, exits, crisis panel, and saving are all in code. The prompt bans diagnosis, advice, hype, and anything implying monitoring, and a code check replaces bad or long replies with a fallback line. On timeout or error, the app uses a fixed line and keeps going.

**Crisis-related input:** the optional note is checked against a keyword list *before* any model call. On a match, the model isn't called, a fixed message shows, and the crisis panel opens. The limits: it misses indirect wording and flags sports slang like "this drill is killing me". I accept extra false positives because a false positive only opens an info panel.

## Data stored
SQLite tables: `sessions` (skill, done/stopped, duration, optional 1-tap feedback), `messages` (model and user lines, source, crisis flag), and `skill_steps` (the fixed script). History shows date, skill, Done/Stopped, and length, with a "Clear history" button.

## Timing
Breath reset ≈ **66 s** (3 s instruction + 6 × 10 s breaths + 3 s close). Ground reset ≈ **56 s** at 2.5 s per item, **78 s** at 4 s per item. Entry is ~3–5 s, counted separately. No timer ever ends the exercise.

## What's complete
The design, flow diagram, screen sketches, decision table linked to R1–R4/D1–D6, model role and limits, crisis decision, data model, timing estimates, and project docs.

## What's unresolved
- Whether the sports framing works for non-sports users.
- Whether the breathing exercise should also offer a shorter version.
- Whether to save free-text notes at all.
- Whether the optional note + reply is "conversational" enough.
- The size of the crisis keyword list and how to test misses.
- I still need to review existing breathing/grounding app interfaces.

Full list in `docs/design.md` §10.
