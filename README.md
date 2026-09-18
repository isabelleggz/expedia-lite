# Expedia Lite

Expedia Lite is a small travel-search application with a FastAPI backend and a Vue frontend.

## Project layout

- `backend/` — FastAPI service and API code.
- `frontend/` — Vue client application.
- `AGENTS.md` — project conventions for contributors and coding agents.

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

Start the backend from `backend/` with:

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend creates `backend/data/expedia_lite.sqlite3` on its first start and
imports the tracked hotel, trip, user, and booking CSV files in one transaction.
A stored seed marker prevents later starts from overwriting updates, restoring
deleted bookings, or duplicating records. The SQLite file is local generated data
and is excluded from version control.

The backend API includes:

- `GET /health`
- `GET /api/v1/hotels/search?hotel_name=...`
- `GET /api/v1/users`
- `POST /api/v1/bookings`
- `GET /api/v1/users/{user_id}/bookings`
- `PATCH /api/v1/bookings/{booking_id}`
- `DELETE /api/v1/bookings/{booking_id}`
