# Expedia Lite — Part 1

## Repository and commit

- GitHub repository: [https://github.com/isabelleggz/expedia-lite](https://github.com/isabelleggz/expedia-lite)
- Part 1 application commit: [`c2f60bd3a7f3d7da61411cc40aef54f330d65bd1`](https://github.com/isabelleggz/expedia-lite/commit/c2f60bd3a7f3d7da61411cc40aef54f330d65bd1)

The exact application snapshot is preserved at the commit above. This report and
its screenshots are documentation-only additions on `main`; they do not alter the
submitted application snapshot.

## Implementation

Expedia Lite implements a hotel-name search from the Vue interface through a
versioned FastAPI endpoint and back as JSON:

1. `frontend/src/App.vue` collects a whole or partial hotel name, manages loading
   and error state, and renders either a results table or a no-results message.
2. `frontend/src/services/hotelSearch.js` keeps the request separate from
   presentation code. It sends a relative request to
   `GET /api/v1/hotels/search?hotel_name=...`, checks the HTTP response, parses
   JSON, and validates that the response contains a hotel array.
3. `frontend/vite.config.js` proxies `/api` during development, keeping the Vue
   source independent of a hard-coded backend host.
4. `backend/app/main.py` creates the FastAPI application and includes the API
   router. `backend/app/api.py` owns the endpoint and typed JSON response models.
5. `backend/app/hotel_search.py` remains framework-free. It loads hotels and
   available stays from CSV files, links them through `hotel_id`, and performs
   trimmed, case-insensitive partial-name matching.
6. FastAPI serializes a response containing `query`, `count`, and `hotels`. A
   search with no match intentionally returns HTTP 200 with `count: 0` and an
   empty `hotels` array so Vue can present a clear empty state.

The backend tests cover CSV loading, hotel/stay linking, successful and empty
searches, the API response, and the required query parameter.

## Verification

The following manual review and browser checks were performed against the current
application on 2026-09-11.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Review the frontend request boundary and backend route | Vue presentation calls a separate JavaScript service; FastAPI keeps HTTP concerns separate from plain Python search logic | Confirmed in `App.vue`, `hotelSearch.js`, `api.py`, and `hotel_search.py` |
| Open the Vue application | A page headed “Hotel Search” displays a “Hotel name” search box and Search button | Confirmed; the button was initially disabled while the required input was empty |
| Search for `Harbor Lantern Hotel` | One table row displays hotel ID `H001`, Harbor Lantern Hotel, Boston, MA, and `$150.00` | Confirmed exactly; the interface reported “1 hotel found” |
| Search for `Hotel That Does Not Exist` | The results table is replaced by a clear no-results message | Confirmed; no table remained and the page displayed `No hotels match “Hotel That Does Not Exist”. Try another hotel name.` |
| Inspect browser warnings and errors after both searches | No application warning or error is reported | Confirmed; the browser log query returned no warnings or errors for either state |

Successful-search evidence:

![Expedia Lite successful hotel search](https://raw.githubusercontent.com/isabelleggz/expedia-lite/main/docs/screenshots/hotel-search-result.jpg)

[Open the successful-search screenshot](https://github.com/isabelleggz/expedia-lite/blob/main/docs/screenshots/hotel-search-result.jpg)

No-results evidence:

![Expedia Lite no-results hotel search](https://raw.githubusercontent.com/isabelleggz/expedia-lite/main/docs/screenshots/hotel-search-no-results.jpg)

[Open the no-results screenshot](https://github.com/isabelleggz/expedia-lite/blob/main/docs/screenshots/hotel-search-no-results.jpg)

Supporting checks run in the current workspace:

- Backend: `.venv/bin/python -B -m pytest -p no:cacheprovider` from `backend/`
  passed all nine tests. Two dependency deprecation warnings were reported; no
  test failed.
- Frontend: `./node_modules/.bin/oxlint .` and
  `./node_modules/.bin/eslint . --no-cache` from `frontend/` both exited
  successfully with no output.
- Live API: the backend health endpoint, successful search, intentional empty
  search, frontend root, and frontend `/api` proxy all returned successful
  responses.

## Project context and next steps

- [README](../README.md)
- [Project rules (`AGENTS.md`)](../AGENTS.md)
- [Design pipeline](design-pipeline.md)
- Selected prompts:
  - [Backend hotel search](../prompts/04-backend-hotel-search.md)
  - [FastAPI API and tests](../prompts/05-fastapi-api-and-tests.md)
  - [Vue search integration](../prompts/06-vue-search-integration.md)
  - [AutoLoop smoke test](../prompts/07-autoloop-smoke-test.md)
- [Current handoff](../handoffs/current.md)

Remaining limitations:

- Part 1 implements hotel search only. Booking inputs, validation, routes, and
  tests have not been implemented.
- The API returns available stays, but the Part 1 table presents only the hotel
  ID, name, city, state, and nightly rate required for the initial interface.
- The exact narrow booking contract still needs to be specified before Part 2.
- The full `npm run build` check was not rerun while preparing this report.
- The documentation, handoff, prompt library, report, and screenshots were added
  after the exact Part 1 application commit linked above.
- The tracked development proxy target uses port `8000`, while the currently
  verified Expedia backend runs on `8001`. The live frontend proxy works, but the
  intended ports should be reconciled before a clean restart.

The next functional task is to define the narrow booking request/response
contract, then add backend booking validation and tests before adding Vue guest
inputs and booking controls.
