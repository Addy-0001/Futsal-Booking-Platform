<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "Bookings | Booksall" });

const api = useApi();
const auth = useAuthStore();
const toast = useToast();

// ---------- Venue / court / date selection ----------
const { data: venues, pending: venuesPending } = await useMyVenues();
const selectedVenueId = ref(null);
const selectedVenue = computed(() => (venues.value || []).find((v) => v.id === selectedVenueId.value));
const courts = computed(() => selectedVenue.value?.courts || []);
const selectedCourt = ref(null);

watch(venues, (list) => {
    if (list?.length && !selectedVenueId.value) selectedVenueId.value = list[0].id;
}, { immediate: true });
watch(selectedVenue, (v) => {
    selectedCourt.value = v?.courts?.[0]?.id ?? null;
}, { immediate: true });

// Next 7 days as chips + free-form date input for anything else.
const days = computed(() => {
    const out = [];
    const base = new Date();
    for (let i = 0; i < 7; i++) {
        const d = new Date(base);
        d.setDate(base.getDate() + i);
        out.push({
            value: d.toLocaleDateString("en-CA"),
            dow: d.toLocaleDateString([], { weekday: "short" }),
            day: d.getDate(),
            month: d.toLocaleDateString([], { month: "short" }),
            isToday: i === 0,
        });
    }
    return out;
});
const date = ref(new Date().toLocaleDateString("en-CA"));

// ---------- Day data: availability grid + bookings overlay ----------
const version = ref(0);
const dayRange = computed(() => {
    const start = new Date(`${date.value}T00:00:00`);
    const end = new Date(start);
    end.setDate(start.getDate() + 1);
    return { gte: start.toISOString(), lt: end.toISOString() };
});

const { data: avail, pending: availPending, error: availError } = useAsyncData(
    () => `manage-avail-${selectedCourt.value}-${date.value}-${version.value}`,
    () => api("/api/availability/", { query: { court: selectedCourt.value, date: date.value } }),
    { server: false, lazy: true, watch: [selectedCourt, date, version], immediate: true }
);
const { data: dayBookings } = useAsyncData(
    () => `manage-bookings-${selectedCourt.value}-${date.value}-${version.value}`,
    () => api("/api/bookings/", {
        query: { court: selectedCourt.value, start_at__gte: dayRange.value.gte, start_at__lt: dayRange.value.lt, page_size: 100 },
    }),
    { server: false, lazy: true, watch: [selectedCourt, date, version], immediate: true }
);

const OVERLAY_STATUSES = new Set(["PENDING_APPROVAL", "APPROVED", "COMPLETED"]);
function bookingForSlot(slot) {
    const t = new Date(slot.start_at).getTime();
    return (dayBookings.value?.results || []).find((b) =>
        OVERLAY_STATUSES.has(b.status) &&
        new Date(b.start_at).getTime() <= t && t < new Date(b.end_at).getTime());
}
// Slots decorated with their booking (if any).
const slots = computed(() => (avail.value?.slots || []).map((s) => ({ ...s, booking: bookingForSlot(s) })));
const dayStats = computed(() => {
    const out = { pending: 0, approved: 0, free: 0 };
    const seen = new Set();
    for (const s of slots.value) {
        if (s.booking && !seen.has(s.booking.id)) {
            seen.add(s.booking.id);
            if (s.booking.status === "PENDING_APPROVAL") out.pending++;
            else if (s.booking.status === "APPROVED") out.approved++;
        } else if (!s.booking && s.available) out.free++;
    }
    return out;
});

function slotClass(s) {
    if (selectedKey.value === s.start_at) return "border-[#c9ff47] bg-[#c9ff47]/15 ring-1 ring-[#c9ff47]/60";
    if (s.booking?.status === "PENDING_APPROVAL") return "border-amber-400/40 bg-amber-400/10 hover:border-amber-400/70";
    if (s.booking?.status === "APPROVED") return "border-emerald-400/40 bg-emerald-400/10 hover:border-emerald-400/70";
    if (s.booking?.status === "COMPLETED") return "border-white/[0.08] bg-[#181818] text-[#8f8f8f]";
    if (!s.available) return "border-white/[0.06] bg-[#111111] text-[#6b6b6b]";
    return "border-white/[0.08] bg-[#141414] hover:border-[#c9ff47]/50 hover:bg-[#1a1a1a]";
}
function slotLabel(s) {
    if (s.booking) {
        if (s.booking.user === auth.user?.id) return "Blocked / walk-in";
        return s.booking.user_name || "Booked";
    }
    return s.available ? "Free" : "Past";
}

// ---------- Selection + actions ----------
const selectedKey = ref(null);
const selectedSlot = computed(() => slots.value.find((s) => s.start_at === selectedKey.value) || null);
watch([selectedCourt, date], () => (selectedKey.value = null));

const acting = ref(false);
const reason = ref("");
const showReason = ref(null); // "reject" | "cancel" | null
watch(selectedKey, () => { reason.value = ""; showReason.value = null; });

function fmtTime(iso) {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function fmtWhen(iso) {
    return new Date(iso).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
function telHref(phone) {
    return `tel:${(phone || "").replace(/\s+/g, "")}`;
}

async function refreshDay() {
    version.value++;
    await refreshPending();
}

async function act(booking, action, { withReason = false, success } = {}) {
    acting.value = true;
    try {
        const body = withReason && reason.value.trim() ? { reason: reason.value.trim() } : {};
        await api(`/api/bookings/${booking.id}/${action}/`, { method: "POST", body });
        toast.add({ title: success, color: action === "approve" || action === "complete" ? "green" : "amber" });
        showReason.value = null;
        reason.value = "";
        await refreshDay();
    } catch (e) {
        toast.add({ title: "Action failed", description: apiErrorMessage(e), color: "red" });
    } finally {
        acting.value = false;
    }
}

// Owner blocks a free slot (walk-in / maintenance): create + self-approve.
async function blockSlot(slot) {
    acting.value = true;
    try {
        const b = await api("/api/bookings/", {
            method: "POST",
            body: { court: selectedCourt.value, start_at: slot.start_at, end_at: slot.end_at, note: "Blocked by venue (walk-in/offline)" },
        });
        await api(`/api/bookings/${b.id}/approve/`, { method: "POST" });
        toast.add({ title: "Slot blocked", description: `${fmtTime(slot.start_at)} is now reserved.`, color: "green" });
        await refreshDay();
    } catch (e) {
        toast.add({ title: "Could not block slot", description: apiErrorMessage(e), color: "red" });
    } finally {
        acting.value = false;
    }
}

// ---------- Pending queue (all courts of the selected venue) ----------
const { data: pendingData, refresh: refreshPending, pending: pendingLoading } = useAsyncData(
    () => `manage-pending-${selectedVenueId.value}`,
    () => api("/api/bookings/", {
        query: { court__futsal: selectedVenueId.value, status: "PENDING_APPROVAL", ordering: "start_at", page_size: 100 },
    }),
    { server: false, lazy: true, watch: [selectedVenueId], immediate: true }
);
const queue = computed(() => pendingData.value?.results || []);

function jumpTo(b) {
    const d = new Date(b.start_at).toLocaleDateString("en-CA");
    selectedCourt.value = b.court;
    date.value = d;
    // Select once the grid refetches.
    selectedKey.value = b.start_at;
}

function fmtRange(startIso, endIso) {
    const start = new Date(startIso);
    const day = start.toLocaleString([], { weekday: "short", day: "numeric", month: "short" });
    return `${day}, ${fmtTime(startIso)} – ${fmtTime(endIso)}`;
}
</script>

<template>
  <div>
    <ClientOnly>
      <!-- Header -->
      <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 class="font-display text-3xl font-bold text-[#f0f0f0]">Bookings</h1>
          <p class="text-sm text-[#888888] mt-1">Approve requests, manage the schedule, and block slots for walk-ins.</p>
        </div>
        <UBadge v-if="queue.length" color="amber" variant="subtle" size="lg">{{ queue.length }} pending</UBadge>
      </div>

      <div v-if="venuesPending" class="space-y-3">
        <USkeleton class="h-24 rounded-2xl" />
        <USkeleton class="h-64 rounded-2xl" />
      </div>

      <div v-else-if="!venues?.length" class="rounded-3xl border border-white/[0.06] bg-[#141414] text-center py-16">
        <div class="mx-auto w-14 h-14 rounded-2xl bg-[#1a1a1a] grid place-items-center text-[#c9ff47]">
          <UIcon name="i-heroicons-building-storefront" class="text-3xl" />
        </div>
        <p class="mt-4 font-display font-semibold text-[#f0f0f0]">No venues yet</p>
        <p class="mt-1 text-[#888888]">Add a futsal to start managing bookings.</p>
        <UButton to="/manage" color="primary" variant="soft" class="mt-5">Go to manager dashboard</UButton>
      </div>

      <template v-else>
        <!-- Venue / court selectors -->
        <div class="rounded-2xl border border-white/[0.06] bg-[#141414] p-4 sm:p-5 mb-6">
          <div v-if="venues.length > 1" class="mb-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-[#888888] mb-2">Venue</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="v in venues" :key="v.id" type="button"
                class="px-3.5 py-1.5 rounded-full text-sm font-semibold transition-colors"
                :class="selectedVenueId === v.id ? 'bg-[#c9ff47] text-black' : 'bg-[#1a1a1a] border border-white/[0.08] text-[#bdbdbd] hover:text-white hover:border-white/25'"
                @click="selectedVenueId = v.id"
              >
                {{ v.name }}
              </button>
            </div>
          </div>

          <div v-if="courts.length > 1" class="mb-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-[#888888] mb-2">Court</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="c in courts" :key="c.id" type="button"
                class="px-3.5 py-1.5 rounded-full text-sm font-semibold transition-colors"
                :class="selectedCourt === c.id ? 'bg-[#c9ff47] text-black' : 'bg-[#1a1a1a] border border-white/[0.08] text-[#bdbdbd] hover:text-white hover:border-white/25'"
                @click="selectedCourt = c.id"
              >
                {{ c.name }}
              </button>
            </div>
          </div>

          <!-- Date chips + date picker -->
          <p class="text-xs font-semibold uppercase tracking-wide text-[#888888] mb-2">Date</p>
          <div class="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
            <button
              v-for="d in days" :key="d.value" type="button"
              class="shrink-0 w-16 py-2 rounded-xl border text-center transition-colors"
              :class="date === d.value ? 'bg-[#c9ff47] border-transparent text-black' : 'bg-[#1a1a1a] border-white/[0.08] text-[#bdbdbd] hover:border-white/25'"
              @click="date = d.value"
            >
              <span class="block text-[11px] font-semibold uppercase" :class="date === d.value ? 'text-black/70' : 'text-[#888888]'">
                {{ d.isToday ? "Today" : d.dow }}
              </span>
              <span class="block font-display text-lg font-bold leading-none mt-0.5">{{ d.day }}</span>
              <span class="block text-[10px] uppercase" :class="date === d.value ? 'text-black/60' : 'text-[#666]'">{{ d.month }}</span>
            </button>
            <input
              v-model="date"
              type="date"
              class="shrink-0 h-[3.75rem] rounded-xl border border-white/[0.08] bg-[#1a1a1a] px-3 text-sm text-[#bdbdbd] focus:outline-none focus:border-[#c9ff47]/60 [color-scheme:dark]"
            />
          </div>
        </div>

        <div class="grid lg:grid-cols-[minmax(0,1fr)_340px] gap-6 items-start">
          <!-- Day schedule grid -->
          <div class="rounded-2xl border border-white/[0.08] bg-[#141414] overflow-hidden">
            <div class="flex flex-wrap items-center justify-between gap-2 px-5 py-4 border-b border-white/[0.06]">
              <h2 class="font-display text-lg font-black uppercase tracking-tight text-white inline-flex items-center gap-2">
                <UIcon name="i-heroicons-calendar-days" class="text-[#c9ff47]" />
                Day schedule
              </h2>
              <div class="flex items-center gap-3 text-xs text-[#888888]">
                <span class="inline-flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400" /> {{ dayStats.approved }} approved</span>
                <span class="inline-flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-400" /> {{ dayStats.pending }} pending</span>
                <span class="inline-flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-[#333]" /> {{ dayStats.free }} free</span>
              </div>
            </div>

            <div class="p-5">
              <div v-if="availPending" class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <USkeleton v-for="i in 9" :key="i" class="h-16 rounded-xl" />
              </div>

              <div v-else-if="availError" class="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                <p class="text-sm font-semibold text-red-300">Could not load the schedule</p>
                <p class="text-xs text-red-200/80 mt-1">{{ apiErrorMessage(availError) }}</p>
                <UButton color="primary" size="xs" class="mt-3" icon="i-heroicons-arrow-path" @click="version++">Retry</UButton>
              </div>

              <div v-else-if="avail && !avail.is_open" class="text-center py-12 text-[#888888]">
                <UIcon name="i-heroicons-no-symbol" class="text-3xl" />
                <p class="mt-2">Closed on this date.</p>
              </div>

              <div v-else class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <button
                  v-for="s in slots" :key="s.start_at" type="button"
                  class="relative rounded-xl border px-3 py-2.5 text-sm text-left transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60"
                  :class="slotClass(s)"
                  @click="selectedKey = selectedKey === s.start_at ? null : s.start_at"
                >
                  <span class="block font-medium text-[#f0f0f0]">{{ fmtTime(s.start_at) }}–{{ fmtTime(s.end_at) }}</span>
                  <span class="block text-xs mt-0.5 truncate"
                    :class="s.booking?.status === 'PENDING_APPROVAL' ? 'text-amber-400'
                      : s.booking?.status === 'APPROVED' ? 'text-emerald-400'
                      : s.booking?.status === 'COMPLETED' ? 'text-[#8f8f8f]'
                      : s.available ? 'text-[#c9ff47]' : 'text-[#6b6b6b]'">
                    {{ slotLabel(s) }}
                  </span>
                </button>
              </div>

              <div class="mt-4 flex flex-wrap items-center gap-4 text-xs text-[#888888]">
                <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#141414] border border-white/[0.12]" /> Free</span>
                <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-400/20 border border-amber-400/40" /> Pending</span>
                <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-400/20 border border-emerald-400/40" /> Approved</span>
                <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#181818] border border-white/[0.08]" /> Completed / past</span>
              </div>
            </div>
          </div>

          <!-- Detail / action panel -->
          <aside class="lg:sticky lg:top-24 rounded-2xl border border-white/[0.08] bg-[#141414]">
            <div class="px-5 py-4 border-b border-white/[0.06]">
              <h2 class="font-display text-lg font-black uppercase tracking-tight text-white">Slot details</h2>
            </div>

            <div v-if="!selectedSlot" class="p-6 text-center text-[#888888]">
              <UIcon name="i-heroicons-cursor-arrow-rays" class="text-3xl" />
              <p class="mt-2 text-sm">Select a slot on the schedule to view or manage it.</p>
            </div>

            <div v-else class="p-5 space-y-4">
              <div>
                <p class="text-xs text-[#666]">Time</p>
                <p class="font-display text-lg font-semibold text-[#f0f0f0]">
                  {{ fmtTime(selectedSlot.start_at) }} – {{ fmtTime(selectedSlot.end_at) }}
                </p>
              </div>

              <!-- Booked slot -->
              <template v-if="selectedSlot.booking">
                <div class="rounded-xl bg-[#0f0f0f] border border-white/[0.05] p-4 space-y-3">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-xs text-[#666]">Status</p>
                    <span
                      class="text-xs font-bold px-2.5 py-1 rounded-full"
                      :class="selectedSlot.booking.status === 'PENDING_APPROVAL' ? 'bg-amber-400/15 text-amber-400'
                        : selectedSlot.booking.status === 'APPROVED' ? 'bg-emerald-400/15 text-emerald-400'
                        : 'bg-white/5 text-[#8f8f8f]'"
                    >
                      {{ selectedSlot.booking.status === 'PENDING_APPROVAL' ? 'Pending' : selectedSlot.booking.status === 'APPROVED' ? 'Approved' : 'Completed' }}
                    </span>
                  </div>
                  <div>
                    <p class="text-xs text-[#666] mb-1">Booked by</p>
                    <p class="font-semibold text-[#f0f0f0]">
                      {{ selectedSlot.booking.user === auth.user?.id ? "You (blocked slot)" : selectedSlot.booking.user_name || "Unnamed player" }}
                    </p>
                    <a
                      v-if="selectedSlot.booking.user_phone && selectedSlot.booking.user !== auth.user?.id"
                      :href="telHref(selectedSlot.booking.user_phone)"
                      class="inline-flex items-center gap-1.5 text-sm text-[#c9ff47] hover:text-[#d9ff6b] mt-1"
                    >
                      <UIcon name="i-heroicons-phone" /> {{ selectedSlot.booking.user_phone }}
                    </a>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-[#888888]">Price</span>
                    <span class="text-[#f0f0f0] font-semibold">NPR {{ selectedSlot.booking.price_at_booking }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-[#888888]">Requested</span>
                    <span class="text-[#c4c4c4]">{{ fmtWhen(selectedSlot.booking.created_at) }}</span>
                  </div>
                  <p v-if="selectedSlot.booking.note" class="text-sm text-[#c4c4c4] italic border-t border-white/[0.06] pt-3">
                    "{{ selectedSlot.booking.note }}"
                  </p>
                </div>

                <!-- Actions by status -->
                <div v-if="selectedSlot.booking.status === 'PENDING_APPROVAL'" class="space-y-2">
                  <UButton block color="primary" icon="i-heroicons-check" :loading="acting"
                    @click="act(selectedSlot.booking, 'approve', { success: 'Booking approved' })">
                    Approve booking
                  </UButton>
                  <UButton block color="red" variant="soft" icon="i-heroicons-x-mark" :disabled="acting"
                    @click="showReason = showReason === 'reject' ? null : 'reject'">
                    Reject
                  </UButton>
                  <div v-if="showReason === 'reject'" class="flex gap-2">
                    <UInput v-model="reason" placeholder="Reason (optional)" class="flex-1" size="sm" />
                    <UButton color="red" size="sm" :loading="acting"
                      @click="act(selectedSlot.booking, 'reject', { withReason: true, success: 'Booking rejected' })">
                      Confirm
                    </UButton>
                  </div>
                </div>

                <div v-else-if="selectedSlot.booking.status === 'APPROVED'" class="space-y-2">
                  <UButton block color="primary" variant="soft" icon="i-heroicons-flag" :loading="acting"
                    @click="act(selectedSlot.booking, 'complete', { success: 'Marked as completed' })">
                    Mark as completed
                  </UButton>
                  <UButton block color="red" variant="soft" icon="i-heroicons-trash" :disabled="acting"
                    @click="showReason = showReason === 'cancel' ? null : 'cancel'">
                    Cancel booking
                  </UButton>
                  <div v-if="showReason === 'cancel'" class="flex gap-2">
                    <UInput v-model="reason" placeholder="Reason (optional)" class="flex-1" size="sm" />
                    <UButton color="red" size="sm" :loading="acting"
                      @click="act(selectedSlot.booking, 'cancel', { withReason: true, success: 'Booking cancelled' })">
                      Confirm
                    </UButton>
                  </div>
                </div>
              </template>

              <!-- Free slot -->
              <template v-else-if="selectedSlot.available">
                <p class="text-sm text-[#888888]">This slot is free. Block it for a walk-in customer, a phone booking, or maintenance.</p>
                <UButton block color="primary" variant="soft" icon="i-heroicons-lock-closed" :loading="acting" @click="blockSlot(selectedSlot)">
                  Block this slot
                </UButton>
              </template>

              <p v-else class="text-sm text-[#888888]">This slot is in the past.</p>
            </div>
          </aside>
        </div>

        <!-- Pending queue across the venue -->
        <div class="mt-10">
          <div class="flex items-center gap-3 mb-4">
            <h2 class="font-display text-2xl font-bold text-[#f0f0f0]">Pending requests</h2>
            <UBadge v-if="queue.length" color="amber" variant="subtle">{{ queue.length }}</UBadge>
            <UButton class="ml-auto" color="gray" variant="soft" size="sm" icon="i-heroicons-arrow-path" :loading="pendingLoading" @click="refreshPending()">
              Refresh
            </UButton>
          </div>

          <div v-if="queue.length" class="space-y-3">
            <div v-for="b in queue" :key="b.id" class="rounded-2xl border border-white/[0.06] bg-[#141414] p-4 flex flex-wrap items-center justify-between gap-3">
              <div class="min-w-0">
                <p class="text-xs font-medium uppercase tracking-wide text-[#c9ff47]">{{ b.court_name }}</p>
                <p class="font-display font-semibold text-[#f0f0f0]">{{ fmtRange(b.start_at, b.end_at) }}</p>
                <p class="text-sm text-[#888888] mt-0.5">
                  {{ b.user_name || "Unnamed player" }}
                  <a v-if="b.user_phone" :href="telHref(b.user_phone)" class="text-[#c9ff47] hover:text-[#d9ff6b] ml-1">{{ b.user_phone }}</a>
                  · NPR {{ b.price_at_booking }}
                </p>
              </div>
              <div class="flex gap-2 shrink-0">
                <UButton color="gray" variant="soft" size="sm" icon="i-heroicons-eye" @click="jumpTo(b)">View in schedule</UButton>
                <UButton color="primary" size="sm" :loading="acting" @click="act(b, 'approve', { success: 'Booking approved' })">Approve</UButton>
              </div>
            </div>
          </div>

          <div v-else class="rounded-2xl border border-white/[0.06] bg-[#141414] text-center py-10">
            <UIcon name="i-heroicons-check-circle" class="text-2xl text-[#c9ff47]" />
            <p class="mt-2 text-[#888888]">No pending requests — you're all caught up.</p>
          </div>
        </div>
      </template>

      <template #fallback>
        <div class="space-y-3">
          <USkeleton class="h-24 rounded-2xl" />
          <USkeleton class="h-64 rounded-2xl" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>
