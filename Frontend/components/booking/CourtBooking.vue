<script setup>
const props = defineProps(["venue"]);
const api = useApi();
const auth = useAuthStore();
const route = useRoute();
const toast = useToast();

const courts = computed(() => props.venue.courts || []);
const selectedCourt = ref(courts.value[0]?.id ?? "");
const selectedCourtObj = computed(() => courts.value.find((c) => c.id === selectedCourt.value));

// Next 7 days as selectable chips (local dates).
const days = computed(() => {
  const out = [];
  const base = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(base);
    d.setDate(base.getDate() + i);
    out.push({
      value: d.toLocaleDateString("en-CA"), // YYYY-MM-DD
      dow: d.toLocaleDateString([], { weekday: "short" }),
      day: d.getDate(),
      month: d.toLocaleDateString([], { month: "short" }),
      isToday: i === 0,
    });
  }
  return out;
});
const date = ref(days.value[0].value);

const version = ref(0); // bump to force the grid to refetch
const selected = ref([]);
const selectedKeys = computed(() => selected.value.map((s) => s.start_at));
const total = computed(() => selected.value.reduce((sum, s) => sum + Number(s.price), 0));

// Changing court/date clears the current selection.
watch([selectedCourt, date], () => (selected.value = []));

const booking = ref(false);
const justBooked = ref([]); // slots successfully booked in the last action
const bookError = ref("");

function onToggle(slot) {
  justBooked.value = [];
  bookError.value = "";
  const i = selected.value.findIndex((s) => s.start_at === slot.start_at);
  if (i >= 0) selected.value.splice(i, 1);
  else selected.value = [...selected.value, slot].sort((a, b) => a.start_at.localeCompare(b.start_at));
}
function clearSelection() {
  selected.value = [];
}
function loginRedirect() {
  return navigateTo(`/login?next=${encodeURIComponent(route.fullPath)}`);
}
function fmtDate(iso) {
  return new Date(iso).toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}
function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

async function book() {
  if (!selected.value.length) return;
  if (!auth.isAuthenticated) return loginRedirect();

  booking.value = true;
  bookError.value = "";
  let ok = [];
  const failed = [];
  for (const slot of [...selected.value].sort((a, b) => a.start_at.localeCompare(b.start_at))) {
    try {
      await api("/api/bookings/", {
        method: "POST",
        body: { court: selectedCourt.value, start_at: slot.start_at, end_at: slot.end_at },
      });
      ok.push(slot);
    } catch (e) {
      const status = e?.statusCode || e?.response?.status;
      let msg = apiErrorMessage(e);
      if (!status) msg = "Can't reach the server (network/CORS). Make sure the backend is running and this site is allowed.";
      else if (status === 401) msg = "Your session expired — please sign in again.";
      failed.push(`${fmtTime(slot.start_at)} — ${msg}`);
    }
  }
  booking.value = false;
  version.value++; // refresh grid so booked slots show as taken
  clearSelection();

  if (ok.length && !failed.length) {
    justBooked.value = ok;
    toast.add({ title: `${ok.length} slot${ok.length > 1 ? "s" : ""} requested`, description: "Pending venue approval.", color: "green" });
  } else if (ok.length && failed.length) {
    justBooked.value = ok;
    bookError.value = failed[0];
    toast.add({ title: `${ok.length} booked, ${failed.length} failed`, description: failed[0], color: "orange" });
  } else {
    bookError.value = failed[0] || "Please try again.";
    toast.add({ title: "Could not book", description: bookError.value, color: "red" });
  }
}
</script>

<template>
  <div class="rounded-2xl border border-white/[0.08] bg-[#141414] overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3 px-5 py-4 border-b border-white/[0.06]">
      <h2 class="font-display text-xl font-black uppercase tracking-tight text-white inline-flex items-center gap-2">
        <UIcon name="i-heroicons-bolt-solid" class="text-[#c9ff47]" />
        Book a slot
      </h2>
      <span class="text-xs text-[#888888] hidden sm:block">Tap a time, then book — pay at the venue</span>
    </div>

    <div class="p-5">
      <!-- Success banner -->
      <div
        v-if="justBooked.length"
        class="mb-5 rounded-xl border border-[#c9ff47]/30 bg-[#c9ff47]/[0.06] p-4"
      >
        <div class="flex items-start gap-3">
          <UIcon name="i-heroicons-check-circle-solid" class="text-[#c9ff47] text-2xl shrink-0" />
          <div class="flex-1">
            <p class="font-semibold text-white">Requested {{ justBooked.length }} slot{{ justBooked.length > 1 ? "s" : "" }} — pending approval</p>
            <p class="text-sm text-[#9a9a9a] mt-0.5">
              {{ justBooked.map((s) => fmtTime(s.start_at)).join(", ") }} · {{ fmtDate(justBooked[0].start_at) }}
            </p>
            <NuxtLink to="/dashboard/bookings" class="inline-flex items-center gap-1 mt-2 text-sm font-semibold text-[#c9ff47] hover:text-[#d9ff6b]">
              View my bookings <UIcon name="i-heroicons-arrow-right" />
            </NuxtLink>
          </div>
          <button class="text-[#666] hover:text-white" @click="justBooked = []"><UIcon name="i-heroicons-x-mark" /></button>
        </div>
      </div>

      <!-- Booking error banner -->
      <div v-if="bookError" class="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
        <div class="flex items-start gap-3">
          <UIcon name="i-heroicons-exclamation-triangle" class="text-red-400 text-xl shrink-0" />
          <div class="flex-1">
            <p class="font-semibold text-red-300">Booking didn't go through</p>
            <p class="text-sm text-red-200/80 mt-0.5">{{ bookError }}</p>
          </div>
          <button class="text-[#666] hover:text-white" @click="bookError = ''"><UIcon name="i-heroicons-x-mark" /></button>
        </div>
      </div>

      <!-- Court selector (only when more than one) -->
      <div v-if="courts.length > 1" class="mb-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-[#888888] mb-2">Court</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="c in courts"
            :key="c.id"
            type="button"
            class="px-3.5 py-1.5 rounded-full text-sm font-semibold transition-colors"
            :class="selectedCourt === c.id
              ? 'bg-[#c9ff47] text-black'
              : 'bg-[#1a1a1a] border border-white/[0.08] text-[#bdbdbd] hover:text-white hover:border-white/25'"
            @click="selectedCourt = c.id"
          >
            {{ c.name }}
          </button>
        </div>
      </div>

      <!-- Date chips -->
      <p class="text-xs font-semibold uppercase tracking-wide text-[#888888] mb-2">Date</p>
      <div class="flex gap-2 overflow-x-auto no-scrollbar pb-1 mb-5">
        <button
          v-for="d in days"
          :key="d.value"
          type="button"
          class="shrink-0 w-16 py-2 rounded-xl border text-center transition-colors"
          :class="date === d.value
            ? 'bg-[#c9ff47] border-transparent text-black'
            : 'bg-[#1a1a1a] border-white/[0.08] text-[#bdbdbd] hover:border-white/25'"
          @click="date = d.value"
        >
          <span class="block text-[11px] font-semibold uppercase" :class="date === d.value ? 'text-black/70' : 'text-[#888888]'">
            {{ d.isToday ? "Today" : d.dow }}
          </span>
          <span class="block font-display text-lg font-bold leading-none mt-0.5">{{ d.day }}</span>
          <span class="block text-[10px] uppercase" :class="date === d.value ? 'text-black/60' : 'text-[#666]'">{{ d.month }}</span>
        </button>
      </div>

      <!-- Slot grid -->
      <AvailabilityGrid
        v-if="selectedCourt"
        :key="`${selectedCourt}-${date}-${version}`"
        :court-id="selectedCourt"
        :date="date"
        :selected="selectedKeys"
        @toggle="onToggle"
      />
      <p v-else class="text-[#888888] text-sm">No courts available to book.</p>

      <!-- Legend -->
      <div class="mt-4 flex flex-wrap items-center gap-4 text-xs text-[#888888]">
        <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#141414] border border-white/[0.12]" /> Available</span>
        <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#c9ff47]" /> Selected</span>
        <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#111111] border border-white/[0.06]" /> Booked / past</span>
      </div>
    </div>

    <!-- Sticky booking bar -->
    <div
      v-if="selected.length"
      class="sticky bottom-0 border-t border-white/[0.08] bg-[#0f0f0f]/95 backdrop-blur px-5 py-4"
    >
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="font-display text-lg font-bold text-white leading-none">
            {{ selected.length }} slot{{ selected.length > 1 ? "s" : "" }}
            <span class="text-[#c9ff47]">· NPR {{ total }}</span>
          </p>
          <p class="text-xs text-[#888888] mt-1">
            {{ selectedCourtObj?.name }} · {{ selected.map((s) => fmtTime(s.start_at)).join(", ") }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button class="px-3 py-2 text-sm font-semibold text-[#9a9a9a] hover:text-white" @click="clearSelection">Clear</button>
          <button
            class="inline-flex items-center gap-2 rounded-full bg-[#c9ff47] px-6 py-2.5 text-sm font-bold text-black hover:bg-[#d9ff6b] transition-colors disabled:opacity-60"
            :disabled="booking"
            @click="book"
          >
            <UIcon v-if="booking" name="i-heroicons-arrow-path" class="animate-spin" />
            <UIcon v-else-if="!auth.isAuthenticated" name="i-heroicons-lock-closed" />
            {{ auth.isAuthenticated ? (booking ? "Booking…" : "Book now") : "Sign in to book" }}
          </button>
        </div>
      </div>
      <p class="text-[11px] text-[#666] mt-2">Each slot is sent to the venue for approval. No payment now — pay at the venue.</p>
    </div>
  </div>
</template>
