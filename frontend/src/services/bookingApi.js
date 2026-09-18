import { requestJson } from './apiClient'

export async function fetchUsers() {
  const result = await requestJson('/users', undefined, 'Unable to load travelers right now.')
  if (!Array.isArray(result.users)) {
    throw new Error('The traveler list returned an unexpected response.')
  }
  return result
}

export async function fetchBookingHistory(userId) {
  const result = await requestJson(
    `/users/${encodeURIComponent(userId)}/bookings`,
    undefined,
    'Unable to load booking history right now.',
  )
  if (!Array.isArray(result.bookings)) {
    throw new Error('The booking history returned an unexpected response.')
  }
  return result
}

export function createBooking(userId, tripId) {
  return requestJson(
    '/bookings',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, trip_id: tripId }),
    },
    'Unable to create the booking right now.',
  )
}

export function cancelBooking(bookingId) {
  return requestJson(
    `/bookings/${encodeURIComponent(bookingId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'cancelled' }),
    },
    'Unable to cancel the booking right now.',
  )
}

export function deleteBooking(bookingId) {
  return requestJson(
    `/bookings/${encodeURIComponent(bookingId)}`,
    { method: 'DELETE' },
    'Unable to delete the booking right now.',
  )
}
