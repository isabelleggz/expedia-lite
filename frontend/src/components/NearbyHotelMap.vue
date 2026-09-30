<script setup>
import L from 'leaflet'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  hotels: {
    type: Array,
    required: true,
  },
  searchCenter: {
    type: Object,
    required: true,
  },
  selectedPlaceId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['select'])
const mapElement = ref(null)
const tileLoadFailed = ref(false)

let map = null
let hotelLayer = null
let searchArea = null
const markers = new Map()

const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Places via <a href="https://www.geoapify.com/">Geoapify</a>'

function hotelLabel(hotel) {
  return hotel.name || 'Hotel place with provider name unavailable'
}

function locationLine(hotel) {
  return [hotel.locality, hotel.region, hotel.postcode].filter(Boolean).join(', ')
}

function createPopupContent(hotel) {
  const container = document.createElement('div')
  container.className = 'hotel-popup'

  const name = document.createElement('strong')
  name.textContent = hotel.name || 'Name unavailable from provider'
  container.append(name)

  if (hotel.address) {
    const address = document.createElement('span')
    address.textContent = hotel.address
    container.append(address)
  }

  const location = locationLine(hotel)
  if (location) {
    const locationText = document.createElement('span')
    locationText.textContent = location
    container.append(locationText)
  }

  const coordinates = document.createElement('span')
  coordinates.textContent = `Coordinates: ${hotel.latitude.toFixed(5)}, ${hotel.longitude.toFixed(5)}`
  container.append(coordinates)

  return container
}

function setMarkerAccessibility(placeId, marker) {
  const element = marker.getElement()
  const hotel = props.hotels.find((candidate) => candidate.place_id === placeId)
  if (!element || !hotel) {
    return
  }

  const isSelected = props.selectedPlaceId === placeId
  element.classList.toggle('is-selected', isSelected)
  element.setAttribute('role', 'button')
  element.setAttribute('aria-label', `${hotelLabel(hotel)} map marker`)
  element.setAttribute('aria-pressed', String(isSelected))
}

function updateMarkerSelection() {
  markers.forEach((marker, placeId) => setMarkerAccessibility(placeId, marker))
}

function selectMarker(placeId, marker) {
  marker.openPopup()
  emit('select', placeId)
}

function renderHotels() {
  if (!map || !hotelLayer) {
    return
  }

  hotelLayer.clearLayers()
  markers.clear()
  if (searchArea) {
    searchArea.remove()
  }

  const center = [props.searchCenter.latitude, props.searchCenter.longitude]
  map.setView(center, 13, { animate: false })
  searchArea = L.circle(center, {
    radius: 5000,
    color: '#356e5c',
    weight: 1.5,
    opacity: 0.7,
    fillColor: '#9fc8b8',
    fillOpacity: 0.08,
    interactive: false,
  }).addTo(map)

  props.hotels.forEach((hotel, index) => {
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      alt: hotelLabel(hotel),
      title: hotelLabel(hotel),
      keyboard: true,
      riseOnHover: true,
      icon: L.divIcon({
        className: 'hotel-map-marker-shell',
        html: `<span aria-hidden="true"><b>${index + 1}</b></span>`,
        iconSize: [34, 42],
        iconAnchor: [17, 42],
        popupAnchor: [0, -36],
      }),
    })
    marker.bindPopup(createPopupContent(hotel))
    marker.on('click', () => emit('select', hotel.place_id))
    marker.on('keydown', (event) => {
      if (!['Enter', ' '].includes(event.originalEvent.key)) {
        return
      }
      event.originalEvent.preventDefault()
      selectMarker(hotel.place_id, marker)
    })
    marker.on('add', () => setMarkerAccessibility(hotel.place_id, marker))
    marker.addTo(hotelLayer)
    markers.set(hotel.place_id, marker)
  })

  map.fitBounds(searchArea.getBounds(), {
    animate: false,
    padding: [22, 22],
    maxZoom: 13,
  })

  nextTick(() => {
    map?.invalidateSize({ pan: false })
    updateMarkerSelection()
  })
}

function focusMarker(placeId) {
  const marker = markers.get(placeId)
  if (!map || !marker) {
    return
  }

  map.panTo(marker.getLatLng())
  marker.openPopup()
  requestAnimationFrame(() => {
    setMarkerAccessibility(placeId, marker)
    marker.getElement()?.focus({ preventScroll: true })
  })
}

onMounted(() => {
  map = L.map(mapElement.value, {
    scrollWheelZoom: false,
  })
  const tiles = L.tileLayer(TILE_URL, {
    attribution: TILE_ATTRIBUTION,
    maxZoom: 19,
  })
  tiles.on('tileerror', () => {
    tileLoadFailed.value = true
  })
  tiles.addTo(map)
  hotelLayer = L.layerGroup().addTo(map)
  renderHotels()
})

watch(
  () => [props.hotels, props.searchCenter],
  () => renderHotels(),
  { deep: true },
)

watch(
  () => props.selectedPlaceId,
  () => updateMarkerSelection(),
)

onBeforeUnmount(() => {
  markers.clear()
  hotelLayer = null
  searchArea = null
  map?.remove()
  map = null
})

defineExpose({ focusMarker })
</script>

<template>
  <section class="nearby-map-region" aria-labelledby="nearby-map-title">
    <div class="region-heading">
      <h3 id="nearby-map-title">
        {{ hotels.length }} {{ hotels.length === 1 ? 'place' : 'places' }} returned
        <template v-if="searchCenter.locality"> near {{ searchCenter.locality }}</template>
      </h3>
    </div>
    <div
      ref="mapElement"
      class="nearby-map"
      role="region"
      :aria-label="`Hotel places within 5 km of ZIP ${searchCenter.zip}`"
    ></div>
    <p v-if="tileLoadFailed" class="tile-error" role="status">
      Base map tiles could not be loaded. The hotel list remains available.
    </p>
  </section>
</template>

<style scoped>
.nearby-map-region {
  min-width: 0;
}

.region-heading {
  margin-bottom: 0.85rem;
}

.region-heading h3 {
  margin: 0.15rem 0;
  color: #183b33;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.35rem;
}

.region-heading p {
  margin: 0;
  color: #68736f;
  font-size: 0.84rem;
}

.nearby-map {
  z-index: 0;
  width: 100%;
  min-height: 34rem;
  overflow: hidden;
  border: 1px solid #cad5ce;
  border-radius: 1rem;
  background: #e7ede8;
}

.tile-error {
  margin: 0.7rem 0 0;
  padding: 0.7rem 0.8rem;
  border-radius: 0.65rem;
  background: #fff4f1;
  color: #7f3227;
  font-size: 0.8rem;
}

:deep(.hotel-map-marker-shell) {
  display: grid;
  border: 0;
  background: transparent;
  place-items: center;
}

:deep(.hotel-map-marker-shell span) {
  display: grid;
  width: 2.1rem;
  height: 2.1rem;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 0;
  background: #255c4d;
  color: #fff;
  box-shadow: 0 0.3rem 0.8rem rgba(20, 51, 43, 0.28);
  place-items: center;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 0.75rem;
  font-weight: 850;
  transform: rotate(-45deg);
}

:deep(.hotel-map-marker-shell b) {
  display: block;
  font: inherit;
  transform: rotate(45deg);
}

:deep(.hotel-map-marker-shell.is-selected span) {
  background: #d85f3d;
  box-shadow:
    0 0 0 4px rgba(216, 95, 61, 0.25),
    0 0.35rem 0.9rem rgba(20, 51, 43, 0.3);
  transform: rotate(-45deg) scale(1.15);
}

:deep(.hotel-map-marker-shell:focus-visible) {
  outline: 3px solid #f6a56f;
  outline-offset: 4px;
}

:deep(.hotel-popup) {
  display: flex;
  min-width: 12rem;
  flex-direction: column;
  gap: 0.25rem;
  color: #334d46;
}

:deep(.hotel-popup strong) {
  color: #173a32;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1rem;
}

:deep(.hotel-popup span) {
  font-size: 0.78rem;
  line-height: 1.4;
}

:deep(.leaflet-control-attribution) {
  max-width: calc(100% - 0.5rem);
  background: rgba(255, 255, 255, 0.9);
  white-space: normal;
}

@media (max-width: 760px) {
  .nearby-map {
    min-height: 25rem;
  }
}
</style>
