<script setup>
import { computed, nextTick, ref } from 'vue'

import { ApiRequestError } from '../services/apiClient'
import { searchNearbyHotels } from '../services/nearbyHotels'
import NearbyHotelList from './NearbyHotelList.vue'
import NearbyHotelMap from './NearbyHotelMap.vue'

const zip = ref('')
const requestedZip = ref('')
const searchState = ref('idle')
const result = ref(null)
const selectedPlaceId = ref('')
const failureMessage = ref('')
const zipInput = ref(null)
const hotelList = ref(null)
const hotelMap = ref(null)

const normalizedZip = computed(() => zip.value.trim())
const hasValidZip = computed(() => /^[0-9]{5}$/.test(normalizedZip.value))
const selectedHotelName = computed(() => {
  const selected = result.value?.hotels.find(
    (hotel) => hotel.place_id === selectedPlaceId.value,
  )
  return selected?.name || (selected ? 'provider hotel with no returned name' : '')
})

function clearResults() {
  result.value = null
  selectedPlaceId.value = ''
}

function handleInput() {
  if (!['loading', 'results'].includes(searchState.value)) {
    searchState.value = 'idle'
    failureMessage.value = ''
  }
}

function handleSearchError(error) {
  if (error instanceof ApiRequestError) {
    if (error.code === 'invalid_zip') {
      searchState.value = 'invalid'
      return
    }
    if (error.code === 'unresolved_zip') {
      searchState.value = 'unresolved'
      return
    }
    if (error.code === 'no_nearby_hotels') {
      searchState.value = 'empty'
      return
    }
    if (error.code === 'geoapify_not_configured') {
      failureMessage.value = 'Hotel-place search is not configured on the server yet.'
    } else if (error.code === 'geoapify_rate_limited') {
      failureMessage.value = 'The location provider is temporarily rate-limited. Please try again later.'
    } else {
      failureMessage.value = error.message
    }
  } else {
    failureMessage.value =
      error instanceof Error
        ? error.message
        : 'Unable to search for nearby hotel places right now.'
  }
  searchState.value = 'error'
}

async function submitSearch() {
  if (!hasValidZip.value) {
    clearResults()
    requestedZip.value = normalizedZip.value
    searchState.value = 'invalid'
    await nextTick()
    zipInput.value?.focus()
    return
  }

  requestedZip.value = normalizedZip.value
  clearResults()
  failureMessage.value = ''
  searchState.value = 'loading'

  try {
    const searchResult = await searchNearbyHotels(requestedZip.value)
    if (!searchResult.hotels.length) {
      searchState.value = 'empty'
      return
    }
    result.value = searchResult
    searchState.value = 'results'
  } catch (error) {
    handleSearchError(error)
  }
}

async function selectFromList(placeId) {
  selectedPlaceId.value = placeId
  await nextTick()
  hotelMap.value?.focusMarker(placeId)
}

async function selectFromMap(placeId) {
  selectedPlaceId.value = placeId
  await nextTick()
  hotelList.value?.focusHotel(placeId)
}
</script>

<template>
  <section id="nearby-search" class="nearby-search-panel" aria-labelledby="nearby-search-title">
    <div class="nearby-search-header">
      <div>
        <h2 id="nearby-search-title">Search Hotels by ZIP code</h2>
      </div>
    </div>

    <form class="nearby-search-form" novalidate @submit.prevent="submitSearch">
      <label for="nearby-zip">Five-digit U.S. ZIP code</label>
      <div class="nearby-search-controls">
        <input
          id="nearby-zip"
          ref="zipInput"
          v-model="zip"
          name="zip"
          type="text"
          inputmode="numeric"
          autocomplete="postal-code"
          pattern="[0-9]{5}"
          maxlength="5"
          placeholder="02108"
          required
          :disabled="searchState === 'loading'"
          :aria-invalid="searchState === 'invalid'"
          :aria-describedby="searchState === 'invalid' ? 'nearby-zip-error' : undefined"
          @input="handleInput"
        />
        <button type="submit" :disabled="searchState === 'loading'">
          {{ searchState === 'loading' ? 'Searching…' : 'Search nearby hotels' }}
        </button>
      </div>
      <p v-if="searchState === 'invalid'" id="nearby-zip-error" class="state-alert" role="alert">
        Enter a five-digit U.S. ZIP code using numbers only.
      </p>
    </form>

    <div class="nearby-state-region" aria-live="polite">
      <div v-if="searchState === 'loading'" class="nearby-state-card loading-state" role="status">
        <span class="loading-pulse" aria-hidden="true"></span>
        <div>
          <strong>Searching around ZIP {{ requestedZip }}…</strong>
          <p>Resolving the exact ZIP, then requesting hotel places within 5 km.</p>
        </div>
      </div>

      <div v-else-if="searchState === 'unresolved'" class="nearby-state-card error-state" role="alert">
        <strong>That ZIP could not be resolved exactly.</strong>
        <p>No different or nearby place was searched. Check ZIP {{ requestedZip }} and try again.</p>
      </div>

      <div v-else-if="searchState === 'empty'" class="nearby-state-card empty-state-card" role="status">
        <strong>No nearby hotel places were returned.</strong>
        <p>
          Geoapify returned no usable hotel places within 5 km of ZIP {{ requestedZip }}.
          This does not mean no hotels exist there.
        </p>
      </div>

      <div v-else-if="searchState === 'error'" class="nearby-state-card error-state" role="alert">
        <strong>The nearby hotel request failed.</strong>
        <p>{{ failureMessage }}</p>
      </div>
    </div>

    <section
      v-if="searchState === 'results' && result"
      class="nearby-results"
      aria-labelledby="nearby-results-title"
      aria-live="polite"
    >
      <header class="nearby-results-header">
        <div>
          <h2 id="nearby-results-title">Hotels Near ZIP {{ result.zip }}</h2>
        </div>
      </header>

      <p v-if="selectedHotelName" class="sr-only" role="status">
        Selected {{ selectedHotelName }}.
      </p>

      <div class="nearby-results-layout">
        <NearbyHotelList
          ref="hotelList"
          :hotels="result.hotels"
          :selected-place-id="selectedPlaceId"
          @select="selectFromList"
        />
        <NearbyHotelMap
          ref="hotelMap"
          :hotels="result.hotels"
          :search-center="result.search_center"
          :selected-place-id="selectedPlaceId"
          @select="selectFromMap"
        />
      </div>
    </section>
  </section>
</template>

<style scoped>
.nearby-search-panel {
  overflow: hidden;
  border: 1px solid #d7e0d9;
  border-radius: 1.25rem;
  background: #fffefa;
  box-shadow: 0 1.6rem 4rem rgba(29, 58, 52, 0.13);
}

.nearby-search-header,
.nearby-results-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
}

.nearby-search-header {
  padding: 1.8rem 2rem 1rem;
  background: linear-gradient(135deg, #f8fbf5, #fff9f1);
}

.nearby-search-header h2,
.nearby-results-header h2 {
  margin: 0;
  color: #183b33;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 40px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.nearby-search-form {
  padding: 1.2rem 2rem 1.7rem;
  border-top: 1px solid #edf0eb;
}

.nearby-search-form > label {
  display: block;
  margin-bottom: 0.45rem;
  color: #294c42;
  font-size: 0.78rem;
  font-weight: 820;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.nearby-search-controls {
  display: grid;
  max-width: 38rem;
  grid-template-columns: minmax(9rem, 1fr) auto;
  gap: 0.65rem;
}

.nearby-search-controls input {
  width: 100%;
  min-height: 3.5rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid #96a69e;
  border-radius: 0.75rem;
  background: #fff;
  color: #173a32;
  font: inherit;
  font-size: 1.05rem;
  font-weight: 760;
  letter-spacing: 0.08em;
}

.nearby-search-controls input[aria-invalid='true'] {
  border-color: #b84d32;
  box-shadow: 0 0 0 3px rgba(184, 77, 50, 0.12);
}

.nearby-search-controls button {
  min-height: 3.5rem;
  padding: 0.75rem 1.2rem;
  border: 1px solid #b84d32;
  border-radius: 0.75rem;
  background: #d85f3d;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-weight: 820;
}

.nearby-search-controls button:hover:not(:disabled) {
  background: #b94b30;
}

.state-alert {
  max-width: 38rem;
  margin: 0.5rem 0 0;
  font-size: 0.8rem;
  line-height: 1.45;
}

.state-alert {
  color: #9a3627;
  font-weight: 700;
}

.nearby-state-region:empty {
  display: none;
}

.nearby-state-card {
  display: flex;
  margin: 0 2rem 1.7rem;
  padding: 1rem 1.1rem;
  border: 1px solid #d8e0da;
  border-radius: 0.85rem;
  align-items: center;
  gap: 0.8rem;
  background: #f5f8f3;
  color: #294c42;
}

.nearby-state-card strong,
.nearby-state-card p {
  display: block;
  margin: 0;
}

.nearby-state-card p {
  margin-top: 0.18rem;
  font-size: 0.84rem;
  line-height: 1.45;
}

.error-state {
  border-color: #d7a09a;
  background: #fff4f1;
  color: #842f24;
}

.empty-state-card {
  border-color: #d8c38f;
  background: #fff9e9;
  color: #675124;
}

.loading-pulse {
  width: 0.9rem;
  height: 0.9rem;
  flex: 0 0 0.9rem;
  border-radius: 50%;
  background: #d85f3d;
  animation: loading-pulse 1s ease-in-out infinite alternate;
}

@keyframes loading-pulse {
  to {
    opacity: 0.3;
    transform: scale(0.72);
  }
}

@media (prefers-reduced-motion: reduce) {
  .loading-pulse {
    animation: none;
  }
}

.nearby-results {
  padding: 1.8rem 2rem 2rem;
  border-top: 1px solid #dfe6e0;
  background: #f8faf6;
}

.nearby-results-header {
  display: block;
  margin-bottom: 1.4rem;
  text-align: center;
}

.nearby-results-layout {
  display: grid;
  align-items: start;
  grid-template-columns: minmax(18rem, 0.88fr) minmax(0, 1.35fr);
  gap: 1.35rem;
}

@media (max-width: 820px) {
  .nearby-search-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .nearby-results-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 540px) {
  .nearby-search-header,
  .nearby-search-form,
  .nearby-results {
    padding-right: 1.1rem;
    padding-left: 1.1rem;
  }

  .nearby-state-card {
    margin-right: 1.1rem;
    margin-left: 1.1rem;
  }

  .nearby-search-controls {
    grid-template-columns: 1fr;
  }
}
</style>
