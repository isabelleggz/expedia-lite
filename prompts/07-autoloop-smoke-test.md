# 07 — AutoLoop smoke test

Purpose: Exercise the complete hotel-search path and allow only bounded, evidence-driven corrections to in-scope source failures.

## Copyable prompt

```text
AutoLoop: run the smoke test.

Read AGENTS.md, README.md, and docs/verification.md. State the acceptance checks, then:
1. Run `.venv/bin/python -B -m pytest -p no:cacheprovider` from backend/.
2. Run `npm run lint` and `npm run build` from frontend/.
3. Inspect the intended backend port 8000 and frontend port 5173. Never stop an unrelated process.
4. Start only the services needed for this test in Codex-managed terminals.
5. Verify GET /api/v1/hotels/search returns Harbor Lantern Hotel with count 1, hotel ID H001, Boston, MA, nightly rate 150.0, and available stays.
6. Verify an unknown hotel returns HTTP 200 with count 0 and an empty hotels array.
7. Use automated browser control to search for Harbor Lantern Hotel and confirm H001, Boston, MA, and $150.00 appear in the interface.
8. Search for Hotel That Does Not Exist and confirm the no-results message replaces the table without a visible application or browser-console error.
9. Unless asked to keep the app running, stop only processes created by this smoke test.

If an in-scope source-code failure occurs, inspect the evidence, make the smallest relevant correction, and repeat the entire smoke test. Stop after at most five correction cycles or earlier if the next action requires a dependency change, machine-level permission, destructive action, an unrelated process to be stopped, or broader scope. Report every cycle, final evidence, cleanup, failures, and anything not verified.
```
