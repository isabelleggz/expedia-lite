const HOTEL_SEARCH_ENDPOINT = '/api/v1/hotels/search'

export async function searchHotelsByName(hotelName) {
  const query = new URLSearchParams({ hotel_name: hotelName })
  const response = await fetch(`${HOTEL_SEARCH_ENDPOINT}?${query}`)

  if (!response.ok) {
    throw new Error('Unable to search hotels right now. Please try again.')
  }

  const result = await response.json()
  if (!Array.isArray(result.hotels)) {
    throw new Error('The hotel search returned an unexpected response.')
  }

  return result
}
