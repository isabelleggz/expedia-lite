# 04 — Backend hotel search

Purpose: Implement testable hotel-search behavior in plain Python while keeping HTTP framework concerns out of the business logic.

## Copyable prompt

```text
Read AGENTS.md and README.md. Work only inside expedia-agent and use backend/.venv for Python checks.

Implement only the framework-free hotel-search logic in the Python backend. Create readable named functions to:
- load hotel records from backend/data/hotels.csv;
- load available-stay records from backend/data/trips.csv;
- connect hotel and stay records using hotel_id; and
- find matching hotels by hotel name, including their available stays.

Name matching must ignore case, support whole or partial names, and return an intentional, testable empty list for a blank or unmatched name. Keep the data types and validation readable. Do not add FastAPI paths or change frontend files. Do not add dependencies. Run the smallest relevant backend checks and report every file changed and all verification evidence.
```
