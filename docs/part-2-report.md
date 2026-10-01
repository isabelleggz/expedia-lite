# Expedia Lite — Part 2

## Repository and commits

- GitHub repository: [https://github.com/isabelleggz/expedia-lite](https://github.com/isabelleggz/expedia-lite)
- Part 1 checkpoint: [`c2f60bd3a7f3d7da61411cc40aef54f330d65bd1`](https://github.com/isabelleggz/expedia-lite/commit/c2f60bd3a7f3d7da61411cc40aef54f330d65bd1)
- Part 2 submission commit: [`56f7e44353cbdef32308dd91c84b728880a27bff`](https://github.com/isabelleggz/expedia-lite/commit/56f7e44353cbdef32308dd91c84b728880a27bff) — `Merge Part 2 SQLite booking workflow`

Part 2 was developed on `feature/part-2-sqlite-bookings`, reviewed, merged into
`main`, verified again as the combined application, and pushed normally to
`origin/main`. The Part 1 checkpoint remains in the submitted history.

## Demo video


## Implementation

### Part 1 behavior retained

The Vue frontend still sends a full or partial hotel name to the versioned
FastAPI endpoint `GET /api/v1/hotels/search?hotel_name=...`. FastAPI returns a
JSON envelope containing the query, match count, matching hotel records, and
available stays. A non-matching search intentionally returns HTTP 200 with
`count: 0` and `hotels: []`, allowing Vue to show a clear no-results state.

### Changes since Part 1

Part 2 replaces runtime CSV reads with SQLite after initial setup. On the first
application start, the backend creates the local database and imports the
supplied hotel, trip, user, and booking records in one transaction. A seed
marker prevents later starts from reloading starter data, duplicating rows,
overwriting updates, or restoring deleted bookings. The generated database file
is ignored by Git.

The Python backend owns database initialization, persistence rules, and booking
business logic:

- `backend/app/database.py` creates the SQLite schema and performs one-time,
  validated seeding.
- `backend/app/booking_service.py` searches persisted hotels, lists users and
  booking history, creates bookings with unique IDs, cancels bookings
  idempotently, and deletes a selected booking.
- `backend/app/schemas.py` defines typed request and response models.
- `backend/app/api.py` keeps FastAPI routes thin and exposes the versioned JSON
  endpoints.

The Vue frontend owns interactions and presentation:

- `frontend/src/services/apiClient.js`, `hotelSearch.js`, and `bookingApi.js`
  keep HTTP work separate from Vue components and use a relative `/api` path.
- `frontend/src/App.vue` coordinates hotel search, traveler selection, booking
  creation, visible success and error states, cancellation, and deletion.
- `frontend/src/components/HotelResults.vue` presents matching hotels and
  available stays with booking actions.
- `frontend/src/components/BookingHistory.vue` displays each user's confirmed
  and cancelled bookings, supports cancellation without removing the record,
  and requires a visible confirmation before deletion.

The Part 2 API provides `GET /api/v1/users`, `POST /api/v1/bookings`,
`GET /api/v1/users/{user_id}/bookings`, `PATCH /api/v1/bookings/{booking_id}`,
and `DELETE /api/v1/bookings/{booking_id}` alongside the retained hotel-search
endpoint. New booking IDs are unique; duplicate active bookings are permitted;
and cancelling an already-cancelled booking succeeds without reactivating it.

## Verification

The changes were manually scanned in VS Code before committing. The following
browser, API, persistence, and build checks were recorded during Part 2 review.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Run backend tests | Seed behavior, SQLite persistence, retained search, and booking CRUD pass | `.venv/bin/python -B -m pytest -p no:cacheprovider` passed **22 tests**. Two dependency deprecation warnings were reported; no test failed. |
| Run frontend lint and production build | The client is valid and production-buildable | `npm run lint` passed with exit code `0`; `npm run build` passed, transforming 16 modules. |
| Search `Harbor Lantern Hotel` through the API | One result has `H001`, Boston, MA, a rate of `150.0`, and available stays | HTTP 200; `count: 1`; hotel `H001`; Boston, MA; rate `150.0`; two available stays. |
| Search for an unknown hotel through the API | An intentional empty JSON response is returned | HTTP 200 with `count: 0` and `hotels: []`. |
| Search `Harbor Lantern Hotel` in the browser | The matching hotel and its rate appear | The UI displayed `H001`, Harbor Lantern Hotel, Boston, MA, and `$150.00`. |
| Search for an unknown hotel in the browser | A clear no-results message replaces the results table | The expected no-results message appeared and the table was removed. |
| Create a booking through the browser | A new, uniquely identified record appears immediately in history | New test booking `B007` was created and displayed in the selected user's booking history. |
| Cancel `B007` through the browser | Its status changes to cancelled and its record remains in history | `B007` remained visible with status `cancelled`. |
| Refresh and restart services using the same dedicated SQLite database | Created and cancelled records persist; seed data is not duplicated | The persistence verification used four controlled backend starts on isolated port `8002` and frontend port `5175`; the recorded booking state persisted across the required checks and starter counts remained unchanged. |
| Open the deletion confirmation, choose **Keep booking**, then delete only `B007` | Keeping leaves the booking intact; confirming deletes only the test record | Keeping preserved `B007`. Confirmed deletion produced a success message and the record no longer appeared in history. |
| Restart services after deletion | The deleted test record remains deleted | The final persistence check completed before temporary-service cleanup. |
| Inspect browser health during normal workflows | No visible application or console errors occur | No browser warnings or errors appeared during normal CRUD behavior. A deliberate backend shutdown displayed the expected search error and proxy connection-refused diagnostic. |
| Review merged application and publish | Part 2 is on `main`, Part 1 remains in history, and the remote is current | `main` was merged and pushed normally to `origin/main`; final Git status was clean and matched the remote. |

Part 1 browser evidence retained in the repository:

![Successful hotel search](https://raw.githubusercontent.com/isabelleggz/expedia-lite/main/docs/screenshots/hotel-search-result.jpg)

[Open the successful-search screenshot](https://github.com/isabelleggz/expedia-lite/blob/main/docs/screenshots/hotel-search-result.jpg)

![No-results hotel search](https://raw.githubusercontent.com/isabelleggz/expedia-lite/main/docs/screenshots/hotel-search-no-results.jpg)

[Open the no-results screenshot](https://github.com/isabelleggz/expedia-lite/blob/main/docs/screenshots/hotel-search-no-results.jpg)

Temporary services used for controlled verification were stopped afterward. The
temporary SQLite database and browser tab were removed, while unrelated local
services were left untouched.

## Project context and next steps

- [README](../README.md)
- [Project rules (`AGENTS.md`)](../AGENTS.md)
- [Part 1 report](report.md)
- [Design pipeline](design-pipeline.md)
- [Prompt archive](../prompts/)
- [Current handoff](../handoffs/current.md)

Remaining submission requirement:

- Record and link the required under-three-minute Part 2 demo video in the
  section above. It should demonstrate the visible booking workflow; no source
  code or test output is a substitute for this requirement.

The later visual redesign commit is intentionally not used as the Part 2
checkpoint. This report identifies the exact merged Part 2 application commit
so the submitted scope remains clear.
