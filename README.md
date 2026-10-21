# Reset: Skills Prototype (Assignment 3)

A coursework prototype with two short skills, **Breath reset** (paced breathing, 4 in and 6 out, with optional microphone or press-and-hold sensing) and **Ground reset** (5-4-3-2-1 grounding by tapping), plus a **Journal** with a calm journaling companion.

> **This is a class project.** It is not a mental health tool, does not provide therapy, and nobody monitors it. It is tested only with fictional scenarios. Do not share it or recommend it to anyone as support during a hard moment.

## Status

| Part | Status |
|---|---|
| 3.1 Research and Design | Done. [Report](reports/3.1/report.md) |
| 3.2 Working Application and Safety | Done with mocked model replies. [Report](reports/3.2/report.md), [evidence](docs/evidence/3.2/README.md) |
| 3.3 Integration and Evaluation | Not started |

## Run it

You need Python 3.11+ and Node 18+.

**Backend** (terminal 1):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

The backend runs in `LLM_MODE=mock` by default, so no API key is needed. To use the live model, set `LLM_MODE=live` and `ANTHROPIC_API_KEY=...` in `backend/.env`. Live calls stop after `LLM_CALL_LIMIT` (default 50) and the app switches to mock replies.

To see what happens when the model fails, open History, then Prototype tools, then choose **fail**. This only works when `DEV_ENDPOINTS=1`.

## Tests and inspection

```bash
cd backend
python -m pytest -q                # all tests use mocked replies
python tools/inspect_db.py         # prints the SQLite tables
```

## Where things are

- `docs/design.md`: design, decisions linked to R1–R4 and D1–D6, model role, crisis route, timing, data, and the 3.2 changes (section 12)
- `docs/evidence/`: screenshots, database output, test results
- `docs/evidence-log.md`: decisions, revised approaches, failures
- `backend/app/prompts/journal_system.md`: the Journal system prompt
- `AGENTS.md`: rules for the coding agent
- `AI-USE.md`: AI tools used and how

## Planned stack

Vue 3 (Vite), FastAPI, SQLite, and the Anthropic API (Claude, called only from the backend).
