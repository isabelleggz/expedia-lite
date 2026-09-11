# 06 — Vue search integration

Purpose: Add the first accessible hotel-search interface while isolating backend requests from Vue presentation code.

## Copyable prompt

```text
Read AGENTS.md, README.md, and docs/design-pipeline.md. Work only inside expedia-agent.

Implement the smallest useful Vue hotel-search interface for the existing FastAPI endpoint. Include:
- a “Hotel Search” page heading;
- a search input labeled “Hotel name”;
- a Search button beside the input;
- loading and backend-error states;
- a request using the entered name;
- a plain results table with Hotel ID, Hotel Name, City, State, and Nightly Rate; and
- a clear visible message for a successful search with no matches.

Keep HTTP requests in frontend/src/services/hotelSearch.js and presentation in focused Vue code. Use the existing relative /api/v1/hotels/search path and the development-time Vite proxy configured through VITE_API_PROXY_TARGET; do not hard-code a backend host or add broad CORS. Preserve the backend contract, do not add dependencies, and do not add unrelated interface features.

Run the backend pytest suite, then run `npm run lint` and `npm run build` from frontend/. Report the connection method and why it preserves the frontend/backend boundary, every changed file, and all check results.
```
