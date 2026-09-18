<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['dates-updated'])

const dialogRef = ref(null)
const selectedDates = ref([])

function buildMonth(year, monthIndex, name) {
  const firstDay = new Date(year, monthIndex, 1).getDay()
  const dayCount = new Date(year, monthIndex + 1, 0).getDate()
  const days = Array.from({ length: firstDay }, () => null)

  for (let day = 1; day <= dayCount; day += 1) {
    const month = String(monthIndex + 1).padStart(2, '0')
    const paddedDay = String(day).padStart(2, '0')
    days.push({ day, iso: `${year}-${month}-${paddedDay}` })
  }

  return { year, monthIndex, name, days }
}

const months = [
  buildMonth(2026, 8, 'September'),
  buildMonth(2026, 9, 'October'),
]

const selectedSummary = computed(() => {
  if (!selectedDates.value.length) {
    return 'Check-in — Check-out'
  }

  const formatter = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
  const labels = selectedDates.value.map((date) => formatter.format(new Date(`${date}T00:00:00Z`)))
  return labels.length === 1 ? `${labels[0]} — Check-out` : `${labels[0]} — ${labels[1]}`
})

function accessibleDate(iso) {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(new Date(`${iso}T00:00:00Z`))
}

function selectDate(iso) {
  if (selectedDates.value.includes(iso)) {
    selectedDates.value = selectedDates.value.filter((date) => date !== iso)
    return
  }

  if (selectedDates.value.length >= 2) {
    selectedDates.value = [iso]
    return
  }

  selectedDates.value = [...selectedDates.value, iso].sort()
}

function clearDates() {
  selectedDates.value = []
}

function open() {
  if (!dialogRef.value?.open) {
    dialogRef.value?.showModal()
  }
}

function close() {
  dialogRef.value?.close()
}

function applyDates() {
  emit('dates-updated', selectedSummary.value)
  close()
}

defineExpose({ open, close })
</script>

<template>
  <dialog ref="dialogRef" class="date-dialog" aria-labelledby="date-dialog-title" aria-describedby="date-dialog-description">
    <div class="dialog-header">
      <div>
        <p class="eyebrow">Planning preference</p>
        <h2 id="date-dialog-title">Plan your dates</h2>
        <p id="date-dialog-description">Choose an optional check-in and check-out window.</p>
      </div>
      <button class="icon-button" type="button" aria-label="Close date planner" @click="close">
        <span aria-hidden="true">×</span>
      </button>
    </div>

    <div class="calendar-pair">
      <section v-for="month in months" :key="month.name" class="calendar" :aria-labelledby="`${month.name}-title`">
        <h3 :id="`${month.name}-title`">{{ month.name }} {{ month.year }}</h3>
        <div class="weekday-row" aria-hidden="true">
          <span v-for="weekday in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']" :key="weekday">
            {{ weekday }}
          </span>
        </div>
        <div class="calendar-grid">
          <template v-for="(date, index) in month.days" :key="date?.iso || `${month.name}-${index}`">
            <span v-if="!date" aria-hidden="true"></span>
            <button
              v-else
              type="button"
              class="date-button"
              :class="{ 'is-selected': selectedDates.includes(date.iso) }"
              :aria-label="accessibleDate(date.iso)"
              :aria-pressed="selectedDates.includes(date.iso)"
              @click="selectDate(date.iso)"
            >
              {{ date.day }}
            </button>
          </template>
        </div>
      </section>
    </div>

    <div class="dialog-footer">
      <p aria-live="polite">{{ selectedSummary }}</p>
      <div class="dialog-actions">
        <button class="text-button" type="button" @click="clearDates">Clear dates</button>
        <button type="button" @click="applyDates">Done</button>
      </div>
    </div>
  </dialog>
</template>
