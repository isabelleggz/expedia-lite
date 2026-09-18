<script setup>
import { computed, onMounted, ref } from 'vue'

import BookingHistory from './components/BookingHistory.vue'
import DatePlannerDialog from './components/DatePlannerDialog.vue'
import HotelResults from './components/HotelResults.vue'
import TravelCategories from './components/TravelCategories.vue'
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
const dateSummary = ref('Add dates')
const dateDialog = ref(null)

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

async function searchFeaturedStay() {
  hotelName.value = 'Valley Trail Inn'
  await submitSearch()
}

function openDatePlanner() {
  dateDialog.value?.open()
}

function updateDates(summary) {
  dateSummary.value = summary === 'Check-in — Check-out' ? 'Add dates' : summary
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
  <main>
    <section class="hero" aria-labelledby="page-title">
      <div class="hero-sky" aria-hidden="true">
        <span class="hero-sun"></span>
        <span class="mountain mountain-back"></span>
        <span class="mountain mountain-front"></span>
        <span class="hero-lake"></span>
      </div>

      <header class="site-header">
        <a class="brand" href="#hotel-search" aria-label="Expedia Lite hotel search">
          <span class="brand-mark" aria-hidden="true">EL</span>
          <span>Expedia Lite</span>
        </a>
        <a class="header-link" href="#booking-history">My bookings</a>
      </header>

      <div class="hero-copy">
        <p class="eyebrow light-eyebrow">A small stay finder for big weekends</p>
        <h1 id="page-title">Room to roam.<br />A place to land.</h1>
        <p>Search a handpicked collection of city stays, then keep every booking in one calm place.</p>
      </div>
    </section>

    <div class="content-shell">
      <section id="hotel-search" class="search-panel" aria-labelledby="search-title">
        <TravelCategories />

        <div class="search-intro">
          <div>
            <p class="eyebrow">Start with a name</p>
            <h2 id="search-title">Find your next stay</h2>
          </div>
          <p>Full or partial hotel names work.</p>
        </div>

        <form class="search-form" @submit.prevent="submitSearch">
          <div class="search-controls">
            <label class="search-field hotel-field" for="hotel-name">
              <span class="field-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 21s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z" /><circle cx="12" cy="9" r="2.5" /></svg>
              </span>
              <span class="field-copy">
                <span class="field-label">Hotel name</span>
                <input
                  id="hotel-name"
                  v-model="hotelName"
                  name="hotel-name"
                  type="search"
                  autocomplete="off"
                  placeholder="Try Inn or Trail"
                  required
                />
              </span>
            </label>

            <button class="search-field field-button" type="button" aria-haspopup="dialog" @click="openDatePlanner">
              <span class="field-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2zM3 9h18M8 2v4M16 2v4" /></svg>
              </span>
              <span class="field-copy">
                <span class="field-label">Dates</span>
                <span class="field-value">{{ dateSummary }}</span>
              </span>
            </button>

            <label class="search-field traveler-field" for="traveler">
              <span class="field-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="7" r="4" /><path d="M4 21a8 8 0 0 1 16 0z" /></svg>
              </span>
              <span class="field-copy">
                <span class="field-label">Travelers</span>
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
              </span>
            </label>

            <button class="search-button" type="submit" :disabled="isSearching || !hotelName.trim()">
              {{ isSearching ? 'Searching…' : 'Search stays' }}
            </button>
          </div>

          <p class="planning-note">
            <span aria-hidden="true">✦</span>
            Dates and travelers are planning preferences and do not filter hotel results. Only hotel name filters this collection.
          </p>
        </form>
      </section>

      <p v-if="successMessage" class="message success-message" role="status">
        {{ successMessage }}
      </p>

      <p v-if="errorMessage" class="message error-message" role="alert">
        {{ errorMessage }}
      </p>

      <aside class="stay-spotlight" aria-labelledby="spotlight-title">
        <div class="spotlight-art" aria-hidden="true"><span></span></div>
        <div class="spotlight-copy">
          <p class="eyebrow">Stay spotlight</p>
          <h2 id="spotlight-title">Trade the noise for a trail weekend.</h2>
          <p>Valley Trail Inn puts State College and a slower pace within easy reach.</p>
        </div>
        <button class="spotlight-button" type="button" @click="searchFeaturedStay">
          Find this stay <span aria-hidden="true">→</span>
        </button>
      </aside>

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
        id="booking-history"
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
    </div>

    <DatePlannerDialog ref="dateDialog" @dates-updated="updateDates" />
  </main>
</template>
