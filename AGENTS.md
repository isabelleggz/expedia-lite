# Project rules

## Scope and structure

- Keep API code in `backend/app/` and UI code in `frontend/src/`.
- Keep frontend and backend concerns separate; communicate through versioned HTTP endpoints under `/api` when application APIs are added.
- Do not add generated files, dependency directories, build output, or secrets to version control.

## Backend

- Use FastAPI with type hints and clear request/response models.
- Keep routes thin; move business logic into focused modules as the app grows.
- Add or update tests whenever behavior changes.

## Frontend

- Use Vue single-file components and keep components focused and accessible.
- Avoid hard-coded API hosts; use environment-based configuration when API calls are introduced.

## Workflow

- Do not install or upgrade dependencies unless explicitly asked.
- Make small, scoped changes and document any new setup requirements in `README.md`.

## Course macros

### AutoLoop

Trigger: When the user says "AutoLoop", perform a bounded fix-and-verify loop.

1. Read `AGENTS.md`, `README.md`, and the relevant verification instructions.
2. State the acceptance check for the current task.
3. Run the smallest relevant check.
4. If the check fails for an in-scope source-code reason, inspect the evidence, make the smallest relevant correction, and rerun the check.
5. Repeat for no more than five correction cycles.
6. Stop early and ask for direction if the next action requires a dependency change, machine-level permission, destructive action, an unrelated process to be stopped, or broader scope.
7. Report every cycle, the final evidence, and anything not verified.

### SmokeTest

Trigger: When the user says "Run the smoke test", verify the working application without changing source code or dependency declarations.

1. Read `AGENTS.md`, `README.md`, and `docs/verification.md`.
2. Run the backend pytest suite.
3. Run the frontend lint and production build.
4. Check the intended backend and frontend ports. Never stop an unrelated process.
5. Start only the backend and frontend processes needed for this test in Codex-managed terminals.
6. Verify one successful hotel-search API request using a hotel from the supplied data, and verify that a search with no matching hotel returns the intentional empty JSON result.
7. Use automated browser control to operate the visible hotel search. Search for `Harbor Lantern Hotel` and confirm that the results show hotel ID `H001`, Boston, MA, and a nightly rate of `$150.00`.
8. Search for a name that does not exist, confirm that the clear no-results message appears, confirm that the browser displays no application error, and report any UI behavior that could not be tested.
9. Unless the user asks to keep the app running, stop only the processes created by this smoke test.
10. Report concise evidence from tests, builds, hotel-search endpoints, the automated UI interactions, and service cleanup.

### Combined trigger

When the user says "AutoLoop: run the smoke test", run the SmokeTest macro. If an in-scope check fails, use the AutoLoop rules to make the smallest correction and repeat the smoke test until it passes, five correction cycles are exhausted, or a stopping condition is reached.
