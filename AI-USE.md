# AI Use Disclosure

| Tool / model | Identifier | Where | Role |
|---|---|---|---|
| Claude (claude.ai app) | Claude Opus 5.5 (`claude-opus-5-5`) | Part 3.1 | Asked me questions to settle design choices, then drafted the design notes, README, AGENTS.md, report, and this file from my decisions. I reviewed and edited them. |
| Claude (claude.ai app, agent mode) | Claude Opus 5.5 (`claude-opus-5-5`) | Part 3.2 | Turned my instructor's suggestions and my choices into code: the FastAPI backend, the Vue frontend, the Journal system prompt, the tests, and the browser evidence script. It also ran the app, took the screenshots, inspected the database, and drafted the 3.2 report and docs. I reviewed the results and asked for changes. |
| Claude via Anthropic API | `claude-haiku-5-5` (set by `MODEL_ID`) | Inside the app | Writes short opening and closing lines and the Journal companion's replies. It does not generate skill steps. Not used live yet; all 3.2 evidence uses mock replies. |

## My decisions (not generated)
In 3.1 I chose the two skills, the endurance-sport "reset" framing, a tap-based entry with "Your usual", a small model role, an always-visible crisis button with a keyword check, and starting from a clean project.

In 3.2 I chose which of my instructor's suggestions to build now (breath sensing and the Journal) and which to leave for 3.3 (voice and drawing), and I chose to offer both microphone and press-and-hold for breath sensing.

## How I check AI output
I read the generated documents against the assignment and the R/D findings and change anything I don't agree with or can't explain. For code, I rely on the automated tests (mocked), the browser screenshots, and the database inspection in `docs/evidence/`, and I record failures and changes in `docs/evidence-log.md`.
