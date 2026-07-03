<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "My Bookings | Booksall" });
const api = useApi();
const auth = useAuthStore();
const img = useImages();
const toast = useToast();
const { data, pending, refresh } = await useAsyncData("my-bookings", () => api("/api/bookings/", { query: { ordering: "-start_at" } }), { server: false });
const ACTIVE = ["PENDING_APPROVAL", "APPROVED"];
const now = () => new Date();
const all = computed(() => data.value?.results || []);
const isUpcoming = (b) => new Date(b.start_at) >= now() && !["CANCELLED", "REJECTED", "EXPIRED"].includes(b.status);
const stats = computed(() => ({
    upcoming: all.value.filter(isUpcoming).length,
    pending: all.value.filter((b) => b.status === "PENDING_APPROVAL").length,
    completed: all.value.filter((b) => b.status === "COMPLETED").length,
}));
const tab = ref("upcoming");
const tabs = [
    { key: "upcoming", label: "Upcoming" },
    { key: "past", label: "Past" },
    { key: "all", label: "All" },
];
const filtered = computed(() => {
    if (tab.value === "all")
        return all.value;
    if (tab.value === "upcoming")
        return all.value.filter(isUpcoming);
    return all.value.filter((b) => !isUpcoming(b));
});
const cancelling = ref(null);
function fmtDate(iso) {
    return new Date(iso).toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}
function fmtTime(iso) {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
async function cancel(b) {
    cancelling.value = b.id;
    try {
        await api(`/api/bookings/${b.id}/cancel/`, { method: "POST", body: {} });
        toast.add({ title: "Booking cancelled", color: "green" });
        await refresh();
    }
    catch (e) {
        toast.add({ title: "Could not cancel", description: apiErrorMessage(e), color: "red" });
    }
    finally {
        cancelling.value = null;
    }
}
</script>

<template>
  <div>
    <!-- Greeting -->
    <div class="mb-8">
      <ClientOnly>
        <p class="text-[#c9ff47] font-medium">Welcome back{{ auth.user?.full_name ? ", " + auth.user.full_name.split(" ")[0] : "" }} 👋</p>
        <template #fallback><p class="text-[#c9ff47] font-medium">Welcome back 👋</p></template>
      </ClientOnly>
      <h1 class="font-display text-3xl font-bold text-[#f0f0f0] mt-1">Your bookings</h1>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-3 gap-3 sm:gap-4 mb-8">
      <div class="rounded-2xl bg-[#141414] border border-white/[0.06] p-4 sm:p-5">
        <p class="text-sm text-[#888888]">Upcoming</p>
        <p class="font-display text-3xl font-bold text-[#c9ff47] mt-1">{{ stats.upcoming }}</p>
      </div>
      <div class="rounded-2xl bg-[#141414] border border-white/[0.06] p-4 sm:p-5">
        <p class="text-sm text-[#888888]">Awaiting approval</p>
        <p class="font-display text-3xl font-bold text-amber-500 mt-1">{{ stats.pending }}</p>
      </div>
      <div class="rounded-2xl bg-[#141414] border border-white/[0.06] p-4 sm:p-5">
        <p class="text-sm text-[#888888]">Played</p>
        <p class="font-display text-3xl font-bold text-[#f0f0f0] mt-1">{{ stats.completed }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 p-1 bg-[#1a1a1a] rounded-xl w-fit mb-6">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
        :class="tab === t.key ? 'bg-[#141414] text-[#f0f0f0] shadow-sm' : 'text-[#888888] hover:text-[#c4c4c4]'"
        @click="tab = t.key"
      >
        {{ t.label }}
      </button>
    </div>

    <div v-if="pending" class="space-y-3">
      <USkeleton v-for="i in 3" :key="i" class="h-28 rounded-2xl" />
    </div>

    <div v-else-if="filtered.length" class="space-y-4">
      <div
        v-for="b in filtered"
        :key="b.id"
        class="flex gap-4 rounded-2xl bg-[#141414] border border-white/[0.06] overflow-hidden hover:shadow-md transition-shadow"
      >
        <img :src="img.venueFallback(b.futsal, 240, 240)" :alt="b.futsal_name"
          class="w-24 sm:w-32 object-cover shrink-0" loading="lazy" />
        <div class="flex-1 min-w-0 py-4 pr-4 flex items-center justify-between gap-3">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="font-display font-semibold text-[#f0f0f0] truncate">{{ b.futsal_name }}</h3>
              <BookingStatusBadge :status="b.status" />
            </div>
            <p class="text-sm text-[#888888] mt-1">{{ b.court_name }}</p>
            <div class="flex items-center gap-3 mt-2 text-sm">
              <span class="inline-flex items-center gap-1 text-[#c4c4c4]">
                <UIcon name="i-heroicons-calendar" class="text-[#c9ff47]" /> {{ fmtDate(b.start_at) }}
              </span>
              <span class="inline-flex items-center gap-1 text-[#c4c4c4]">
                <UIcon name="i-heroicons-clock" class="text-[#c9ff47]" /> {{ fmtTime(b.start_at) }}
              </span>
              <span class="font-medium text-[#f0f0f0]">NPR {{ b.price_at_booking }}</span>
            </div>
          </div>
          <UButton
            v-if="ACTIVE.includes(b.status) && isUpcoming(b)"
            color="red" variant="soft" size="sm"
            :loading="cancelling === b.id"
            @click="cancel(b)"
          >
            Cancel
          </UButton>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="rounded-3xl bg-[#141414] border border-white/[0.06] overflow-hidden grid sm:grid-cols-2">
      <div class="p-8 sm:p-10 flex flex-col justify-center">
        <h3 class="font-display text-xl font-bold text-[#f0f0f0]">
          {{ tab === "upcoming" ? "No upcoming games" : "Nothing here yet" }}
        </h3>
        <p class="text-[#888888] mt-2">Find a pitch, lock a slot, and it'll show up right here.</p>
        <div>
          <UButton to="/futsals" color="primary" class="mt-5">Find a futsal</UButton>
        </div>
      </div>
      <img :src="img.action(1, 600, 400)" alt="Futsal" class="hidden sm:block object-cover w-full h-full" loading="lazy" />
    </div>
  </div>
</template>
