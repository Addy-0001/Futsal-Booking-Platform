<script setup>
const api = useApi();
const img = useImages();
const route = useRoute();
const config = useRuntimeConfig();
const toast = useToast();
const slug = route.params.slug;
const { data: venue, error } = await useAsyncData(`futsal-${slug}`, () => api(`/api/futsals/${slug}/`));
if (error.value || !venue.value) {
    throw createError({ statusCode: 404, statusMessage: "Futsal not found", fatal: true });
}
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const surfaceLabel = {
    ARTIFICIAL: "Artificial turf",
    NATURAL: "Natural grass",
    INDOOR: "Indoor",
};
const surfaceIcon = {
    ARTIFICIAL: "i-heroicons-squares-2x2",
    NATURAL: "i-heroicons-sun",
    INDOOR: "i-heroicons-home-modern",
};

// --- Gallery (click a thumbnail to feature it) ---
const gallery = computed(() => {
    const imgs = venue.value?.images || [];
    if (imgs.length) return imgs.map((p) => ({ id: p.id, src: p.image, alt: p.caption || venue.value.name }));
    return [{ id: "fallback", src: img.venueFallback(venue.value.id, 1400, 800), alt: venue.value.name }];
});
const featured = ref(0);

// --- Quick facts ---
const fromPrice = computed(() => {
    const prices = (venue.value?.courts || []).map((c) => Number(c.default_price)).filter((n) => n > 0);
    return prices.length ? Math.min(...prices) : null;
});
const courtCount = computed(() => venue.value?.courts?.length ?? 0);
const surfaces = computed(() => [...new Set((venue.value?.courts || []).map((c) => surfaceLabel[c.surface_type]).filter(Boolean))]);
const todayHours = computed(() => {
    const weekday = (new Date().getDay() + 6) % 7; // JS Sun=0 → our Mon=0
    const spans = (venue.value?.courts || [])
        .flatMap((c) => c.operating_hours || [])
        .filter((h) => h.weekday === weekday);
    if (!spans.length) return null;
    const open = spans.map((h) => h.open_time.slice(0, 5)).sort()[0];
    const close = spans.map((h) => h.close_time.slice(0, 5)).sort().at(-1);
    return `${open} – ${close}`;
});
const mapsUrl = computed(() => venue.value?.latitude && venue.value?.longitude
    ? `https://www.google.com/maps?q=${venue.value.latitude},${venue.value.longitude}`
    : null);

// Per-court hours toggle
const openHours = ref(new Set());
function toggleHours(id) {
    const s = new Set(openHours.value);
    s.has(id) ? s.delete(id) : s.add(id);
    openHours.value = s;
}

async function shareVenue() {
    const url = canonical.value;
    if (import.meta.client && navigator.share) {
        try { await navigator.share({ title: venue.value.name, url }); return; } catch { /* cancelled */ }
    }
    if (import.meta.client) {
        await navigator.clipboard.writeText(url);
        toast.add({ title: "Link copied to clipboard", icon: "i-heroicons-link" });
    }
}

function scrollToBooking() {
    if (import.meta.client) document.getElementById("book")?.scrollIntoView({ behavior: "smooth" });
}

const canonical = computed(() => `${config.public.siteUrl}/futsals/${slug}`);
// SEO meta
useSeoMeta({
    title: () => `${venue.value?.name}${venue.value?.city ? " — " + venue.value.city : ""} | Booksall`,
    description: () => venue.value?.description ||
        `Book ${venue.value?.name}${venue.value?.city ? " in " + venue.value.city : ""} on Booksall — live availability and transparent pricing.`,
    ogTitle: () => venue.value?.name,
    ogType: "website",
});
useHead({
    link: [{ rel: "canonical", href: canonical }],
    script: [
        {
            type: "application/ld+json",
            innerHTML: computed(() => JSON.stringify({
                "@context": "https://schema.org",
                "@type": "SportsActivityLocation",
                name: venue.value?.name,
                description: venue.value?.description || undefined,
                address: venue.value?.address
                    ? {
                        "@type": "PostalAddress",
                        streetAddress: venue.value.address,
                        addressLocality: venue.value?.city || undefined,
                        addressCountry: "NP",
                    }
                    : undefined,
                geo: venue.value?.latitude && venue.value?.longitude
                    ? {
                        "@type": "GeoCoordinates",
                        latitude: venue.value.latitude,
                        longitude: venue.value.longitude,
                    }
                    : undefined,
                url: canonical.value,
            })),
        },
    ],
});
</script>

<template>
  <UContainer v-if="venue" class="py-8 md:py-10">
    <!-- Breadcrumb -->
    <nav class="text-sm text-[#888888] mb-5 flex items-center gap-1">
      <NuxtLink to="/futsals" class="hover:text-[#c9ff47] transition-colors">Futsals</NuxtLink>
      <UIcon name="i-heroicons-chevron-right" class="text-xs" />
      <span class="text-[#c4c4c4]">{{ venue.name }}</span>
    </nav>

    <!-- Gallery -->
    <section class="mb-8">
      <div class="grid gap-3" :class="gallery.length > 1 ? 'lg:grid-cols-[minmax(0,3fr)_minmax(0,1fr)]' : ''">
        <div class="relative overflow-hidden rounded-3xl">
          <Transition name="fade" mode="out-in">
            <img
              :key="gallery[featured].id"
              :src="gallery[featured].src"
              :alt="gallery[featured].alt"
              class="w-full h-72 md:h-[26rem] object-cover"
              loading="eager"
            />
          </Transition>
          <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent p-5 md:p-7">
            <div class="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 class="font-display text-3xl md:text-5xl font-black uppercase tracking-tight text-white">{{ venue.name }}</h1>
                <p v-if="venue.city || venue.address" class="text-white/80 mt-1 text-sm md:text-base">
                  <UIcon name="i-heroicons-map-pin" class="align-text-bottom text-[#c9ff47]" />
                  {{ [venue.address, venue.city].filter(Boolean).join(", ") }}
                </p>
              </div>
              <div class="flex gap-2">
                <UButton color="primary" size="lg" icon="i-heroicons-calendar-days" @click="scrollToBooking">Book a slot</UButton>
                <UButton color="gray" variant="solid" size="lg" icon="i-heroicons-share" aria-label="Share" @click="shareVenue" />
              </div>
            </div>
          </div>
        </div>

        <!-- Thumbnails -->
        <div v-if="gallery.length > 1" class="flex lg:flex-col gap-3 overflow-x-auto lg:overflow-y-auto lg:max-h-[26rem]">
          <button
            v-for="(g, i) in gallery" :key="g.id"
            type="button"
            class="relative shrink-0 rounded-2xl overflow-hidden transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60"
            :class="featured === i ? 'ring-2 ring-[#c9ff47]' : 'opacity-70 hover:opacity-100'"
            @click="featured = i"
          >
            <img :src="g.src" :alt="g.alt" class="h-20 w-32 lg:w-full lg:h-24 object-cover" loading="lazy" />
          </button>
        </div>
      </div>
    </section>

    <div class="grid lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] gap-8 items-start">
      <!-- Main column -->
      <div class="min-w-0">
        <section v-if="venue.description" class="mb-10">
          <h2 class="font-display text-2xl font-black uppercase tracking-tight text-[#f0f0f0] mb-3">About this venue</h2>
          <p class="text-[#c4c4c4] leading-relaxed">{{ venue.description }}</p>
        </section>

        <section v-if="venue.courts?.length" id="book" class="mb-12 scroll-mt-24">
          <ClientOnly>
            <CourtBooking :venue="venue" />
            <template #fallback>
              <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-6"><USkeleton class="h-40" /></div>
            </template>
          </ClientOnly>
        </section>

        <section>
          <h2 class="font-display text-2xl font-black uppercase tracking-tight text-[#f0f0f0] mb-4">Courts</h2>
          <div class="grid gap-4 md:grid-cols-2">
            <div
              v-for="court in venue.courts" :key="court.id"
              class="rounded-2xl border border-white/[0.08] bg-[#141414] p-5 hover:border-[#c9ff47]/30 transition-colors"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="flex items-center gap-3 min-w-0">
                  <div class="shrink-0 w-10 h-10 rounded-xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47]">
                    <UIcon :name="surfaceIcon[court.surface_type] || 'i-heroicons-squares-2x2'" class="text-xl" />
                  </div>
                  <div class="min-w-0">
                    <h3 class="font-semibold text-[#f0f0f0] truncate">{{ court.name }}</h3>
                    <p class="text-sm text-[#888888]">{{ surfaceLabel[court.surface_type] }}</p>
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-xs text-[#6b6b6b]">from</p>
                  <p class="font-display font-bold text-[#c9ff47]">NPR {{ court.default_price }}</p>
                </div>
              </div>

              <div v-if="court.images?.length" class="mt-4 flex gap-2 overflow-x-auto">
                <img
                  v-for="ci in court.images"
                  :key="ci.id"
                  :src="ci.image"
                  :alt="ci.caption || court.name"
                  class="h-20 w-28 object-cover rounded-lg flex-shrink-0"
                  loading="lazy"
                />
              </div>

              <div v-if="court.operating_hours?.length" class="mt-4 border-t border-white/[0.06] pt-3">
                <button
                  type="button"
                  class="flex w-full items-center justify-between text-xs font-medium text-[#8f8f8f] uppercase tracking-wide hover:text-[#c9ff47] transition-colors"
                  @click="toggleHours(court.id)"
                >
                  Open hours
                  <UIcon name="i-heroicons-chevron-down" class="text-sm transition-transform" :class="openHours.has(court.id) ? 'rotate-180' : ''" />
                </button>
                <div
                  class="grid transition-[grid-template-rows] duration-300 ease-out"
                  :class="openHours.has(court.id) ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
                >
                  <ul class="overflow-hidden text-sm text-[#8f8f8f]">
                    <li v-for="h in court.operating_hours" :key="h.id" class="flex justify-between pt-1.5 first:pt-3">
                      <span>{{ WEEKDAYS[h.weekday] }}</span>
                      <span class="text-[#c4c4c4]">{{ h.open_time.slice(0, 5) }}–{{ h.close_time.slice(0, 5) }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <p v-if="!venue.courts?.length" class="text-[#888888]">No courts listed yet.</p>
        </section>
      </div>

      <!-- Sidebar: quick facts -->
      <aside class="lg:sticky lg:top-24 space-y-4">
        <div class="rounded-3xl border border-white/[0.08] bg-[#141414] p-6">
          <p class="font-display font-semibold text-[#f0f0f0] mb-4">At a glance</p>
          <dl class="space-y-4 text-sm">
            <div class="flex items-center gap-3">
              <UIcon name="i-heroicons-trophy" class="text-[#c9ff47] text-lg shrink-0" />
              <div class="flex-1 flex justify-between gap-2">
                <dt class="text-[#888888]">Courts</dt>
                <dd class="text-[#f0f0f0] font-semibold">{{ courtCount }}</dd>
              </div>
            </div>
            <div v-if="fromPrice" class="flex items-center gap-3">
              <UIcon name="i-heroicons-banknotes" class="text-[#c9ff47] text-lg shrink-0" />
              <div class="flex-1 flex justify-between gap-2">
                <dt class="text-[#888888]">Price from</dt>
                <dd class="text-[#f0f0f0] font-semibold">NPR {{ fromPrice }}/hr</dd>
              </div>
            </div>
            <div v-if="surfaces.length" class="flex items-center gap-3">
              <UIcon name="i-heroicons-squares-2x2" class="text-[#c9ff47] text-lg shrink-0" />
              <div class="flex-1 flex justify-between gap-2">
                <dt class="text-[#888888]">Surface</dt>
                <dd class="text-[#f0f0f0] font-semibold text-right">{{ surfaces.join(", ") }}</dd>
              </div>
            </div>
            <div v-if="todayHours" class="flex items-center gap-3">
              <UIcon name="i-heroicons-clock" class="text-[#c9ff47] text-lg shrink-0" />
              <div class="flex-1 flex justify-between gap-2">
                <dt class="text-[#888888]">Open today</dt>
                <dd class="text-[#f0f0f0] font-semibold">{{ todayHours }}</dd>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <UIcon name="i-heroicons-credit-card" class="text-[#c9ff47] text-lg shrink-0" />
              <div class="flex-1 flex justify-between gap-2">
                <dt class="text-[#888888]">Payment</dt>
                <dd class="text-[#f0f0f0] font-semibold">At the venue</dd>
              </div>
            </div>
          </dl>
          <UButton block color="primary" size="lg" class="mt-6" icon="i-heroicons-calendar-days" @click="scrollToBooking">
            Check availability
          </UButton>
        </div>

        <a
          v-if="mapsUrl"
          :href="mapsUrl"
          target="_blank"
          rel="noopener"
          class="group flex items-center justify-between rounded-3xl border border-white/[0.08] bg-[#141414] p-5 hover:border-[#c9ff47]/40 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47]">
              <UIcon name="i-heroicons-map" class="text-xl" />
            </div>
            <div>
              <p class="font-semibold text-[#f0f0f0] text-sm">Get directions</p>
              <p class="text-xs text-[#888888]">Open in Google Maps</p>
            </div>
          </div>
          <UIcon name="i-heroicons-arrow-top-right-on-square" class="text-[#888888] group-hover:text-[#c9ff47] transition-colors" />
        </a>
      </aside>
    </div>
  </UContainer>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
