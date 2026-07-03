<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "Manager dashboard | Booksall" });

const api = useApi();
const img = useImages();
const toast = useToast();

const { data: venues, pending, refresh } = await useMyVenues();

// ---------- Aggregated stats (all math happens in the backend) ----------
const days = ref(30);
const statsVenue = ref(null); // null = all venues
const { data: stats, pending: statsPending } = useAsyncData(
    () => `manager-stats-${days.value}-${statsVenue.value ?? "all"}`,
    () => api("/api/manage/stats/", {
        query: { days: days.value, ...(statsVenue.value ? { futsal: statsVenue.value } : {}) },
    }),
    { server: false, lazy: true, watch: [days, statsVenue], immediate: true }
);

const RANGES = [
    { label: "7 days", value: 7 },
    { label: "30 days", value: 30 },
    { label: "90 days", value: 90 },
];

// Daily chart: bookings as bars, revenue as line.
const dailyChart = computed(() => (stats.value?.daily || []).map((d) => {
    const dt = new Date(d.date + "T00:00:00");
    const label = dt.toLocaleDateString([], { day: "numeric", month: "short" });
    return {
        label,
        value: d.bookings,
        line: d.revenue,
        title: `${label} — ${d.bookings} booking${d.bookings === 1 ? "" : "s"}, NPR ${d.revenue.toLocaleString()}`,
    };
}));

// Peak hours: only show a sensible window (05:00–23:00) — nobody plays at 3 AM.
const peakChart = computed(() => (stats.value?.peak_hours || [])
    .filter((h) => h.hour >= 5)
    .map((h) => {
        const label = h.hour === 12 ? "12p" : h.hour < 12 ? `${h.hour}a` : `${h.hour - 12}p`;
        return { label, value: h.bookings, title: `${String(h.hour).padStart(2, "0")}:00 — ${h.bookings} booking${h.bookings === 1 ? "" : "s"}` };
    }));
const peakHour = computed(() => {
    const rows = stats.value?.peak_hours || [];
    if (!rows.some((r) => r.bookings > 0)) return null;
    const top = rows.reduce((a, b) => (b.bookings > a.bookings ? b : a));
    return `${String(top.hour).padStart(2, "0")}:00`;
});

// Status breakdown (stacked bar).
const STATUS_META = [
    { key: "APPROVED", label: "Approved", cls: "bg-emerald-400" },
    { key: "COMPLETED", label: "Completed", cls: "bg-[#4aa3ff]" },
    { key: "PENDING_APPROVAL", label: "Pending", cls: "bg-amber-400" },
    { key: "CANCELLED", label: "Cancelled", cls: "bg-[#666]" },
    { key: "REJECTED", label: "Rejected", cls: "bg-red-400" },
    { key: "EXPIRED", label: "Expired", cls: "bg-[#444]" },
];
const statusRows = computed(() => {
    const src = stats.value?.by_status || {};
    const total = Object.values(src).reduce((s, n) => s + n, 0);
    return STATUS_META
        .map((m) => ({ ...m, n: src[m.key] || 0, pct: total ? ((src[m.key] || 0) / total) * 100 : 0 }))
        .filter((r) => r.n > 0);
});

// Top courts (progress list).
const topCourts = computed(() => {
    const rows = stats.value?.by_court || [];
    const max = Math.max(1, ...rows.map((r) => r.bookings));
    return rows.map((r) => ({ ...r, pct: (r.bookings / max) * 100 }));
});

const cancelRate = computed(() => {
    const p = stats.value?.period;
    if (!p?.bookings) return 0;
    return Math.round((p.cancelled / p.bookings) * 100);
});

// ---------- Upcoming bookings (small list, unchanged behaviour) ----------
const { data: bookingData, pending: bPending } = await useAsyncData(
    "manager-bookings",
    () => api("/api/bookings/", { query: { page_size: 20, ordering: "start_at", start_at__gte: new Date().toISOString() } }),
    { server: false, lazy: true }
);
const managedIds = computed(() => new Set((venues.value || []).map((v) => v.id)));
const upcomingList = computed(() =>
    (bookingData.value?.results || [])
        .filter((b) => managedIds.value.has(b.futsal) && !["CANCELLED", "REJECTED"].includes(b.status))
        .slice(0, 6)
);

// ---------- Create venue ----------
const modalOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({ name: "", city: "", address: "", description: "" });
async function createVenue() {
    saving.value = true;
    error.value = "";
    try {
        await api("/api/futsals/", { method: "POST", body: { ...form } });
        toast.add({ title: "Venue created", description: "It's pending review before going public.", color: "green" });
        modalOpen.value = false;
        Object.assign(form, { name: "", city: "", address: "", description: "" });
        await refresh();
    } catch (e) {
        error.value = apiErrorMessage(e, "Could not create venue.");
    } finally {
        saving.value = false;
    }
}

function cover(v) {
    const imgs = v.images || [];
    return (imgs.find((i) => i.is_primary) || imgs[0])?.image || img.venueFallback(v.id, 400, 240);
}
const statusColor = { ACTIVE: "green", PENDING: "amber", INACTIVE: "gray" };
const fmt = (iso) => new Date(iso).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const BSTATUS = {
    PENDING_APPROVAL: "text-[#f5c842]", APPROVED: "text-[#22c55e]",
    COMPLETED: "text-[#4aa3ff]", REJECTED: "text-red-400", CANCELLED: "text-[#888]", EXPIRED: "text-[#888]",
};
</script>

<template>
  <div>
    <div class="flex items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="font-display text-3xl md:text-4xl font-black uppercase tracking-tight text-[#f0f0f0]">Manager dashboard</h1>
        <p class="text-[#888888] mt-1">Your venues, bookings, and revenue at a glance.</p>
      </div>
      <button class="inline-flex items-center gap-1.5 rounded-full bg-[#c9ff47] px-5 py-2.5 text-sm font-bold text-black hover:bg-[#d9ff6b] transition-colors shrink-0" @click="modalOpen = true">
        <UIcon name="i-heroicons-plus" /> Add venue
      </button>
    </div>

    <ClientOnly>
      <!-- Filters: venue + range -->
      <div class="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div v-if="(venues?.length ?? 0) > 1" class="flex flex-wrap gap-2">
          <button
            type="button"
            class="px-3 py-1 rounded-full text-xs font-semibold transition-colors"
            :class="!statsVenue ? 'bg-[#c9ff47] text-black' : 'bg-[#1a1a1a] border border-white/[0.08] text-[#bdbdbd] hover:border-white/25'"
            @click="statsVenue = null"
          >
            All venues
          </button>
          <button
            v-for="v in venues" :key="v.id" type="button"
            class="px-3 py-1 rounded-full text-xs font-semibold transition-colors"
            :class="statsVenue === v.id ? 'bg-[#c9ff47] text-black' : 'bg-[#1a1a1a] border border-white/[0.08] text-[#bdbdbd] hover:border-white/25'"
            @click="statsVenue = v.id"
          >
            {{ v.name }}
          </button>
        </div>
        <div class="flex gap-1 rounded-xl bg-[#141414] border border-white/[0.08] p-1 ml-auto">
          <button
            v-for="r in RANGES" :key="r.value" type="button"
            class="px-3 py-1 rounded-lg text-xs font-semibold transition-colors"
            :class="days === r.value ? 'bg-[#c9ff47] text-black' : 'text-[#8f8f8f] hover:text-white'"
            @click="days = r.value"
          >
            {{ r.label }}
          </button>
        </div>
      </div>

      <!-- Stat cards -->
      <div v-if="statsPending && !stats" class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <USkeleton v-for="i in 4" :key="i" class="h-24 rounded-2xl" />
      </div>
      <div v-else class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <NuxtLink to="/manage/bookings" class="rounded-2xl border p-4 transition-colors"
          :class="stats?.totals?.pending ? 'border-[#f5c842]/40 bg-[#f5c842]/[0.06] hover:border-[#f5c842]' : 'border-white/[0.08] bg-[#141414] hover:border-white/20'">
          <p class="text-xs uppercase tracking-wide text-[#888]">Pending approvals</p>
          <p class="font-display text-3xl font-black mt-1" :class="stats?.totals?.pending ? 'text-[#f5c842]' : 'text-white'">{{ stats?.totals?.pending ?? 0 }}</p>
        </NuxtLink>
        <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-4">
          <p class="text-xs uppercase tracking-wide text-[#888]">Upcoming</p>
          <p class="font-display text-3xl font-black text-white mt-1">{{ stats?.totals?.upcoming ?? 0 }}</p>
        </div>
        <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-4">
          <p class="text-xs uppercase tracking-wide text-[#888]">Weekly avg bookings</p>
          <p class="font-display text-3xl font-black text-white mt-1">{{ stats?.period?.weekly_avg_bookings ?? 0 }}</p>
          <p class="text-[11px] text-[#666] mt-0.5">{{ stats?.period?.daily_avg_bookings ?? 0 }}/day over {{ stats?.days ?? days }} days</p>
        </div>
        <div class="rounded-2xl border border-[#c9ff47]/25 bg-[#c9ff47]/[0.05] p-4">
          <p class="text-xs uppercase tracking-wide text-[#888]">Revenue ({{ stats?.days ?? days }}d)</p>
          <p class="font-display text-2xl font-black text-[#c9ff47] mt-1">NPR {{ (stats?.period?.revenue ?? 0).toLocaleString() }}</p>
          <p class="text-[11px] text-[#666] mt-0.5">All-time: NPR {{ (stats?.totals?.revenue_confirmed ?? 0).toLocaleString() }}</p>
        </div>
      </div>

      <!-- Charts row: daily bookings + revenue -->
      <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-5 mb-6">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h2 class="font-display text-lg font-bold text-white">Daily bookings & revenue</h2>
          <p class="text-xs text-[#888888]">
            {{ stats?.period?.bookings ?? 0 }} bookings · {{ cancelRate }}% cancelled/rejected
          </p>
        </div>
        <USkeleton v-if="statsPending && !stats" class="h-40 rounded-xl" />
        <StatChart v-else :data="dailyChart" :height="170" bar-label="Bookings" line-label="Revenue (NPR)" />
      </div>

      <div class="grid lg:grid-cols-2 gap-6 mb-6">
        <!-- Peak hours -->
        <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-5">
          <div class="flex items-center justify-between gap-2 mb-3">
            <h2 class="font-display text-lg font-bold text-white">Popular kickoff times</h2>
            <span v-if="peakHour" class="text-xs font-semibold text-[#c9ff47]">Peak: {{ peakHour }}</span>
          </div>
          <USkeleton v-if="statsPending && !stats" class="h-32 rounded-xl" />
          <StatChart v-else :data="peakChart" :height="140" :max-ticks="10" />
        </div>

        <!-- Status breakdown -->
        <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-5">
          <h2 class="font-display text-lg font-bold text-white mb-4">Booking outcomes ({{ stats?.days ?? days }}d)</h2>
          <template v-if="statusRows.length">
            <div class="flex h-3 rounded-full overflow-hidden bg-[#0f0f0f]">
              <div v-for="r in statusRows" :key="r.key" :class="r.cls" :style="{ width: r.pct + '%' }" :title="`${r.label}: ${r.n}`" />
            </div>
            <div class="mt-4 grid grid-cols-2 gap-x-4 gap-y-2">
              <div v-for="r in statusRows" :key="r.key" class="flex items-center justify-between text-sm">
                <span class="inline-flex items-center gap-2 text-[#8f8f8f]">
                  <span class="w-2.5 h-2.5 rounded-full" :class="r.cls" /> {{ r.label }}
                </span>
                <span class="font-semibold text-[#f0f0f0]">{{ r.n }}</span>
              </div>
            </div>
          </template>
          <p v-else class="text-sm text-[#888888] py-6 text-center">No bookings in this period yet.</p>
        </div>
      </div>

      <div class="grid lg:grid-cols-5 gap-6">
        <!-- Top courts + venues -->
        <div class="lg:col-span-3 space-y-6">
          <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-5">
            <h2 class="font-display text-lg font-bold text-white mb-4">Busiest courts ({{ stats?.days ?? days }}d)</h2>
            <div v-if="topCourts.length" class="space-y-3">
              <div v-for="c in topCourts" :key="c.court">
                <div class="flex items-center justify-between text-sm mb-1">
                  <p class="text-[#f0f0f0] font-medium truncate">
                    {{ c.name }} <span class="text-[#666] font-normal">· {{ c.futsal_name }}</span>
                  </p>
                  <p class="text-[#8f8f8f] shrink-0 ml-3">{{ c.bookings }} · NPR {{ c.revenue.toLocaleString() }}</p>
                </div>
                <div class="h-2 rounded-full bg-[#0f0f0f] overflow-hidden">
                  <div class="h-full rounded-full bg-[#c9ff47]/80" :style="{ width: c.pct + '%' }" />
                </div>
              </div>
            </div>
            <p v-else class="text-sm text-[#888888] py-4 text-center">No court activity in this period.</p>
          </div>

          <div>
            <h2 class="font-display text-lg font-bold text-white mb-3">Your venues</h2>
            <div v-if="pending" class="grid gap-3 sm:grid-cols-2">
              <USkeleton v-for="i in 2" :key="i" class="h-32 rounded-2xl" />
            </div>
            <div v-else-if="venues?.length" class="grid gap-3 sm:grid-cols-2">
              <NuxtLink v-for="v in venues" :key="v.id" :to="`/manage/${v.slug}`"
                class="group block overflow-hidden rounded-2xl border border-white/[0.08] bg-[#141414] hover:-translate-y-0.5 hover:border-[#c9ff47]/40 transition-all">
                <div class="flex">
                  <img :src="cover(v)" :alt="v.name" class="w-24 object-cover shrink-0" loading="lazy" />
                  <div class="flex-1 p-3.5 min-w-0">
                    <div class="flex items-start justify-between gap-2">
                      <h3 class="font-semibold text-[#f0f0f0] truncate group-hover:text-[#c9ff47] transition-colors">{{ v.name }}</h3>
                      <UBadge :color="statusColor[v.status] || 'gray'" variant="subtle" size="xs">{{ v.status }}</UBadge>
                    </div>
                    <p class="text-sm text-[#888888] mt-1">{{ v.city || "—" }} · {{ v.courts?.length || 0 }} courts</p>
                  </div>
                </div>
              </NuxtLink>
            </div>
            <div v-else class="rounded-2xl border border-white/[0.08] bg-[#141414] text-center py-12">
              <UIcon name="i-heroicons-building-storefront" class="text-4xl text-[#444]" />
              <p class="mt-3 text-[#888888]">No venues yet.</p>
              <button class="mt-3 text-sm font-semibold text-[#c9ff47] hover:underline" @click="modalOpen = true">Add your first venue</button>
            </div>
          </div>
        </div>

        <!-- Upcoming bookings -->
        <div class="lg:col-span-2">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-display text-lg font-bold text-white">Upcoming bookings</h2>
            <NuxtLink to="/manage/bookings" class="text-xs font-semibold text-[#c9ff47] hover:underline">Manage bookings →</NuxtLink>
          </div>
          <div v-if="bPending" class="space-y-2"><USkeleton v-for="i in 4" :key="i" class="h-14 rounded-xl" /></div>
          <div v-else-if="upcomingList.length" class="space-y-2">
            <div v-for="b in upcomingList" :key="b.id" class="rounded-xl border border-white/[0.08] bg-[#141414] p-3">
              <div class="flex items-center justify-between gap-2">
                <p class="text-sm font-medium text-[#f0f0f0] truncate">{{ b.futsal_name }} · {{ b.court_name }}</p>
                <span class="text-xs font-semibold shrink-0" :class="BSTATUS[b.status]">{{ b.status.replace("_", " ") }}</span>
              </div>
              <p class="text-xs text-[#888888] mt-0.5">{{ fmt(b.start_at) }} · NPR {{ Number(b.price_at_booking).toLocaleString() }}</p>
            </div>
          </div>
          <div v-else class="rounded-2xl border border-white/[0.08] bg-[#141414] text-center py-10 text-sm text-[#888]">
            No upcoming bookings.
          </div>
        </div>
      </div>

      <template #fallback>
        <div class="space-y-4">
          <USkeleton class="h-24 rounded-2xl" />
          <USkeleton class="h-48 rounded-2xl" />
        </div>
      </template>
    </ClientOnly>

    <!-- Create venue modal -->
    <UModal v-model="modalOpen">
      <UCard>
        <template #header><h3 class="font-display font-bold text-white">Add a venue</h3></template>
        <div class="space-y-4">
          <UAlert v-if="error" color="red" variant="soft" :title="error" />
          <UFormGroup label="Name" required><UInput v-model="form.name" placeholder="Prime Futsal" /></UFormGroup>
          <div class="grid sm:grid-cols-2 gap-4">
            <UFormGroup label="City"><UInput v-model="form.city" placeholder="Kathmandu" /></UFormGroup>
            <UFormGroup label="Address"><UInput v-model="form.address" placeholder="Street, area" /></UFormGroup>
          </div>
          <UFormGroup label="Description"><UTextarea v-model="form.description" :rows="3" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="modalOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="saving" @click="createVenue">Create venue</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>
