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

const stayRows = computed(() =>
  props.hotels.flatMap((hotel) =>
    hotel.available_stays.map((stay) => ({
      ...stay,
      hotel_id: hotel.hotel_id,
      hotel_name: hotel.hotel_name,
      city: hotel.city,
      state: hotel.state,
      nightly_rate_usd: hotel.nightly_rate_usd,
    })),
  ),
)
</script>

<template>
  <section v-if="hasSearched" class="results-panel" aria-live="polite">
    <template v-if="stayRows.length">
      <div class="results-heading">
        <h2>Available stays</h2>
        <p>{{ stayRows.length }} {{ stayRows.length === 1 ? 'stay' : 'stays' }} found</p>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th scope="col">Hotel ID</th>
              <th scope="col">Hotel Name</th>
              <th scope="col">City</th>
              <th scope="col">State</th>
              <th scope="col">Nightly Rate</th>
              <th scope="col">Available Stay</th>
              <th scope="col">Dates</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stay in stayRows" :key="stay.trip_id">
              <td><span class="record-id">{{ stay.hotel_id }}</span></td>
              <td class="primary-value">{{ stay.hotel_name }}</td>
              <td>{{ stay.city }}</td>
              <td>{{ stay.state }}</td>
              <td>{{ currencyFormatter.format(stay.nightly_rate_usd) }}</td>
              <td>
                <span class="primary-value">{{ stay.trip_name }}</span>
                <span class="secondary-value">{{ stay.trip_id }}</span>
              </td>
              <td>
                <time :datetime="stay.check_in">{{ stay.check_in }}</time>
                <span aria-hidden="true">–</span>
                <time :datetime="stay.check_out">{{ stay.check_out }}</time>
              </td>
              <td>
                <button
                  type="button"
                  class="compact-button"
                  :disabled="!selectedUserId || Boolean(busyTripId)"
                  :aria-label="`Book ${stay.trip_name}`"
                  @click="emit('book', stay)"
                >
                  {{ busyTripId === stay.trip_id ? 'Booking…' : 'Book' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <p v-else-if="hotels.length" class="message inline-message empty-message" role="status">
      Matching hotels have no available stays.
    </p>

    <p v-else class="message inline-message empty-message" role="status">
      No hotels match “{{ lastQuery }}”. Try another hotel name.
    </p>
  </section>
</template>
