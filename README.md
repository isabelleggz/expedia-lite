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

Start the backend from `backend/` with:

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend creates `backend/data/expedia_lite.sqlite3` on its first start and
imports the tracked hotel, trip, user, and booking CSV files in one transaction.
A stored seed marker prevents later starts from overwriting updates, restoring
deleted bookings, or duplicating records. The SQLite file is local generated data
and is excluded from version control.

Backend environment configuration is loaded by `backend/app/config.py` from the
project-root `.env` file. Create that ignored local file and add a server-side
Geoapify key:

```dotenv
GEOAPIFY_API_KEY=your_geoapify_key
```

Restart the backend after editing `.env` so the running process loads the updated
setting. The key is used only for backend provider requests. It is never returned
by the search or health APIs and must not be added to frontend configuration.

`GET /api/v1/hotels/nearby?zip=02108` geocodes an exact five-digit U.S. ZIP,
then requests Geoapify places in the `accommodation.hotel` category within a
5 km circle centered on that validated result. The response contains the search
center and only provider-supported place ID, name, address/location text, and
coordinates. Optional provider fields remain `null` when missing. It does not
derive or claim prices, ratings, room availability, booking availability, or an
exhaustive hotel inventory.

Expected nearby-search failures use an `error.code` value that clients can act
on:

| HTTP status | `error.code` | Meaning |
| --- | --- | --- |
| 400 | `invalid_zip` | Input is not exactly five digits. |
| 404 | `unresolved_zip` | Geoapify returned no exact U.S. ZIP match. |
| 404 | `no_nearby_hotels` | No usable hotel places were returned within 5 km. |
| 429 | `geoapify_rate_limited` | Geoapify reported a quota or rate limit. |
| 502 | `geoapify_unavailable` | Provider network, HTTP, or response validation failed. |
| 503 | `geoapify_not_configured` | The server has no usable Geoapify key. |

The backend API includes:

- `GET /health`
- `GET /api/health`
- `GET /api/demo/zip-location`
- `GET /api/v1/hotels/nearby?zip=...`
- `GET /api/v1/hotels/search?hotel_name=...`
- `GET /api/v1/users`
- `POST /api/v1/bookings`
- `GET /api/v1/users/{user_id}/bookings`
- `PATCH /api/v1/bookings/{booking_id}`
- `DELETE /api/v1/bookings/{booking_id}`
