import { requestJson } from './apiClient'

export async function searchHotelsByName(hotelName) {
  const query = new URLSearchParams({ hotel_name: hotelName })
  const result = await requestJson(
    `/hotels/search?${query}`,
    undefined,
    'Unable to search hotels right now. Please try again.',
  )
  if (!Array.isArray(result.hotels)) {
    throw new Error('The hotel search returned an unexpected response.')
  }

  return result
}
