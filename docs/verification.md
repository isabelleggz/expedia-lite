# Verification

Do not install or upgrade dependencies while verifying.

## Static checks

- Backend: run `.venv/bin/python -B -m pytest -p no:cacheprovider` from `backend/`.
- Frontend lint: run `npm run lint` from `frontend/`.
- Frontend production build: run `npm run build` from `frontend/`.

Record each command, exit status, passed checks, warnings, and failures. Build output is generated verification output and must not be committed.

## Development services

- The intended backend address is `http://127.0.0.1:8000`.
- The intended frontend address is `http://127.0.0.1:5173`.
- Inspect both ports before starting anything. Do not stop or replace a listener that the verification run did not create.
- Start only the services needed for the check in Codex-managed terminals, record their process or session identifiers, and stop only those services afterward unless the user asks to keep them running.

## Application smoke test

Use `GET /api/v1/hotels/search` with its `hotel_name` query parameter.

1. Search the API for `Harbor Lantern Hotel`. Confirm a successful response with `count` equal to `1` and a hotel record containing ID `H001`, Boston, MA, a nightly rate of `150.0`, and its available stays.
2. Search the API for `Hotel That Does Not Exist`. Confirm the intentional empty result has `count` equal to `0` and an empty `hotels` array.
3. Use automated browser control to search for `Harbor Lantern Hotel`. Confirm that the results table displays `H001`, the hotel name, Boston, MA, and `$150.00`.
4. Search in the browser for `Hotel That Does Not Exist`. Confirm that a clear no-results message replaces the results table.
5. Confirm that neither interaction produces a visible application error or a browser console error. Report any behavior that could not be verified.

If the named supplied-data record changes, use another known hotel from `backend/data/hotels.csv` and report the expected values used. Do not change application source or dependency declarations during the smoke test. Stop any services started by the test unless the user asks to keep them running.
