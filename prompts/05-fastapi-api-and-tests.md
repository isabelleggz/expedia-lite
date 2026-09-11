# 05 — FastAPI API and tests

Purpose: Expose the existing business logic through a thin JSON API and protect its established behavior with focused pytest coverage.

## Copyable prompt

```text
Read AGENTS.md and README.md. Work only inside expedia-agent.

Expose the existing hotel-search logic through one FastAPI endpoint: GET /api/v1/hotels/search with a required hotel_name query parameter. Return matching hotels and their available stays in a clear JSON envelope containing query, count, and hotels. An unmatched search must return HTTP 200 with count 0 and an empty hotels array. Keep CSV loading, hotel_id linking, and name matching in the framework-free backend module; keep the route thin and use typed response models.

Add the smallest useful pytest coverage for:
- loading the supplied hotel and stay CSV records;
- linking records through hotel_id;
- successful partial, case-insensitive hotel-name search;
- an unmatched search;
- the successful API JSON response;
- the structured empty API response; and
- the required query parameter.

Do not change frontend files or dependencies. Run `.venv/bin/python -B -m pytest -p no:cacheprovider` from backend/. Report the endpoint, representative request and response JSON, exact test command, passed checks, failures, and every file changed.
```
