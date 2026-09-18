<script setup>
import { computed } from 'vue'

const props = defineProps({
  hotels: {
    type: Array,
    required: true,
  },
  lastQuery: {
    type: String,
    required: true,
  },
  hasSearched: {
    type: Boolean,
    required: true,
  },
  selectedUserId: {
    type: String,
    required: true,
  },
  busyTripId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['book'])

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

const totalStays = computed(() =>
  props.hotels.reduce((count, hotel) => count + hotel.available_stays.length, 0),
)
</script>

<template>
  <section v-if="hasSearched" id="search-results" class="results-panel" aria-labelledby="results-title" aria-live="polite">
    <template v-if="hotels.length">
      <div class="results-heading">
        <div>
          <p class="eyebrow">Your next getaway</p>
          <h2 id="results-title">Stays for “{{ lastQuery }}”</h2>
          <p>
            {{ hotels.length }} {{ hotels.length === 1 ? 'hotel' : 'hotels' }} ·
            {{ totalStays }} available {{ totalStays === 1 ? 'stay' : 'stays' }}
          </p>
        </div>
        <span class="collection-pill">Expedia Lite collection</span>
      </div>

      <div class="hotel-list">
        <article v-for="hotel in hotels" :key="hotel.hotel_id" class="hotel-card">
          <div class="hotel-summary">
            <div class="hotel-illustration" aria-hidden="true">
              <svg viewBox="0 0 48 48" role="img">
                <path d="M8 29V18a4 4 0 0 1 4-4h24a4 4 0 0 1 4 4v11" />
                <path d="M6 29h36v10H6zM12 23h10v6H12zM26 23h10v6H26z" />
              </svg>
            </div>
            <div class="hotel-title-block">
              <span class="record-id">{{ hotel.hotel_id }}</span>
              <h3>{{ hotel.hotel_name }}</h3>
              <p>{{ hotel.city }}, {{ hotel.state }}</p>
            </div>
            <div class="rate-block">
              <strong>{{ currencyFormatter.format(hotel.nightly_rate_usd) }}</strong>
              <span>per night</span>
            </div>
          </div>

          <div class="available-stays">
            <p class="available-label">Available stays</p>
            <ul>
              <li v-for="stay in hotel.available_stays" :key="stay.trip_id">
                <div>
                  <strong>{{ stay.trip_name }}</strong>
                  <span>
                    {{ stay.trip_id }} ·
                    <time :datetime="stay.check_in">{{ stay.check_in }}</time>
                    –
                    <time :datetime="stay.check_out">{{ stay.check_out }}</time>
                  </span>
                </div>
                <button
                  type="button"
                  class="compact-button"
                  :disabled="!selectedUserId || Boolean(busyTripId)"
                  :aria-label="`Book ${stay.trip_name} at ${hotel.hotel_name}`"
                  @click="emit('book', stay)"
                >
                  {{ busyTripId === stay.trip_id ? 'Booking…' : 'Book stay' }}
                </button>
              </li>
            </ul>
          </div>
        </article>
      </div>
    </template>

    <div v-else class="empty-state" role="status">
      <span class="empty-state-mark" aria-hidden="true">⌁</span>
      <h2 id="results-title">No stays found</h2>
      <p>No hotels match “{{ lastQuery }}”. Try another full or partial hotel name.</p>
    </div>
  </section>
</template>
