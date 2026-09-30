<script setup>
import { nextTick } from 'vue'

defineProps({
  hotels: {
    type: Array,
    required: true,
  },
  selectedPlaceId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['select'])
const hotelButtons = new Map()

function setHotelButton(element, placeId) {
  if (element) {
    hotelButtons.set(placeId, element)
  } else {
    hotelButtons.delete(placeId)
  }
}

function locationLine(hotel) {
  return [hotel.locality, hotel.region, hotel.postcode].filter(Boolean).join(', ')
}

function coordinateLine(hotel) {
  if (!Number.isFinite(hotel.latitude) || !Number.isFinite(hotel.longitude)) {
    return ''
  }
  return `${hotel.latitude.toFixed(5)}, ${hotel.longitude.toFixed(5)}`
}

function selectWithKeyboard(event, placeId) {
  if (!['Enter', ' '].includes(event.key)) {
    return
  }
  event.preventDefault()
  emit('select', placeId)
}

async function focusHotel(placeId) {
  await nextTick()
  const button = hotelButtons.get(placeId)
  if (!button) {
    return
  }
  button.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  button.focus({ preventScroll: true })
}

defineExpose({ focusHotel })
</script>

<template>
  <section class="nearby-list-region" aria-labelledby="nearby-list-title">
    <div class="region-heading">
      <h3 id="nearby-list-title">Hotel list</h3>
    </div>

    <ol class="nearby-hotel-list">
      <li v-for="(hotel, index) in hotels" :key="hotel.place_id">
        <button
          :ref="(element) => setHotelButton(element, hotel.place_id)"
          type="button"
          class="nearby-hotel-card"
          :class="{ 'is-selected': selectedPlaceId === hotel.place_id }"
          :aria-pressed="selectedPlaceId === hotel.place_id"
          @click="emit('select', hotel.place_id)"
          @keydown="selectWithKeyboard($event, hotel.place_id)"
        >
          <span class="hotel-index" aria-hidden="true">{{ index + 1 }}</span>
          <span class="hotel-card-copy">
            <span class="hotel-provider-name">
              {{ hotel.name || 'Name unavailable from provider' }}
            </span>
            <span v-if="hotel.address" class="hotel-provider-address">{{ hotel.address }}</span>
            <span v-if="locationLine(hotel)" class="hotel-provider-location">
              {{ locationLine(hotel) }}
            </span>
            <span v-if="coordinateLine(hotel)" class="hotel-provider-coordinates">
              Coordinates: {{ coordinateLine(hotel) }}
            </span>
          </span>
          <span v-if="selectedPlaceId === hotel.place_id" class="selected-label">
            Selected
          </span>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.nearby-list-region {
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

.nearby-hotel-list {
  display: grid;
  margin: 0;
  padding: 0;
  gap: 0.7rem;
  list-style: none;
}

.nearby-hotel-card {
  display: grid;
  width: 100%;
  min-height: 7.5rem;
  padding: 1rem;
  border: 1px solid #d8e0da;
  border-radius: 0.9rem;
  align-items: start;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.8rem;
  background: #fffefa;
  color: #203d36;
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.nearby-hotel-card:hover {
  border-color: #7f9c91;
  background: #f8faf6;
}

.nearby-hotel-card.is-selected {
  border-color: #c55235;
  background: #fff5ef;
  box-shadow: 0 0 0 3px rgba(216, 95, 61, 0.14);
}

.hotel-index {
  display: grid;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: #e5eee7;
  color: #255346;
  place-items: center;
  font-size: 0.78rem;
  font-weight: 850;
}

.is-selected .hotel-index {
  background: #d85f3d;
  color: #fff;
}

.hotel-card-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.28rem;
}

.hotel-provider-name {
  color: #173a32;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.05rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.hotel-provider-address,
.hotel-provider-location,
.hotel-provider-coordinates {
  color: #64716c;
  font-size: 0.8rem;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.hotel-provider-coordinates {
  color: #425c54;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
}

.selected-label {
  padding: 0.28rem 0.48rem;
  border-radius: 999px;
  background: #f5d7ca;
  color: #833722;
  font-size: 0.66rem;
  font-weight: 850;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

@media (max-width: 480px) {
  .nearby-hotel-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .selected-label {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
