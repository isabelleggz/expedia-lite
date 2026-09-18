<template>
  <nav class="travel-categories" aria-label="Travel categories">
    <a class="category-item is-active" href="#hotel-search" aria-current="page">
      <span class="category-icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="M8 29V18a4 4 0 0 1 4-4h24a4 4 0 0 1 4 4v11" />
          <path d="M6 29h36v10H6zM12 23h10v6H12zM26 23h10v6H26zM10 39v4M38 39v4" />
        </svg>
      </span>
      <span>Stays</span>
    </a>

    <a
      class="category-item"
      href="https://www.expedia.com/Flights"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Flights – opens Expedia in a new tab"
    >
      <span class="category-icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="m7 27 14-5 10-14 5 2-6 15 10 6-2 4-12-3-7 9-4-2 3-10-9 2z" />
        </svg>
      </span>
      <span>Flights</span>
      <span class="external-mark" aria-hidden="true">↗</span>
    </a>

    <button class="category-item" type="button" disabled title="Road trips are coming soon">
      <span class="category-icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="M10 29h28l-3-10H14zM8 29v8h32v-8M14 37v4M34 37v4" />
          <circle cx="15" cy="32" r="2" />
          <circle cx="33" cy="32" r="2" />
        </svg>
      </span>
      <span>Road trips</span>
    </button>

    <button class="category-item" type="button" disabled title="Rail trips are coming soon">
      <span class="category-icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="M13 8h22a4 4 0 0 1 4 4v21H9V12a4 4 0 0 1 4-4zM13 15h22M16 38l-4 4M32 38l4 4" />
          <circle cx="16" cy="28" r="2" />
          <circle cx="32" cy="28" r="2" />
        </svg>
      </span>
      <span>Rail</span>
    </button>

    <button class="category-item" type="button" disabled title="Local picks are coming soon">
      <span class="category-icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="m7 37 11-16 7 9 5-7 11 14z" />
          <circle cx="34" cy="13" r="5" />
          <path d="M24 37c0-8 4-14 10-18" />
        </svg>
      </span>
      <span>Local picks</span>
    </button>
  </nav>
</template>
