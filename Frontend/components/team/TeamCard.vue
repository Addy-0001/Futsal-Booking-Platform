<script setup>
const props = defineProps(['team']);
const memberCount = computed(() => props.team.members?.length ?? 0);
const initials = computed(() => props.team.name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase());
</script>

<template>
  <NuxtLink
    :to="`/teams/${team.slug}`"
    class="card-lift group flex items-center gap-4 rounded-2xl border border-white/[0.08] bg-[#141414] p-4 hover:shadow-card-hover hover:border-[#c9ff47]/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60"
  >
    <div class="shrink-0">
      <img v-if="team.logo" :src="team.logo" :alt="team.name" class="w-14 h-14 rounded-2xl object-cover ring-2 ring-white/[0.08]" />
      <div v-else class="w-14 h-14 rounded-2xl grid place-items-center surface-volt text-ink-950 font-display font-extrabold text-lg shadow-volt">
        {{ initials }}
      </div>
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="font-display font-bold text-[#f0f0f0] truncate group-hover:text-[#c9ff47] transition-colors">
        {{ team.name }}
      </h3>
      <p class="mt-0.5 inline-flex items-center gap-1.5 text-sm text-[#888888]">
        <UIcon name="i-heroicons-users" class="text-[#c9ff47]" />
        {{ memberCount }} {{ memberCount === 1 ? "player" : "players" }}
      </p>
    </div>
    <UIcon name="i-heroicons-arrow-right" class="text-[#565656] group-hover:text-[#c9ff47] group-hover:translate-x-0.5 transition-all" />
  </NuxtLink>
</template>
