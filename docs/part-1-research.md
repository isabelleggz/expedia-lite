# Assignment 2 — Part 1 research

Research date: 2026-09-29

## Scope

These notes cover the official documentation needed for the Part 1 ZIP-to-hotel-place search and early interface design. No live Geoapify request was made during this research. The adopted design uses Geoapify only through the backend and treats the returned records as map places, not Expedia Lite inventory or bookable rooms.

## Official sources

### Geoapify

- [Forward Geocoding API documentation](https://apidocs.geoapify.com/docs/geocoding/) — structured postcode input, <code>type=postcode</code>, country filters, result fields, API-key requirements, and one-credit geocoding cost.
- [Places API documentation](https://apidocs.geoapify.com/docs/places/) — <code>accommodation.hotel</code>, circle filters, proximity bias, result limits, GeoJSON fields, and Places credit calculation.
- [How to Retrieve Places Across a Large Area](https://apidocs.geoapify.com/how-to/place-discovery/retrieve-places-large-area/) — explicitly says Places is optimized for focused discovery and is not a guaranteed exhaustive export.
- [Geoapify overview of OpenStreetMap data](https://www.geoapify.com/ways-to-get-openstreetmap-data/) — explains the Places API’s OSM basis and OSM quality/coverage limitations.
- [Geoapify pricing](https://www.geoapify.com/pricing/) — current plan quotas and request-rate limits.
- [Geoapify terms and attribution](https://www.geoapify.com/terms-and-conditions/) — mandatory OpenStreetMap attribution and Geoapify attribution for the Free plan.

### Leaflet

- [Leaflet API reference](https://leafletjs.com/reference) — map lifecycle, markers, keyboard behavior, events, popups, bounds, attribution, and safe popup content.
- [Leaflet quick start](https://leafletjs.com/examples/quick-start/) — tile layers, markers, popups, events, and attribution patterns.

### OpenStreetMap

- [OpenStreetMap Standard tile usage policy](https://operations.osmfoundation.org/policies/tiles/) — correct tile URL, visible attribution, browser identification/referrer behavior, caching, best-effort availability, and prohibited bulk/offline use.
- [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright) — ODbL obligations and attribution guidance.

## Findings and adopted decisions

### 1. Exact five-digit U.S. postcode matching

Official basis:

- Geoapify recommends <code>type=postcode</code> for ZIP/postcode geocoding.
- The geocoding documentation notes that postcodes are unique only within a country and strongly recommends a country filter.
- Structured address input supports a <code>postcode</code> parameter. The app should not combine structured postcode input with free-form <code>text</code> input.

Adopted request:

~~~text
GET https://api.geoapify.com/v1/geocode/search
  ?postcode={ZIP}
  &type=postcode
  &filter=countrycode:us
  &format=json
  &limit=5
  &apiKey={server-side key}
~~~

Adopted validation and matching rules:

- Trim the form value, then require exactly five ASCII digits with <code>^[0-9]{5}$</code>. ZIP+4 and partial prefixes are outside Part 1.
- Reject invalid syntax before any provider request.
- Accept a geocoder result only when its returned postcode exactly equals the submitted five digits, its country code equals <code>us</code> case-insensitively, and its latitude/longitude are finite and in range.
- Do not silently accept a nearby, prefix, or differently formatted postcode result.
- If no exact usable result remains, show the unresolved-ZIP state rather than a generic request failure.
- The resolved postcode coordinates are the search origin. Browser geolocation, IP geolocation, traveler profile location, and map viewport location are not used.

This keeps the geographic meaning stable and makes the same ZIP produce the same center regardless of the traveler’s device or account.

### 2. Five-kilometre hotel-place search

Official basis:

- The Places API supports the specific category <code>accommodation.hotel</code>.
- A circle filter strictly limits results to a radius in metres.
- A proximity bias orders matching results by distance from the supplied point.
- The default result limit is 20, and 20 returned places cost one Places credit.

Adopted request after exact postcode resolution:

~~~text
GET https://api.geoapify.com/v2/places
  ?categories=accommodation.hotel
  &filter=circle:{postcode-longitude},{postcode-latitude},5000
  &bias=proximity:{postcode-longitude},{postcode-latitude}
  &limit=20
  &lang=en
  &apiKey={server-side key}
~~~

Adopted behavior:

- The circle is exactly 5,000 metres around the geocoded postcode point, not around a traveler, browser, or selected hotel.
- Proximity bias is used only to order results; the circle filter is what enforces the 5 km boundary.
- Part 1 requests one page of at most 20 places. It does not paginate or claim completeness.
- Normalize only stable <code>place_id</code>, provider name/address fields, and valid coordinates. Drop malformed coordinate records because they cannot be synchronized with a marker.
- Do not reject an otherwise usable place merely because Geoapify omits its country code. The required U.S. country filter applies to postcode geocoding; the Places circle is the requested 5 km boundary and may truthfully include a nearby cross-border place for a border ZIP.
- A valid postcode with zero normalized places is the distinct no-nearby-hotels state, not an unresolved postcode or provider failure.

### 3. Coverage, omissions, and truthful claims

Geoapify describes Places as a focused discovery API, not a guaranteed exhaustive place export. Geoapify also documents that its processed Places data is based on OpenStreetMap and that OSM contribution levels vary: features may be missing, stale, inconsistently tagged, or incomplete, particularly in less-mapped areas.

The documented Places response fields are location/point-of-interest data such as name, address components, categories, coordinates, distance, and <code>place_id</code>. They do not establish room inventory, live availability, nightly price, ratings, or a booking relationship.

Adopted product language and omissions:

- Label the section “Hotel places near {ZIP}” rather than “All hotels” or “Available hotels.”
- Add concise supporting text: “Places are provided for discovery and may be incomplete.”
- Never claim exhaustive inventory, bookable rooms, availability, prices, ratings, reviews, or Expedia affiliation.
- Do not merge Geoapify places with the SQLite hotel/stay records, infer commercial fields from the local dataset, or expose booking controls on provider cards.
- Show only provider-supplied name, formatted address/locality/region/postcode, and marker location. Use “Name not provided” or “Address not provided” rather than inventing a value.
- No-result copy says that no hotel places were returned within 5 km; it does not claim that no hotels exist.

### 4. Pricing, quotas, API-key handling, and responsible requests

As researched on the date above:

- Geoapify lists a Free plan with 3,000 credits per day and up to 5 requests per second.
- One Geocoding API request costs one credit.
- Places charges one credit per 20 returned places. With <code>limit=20</code>, one successful Part 1 search normally costs one geocoding credit plus one Places credit.
- Pricing, quotas, and terms can change; implementation documentation should link to the live pricing page instead of treating these figures as permanent.

Adopted controls:

- Keep <code>GEOAPIFY_API_KEY</code> on the backend only. Never place it in Vue source, a browser request, a response, an error, or a log.
- Make provider calls only after explicit form submission and valid local syntax. Do not search on every keystroke or map movement.
- Use a finite timeout, a bounded result limit, and no automatic pagination.
- Prevent duplicate submission while a request is in flight.
- Use mocked provider responses for automated tests. Routine tests must not spend credits or depend on quota/network availability.
- Map provider 429, timeout, non-success status, invalid JSON, and unusable payloads to a stable request-failure state without exposing raw provider detail.
- Recheck the active plan and attribution terms before deployment. Do not spread traffic across keys/accounts to evade limits.

### 5. Leaflet and list/map synchronization

Leaflet provides clickable, keyboard-focusable markers, event listeners, popups, map panning, and bounds fitting. Its reference also warns that popup strings are rendered as HTML; provider content must be inserted through DOM <code>textContent</code> or otherwise safely escaped.

Adopted shared selection model:

- The result list and marker layer render from the same normalized hotel array and one <code>selectedPlaceId</code>.
- Initial populated result: fit the map to the search-center marker and all hotel markers with padding and a maximum zoom. Do not automatically select the first hotel.
- List to map: clicking a card or activating its real button sets <code>selectedPlaceId</code>, highlights that card, pans the marker into view, and opens its popup.
- Map to list: clicking or keyboard-activating a marker sets the same <code>selectedPlaceId</code>, opens the popup, highlights the matching card, and scrolls the card into the nearest visible list position.
- A pointer marker click does not steal keyboard focus. Keyboard marker activation may move focus to the matching list control only when that improves continued keyboard navigation.
- Selection is conveyed with text/shape plus color; selected markers receive a distinct icon/state and selected list controls use an accessible pressed/current state.
- Closing a popup may leave the shared selection intact so the highlighted card remains orientation context. A new search clears selection before replacing results.
- Popups show the same provider fields as the list and create text nodes/DOM elements rather than interpolating provider strings as HTML.
- Marker <code>title</code>/<code>alt</code> values use the provider name or “Hotel place” fallback.

### 6. Map attribution and responsible tile use

Leaflet enables attribution controls but does not supply map tiles. If the Part 1 implementation uses OpenStreetMap Standard raster tiles, the OSM policy requires the exact HTTPS tile URL, visible attribution, normal browser referrer/identification behavior, and cache compliance. It prohibits bulk scraping, prefetch/offline features, forced no-cache headers, hidden attribution, and abusive use. The service is best effort and may block noncompliant use.

Geoapify’s current pricing/terms also require OpenStreetMap attribution and, on the Free plan, Geoapify attribution.

Adopted map decision:

- Use a configurable tile-layer URL; the development candidate is <code>https://tile.openstreetmap.org/{z}/{x}/{y}.png</code>.
- Keep Leaflet’s attribution control visible and unobscured, with direct links for “© OpenStreetMap contributors” and “Powered by Geoapify.”
- Do not add offline download, background prefetching, automated pan/zoom scans, or cache-bypass headers.
- Let the browser honor normal HTTP caching and send its normal referrer.
- Request only tiles needed for the visible interactive viewport.
- Keep the result list usable if tiles fail. A tile-layer failure should show a small map-specific notice without converting valid Geoapify results into a hotel-search failure.
- Reassess the production tile provider if traffic, uptime, or support needs exceed the community tile service’s best-effort policy.

## Visible search states

Each state replaces stale results and is named in visible text; meaning does not depend on color alone.

| State | Trigger | Visible treatment | Result/map treatment |
| --- | --- | --- | --- |
| Loading | Valid ZIP submitted; request pending | Button reads “Searching…”, status says “Searching for hotel places within 5 km of ZIP {ZIP}…”, and duplicate submit is disabled. | Previous list, markers, and selection are cleared immediately. A reserved results region prevents layout ambiguity. |
| Invalid ZIP | Trimmed input is not exactly five ASCII digits | Inline alert: “Enter a five-digit U.S. ZIP code.” Focus remains on or returns to the ZIP field. | No backend/provider call; no list or map results. |
| Unresolved ZIP | Syntax is valid but no exact U.S. postcode result survives matching | Alert: “We could not find that U.S. ZIP code.” | No Places call, list, or hotel markers. |
| No nearby hotels | Exact ZIP resolves; Places returns zero usable hotel features | Status heading: “No hotel places returned within 5 km of {ZIP}.” Supporting coverage disclaimer remains visible. | Empty list; map may show only the postcode center and 5 km context. |
| Request failure | Missing configuration, timeout, 429, provider/non-success response, invalid JSON, or unusable provider payload | Alert: “Location search is temporarily unavailable. Please try again.” Configuration failure may use the more specific “Location search is not configured yet.” | No stale list/markers. Preserve entered ZIP for retry. |
| Populated | Exact ZIP and one or more valid places | Result count and “Hotel places near {ZIP}” heading, plus non-exhaustive/no-booking disclaimer. | One card and one marker per normalized place; shared selection behavior applies. |

## Mockup conventions

The companion [Part 1 mockup](part-1-mockup.svg) uses placeholders such as “Provider hotel name” and “Formatted address if supplied.” They illustrate field placement without asserting that any real hotel, address, room, price, rating, availability, or booking record exists.
