# AI Use Disclosure

| Tool / model | Identifier | Where | Role |
|---|---|---|---|
| Claude (claude.ai app) | Claude Opus 5.5 (`claude-opus-5-5`) | Part 3.1 | Asked me questions to settle design choices, then drafted the design notes, README, AGENTS.md, report, and this file from my decisions. I reviewed and edited them. |
| Claude via Anthropic API | planned `claude-haiku-5-5` | Inside the app (3.2+) | Writes short opening/closing lines and one reply to an optional note. Does not generate skill steps. |

## My decisions (not generated)
I chose: the two skills (breathing + grounding), the sports "reset" framing, a tap-based entry with a "your usual" option instead of a mood check-in, a small model role, an always-visible static crisis button plus a keyword check, and starting from a clean project.

## How I check AI output
I read every generated document against the assignment and the R/D findings and change anything I don't agree with or can't explain. Code generated in later parts will be reviewed, tested, and noted in `docs/evidence-log.md`.

*To be updated in Parts 3.2 and 3.3 with any coding agent or other tools used.*
