<script setup>
const props = defineProps(["venue"]);

const img = useImages();
const courtCount = computed(() => props.venue.courts?.length ?? 0);
const cover = computed(() => {
  const imgs = props.venue.images || [];
  return (imgs.find((i) => i.is_primary) || imgs[0])?.image || img.venueFallback(props.venue.id, 800, 500);
});
const fromPrice = computed(() => {
  const prices = (props.venue.courts || [])
    .map((c) => Number(c.default_price))
    .filter((n) => n > 0);
  return prices.length ? Math.min(...prices) : null;
});
</script>

<template>
  <NuxtLink
    :to="`/futsals/${venue.slug}`"
    class="group block text-left bg-[#141414] border border-white/[0.08] rounded-2xl overflow-hidden hover:border-[#c9ff47]/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60"
  >
    <div class="relative h-48 bg-[#1a1a1a] overflow-hidden">
      <img
        :src="cover"
        :alt="venue.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        loading="lazy"
      />
      <span class="absolute top-3 left-3 inline-flex items-center gap-1 rounded-full bg-black/60 backdrop-blur-sm px-2.5 py-1 text-xs font-bold text-white">
        <UIcon name="i-heroicons-trophy" class="text-[#c9ff47]" />
        {{ courtCount }} {{ courtCount === 1 ? "court" : "courts" }}
      </span>
      <div v-if="fromPrice" class="absolute bottom-3 right-3 bg-black/70 backdrop-blur-sm text-white text-xs font-bold px-2.5 py-1 rounded-lg">
        from NPR {{ fromPrice }}/hr
      </div>
    </div>

    <div class="p-4">
      <div class="flex items-start justify-between mb-1 gap-2">
        <h3 class="font-bold text-base leading-tight text-white truncate">{{ venue.name }}</h3>
        <span class="inline-flex items-center gap-1 shrink-0 text-[#c9ff47]">
          <UIcon name="i-heroicons-star-solid" class="text-xs" />
          <span class="text-sm font-semibold text-white">4.8</span>
        </span>
      </div>
      <div v-if="venue.city" class="flex items-center gap-1 text-[#888888] text-xs mb-3">
        <UIcon name="i-heroicons-map-pin" />
        <span>{{ venue.city }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-xs px-2 py-0.5 rounded-md bg-[#1a1a1a] text-[#888888]">Futsal</span>
        <UIcon
          name="i-heroicons-chevron-right"
          class="text-[#888888] group-hover:text-[#c9ff47] transition-colors"
        />
      </div>
    </div>
  </NuxtLink>
</template>
