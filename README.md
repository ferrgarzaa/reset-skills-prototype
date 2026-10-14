# Reset: Skills Prototype (Assignment 3)

A coursework prototype for two short skills: **Breath reset** (paced breathing 4–6) and **Ground reset** (5-4-3-2-1 grounding with taps).

> **This is a class project.** It is not a mental health tool, does not provide therapy, and nobody monitors it. It is tested only with fictional scenarios. Do not share it or recommend it to anyone as support during a hard moment.

## Status

| Part | Status |
|---|---|
| 3.1 Research and Design | Design notes done; no app code yet |
| 3.2 Working Application and Safety | Not started |
| 3.3 Integration and Evaluation | Not started |

## Where things are

- `docs/design.md`: concept, flow diagram, screen sketches, decisions linked to R1–R4 / D1–D6, model role, crisis route, timing, data model, open questions
- `docs/evidence-log.md`: decisions, revised approaches, tests
- `AGENTS.md`: rules for the coding agent
- `AI-USE.md`: AI tools used and how
- `report.md`: Part 3.1 submission report

## Planned stack

- Frontend: Vue 3 (Vite) in `frontend/`
- Backend: FastAPI (Python 3.11+) in `backend/`
- Database: SQLite file in `backend/data/reset.db` (ignored by git)
- Model: Anthropic API (Claude), called only from the backend

## How to run (to be filled in Part 3.2)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY, or set MOCK_LLM=1
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Planned environment variables: `ANTHROPIC_API_KEY`, `MODEL_ID` (default `claude-haiku-5-5`), `MOCK_LLM` (1 = use saved responses, no API calls), `LLM_CALL_LIMIT` (default 50, for peer testing).
