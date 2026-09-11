# Expedia Lite

Expedia Lite is a small travel-search application with a FastAPI backend and a Vue frontend.

## Project layout

- `backend/` — FastAPI service and API code.
- `frontend/` — Vue client application.
- `AGENTS.md` — project conventions for contributors and coding agents.
- [`docs/design-pipeline.md`](docs/design-pipeline.md) — application boundaries and review flow.
- [`docs/report.md`](docs/report.md) — Part 1 implementation and verification evidence.
- [`prompts/`](prompts/) — reusable prompts from the project workflow.
- [`handoffs/`](handoffs/) — project handoff notes.

## Getting started

Python 3.10 or newer is required. The backend environment can be created from the project root with:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

The frontend requires Node.js `^22.18.0` or `>=24.12.0`. Install and verify it from the project root with:

```sh
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

Run the FastAPI development server and the Vue development server in separate terminals.

The initial API includes `GET /health` as a service health check.
