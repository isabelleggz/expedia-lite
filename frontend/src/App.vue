<script setup>
import { ref } from 'vue'

import { searchHotelsByName } from './services/hotelSearch'

const hotelName = ref('')
const hotels = ref([])
const lastQuery = ref('')
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatNightlyRate(rate) {
  return currencyFormatter.format(rate)
}

async function submitSearch() {
  const query = hotelName.value.trim()
  if (!query) {
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const result = await searchHotelsByName(query)
    hotels.value = result.hotels
    lastQuery.value = result.query
    hasSearched.value = true
  } catch (error) {
    hotels.value = []
    hasSearched.value = false
    errorMessage.value = error instanceof Error ? error.message : 'Hotel search failed.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="page-shell">
    <section class="search-panel" aria-labelledby="page-title">
      <p class="eyebrow">Expedia Lite</p>
      <h1 id="page-title">Hotel Search</h1>
      <p class="intro">Enter all or part of a hotel name to see matching stays.</p>

      <form class="search-form" @submit.prevent="submitSearch">
        <label for="hotel-name">Hotel name</label>
        <div class="search-controls">
          <input
            id="hotel-name"
            v-model="hotelName"
            name="hotel-name"
            type="search"
            autocomplete="off"
            placeholder="Try Harbor Lantern"
            required
          />
          <button type="submit" :disabled="isLoading || !hotelName.trim()">
            {{ isLoading ? 'Searching…' : 'Search' }}
          </button>
        </div>
      </form>
    </section>

    <p v-if="errorMessage" class="message error-message" role="alert">
      {{ errorMessage }}
    </p>

    <section v-else-if="hasSearched" class="results-panel" aria-live="polite">
      <div v-if="hotels.length" class="results-heading">
        <h2>Search results</h2>
        <p>{{ hotels.length }} {{ hotels.length === 1 ? 'hotel' : 'hotels' }} found</p>
      </div>

      <div v-if="hotels.length" class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th scope="col">Hotel ID</th>
              <th scope="col">Hotel Name</th>
              <th scope="col">City</th>
              <th scope="col">State</th>
              <th scope="col">Nightly Rate</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="hotel in hotels" :key="hotel.hotel_id">
              <td><span class="hotel-id">{{ hotel.hotel_id }}</span></td>
              <td class="hotel-name">{{ hotel.hotel_name }}</td>
              <td>{{ hotel.city }}</td>
              <td>{{ hotel.state }}</td>
              <td>{{ formatNightlyRate(hotel.nightly_rate_usd) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-else class="message empty-message" role="status">
        No hotels match “{{ lastQuery }}”. Try another hotel name.
      </p>
    </section>
  </main>
</template>
