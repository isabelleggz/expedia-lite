<script setup>
defineProps({
  travelerName: {
    type: String,
    required: true,
  },
  bookings: {
    type: Array,
    required: true,
  },
  isLoading: {
    type: Boolean,
    required: true,
  },
  busyBookingId: {
    type: String,
    required: true,
  },
  pendingDeleteId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['refresh', 'cancel', 'request-delete', 'confirm-delete', 'keep'])

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})
</script>

<template>
  <section class="history-panel" aria-labelledby="history-title" aria-live="polite">
    <div class="section-heading">
      <div>
        <h2 id="history-title">Booking history</h2>
        <p>{{ travelerName }}</p>
      </div>
      <button type="button" class="secondary-button compact-button" :disabled="isLoading" @click="emit('refresh')">
        {{ isLoading ? 'Loading…' : 'Refresh history' }}
      </button>
    </div>

    <p v-if="isLoading" class="panel-state" role="status">Loading booking history…</p>

    <div v-else-if="bookings.length" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th scope="col">Booking ID</th>
            <th scope="col">Hotel and Stay</th>
            <th scope="col">Dates</th>
            <th scope="col">Total</th>
            <th scope="col">Status</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="booking in bookings" :key="booking.booking_id">
            <td><span class="record-id">{{ booking.booking_id }}</span></td>
            <td>
              <span class="primary-value">{{ booking.hotel_name }}</span>
              <span class="secondary-value">{{ booking.trip_name }} · {{ booking.trip_id }}</span>
            </td>
            <td>
              <time :datetime="booking.check_in">{{ booking.check_in }}</time>
              <span aria-hidden="true">–</span>
              <time :datetime="booking.check_out">{{ booking.check_out }}</time>
            </td>
            <td>{{ currencyFormatter.format(booking.stay_price_usd) }}</td>
            <td>
              <span class="status-badge" :class="`status-${booking.status}`">
                {{ booking.status }}
              </span>
            </td>
            <td>
              <div v-if="pendingDeleteId === booking.booking_id" class="delete-confirmation" role="group" :aria-labelledby="`delete-${booking.booking_id}`">
                <p :id="`delete-${booking.booking_id}`">
                  Delete booking {{ booking.booking_id }}? This cannot be undone.
                </p>
                <div class="action-group">
                  <button
                    type="button"
                    class="danger-button compact-button"
                    :disabled="busyBookingId === booking.booking_id"
                    @click="emit('confirm-delete', booking)"
                  >
                    {{ busyBookingId === booking.booking_id ? 'Deleting…' : 'Confirm delete' }}
                  </button>
                  <button type="button" class="secondary-button compact-button" :disabled="Boolean(busyBookingId)" @click="emit('keep')">
                    Keep booking
                  </button>
                </div>
              </div>

              <div v-else class="action-group">
                <button
                  v-if="booking.status === 'confirmed'"
                  type="button"
                  class="secondary-button compact-button"
                  :disabled="Boolean(busyBookingId)"
                  @click="emit('cancel', booking)"
                >
                  {{ busyBookingId === booking.booking_id ? 'Cancelling…' : 'Cancel' }}
                </button>
                <button
                  type="button"
                  class="danger-link compact-button"
                  :disabled="Boolean(busyBookingId)"
                  @click="emit('request-delete', booking)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="panel-state empty-message" role="status">
      No bookings yet for this traveler.
    </p>
  </section>
</template>
