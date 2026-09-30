# Expedia Lite — Assignment 2, Part 1 submission report

## Evidence status and scope

This report covers the five-digit U.S. ZIP search, backend-only Geoapify integration, synchronized hotel-place list and Leaflet map, and distinct search-state feedback implemented for Assignment 2, Part 1.

Automated checks used mocked provider responses and a temporary local mock API. Browser annotation evidence supplied on 2026-09-29 also showed the running UI after a search for ZIP `19446`, with five place cards/markers and the locality text “Montgomery Township.” That browser evidence is useful for visual review, but it does not independently prove the upstream source. Mock record counts remain test-fixture facts, not claims about live provider coverage.

Geoapify results are nearby place records, not a hotel inventory. A returned place is not proof of a room's availability, nightly price, rating, reservation status, or bookability. Provider coverage and fields may be incomplete, and results can change over time. Expedia Lite therefore displays only the provider place ID, name when supplied, address/location text when supplied, and coordinates, alongside the validated ZIP center.

## Repository, startup, and configuration

- Repository: [github.com/isabelleggz/expedia-lite](https://github.com/isabelleggz/expedia-lite)
- Assessed Part 1 application commit: [`a46e89c5bc57e12a354893dd890bcb771bf10f0c`](https://github.com/isabelleggz/expedia-lite/commit/a46e89c5bc57e12a354893dd890bcb771bf10f0c)
- Part 1 base revision: [`5d18b4f2bb681beb91e8b9efc16dd0b0e027c446`](https://github.com/isabelleggz/expedia-lite/commit/5d18b4f2bb681beb91e8b9efc16dd0b0e027c446) on `main`
- Earlier hotel-search foundation: [`c2f60bd`](https://github.com/isabelleggz/expedia-lite/commit/c2f60bd) created the original local-data search. It is historical context only and does not contain the current Geoapify Part 1 implementation.
- Required backend runtime: Python 3.10 or newer
- Required frontend runtime: Node.js `^22.18.0` or `>=24.12.0`
- Part 1 endpoint: `GET /api/v1/hotels/nearby?zip=02108`

Clone the repository and create the backend environment:

```sh
git clone https://github.com/isabelleggz/expedia-lite.git
cd expedia-lite
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

Create a file named `.env` at the repository root. It is ignored by Git and must remain untracked. Supply a personal Geoapify key only as a server-side setting:

```dotenv
GEOAPIFY_API_KEY=<YOUR_GEOAPIFY_API_KEY>
```

Do not put the real value in this report, a commit, frontend configuration, screenshots, logs, or a recording. Restart the backend after changing `.env`.

Install the already-declared frontend dependencies from the lockfile:

```sh
cd frontend
npm ci
cd ..
```

Start the backend from one terminal:

```sh
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend from a second terminal:

```sh
cd frontend
npm run dev
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). The frontend uses the existing environment-based `/api/v1` path and development proxy; it does not contain a Geoapify key or a hard-coded production API host.

## Research notes

The detailed notes and official links are preserved in [Part 1 research](part-1-research.md). The sources that directly influenced the implementation were:

| Official source | Useful features observed | Problems or limitations observed | Decision for Expedia Lite |
| --- | --- | --- | --- |
| [Geoapify Geocoding API](https://apidocs.geoapify.com/docs/geocoding/) | Structured `postcode` input, `type=postcode`, country filters, and returned coordinates. | A provider may return approximate or differently formatted matches; postcodes are not globally unique. | Send `filter=countrycode:us`, preserve the ZIP as text, and accept only an exact returned U.S. postcode before searching Places. |
| [Geoapify Places API](https://apidocs.geoapify.com/docs/places/) | `accommodation.hotel`, circle filters, proximity bias, bounded result limits, provider place IDs, and location fields. | Place records may omit names/addresses, contain malformed coordinates, or lack commercial hotel data. | Search a 5,000 m circle around the validated ZIP center, request at most 20 places, keep nullable provider text, and exclude unusable IDs/coordinates. |
| [Geoapify large-area guidance](https://apidocs.geoapify.com/how-to/place-discovery/retrieve-places-large-area/) and [OSM data overview](https://www.geoapify.com/ways-to-get-openstreetmap-data/) | Explain focused place discovery and the OpenStreetMap data basis. | Coverage may be incomplete, stale, or inconsistently tagged; results are not an exhaustive inventory. | Describe results as nearby places and never claim all hotels, rooms, availability, prices, ratings, or bookability. |
| [Geoapify pricing](https://www.geoapify.com/pricing/) and [terms](https://www.geoapify.com/terms-and-conditions/) | Document current credits, rate limits, key use, and attribution obligations. | Quotas and plan terms can change. | Keep the key on the backend, search only on explicit submission, cap requests/results, map distinguishable 429s, and link to current terms rather than treating limits as permanent. |
| [Leaflet API reference](https://leafletjs.com/reference) and [quick start](https://leafletjs.com/examples/quick-start/) | Map lifecycle, markers, popups, keyboard behavior, events, and attribution controls. | Leaflet supplies no basemap; popup HTML can be unsafe when built from provider strings. | Use one shared place ID for list/map selection, create popup DOM with `textContent`, update layers between searches, and remove the map on component unmount. |
| [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/) and [copyright guidance](https://www.openstreetmap.org/copyright) | Standard tile URL, attribution, normal caching/referrer behavior, and responsible interactive use. | The community tile service is best-effort and prohibits bulk/offline fetching and attribution removal. | Request only visible interactive tiles, keep attribution visible, add no prefetch/offline behavior, and leave the list usable if tiles fail. |

These findings produced the exact-match ZIP boundary, backend-only provider calls, 5 km center-based search, honest nullable fields, distinct error states, synchronized selection, and mocked automated tests.

## Early mockup and subsequent changes

- [Part 1 early SVG mockup](part-1-mockup.svg) is the design prepared before implementation. It shows the ZIP form, loading feedback, synchronized list/map selection, attribution, and distinct invalid, unresolved, empty, and request-failure states using provider placeholders rather than invented hotels.
- [Part 1 implementation plan](part-1-plan.md) maps the requirements to the endpoint, components, tests, and preservation constraints.

The mockup displays several annotated states at once. The final application renders one state at a time, uses the existing Expedia Lite visual theme, and switches the list/map between side-by-side and stacked layouts by viewport width. The final layout places the existing supplied-data stay search before the Part 1 ZIP search, centers the dynamic `Hotels Near ZIP {zip}` result title, and uses the returned count/locality as the map headline. The detailed helper labels shown in the wireframe were simplified during visual review. Keyboard focus, two-way selection, truthful missing-name handling, and visible Leaflet/OpenStreetMap attribution remain implemented. The supplied-data search remains a separate component and its local prices/bookings are not attached to Geoapify places.

## Implemented behavior and boundaries

A search accepts exactly five digits and preserves leading zeros. The backend geocodes a U.S. postcode, rejects any result that is not an exact match for the submitted ZIP, and only then searches the `accommodation.hotel` category within a 5 km circle centered on that validated result. An unresolved or mismatched geocoding response never becomes a Places search centered somewhere else.

The list and map consume the same normalized provider records. Selecting a list item focuses its marker; selecting a marker focuses and identifies its list item. A later search clears old markers and selection. OpenStreetMap attribution remains visible on the Leaflet map.

The endpoint uses machine-readable error codes so the UI can keep these outcomes distinct:

| HTTP status | Error code | UI meaning |
| --- | --- | --- |
| 400 | `invalid_zip` | Input was not exactly five digits. |
| 404 | `unresolved_zip` | No exact U.S. ZIP match was accepted. |
| 404 | `no_nearby_hotels` | The provider request succeeded but returned no usable nearby hotel places. |
| 429 | `geoapify_rate_limited` | Geoapify reported a distinguishable quota or rate limit. |
| 502 | `geoapify_unavailable` | A provider, network, HTTP, or response-validation failure occurred. |
| 503 | `geoapify_not_configured` | The backend does not have a usable server-side key. |

## Verification record

“Observed” below means observed in automated tests, a local browser backed by controlled fixture responses, or the specifically qualified browser annotation row.

| Input or action | Expected outcome | Observed outcome | Corrections or limitations |
| --- | --- | --- | --- |
| Submit ZIP `19446` in the running UI on 2026-09-29 | A valid search should show a ZIP-centered result heading, provider place cards, numbered markers, and returned-count/locality context. | User-supplied browser annotation evidence showed `Hotels Near ZIP 19446`, five place cards/markers, and “5 places returned near Montgomery Township.” | The page evidence confirms the visible UI state but does not independently establish that the records came from the live upstream request. |
| Submit `02108` to the local mocked browser/API scenario | Render the validated center, one list item and map marker per usable provider record, and keep list/map selection synchronized. | The fixture returned two records; the UI rendered two cards and two markers. List selection focused the matching marker, and keyboard marker selection focused the matching card. | This was not a Geoapify observation, and two is not an expected live count. The first map pass exposed initialization-order and marker-keyboard issues; both were corrected and the scenario was rerun cleanly. |
| Enter malformed input such as `12A` | Show client-side invalid-input feedback and do not present an empty-success or provider-failure state. | The mocked browser check showed the invalid alert, set the field's invalid state, and did not show prior results. Backend tests also reject malformed ZIPs before provider work. | No live provider call is appropriate for this case. |
| Return `unresolved_zip` for a syntactically valid five-digit request | Show the dedicated unresolved-ZIP state and do not run a Places search after an inexact geocode. | The mocked browser check showed the unresolved state. The focused backend test confirms that an inexact returned ZIP does not call Places. | The fixture ZIP does not establish whether that ZIP is unresolved in the real world. A live outcome remains  |
| Return `no_nearby_hotels` after a valid center and successful empty/filtered Places response | Show “no nearby hotel places” distinctly from unresolved ZIP and request failure. | The mocked browser check showed the no-nearby state and no stale results. Backend mocked-provider tests passed for no usable places. | This means no usable places were returned for that request; it must not be worded as proof that no hotels exist. No live empty region was established. |
| Return `geoapify_unavailable` / simulated upstream failure | Show a request-failure alert, never an empty successful search. | The mocked browser check showed the provider-failure state and cleared prior results. Backend tests cover sanitized provider, network, HTTP, and invalid-response failures. | No real provider outage was induced. |
| Simulate an upstream HTTP 429 during Geocoding or Places | Return `geoapify_rate_limited` with HTTP 429 and present rate-limit-specific failure text. | Mock-transport backend tests passed for both provider stages and assert the safe 429 contract. The frontend has a distinct rate-limit message and passed lint/build. | A 429 was not deliberately triggered against the live service, and this state was not separately recorded in the browser. Live observation:  |
| Search fixture `02108`, then fixture `10001` | Replace old markers/cards and reset selection before allowing a new synchronized selection. | The mocked browser check showed one new card and marker, zero old markers, and no retained selection; selecting the new result still synchronized correctly. | Both result sets were fixtures, not provider observations. |
| Return missing names/addresses or unusable IDs/coordinates | Use honest missing-field behavior and exclude records that cannot be safely identified or mapped. | Mocked backend tests confirm nullable provider text, skip missing IDs or invalid coordinates, and do not propagate provider commercial fields. The browser fixture rendered the missing-name fallback. | Provider omissions remain possible in live use; no values are inferred. |

Automated tests use mocked Geoapify responses (including upstream status and malformed-payload cases), require neither a live API key nor network access, and do **not** depend on a fixed live hotel count.

Verification completed against the current working tree on 2026-09-29:

| Check | Result |
| --- | --- |
| Focused Part 1 backend tests | `25 passed` in `0.16s`; two existing Starlette/FastAPI deprecation warnings. |
| Full backend test suite | `57 passed` in `0.46s`; two existing Starlette/FastAPI deprecation warnings. |
| Frontend lint | Passed. |
| Frontend production build | Passed with Vite `8.3.0`; 27 modules transformed. |
| Local mocked browser verification | Passed the state, responsive layout, attribution, second-search cleanup, keyboard focus, and two-way selection checks described above; final console had no warnings or errors. |
| Browser annotation for ZIP `19446` | On 2026-09-29 the supplied page evidence showed five rendered results near Montgomery Township. This remains qualified visual evidence only; live upstream origin was not independently verified. |

## AI disclosure and evidence log

### Tools and models

| Tool | Specific model or engine | Part 1 use |
| --- | --- | --- |
| OpenAI Codex desktop coding agent | GPT-5 Codex; the more specific deployment identifier was not exposed in the session and should be added from the session UI if the course requires it | Requirements analysis, official-source synthesis, implementation planning, code and test changes, review, verification coordination, and this report. |
| Codex in-app Browser control | Browser automation; no separate generative-model identifier was exposed | Inspected the local UI, responsive layout, result states, focus behavior, list/map synchronization, attribution, and console output. It did not by itself prove the source of upstream data. |
| Shell with `pytest`, npm scripts, ESLint/Oxlint, and Vite | Deterministic command-line tools; no AI model | Ran backend tests, frontend lint, and the production build and supplied their exit/results evidence. |
| Hand-authored SVG artifact | No generative model | Preserved the early design in [`part-1-mockup.svg`](part-1-mockup.svg); no image-generation model was used. |

- Human submitter/reviewer: `<ADD NAME>`
- Codex task/share link or exported transcript: `<ADD LINK OR FILE>`
- Part 1 application commit: [`a46e89c`](https://github.com/isabelleggz/expedia-lite/commit/a46e89c5bc57e12a354893dd890bcb771bf10f0c)
- Base branch and revision: `main` at [`5d18b4f`](https://github.com/isabelleggz/expedia-lite/commit/5d18b4f2bb681beb91e8b9efc16dd0b0e027c446)

### Prompt evidence excerpts

These excerpts identify the requested scope; attach the full task transcript if the course requires complete prompt evidence.

| Prompt excerpt | Use and linked evidence |
| --- | --- |
| “Implement the backend for Assignment 2 Part 1 with thin FastAPI routes, focused service modules, type hints, and Pydantic request/response models.” | Led to the [route](../backend/app/api.py), [response models](../backend/app/schemas.py), [exact postcode lookup](../backend/app/postcode_lookup.py), [nearby-place service](../backend/app/nearby_hotel_search.py), and mocked backend tests linked below. |
| “Implement the Part 1 frontend using focused Vue single-file components.” | Led to the accessible [ZIP search](../frontend/src/components/NearbyHotelSearch.vue), [result list](../frontend/src/components/NearbyHotelList.vue), [Leaflet map](../frontend/src/components/NearbyHotelMap.vue), and [API boundary](../frontend/src/services/nearbyHotels.js). |
| “Research one real provider and prepare the Part 1 design before implementation.” | Led to the [research notes](part-1-research.md), the source-to-decision table above, the [early mockup](part-1-mockup.svg), and the [implementation plan](part-1-plan.md). |
| “Review the completed Part 1 implementation against the assignment requirements and correct only in-scope issues you find.” | Led to the verification record above, regression tests, and the revised Leaflet initialization and marker-keyboard approach documented below. |
| “Prepare the Part 1 submission documentation without fabricating live observations.” | Led to this report and its qualified evidence language. |

### Code-change evidence links

- Backend route and models: [`backend/app/api.py`](../backend/app/api.py), [`backend/app/schemas.py`](../backend/app/schemas.py)
- Provider services: [`backend/app/postcode_lookup.py`](../backend/app/postcode_lookup.py), [`backend/app/nearby_hotel_search.py`](../backend/app/nearby_hotel_search.py)
- Backend tests: [`backend/tests/test_nearby_hotel_api.py`](../backend/tests/test_nearby_hotel_api.py), [`backend/tests/test_postcode_lookup.py`](../backend/tests/test_postcode_lookup.py), [`backend/tests/test_nearby_hotel_search.py`](../backend/tests/test_nearby_hotel_search.py)
- Frontend search and map: [`frontend/src/components/NearbyHotelSearch.vue`](../frontend/src/components/NearbyHotelSearch.vue), [`frontend/src/components/NearbyHotelList.vue`](../frontend/src/components/NearbyHotelList.vue), [`frontend/src/components/NearbyHotelMap.vue`](../frontend/src/components/NearbyHotelMap.vue)
- Frontend API boundary: [`frontend/src/services/nearbyHotels.js`](../frontend/src/services/nearbyHotels.js)
- Integration and separate demo catalog: [`frontend/src/App.vue`](../frontend/src/App.vue)
- Part 1 implementation diff: [`5d18b4f...a46e89c`](https://github.com/isabelleggz/expedia-lite/compare/5d18b4f2bb681beb91e8b9efc16dd0b0e027c446...a46e89c5bc57e12a354893dd890bcb771bf10f0c)


### Revised or failed approach

The initial Leaflet rendering sequence added the 5 km circle before the map had an initial view, which the mocked browser run exposed as a Leaflet coordinate-conversion error. The implementation was revised to establish the validated ZIP center with `setView` before adding the circle and markers. The same run also showed that default marker keyboard activation opened a popup without synchronizing the result card, so explicit Enter/Space handling was added. The mocked browser scenario was then rerun with working two-way selection and no console warnings or errors.

## Remaining limitations

- Geoapify Places coverage is not guaranteed to be exhaustive, and the current request is bounded to a 5 km radius and provider/result limits.
- The app cannot establish room inventory, price, rating, availability, or bookability from a nearby-place response.
- Names and address text may be missing; the UI preserves that uncertainty instead of manufacturing content.
- OpenStreetMap tiles and Geoapify requests depend on separate external services and their respective usage policies.
- Quota/rate-limit behavior is verified through simulation, not by intentionally consuming live quota.
- The separate supplied-data booking demo remains application functionality, but its catalog prices, availability, and bookings do not describe or attach to the live Geoapify place results.
