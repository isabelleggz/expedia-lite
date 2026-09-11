# Expedia Lite design pipeline

## Frontend/backend boundary

The Vue frontend owns the visible hotel-search experience: it collects the hotel
name, starts the request, tracks loading and error state, and renders either the
results table or the no-results message. HTTP access is isolated in
`frontend/src/services/hotelSearch.js`, so `frontend/src/App.vue` does not know
how the backend is hosted. During development, Vite reads
`frontend/.env.development` and proxies relative `/api` requests to FastAPI.

The FastAPI backend owns the versioned HTTP contract under `/api/v1`, response
validation, CSV-backed hotel and stay data, record linking, and name matching.
`backend/app/api.py` translates between HTTP/JSON and the framework-free Python
logic in `backend/app/hotel_search.py`. The backend does not render interface
elements, and the frontend does not read the CSV files directly.

The current repository does not contain an arithmetic calculation function. Its
plain Python computation step is `find_matching_hotels_by_name`, supported by
the CSV loading and `hotel_id` linking functions in `hotel_search.py`.

## Project-file map

This map lists the repository-controlled project files that currently exist.
Ignored environments, installed dependency directories, caches, and build output
are intentionally omitted.

```text
expedia-agent/
|-- .gitignore
|-- AGENTS.md
|-- README.md
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- api.py
|   |   |-- hotel_search.py
|   |   `-- main.py
|   |-- data/
|   |   |-- hotels.csv
|   |   `-- trips.csv
|   |-- tests/
|   |   |-- test_api.py
|   |   `-- test_hotel_search.py
|   `-- requirements.txt
|-- docs/
|   |-- design-pipeline.md
|   |-- part-1-report.md
|   |-- screenshots/
|   |   |-- hotel-search-no-results.jpg
|   |   `-- hotel-search-result.jpg
|   `-- verification.md
|-- handoffs/
|   `-- current.md
|-- prompts/
|   |-- 01-project-scaffold.md
|   |-- 02-environment-readiness.md
|   |-- 03-minimal-implementation-plan.md
|   |-- 04-backend-hotel-search.md
|   |-- 05-fastapi-api-and-tests.md
|   |-- 06-vue-search-integration.md
|   `-- 07-autoloop-smoke-test.md
`-- frontend/
    |-- .editorconfig
    |-- .env.development
    |-- .gitattributes
    |-- .gitignore
    |-- .oxlintrc.json
    |-- .vscode/
    |   `-- extensions.json
    |-- README.md
    |-- eslint.config.js
    |-- index.html
    |-- jsconfig.json
    |-- package-lock.json
    |-- package.json
    |-- public/
    |   `-- favicon.ico
    |-- src/
    |   |-- App.vue
    |   |-- assets/
    |   |   |-- base.css
    |   |   |-- logo.svg
    |   |   `-- main.css
    |   |-- components/
    |   |   |-- HelloWorld.vue
    |   |   |-- TheWelcome.vue
    |   |   |-- WelcomeItem.vue
    |   |   `-- icons/
    |   |       |-- IconCommunity.vue
    |   |       |-- IconDocumentation.vue
    |   |       |-- IconEcosystem.vue
    |   |       |-- IconSupport.vue
    |   |       `-- IconTooling.vue
    |   |-- main.js
    |   `-- services/
    |       `-- hotelSearch.js
    `-- vite.config.js
```

## Hotel-search request flow

At backend import time, the supplied CSV records are prepared once:

```text
backend/data/hotels.csv -- load_hotel_records ---------+
                                                       |
backend/data/trips.csv  -- load_available_stay_records +
                                                       |
                                                       v
                                  connect_records_by_hotel_id
                                                       |
                                                       v
                                                connected_hotels
```

Each user search then follows this round trip:

```text
[User enters a hotel name and selects Search]
                       |
                       v
[Vue: frontend/src/App.vue]
  submitSearch() owns UI state and presentation
                       |
                       v
[JavaScript: frontend/src/services/hotelSearch.js]
  GET /api/v1/hotels/search?hotel_name=<name>
                       |
                       v
[Vite development proxy: frontend/vite.config.js]
  /api -> VITE_API_PROXY_TARGET
                       |
                       v
[FastAPI: backend/app/main.py]
  app includes the API router
                       |
                       v
[FastAPI route: backend/app/api.py]
  search_hotels() validates the query and response model
                       |
                       v
[Plain Python logic: backend/app/hotel_search.py]
  find_matching_hotels_by_name(name, connected_hotels)
                       |
                       v
[HotelSearchResponse serialized as JSON]
  { "query": ..., "count": ..., "hotels": [...] }
                       |
                       v
[JavaScript: response.json()]
  validates that hotels is an array and returns the result
                       |
                       v
[Vue: frontend/src/App.vue]
  renders the table, no-results message, or request error
```

A name with no matches is a successful request, not an exception. The backend
returns a JSON envelope with `count` set to `0` and `hotels` set to an empty
array, which lets Vue render the intentional no-results state.

## Agentic review loop

```text
[Describe the requested behavior]
                 |
                 v
[Predict the blast radius]
  Name the files and layers expected to change
                 |
                 v
[Plan the smallest ordered implementation]
  Pair each change with an acceptance check
                 |
                 v
[Implement the scoped change]
                 |
                 v
[Inspect the Git diff]
  Confirm only expected files changed; exclude generated files and secrets
                 |
                 v
[Verify behavior]
  Run the smallest relevant checks from docs/verification.md
          |
          v
    <Checks pass?>
       /       \
     no         yes
     |           |
     v           v
[Correct smallest]  [Commit reviewed scope]
[in-scope cause]    [when authorized]
     |
     `------------> [Inspect the Git diff and verify again]
```

The relevant existing verification gates are the backend pytest suite, the
frontend lint and production build, and the hotel-search API/browser smoke test
documented in `docs/verification.md`. A documentation-only change should instead
be checked for accurate file references, readable diagrams, and a Git diff whose
paths match the predicted documentation-only blast radius.
