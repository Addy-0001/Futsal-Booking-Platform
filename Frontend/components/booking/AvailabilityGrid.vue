<script setup>
const props = defineProps(["courtId", "date", "selected"]);
const emit = defineEmits(["toggle"]);
const api = useApi();
// Client-side fetch (server: false) — availability is interactive, not SEO content.
// NOTE: intentionally NOT awaited. Awaiting makes this an async-setup component,
// which fails to render inside <ClientOnly> (no Suspense boundary post-hydration).
const { data, pending, error, refresh } = useAsyncData(
  () => `availability-${props.courtId}-${props.date}`,
  () => api("/api/availability/", { query: { court: props.courtId, date: props.date } }),
  { server: false, lazy: true, watch: [() => props.courtId, () => props.date] }
);
const errorMsg = computed(() => {
  if (!error.value) return "";
  const status = error.value?.statusCode || error.value?.response?.status;
  if (!status) return "Can't reach the server. Is the backend running on the API URL, and CORS allowing this site?";
  if (status === 404) return "Court not found or the venue isn't active.";
  return apiErrorMessage(error.value, `Request failed (HTTP ${status}).`);
});
const selectedSet = computed(() => new Set(props.selected || []));
function fmt(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
</script>

<template>
  <div>
    <div v-if="pending" class="grid grid-cols-2 sm:grid-cols-3 gap-2">
      <USkeleton v-for="i in 6" :key="i" class="h-14 rounded-xl" />
    </div>

    <div v-else-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
      <p class="text-sm font-semibold text-red-300">Could not load availability</p>
      <p class="text-xs text-red-200/80 mt-1">{{ errorMsg }}</p>
      <button class="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-[#c9ff47] px-3 py-1.5 text-xs font-bold text-black hover:bg-[#d9ff6b]" @click="refresh()">
        <UIcon name="i-heroicons-arrow-path" /> Retry
      </button>
    </div>

    <div v-else-if="data && !data.is_open" class="text-center py-10 text-[#888888]">
      <UIcon name="i-heroicons-no-symbol" class="text-3xl" />
      <p class="mt-2">Closed on this date.</p>
    </div>

    <div v-else-if="data" class="grid grid-cols-2 sm:grid-cols-3 gap-2">
      <button
        v-for="slot in data.slots"
        :key="slot.start_at"
        type="button"
        :disabled="!slot.available"
        class="relative rounded-xl border px-3 py-2.5 text-sm text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60"
        :class="selectedSet.has(slot.start_at)
          ? 'border-[#c9ff47]/60 surface-volt text-ink-950 shadow-volt scale-[1.02]'
          : slot.available
            ? 'border-white/[0.08] bg-[#141414] hover:border-[#c9ff47]/50 hover:bg-[#1a1a1a] hover:-translate-y-0.5'
            : 'border-white/[0.06] bg-[#111111] text-[#6b6b6b] cursor-not-allowed'"
        @click="emit('toggle', slot)"
      >
        <span class="block font-medium">{{ fmt(slot.start_at) }}–{{ fmt(slot.end_at) }}</span>
        <span
          class="block text-xs font-medium"
          :class="selectedSet.has(slot.start_at)
            ? 'text-ink-950/80'
            : slot.status === 'free' ? 'text-[#c9ff47]' : 'text-[#6b6b6b]'"
        >
          {{ slot.status === 'free' ? `NPR ${slot.price}` : slot.status === 'taken' ? 'Booked' : 'Past' }}
        </span>
        <UIcon
          v-if="selectedSet.has(slot.start_at)"
          name="i-heroicons-check-circle-solid"
          class="absolute top-1.5 right-1.5 text-ink-950"
        />
      </button>
    </div>
  </div>
</template>
