# Expedia Lite current handoff

This handoff is derived from the repository and checks performed on 2026-09-11.
It intentionally contains no credentials or tokens. Commit
`c2f60bd3a7f3d7da61411cc40aef54f330d65bd1` is the exact Part 1 application
snapshot; later commits may contain documentation-only publication updates, so a
new agent must still inspect the live branch, HEAD, and working-tree status.

## 1. Current objective and decisions

The repository contains a working first hotel-search slice for Expedia Lite. The
immediate functional objective is to preserve that behavior while defining the
narrow booking contract for Part 2. Documentation publication must not be
mistaken for a change to the Part 1 application snapshot.

Important recorded decisions:

- Work only inside `/Users/isabellegerhart/Documents/Codex/expedia-agent`.
- FastAPI owns hotel search, availability data, future booking validation, and
  versioned `/api` paths.
- Vue owns user inputs, controls, HTTP requests, loading/error state, and visual
  presentation. The layers exchange JSON.
- Framework-free Python logic stays separate from thin FastAPI routes.
- Frontend requests use a relative API path and a development-time Vite proxy;
  the source does not hard-code an API host.
- The current implemented feature is hotel-name search. There is no calculator
  feature and no booking implementation.
- The supplied hotel/stay records are stored under `backend/data/` and linked by
  `hotel_id`.
- Do not install or upgrade dependencies without explicit permission. Do not
  commit generated dependencies, build output, caches, secrets, or environments.
- `AGENTS.md` defines a five-correction maximum for AutoLoop and a hotel-search
  SmokeTest contract.
- `prompts/03-minimal-implementation-plan.md` records a future preference for a
  narrow booking scope, but it does not define a concrete booking contract.

## 2. Architecture and important files

```text
frontend/src/App.vue
  -> frontend/src/services/hotelSearch.js
  -> GET /api/v1/hotels/search?hotel_name=<name>
  -> Vite /api development proxy (frontend/vite.config.js)
  -> backend/app/main.py FastAPI app
  -> backend/app/api.py route and response models
  -> backend/app/hotel_search.py framework-free search
  -> FastAPI JSON response
  -> JavaScript response parsing
  -> Vue results table, no-results state, or error state
```

Important files:

- `AGENTS.md`: project constraints plus AutoLoop and SmokeTest macros.
- `README.md`: project layout and setup requirements.
- `docs/design-pipeline.md`: detailed boundary, file map, request flow, and
  agentic review loop.
- `docs/part-1-report.md`: Part 1 repository, implementation, verification, and
  next-step report.
- `docs/screenshots/`: successful-search and no-results browser evidence for the
  Part 1 report.
- `docs/verification.md`: authoritative test, port, API, and browser checks.
- `prompts/`: seven ordered reusable project prompts.
- `backend/app/hotel_search.py`: dataclasses, CSV loading, `hotel_id` linking,
  partial case-insensitive name matching, and intentional empty results.
- `backend/app/api.py`: response models and
  `GET /api/v1/hotels/search?hotel_name=...`.
- `backend/app/main.py`: FastAPI app, router registration, and `GET /health`.
- `backend/data/hotels.csv` and `backend/data/trips.csv`: current source data.
- `backend/tests/test_hotel_search.py` and `backend/tests/test_api.py`: nine
  backend tests.
- `frontend/src/App.vue`: accessible search form and result presentation.
- `frontend/src/services/hotelSearch.js`: fetch and JSON-envelope validation.
- `frontend/vite.config.js`: conditional `/api` proxy.
- `frontend/.env.development`: tracked default proxy target
  `http://127.0.0.1:8000`.
- `frontend/package.json`: Vue dependency, Node engine requirement, and lint/build
  scripts.

## 3. Git state

- Current branch: `main`.
- Exact Part 1 application snapshot:
  `c2f60bd3a7f3d7da61411cc40aef54f330d65bd1`, subject
  `Initial Expedia Lite hotel search`.
- Upstream: local `main` tracks `origin/main`.
- Relevant branches found: local `main` and remote-tracking `origin/main`; no
  other branches were listed.
- Configured remote: `origin` uses
  `https://github.com/isabelleggz/expedia-lite.git` for fetch and push.
- Before the documentation publication commit, local `main`, `origin/main`, and
  GitHub all resolved to the Part 1 application snapshot above.
- The documentation publication commit is expected to advance `main` without
  changing application or dependency files. Because a document cannot include
  the hash of the commit that contains itself, verify the published HEAD and clean
  state with:

```text
git status --short --branch
git rev-parse HEAD
git branch -vv --all
```

Treat any future uncommitted file as user-owned work. Do not discard, overwrite,
stage, amend, or commit it without reviewing the diff and receiving appropriate
authorization.

## 4. Completed work

Commit `c2f60bd3a7f3d7da61411cc40aef54f330d65bd1` contains the initial tracked
application and setup:

- project rules, root setup documentation, and ignore rules;
- project-local backend dependency declaration;
- eight hotel records and twelve available-stay records in the CSV data, as
  asserted by the current tests;
- framework-free CSV loading, linking, and hotel-name search;
- the FastAPI health and hotel-search endpoints with response models;
- six framework-free logic tests and three API tests;
- the Vue starter project, hotel-search interface, request service, and Vite
  proxy configuration; and
- `docs/verification.md` with the hotel-search smoke contract.

Documentation added after the exact application snapshot:

- `README.md` links the design pipeline, Part 1 report, prompt library, and
  handoffs.
- `docs/design-pipeline.md` documents architecture and the review loop.
- `docs/part-1-report.md` records the submitted application commit, observed
  verification, screenshots, limitations, and next task.
- `docs/screenshots/hotel-search-result.jpg` and
  `docs/screenshots/hotel-search-no-results.jpg` preserve browser evidence.
- `prompts/01-project-scaffold.md` through
  `prompts/07-autoloop-smoke-test.md` preserve seven reusable milestones.
- `handoffs/current.md` is this repository-derived continuation record.

## 5. Incomplete or requested work

- The production build was not rerun during documentation publication because no
  application or dependency file changed.
- Booking is planned at the ownership level only. There are no guest inputs,
  booking controls, validation functions, booking routes, or booking tests in the
  current application.
- Do not implement booking until a concrete request defines the narrow behavior
  and acceptance checks.

## 6. Verification commands and observed results

### Backend environment and tests

Working directory: `backend/`.

```text
.venv/bin/python -B -m pytest -p no:cacheprovider
```

Observed on 2026-09-11: exit `0`; nine tests passed in `0.22s`. Pytest reported
two dependency deprecation warnings: one from FastAPI/Starlette TestClient about
`httpx2`, and one for the deprecated `anyio.abc.BlockingPortal` alias. No test
failed.

The environment evidence command was:

```text
.venv/bin/python -B -c 'import sys, fastapi, pytest; print(sys.executable); print(sys.version.split()[0]); print(fastapi.__version__); print(pytest.__version__)'
command -v node
node --version
command -v npm
npm --version
```

Observed:

```text
/Users/isabellegerhart/Documents/Codex/expedia-agent/backend/.venv/bin/python
Python 3.14.7
FastAPI 0.141.1
pytest 9.1.1
/usr/local/bin/node
Node.js v24.21.0
/usr/local/bin/npm
npm 11.19.0
```

### Frontend read-only lint

Working directory: `frontend/`.

```text
./node_modules/.bin/oxlint .
./node_modules/.bin/eslint . --no-cache
```

Observed on 2026-09-11: exit `0` with no output from either command. These were
chosen as read-only equivalents. The documented `npm run lint` script includes
`--fix` and a cache, so it was not run under the write-only-handoff constraint.
The documented `npm run build` was also not run in this handoff because it writes
generated output.

### Live backend and proxy behavior

The successful host-local checks were:

```text
curl --silent --show-error --fail http://127.0.0.1:8001/health
curl --silent --show-error --fail --get --data-urlencode 'hotel_name=Harbor Lantern Hotel' http://127.0.0.1:8001/api/v1/hotels/search
curl --silent --show-error --fail --get --data-urlencode 'hotel_name=Hotel That Does Not Exist' http://127.0.0.1:8001/api/v1/hotels/search
curl --silent --show-error --fail --head http://127.0.0.1:5174/
curl --silent --show-error --fail --get --data-urlencode 'hotel_name=Harbor Lantern Hotel' http://127.0.0.1:5174/api/v1/hotels/search
```

Observed on 2026-09-11:

- Backend health returned `{"status":"ok"}`.
- Direct backend search returned `count: 1`, hotel `H001`, Harbor Lantern Hotel,
  Boston, MA, nightly rate `150.0`, and stays `T001` and `T009`.
- Direct no-match search returned `count: 0` and `hotels: []`.
- Frontend root returned HTTP `200 OK`.
- A search sent through the active frontend `/api` proxy returned the same H001
  hotel-search JSON.

The first sandboxed localhost curls returned exit `7`/connection refused even
though host listeners existed. The identical commands succeeded with host-local
access, so that first result is a sandbox-access limitation rather than evidence
that the services were down.

### Git inspection

Read-only commands used included:

```text
git status --short --branch
git rev-parse HEAD
git branch -vv --all
git log -5 --date=iso-strict --pretty=format:'%h %ad %d %s'
git remote -v
git diff --stat
git diff --cached --stat
git ls-remote origin refs/heads/main
```

Observed before documentation publication: the local and remote `main` commits
matched at `c2f60bd...`; the documentation changes were unstaged; and the staged
diff was empty. Rerun the first three commands above for the live post-publication
state.

## 7. Active services and ports

The following Expedia-agent processes were observed and were not changed:

- Backend PID `90049`, listening on `127.0.0.1:8001`, working directory
  `/Users/isabellegerhart/Documents/Codex/expedia-agent/backend`.
  Observed process command:
  `/Library/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python -m uvicorn app.main:app --host 127.0.0.1 --port 8001`.
  Loaded modules were observed under `backend/.venv`.
- Frontend PID `90072`, listening on `127.0.0.1:5174`, working directory
  `/Users/isabellegerhart/Documents/Codex/expedia-agent/frontend`.
  Observed process command:
  `node /Users/isabellegerhart/Documents/Codex/expedia-agent/frontend/node_modules/.bin/vite --host 127.0.0.1 --port 5174 --strictPort`.

The service owner/launcher was not established from repository evidence. Do not
stop either process unless the user asks and ownership is established.

Important collision: ports `8000` and `5173`, which `docs/verification.md`
describes as intended Expedia ports, are currently occupied by processes whose
working directories are under `/Users/isabellegerhart/hello-agent`. Those are
unrelated processes and must not be stopped or replaced. The active Expedia
frontend on `5174` currently proxies hotel-search requests successfully, but its
effective runtime proxy target was not inspected because doing so could expose
process environment data.

## 8. Failures, risks, questions, and assumptions

- The Part 1 report identifies `c2f60bd...` as the exact application snapshot.
  Do not substitute a later documentation-only commit when identifying the code
  submitted for Part 1.
- Backend tests pass but emit two dependency deprecation warnings. Dependency
  changes are not authorized merely to remove those warnings.
- The tracked development proxy target is port `8000`, while the observed Expedia
  backend is on `8001` and an unrelated service owns `8000`. The current running
  frontend proxy works, suggesting a runtime override, but a fresh start using
  only the tracked `.env.development` may target the wrong backend. Verify before
  restarting or changing configuration.
- No current evidence proves `npm run build` passes after the documentation work;
  documentation does not affect application code, but the check remains unrun in
  this handoff.
- Browser interaction performed for the Part 1 report confirmed one successful
  Harbor Lantern Hotel search, the intentional no-results state, and no browser
  warnings or errors. The screenshots are under `docs/screenshots/`.
- The details of the future “recommended narrow booking behavior” are absent from
  executable code and response models. Obtain a concrete contract before coding.
- This handoff assumes the CSV files currently under `backend/data/` remain the
  intended supplied dataset.

## 9. Recommended next action

First read, in order:

1. `handoffs/current.md`
2. `AGENTS.md`
3. `README.md`
4. `docs/design-pipeline.md`
5. `docs/verification.md`
6. the prompt file relevant to the next requested milestone
7. the corresponding files under `backend/app/`, `backend/tests/`, or
   `frontend/src/`

Then inspect `git status` and the current diff before changing anything. If the
next request is booking implementation, obtain a concrete booking contract before
changing application code.

## 10. Verified facts versus claims requiring verification

Verified facts:

- Commit `c2f60bd3a7f3d7da61411cc40aef54f330d65bd1` is the exact Part 1 application
  snapshot and was present on `origin/main` before documentation publication.
- The backend interpreter is `backend/.venv/bin/python`, Python `3.14.7`.
- FastAPI `0.141.1`, pytest `9.1.1`, Node.js `v24.21.0`, and npm `11.19.0` are
  available at the paths recorded above.
- All nine backend tests pass, with two deprecation warnings.
- Read-only Oxlint and ESLint checks pass.
- The backend on `8001`, frontend on `5174`, direct search API, empty search API,
  frontend root, and live frontend API proxy responded successfully.
- Browser checks captured one successful hotel search and the no-results state;
  no browser warnings or errors were reported.
- The source implements hotel search only; booking behavior is absent.

Claims still requiring verification:

- The current `npm run lint` and `npm run build` scripts pass without source or
  generated-output surprises.
- The rendered Vue UI and browser console pass the full SmokeTest interaction.
- The active Expedia processes were started by Codex or may safely be stopped.
- A fresh frontend process will proxy to the Expedia backend while port `8000`
  remains occupied by the unrelated project.
- The live post-publication HEAD and working-tree state; rerun the Git commands in
  section 3.
- The exact future booking request/response and validation contract.
