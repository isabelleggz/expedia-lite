<script setup>
import { computed, onMounted, ref } from 'vue'

import BookingHistory from './components/BookingHistory.vue'
import HotelResults from './components/HotelResults.vue'
import {
  cancelBooking,
  createBooking,
  deleteBooking,
  fetchBookingHistory,
  fetchUsers,
} from './services/bookingApi'
import { searchHotelsByName } from './services/hotelSearch'

const hotelName = ref('')
const hotels = ref([])
const lastQuery = ref('')
const hasSearched = ref(false)
const users = ref([])
const selectedUserId = ref('')
const bookings = ref([])
const isSearching = ref(false)
const isLoadingUsers = ref(false)
const isLoadingHistory = ref(false)
const busyTripId = ref('')
const busyBookingId = ref('')
const pendingDeleteId = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const selectedTraveler = computed(() =>
  users.value.find((user) => user.user_id === selectedUserId.value),
)

function clearFeedback() {
  errorMessage.value = ''
  successMessage.value = ''
}

function readableError(error, fallbackMessage) {
  return error instanceof Error ? error.message : fallbackMessage
}

async function loadUsers() {
  isLoadingUsers.value = true
  clearFeedback()

  try {
    const result = await fetchUsers()
    users.value = result.users
    if (users.value.length) {
      selectedUserId.value = users.value[0].user_id
      await refreshHistory({ clearMessages: false })
    }
  } catch (error) {
    errorMessage.value = readableError(error, 'Unable to load travelers.')
  } finally {
    isLoadingUsers.value = false
  }
}

async function refreshHistory({ clearMessages = true } = {}) {
  if (!selectedUserId.value) {
    bookings.value = []
    return
  }

  isLoadingHistory.value = true
  pendingDeleteId.value = ''
  if (clearMessages) {
    clearFeedback()
  }

  try {
    const result = await fetchBookingHistory(selectedUserId.value)
    bookings.value = result.bookings
  } catch (error) {
    bookings.value = []
    errorMessage.value = readableError(error, 'Unable to load booking history.')
  } finally {
    isLoadingHistory.value = false
  }
}

function changeTraveler() {
  refreshHistory()
}

async function submitSearch() {
  const query = hotelName.value.trim()
  if (!query) {
    return
  }

  isSearching.value = true
  clearFeedback()

  try {
    const result = await searchHotelsByName(query)
    hotels.value = result.hotels
    lastQuery.value = result.query
    hasSearched.value = true
  } catch (error) {
    hotels.value = []
    hasSearched.value = false
    errorMessage.value = readableError(error, 'Hotel search failed.')
  } finally {
    isSearching.value = false
  }
}

async function bookStay(stay) {
  if (!selectedUserId.value) {
    errorMessage.value = 'Choose a traveler before creating a booking.'
    return
  }

  busyTripId.value = stay.trip_id
  clearFeedback()

  try {
    const booking = await createBooking(selectedUserId.value, stay.trip_id)
    successMessage.value = `Booking ${booking.booking_id} was created for ${stay.trip_name}.`
    await refreshHistory({ clearMessages: false })
  } catch (error) {
    errorMessage.value = readableError(error, 'Unable to create the booking.')
  } finally {
    busyTripId.value = ''
  }
}

async function cancelStoredBooking(booking) {
  busyBookingId.value = booking.booking_id
  pendingDeleteId.value = ''
  clearFeedback()

  try {
    await cancelBooking(booking.booking_id)
    successMessage.value = `Booking ${booking.booking_id} is cancelled and remains in history.`
    await refreshHistory({ clearMessages: false })
  } catch (error) {
    errorMessage.value = readableError(error, 'Unable to cancel the booking.')
  } finally {
    busyBookingId.value = ''
  }
}

function requestDelete(booking) {
  clearFeedback()
  pendingDeleteId.value = booking.booking_id
}

function keepBooking() {
  pendingDeleteId.value = ''
}

async function confirmDelete(booking) {
  busyBookingId.value = booking.booking_id
  clearFeedback()

  try {
    await deleteBooking(booking.booking_id)
    pendingDeleteId.value = ''
    successMessage.value = `Booking ${booking.booking_id} was deleted.`
    await refreshHistory({ clearMessages: false })
  } catch (error) {
    errorMessage.value = readableError(error, 'Unable to delete the booking.')
  } finally {
    busyBookingId.value = ''
  }
}

onMounted(loadUsers)
</script>

<template>
  <main class="page-shell">
    <section class="search-panel" aria-labelledby="page-title">
      <p class="eyebrow">Expedia Lite</p>
      <h1 id="page-title">Hotel Search</h1>
      <p class="intro">
        Choose a traveler, search by hotel name, and book one of its available stays.
      </p>

      <div class="traveler-field">
        <label for="traveler">Traveler</label>
        <select
          id="traveler"
          v-model="selectedUserId"
          name="traveler"
          :disabled="isLoadingUsers || !users.length"
          @change="changeTraveler"
        >
          <option value="" disabled>
            {{ isLoadingUsers ? 'Loading travelers…' : 'Choose a traveler' }}
          </option>
          <option v-for="user in users" :key="user.user_id" :value="user.user_id">
            {{ user.display_name }} ({{ user.user_id }})
          </option>
        </select>
        <p class="field-help">New bookings and booking history belong to this traveler.</p>
      </div>

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
          <button type="submit" :disabled="isSearching || !hotelName.trim()">
            {{ isSearching ? 'Searching…' : 'Search' }}
          </button>
        </div>
      </form>
    </section>

    <p v-if="successMessage" class="message success-message" role="status">
      {{ successMessage }}
    </p>

    <p v-if="errorMessage" class="message error-message" role="alert">
      {{ errorMessage }}
    </p>

    <HotelResults
      :hotels="hotels"
      :last-query="lastQuery"
      :has-searched="hasSearched"
      :selected-user-id="selectedUserId"
      :busy-trip-id="busyTripId"
      @book="bookStay"
    />

    <BookingHistory
      v-if="selectedTraveler"
      :traveler-name="`${selectedTraveler.display_name} (${selectedTraveler.user_id})`"
      :bookings="bookings"
      :is-loading="isLoadingHistory"
      :busy-booking-id="busyBookingId"
      :pending-delete-id="pendingDeleteId"
      @refresh="refreshHistory"
      @cancel="cancelStoredBooking"
      @request-delete="requestDelete"
      @confirm-delete="confirmDelete"
      @keep="keepBooking"
    />
  </main>
</template>
