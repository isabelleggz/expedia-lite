# Assignment 2 — Part 1 implementation plan

## Scope and boundary

This plan covers only the requested live five-digit U.S. ZIP search, Geoapify hotel-place results, a synchronized list and Leaflet map, and clear search feedback. It does **not** implement a booking flow for Geoapify places, alter the SQLite hotel collection, or add price, rating, or availability data to a provider result.

The current working tree already contains backend-only Geoapify ZIP lookup scaffolding (config.py, postcode_lookup.py, and /api/demo/zip-location) and a ZipLookupDemo.vue proof of concept. Part 1 should evolve that scoped work into the user-facing, versioned feature below rather than expose the demo route as a second search experience.

## Requirement map

| Part 1 requirement | Backend proposal | Frontend proposal | Automated verification | Documentation |
| --- | --- | --- | --- | --- |
| Accept a five-digit U.S. ZIP search | Add one zip query parameter to a versioned route; reject missing, non-five-digit values before calling a provider; Geoapify geocoding confirms that a syntactically valid ZIP resolves in the U.S. | A labelled numeric ZIP field, maxlength 5, submit button, and client-side enablement only for five digits. Server validation remains authoritative. | Route tests for missing, short, long, and nonnumeric ZIPs; controller tests assert that invalid values cause no mocked provider request. | README explains GEOAPIFY_API_KEY configuration without recording a key; docs/verification.md records the new checks. |
| Perform a live ZIP-based lookup through Geoapify | Reuse the exact-U.S.-ZIP geocoding controller to obtain the search center, then call the Geoapify Places API for accommodation.hotel around that center. Keep the key and raw provider response on the server. | Call only the relative application API; never include a Geoapify key or provider URL in Vue source. | httpx.MockTransport supplies both Geoapify responses and asserts request parameters, timeout, error handling, and key secrecy. | Record provider configuration, no-key behavior, and the fact that tests are mocked. |
| Present nearby hotels in a list and on a Leaflet map | Normalize only valid provider features with stable IDs and coordinates into one typed hotels array. A provider response with no usable hotel features becomes the controlled `no_nearby_hotels` result. | One ZIP-search component owns one result object. Its list and NearbyHotelMap receive the same hotels array and search center, so every list item has one marker and both empty together. The map is created/destroyed with Vue lifecycle hooks and updates markers, bounds, and popups when that array changes. | Backend asserts normalization and the controlled no-results response. Frontend static checks build the Leaflet integration without making a request; the live visual check is manual, not an automated provider test. | Identify the planned map/basemap attribution and manual visual check. |
| Give clear search-state feedback | Map invalid input, unresolved ZIP, missing configuration, and provider failure to stable application errors; do not pass through provider text. | Use an aria-live loading message, a status heading/count after success, an explicit no-hotels message for a successful empty result, and a role=alert error. Clear old list/markers as a new search starts or fails so results are never stale. | API tests cover each status and sanitized payload; existing hotel-search and booking tests remain unchanged. | Include success, empty, and error state expectations in docs/verification.md. |
| Do not invent hotel commercial or booking data | The response model intentionally has no price, rating, availability, trip, user, booking, or database-hotel ID fields. | Do not reuse HotelResults.vue, rate formatting, stay controls, or booking events for provider places. | Response-shape tests assert the exact public payload. | State the displayed fields and explicit omissions below. |

## Proposed API contract

### Route

GET /api/v1/hotels/nearby?zip={five-digit-US-ZIP}

This route is distinct from the existing SQLite-backed GET /api/v1/hotels/search?hotel_name=... route. Nearby always means provider places around a Geoapify-resolved U.S. ZIP, not the local demo-hotel catalogue.

The server first resolves the ZIP with the existing exact-match Geocoding request (type=postcode, filter=countrycode:us), then queries Geoapify Places for accommodation.hotel within a fixed, documented initial radius of 5 km and at most 20 places. The radius and limit are server constants, not query parameters in Part 1; that keeps the public contract small and predictable.

### Successful response — 200

~~~json
{
  "zip": "02108",
  "search_center": {
    "zip": "02108",
    "locality": "Boston",
    "latitude": 42.357,
    "longitude": -71.063
  },
  "count": 1,
  "hotels": [
    {
      "place_id": "provider-place-id",
      "name": "Provider-reported hotel name",
      "address": "Provider-formatted address",
      "locality": "Boston",
      "region": "Massachusetts",
      "postcode": "02108",
      "latitude": 42.356,
      "longitude": -71.062
    }
  ]
}
~~~

Count equals the array length. search_center.locality, and all hotel address/name fields other than coordinates and place_id, may be null when the provider does not supply that fact. A feature with missing or invalid coordinates is excluded, because it cannot remain synchronized with a map marker. place_id is a stable Vue/Leaflet key; it is not a displayed hotel claim.

### Error response — 400, 404, 429, 502, or 503

Every expected application error uses the same envelope:

~~~json
{
  "error": {
    "code": "invalid_zip",
    "message": "Enter a five-digit U.S. ZIP code."
  }
}
~~~

| Status | error.code | Stable user-facing error.message | When returned |
| --- | --- | --- | --- |
| 400 | invalid_zip | Enter a five-digit U.S. ZIP code. | zip is absent or is not exactly five ASCII digits. |
| 404 | unresolved_zip | We could not resolve that exact U.S. ZIP code. | Geoapify has no exact usable U.S. ZIP match. |
| 404 | no_nearby_hotels | No hotel places were returned within 5 km of that ZIP code. | The exact ZIP resolves but Geoapify returns no usable hotel places. |
| 429 | geoapify_rate_limited | Location search is temporarily rate-limited. Please try again later. | Geoapify reports a distinguishable quota or rate limit. |
| 503 | geoapify_not_configured | Location search is not configured yet. | GEOAPIFY_API_KEY is blank or absent. |
| 502 | geoapify_unavailable | Location search is temporarily unavailable. Please try again. | Geoapify times out, returns an HTTP/provider/JSON error, or returns malformed place data. |

A resolved ZIP with no nearby valid hotel places uses the distinct `no_nearby_hotels` code so the frontend can render an empty state rather than an unresolved-ZIP or request-failure state. No response, error, health endpoint, log message, or frontend bundle may expose the API key, a raw provider error, or a raw provider URL.

## Exact displayed data and deliberate omissions

The ZIP search area displays the submitted ZIP and the provider locality when available. Each Geoapify hotel list card and corresponding Leaflet popup/marker display only:

- hotel name, or the explicit placeholder Name not provided;
- formatted street/postal address, or Address not provided;
- locality, region, and postcode, including only the provider values that are present; and
- the point location on the map (marker position), without displaying numeric coordinates as hotel marketing information.

The map's own search-center marker may be labelled ZIP {zip}. It represents the resolved ZIP center, not a hotel.

No Geoapify-place view or API response shows or fabricates a nightly price, currency, rating, review count, availability, available stay, trip, traveler, booking control, booking ID, local hotel_id, check-in/out date, or any other commercial/booking claim. Missing provider facts remain absent or visibly labelled as not provided; they are never inferred from the local SQLite data.

## Existing behavior that must remain unchanged

- The local hotel-name search route, its trimmed case-insensitive partial-match behavior, HotelSearchResponse payload, no-match 200 response, supplied hotel/stay data, and existing HotelResults.vue rate/stay presentation.
- All Part 2 booking functionality: user loading, booking creation, history, cancellation, deletion confirmation, SQLite persistence, booking API routes, and their tests.
- Existing /health and /api/health behavior, including the safe key-configured status but never the key itself.
- The frontend's relative /api requests and Vite proxy configuration; no hard-coded backend host will be introduced.
- Current unrelated working-tree changes, including the travel-category and wider styling edits. The Geoapify demo files are in scope only to be evolved or retired after their versioned replacement is working.

## Proposed implementation files

| File | Proposed change |
| --- | --- |
| docs/part-1-plan.md | This scoped plan. |
| backend/app/postcode_lookup.py | Retain its exact-U.S.-ZIP resolver and controlled errors; share coordinate validation where useful. |
| backend/app/nearby_hotel_search.py (new) | Focused Geoapify Places client and normalization dataclasses; make the radius, limit, timeout, and category explicit. |
| backend/app/schemas.py | Add separate nearby-place and standard-error response models; do not alter local HotelResponse or booking schemas. |
| backend/app/api.py | Add GET /api/v1/hotels/nearby and error translation. |
| backend/app/main.py, backend/app/demo_api.py | Preserve the existing demo route for compatibility during this backend slice. |
| backend/tests/test_postcode_lookup.py, backend/tests/test_nearby_hotel_search.py (new) | Mocked request, success, filtering, timeout, malformed-response, rate-limit, and no-key coverage. |
| backend/tests/test_nearby_hotel_api.py (new) | Verify the success schema and every controlled error mapping without live provider calls. |
| frontend/package.json, frontend/package-lock.json | Add Leaflet only after explicit permission to install the dependency; no package change is authorized by this planning task. |
| frontend/src/services/nearbyHotels.js (new) | Relative versioned request and strict response-envelope validation. |
| frontend/src/components/ZipLookupDemo.vue | Replace the demo-only UI with the ZIP hotel-search state owner, or rename it to describe the production feature. |
| frontend/src/components/NearbyHotelMap.vue (new) | Lifecycle-safe Leaflet map that renders the supplied center and the exact supplied hotel collection. |
| frontend/src/App.vue, frontend/src/assets/main.css | Place and style the scoped ZIP-results experience without changing local search or booking state. |
| frontend/src/services/zipLocation.js | Retire after nearbyHotels.js replaces its demo-only request. |
| README.md, docs/verification.md | Describe the versioned feature, safe configuration, dependency/setup note, and verification evidence. |

docs/report.md, docs/part-2-report.md, booking components/services, local hotel-search code, seed CSV files, and database code are intentionally outside this Part 1 change set.

## Smallest verification plan (no live provider in automated tests)

1. Keep Geoapify tests entirely in-process: use httpx.MockTransport for both ZIP geocoding and Places calls. Assert request shape, finite timeout, U.S.-only exact ZIP handling, normalized successful results, a controlled no-results response, malformed payloads, non-2xx responses, and that test keys never appear in an error.
2. Use FastAPI TestClient with the Geoapify service monkeypatched to verify the exact 200 envelope and each 400/404/429/502/503 error envelope. The test suite must continue exercising the existing hotel-search and booking cases.
3. Do not add a frontend test framework solely for this slice. The smallest automated frontend gates are the project's non-mutating lint commands and production build; neither calls Geoapify. Check the Git diff before and after because the current npm run lint scripts use --fix.
4. After automated checks pass and only with a configured key, perform one manual browser check each for a populated ZIP, a resolved ZIP with no hotel results, malformed input, and provider/configuration failure. Confirm the list count equals marker count, the ZIP-center marker is distinct, the map fits the current results, and no price/rating/availability/booking UI is present. This is deliberately manual so CI and routine tests do not depend on live Geoapify availability or quota.

## Ambiguities and risks

- The request specifies a Leaflet map but not a tile provider. Leaflet supplies map behavior, not base-map tiles; an approved tile source, attribution, and usage policy are still needed. A no-key OpenStreetMap layer is a possible default, subject to its attribution and usage requirements.
- The requested search radius and maximum number of places were not specified. This plan proposes 5 km and 20 results as bounded Part 1 defaults; they should be confirmed if the assignment rubric mandates different values.
- Geoapify may return sparse or category-mislabeled place data. The proposed null/not-provided handling and coordinate filtering preserve truthfulness and list/map synchronization, but may yield fewer displayed hotels than the provider's raw feature count.
- Leaflet is present in the frontend dependencies after its separately approved installation; its stylesheet and required attribution still need to be included when the map is implemented.
- Live provider latency, quota, missing configuration, and map-tile network failure are external operational risks. They need clear UI feedback and mocked automated coverage, not retries that conceal an error or fabricate results.
