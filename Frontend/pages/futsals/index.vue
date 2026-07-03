<script setup>
const api = useApi();
const route = useRoute();
const router = useRouter();

const PAGE_SIZE = 20; // matches DRF DefaultPagination
const CITIES = ["Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara"];
const SORTS = [
    { label: "Newest first", value: "-created_at" },
    { label: "Oldest first", value: "created_at" },
    { label: "Name A–Z", value: "name" },
    { label: "Name Z–A", value: "-name" },
];

// Local search box bound to the URL ?search= so results are SSR + shareable.
const search = ref(route.query.search || "");
watch(() => route.query.search, (v) => { search.value = v || ""; });

const activeCity = computed(() => route.query.city ? String(route.query.city) : null);
const activeSort = computed(() => String(route.query.ordering || "-created_at"));
const page = computed(() => Number(route.query.page) || 1);

const query = computed(() => {
    const q = {};
    if (route.query.search) q.search = String(route.query.search);
    if (route.query.city) q.city = String(route.query.city);
    if (route.query.page) q.page = String(route.query.page);
    if (route.query.ordering) q.ordering = String(route.query.ordering);
    return q;
});

// Re-fetches on the server whenever the URL query changes (SEO-friendly).
const { data, pending } = await useAsyncData("futsals-list", () => api("/api/futsals/", { query: query.value }), { watch: [query] });

const pageCount = computed(() => Math.max(1, Math.ceil((data.value?.count ?? 0) / PAGE_SIZE)));
const hasFilters = computed(() => !!(route.query.search || route.query.city));

function patchQuery(patch) {
    router.push({ query: { ...route.query, ...patch, page: undefined } });
}
function submitSearch() {
    patchQuery({ search: search.value || undefined });
}
function setCity(city) {
    patchQuery({ city: activeCity.value === city ? undefined : city });
}
function setSort(value) {
    patchQuery({ ordering: value === "-created_at" ? undefined : value });
}
function setPage(p) {
    router.push({ query: { ...route.query, page: p > 1 ? String(p) : undefined } });
    if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
function clearFilters() {
    search.value = "";
    router.push({ query: {} });
}

const title = computed(() => route.query.city ? `Futsals in ${route.query.city} | Booksall` : "Find a futsal in Nepal | Booksall");
useSeoMeta({
    title,
    description: "Browse futsal venues across Nepal with live availability and transparent pricing. " +
        "Book your court online in seconds.",
    ogTitle: title,
});

const fade = (delay = 0) => ({
    initial: { opacity: 0, y: 20 },
    visibleOnce: { opacity: 1, y: 0, transition: { duration: 500, delay } },
});
</script>

<template>
  <div>
    <!-- Header band -->
    <section class="relative overflow-hidden bg-mesh-lime border-b border-white/[0.06]">
      <div class="absolute -top-24 right-0 w-96 h-96 rounded-full bg-[#c9ff47]/[0.07] blur-3xl" />
      <UContainer class="relative py-12 md:py-16">
        <p class="text-xs font-semibold text-[#c9ff47] tracking-widest uppercase mb-3">Venues</p>
        <h1 class="font-display text-4xl md:text-6xl font-black uppercase tracking-tight text-[#f0f0f0]">
          Find your <span class="text-[#c9ff47]">pitch</span>
        </h1>
        <p class="text-[#8f8f8f] mt-3 text-lg max-w-xl">
          {{ data?.count ?? 0 }} venue{{ (data?.count ?? 0) === 1 ? "" : "s" }} with live slots and upfront pricing.
        </p>

        <!-- Search -->
        <form class="mt-7 flex w-full max-w-xl rounded-2xl border border-white/[0.08] bg-[#141414] p-1.5 shadow-sm focus-within:ring-2 focus-within:ring-[#c9ff47]/60" @submit.prevent="submitSearch">
          <input
            v-model="search"
            type="text"
            placeholder="Search by name, city or address…"
            class="flex-1 bg-transparent px-3 text-[#e5e5e5] placeholder-[#666666] focus:outline-none"
          />
          <UButton type="submit" color="primary" size="lg" icon="i-heroicons-magnifying-glass">Search</UButton>
        </form>

        <!-- City chips -->
        <div class="mt-5 flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-full px-4 py-1.5 text-sm font-semibold transition-all"
            :class="!activeCity ? 'bg-[#c9ff47] text-black' : 'bg-[#141414] text-[#8f8f8f] border border-white/[0.08] hover:border-[#c9ff47]/40 hover:text-[#f0f0f0]'"
            @click="patchQuery({ city: undefined })"
          >
            All cities
          </button>
          <button
            v-for="c in CITIES" :key="c"
            type="button"
            class="rounded-full px-4 py-1.5 text-sm font-semibold transition-all"
            :class="activeCity === c ? 'bg-[#c9ff47] text-black' : 'bg-[#141414] text-[#8f8f8f] border border-white/[0.08] hover:border-[#c9ff47]/40 hover:text-[#f0f0f0]'"
            @click="setCity(c)"
          >
            {{ c }}
          </button>
        </div>
      </UContainer>
    </section>

    <UContainer class="py-8 md:py-10">
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
        <p class="text-sm text-[#888888]">
          <template v-if="pending">Searching…</template>
          <template v-else>
            Showing <span class="text-[#f0f0f0] font-semibold">{{ data?.results?.length ?? 0 }}</span>
            of {{ data?.count ?? 0 }}
            <template v-if="activeCity"> in <span class="text-[#c9ff47]">{{ activeCity }}</span></template>
            <template v-if="route.query.search"> for “<span class="text-[#c9ff47]">{{ route.query.search }}</span>”</template>
          </template>
        </p>
        <div class="flex items-center gap-2">
          <UButton v-if="hasFilters" color="gray" variant="ghost" size="sm" icon="i-heroicons-x-mark" @click="clearFilters">
            Clear filters
          </UButton>
          <USelectMenu
            :model-value="activeSort"
            :options="SORTS"
            value-attribute="value"
            option-attribute="label"
            size="sm"
            class="w-40"
            @update:model-value="setSort"
          />
        </div>
      </div>

      <!-- Loading skeletons shaped like cards -->
      <div v-if="pending" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 6" :key="i" class="rounded-2xl border border-white/[0.06] bg-[#141414] overflow-hidden">
          <USkeleton class="h-48 rounded-none" />
          <div class="p-4 space-y-3">
            <USkeleton class="h-4 w-2/3" />
            <USkeleton class="h-3 w-1/3" />
            <USkeleton class="h-3 w-1/2" />
          </div>
        </div>
      </div>

      <!-- Results -->
      <template v-else-if="data?.results?.length">
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="(v, i) in data.results" :key="v.id"
            v-motion :initial="fade((i % 3) * 70).initial" :visible-once="fade((i % 3) * 70).visibleOnce"
          >
            <VenueCard :venue="v" />
          </div>
        </div>

        <div v-if="pageCount > 1" class="mt-10 flex justify-center">
          <UPagination
            :model-value="page"
            :page-count="PAGE_SIZE"
            :total="data?.count ?? 0"
            @update:model-value="setPage"
          />
        </div>
      </template>

      <!-- Empty state -->
      <div v-else class="rounded-3xl border border-dashed border-white/[0.12] bg-[#141414]/60 text-center py-20 px-6">
        <div class="mx-auto w-16 h-16 rounded-2xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47] mb-5">
          <UIcon name="i-heroicons-map" class="text-3xl" />
        </div>
        <h2 class="font-display text-xl font-bold text-[#f0f0f0]">No venues found</h2>
        <p class="mt-2 text-[#888888] max-w-sm mx-auto">
          <template v-if="hasFilters">Nothing matches your filters. Try a different city or search term.</template>
          <template v-else>No venues listed yet — check back soon.</template>
        </p>
        <UButton v-if="hasFilters" color="primary" variant="soft" class="mt-6" icon="i-heroicons-arrow-uturn-left" @click="clearFilters">
          Clear all filters
        </UButton>
      </div>
    </UContainer>
  </div>
</template>
