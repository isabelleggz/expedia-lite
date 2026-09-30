import { requestJson } from './apiClient'

function isCoordinate(value, minimum, maximum) {
  return typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum
}

function optionalText(value) {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function normalizeHotel(value) {
  if (
    !value ||
    typeof value !== 'object' ||
    typeof value.place_id !== 'string' ||
    !value.place_id.trim() ||
    !isCoordinate(value.latitude, -90, 90) ||
    !isCoordinate(value.longitude, -180, 180)
  ) {
    throw new Error('The nearby hotel search returned an unexpected response.')
  }

  return {
    place_id: value.place_id.trim(),
    name: optionalText(value.name),
    address: optionalText(value.address),
    locality: optionalText(value.locality),
    region: optionalText(value.region),
    postcode: optionalText(value.postcode),
    latitude: value.latitude,
    longitude: value.longitude,
  }
}

export async function searchNearbyHotels(zip) {
  const query = new URLSearchParams({ zip })
  const result = await requestJson(
    `/hotels/nearby?${query}`,
    undefined,
    'Unable to search for nearby hotel places right now.',
  )

  if (
    !result ||
    typeof result !== 'object' ||
    result.zip !== zip ||
    !result.search_center ||
    result.search_center.zip !== zip ||
    !isCoordinate(result.search_center.latitude, -90, 90) ||
    !isCoordinate(result.search_center.longitude, -180, 180) ||
    !Array.isArray(result.hotels)
  ) {
    throw new Error('The nearby hotel search returned an unexpected response.')
  }

  const hotels = result.hotels.map(normalizeHotel)
  const placeIds = new Set(hotels.map((hotel) => hotel.place_id))
  if (result.count !== hotels.length) {
    throw new Error('The nearby hotel search returned an unexpected response.')
  }
  if (placeIds.size !== hotels.length) {
    throw new Error('The nearby hotel search returned duplicate provider place IDs.')
  }

  return {
    zip: result.zip,
    search_center: {
      zip: result.search_center.zip,
      locality: optionalText(result.search_center.locality),
      latitude: result.search_center.latitude,
      longitude: result.search_center.longitude,
    },
    count: hotels.length,
    hotels,
  }
}
