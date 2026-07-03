<script setup>
// The one site-wide top navbar (logo, main links, account menu). Used by
// both layouts/default.vue (marketing/public pages) and layouts/dashboard.vue
// (account/manager pages) so navigating into your dashboard never strands
// you without a way back to the rest of the site.
const links = [
  { label: "Find a Futsal", to: "/futsals" },
  { label: "Matches", to: "/matches" },
  { label: "Teams", to: "/teams" },
];
const auth = useAuthStore();
const { logout } = useAuth();
const mobileOpen = ref(false);
const menuOpen = ref(false);
const route = useRoute();
watch(() => route.fullPath, () => {
  mobileOpen.value = false;
  menuOpen.value = false;
});
const isActive = (to) => route.path === to || route.path.startsWith(to + "/");

const initials = (name) =>
  (name || "")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase() || "U";

async function onLogout() {
  menuOpen.value = false;
  await logout();
  await navigateTo("/");
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 glass-nav border-b border-white/[0.08]">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <NuxtLink to="/" class="font-display text-2xl font-black tracking-tight uppercase leading-none">
        BOOKS<span class="text-[#c9ff47]">ALL</span>
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-7 text-sm text-[#888888]">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="transition-colors hover:text-white"
          :class="isActive(link.to) ? 'text-white font-semibold' : ''"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="hidden md:flex items-center gap-2">
        <ClientOnly>
          <template v-if="auth.isAuthenticated">
            <div class="relative">
              <button
                class="flex items-center gap-2 bg-[#141414] border border-white/[0.08] rounded-full pl-1 pr-3 py-1 hover:border-white/30 transition-colors"
                @click="menuOpen = !menuOpen"
              >
                <img
                  v-if="auth.user?.avatar"
                  :src="auth.user.avatar"
                  alt=""
                  class="w-7 h-7 rounded-full object-cover"
                />
                <span v-else class="w-7 h-7 rounded-full bg-[#c9ff47] text-black text-xs font-black grid place-items-center">
                  {{ initials(auth.user?.full_name) }}
                </span>
                <span class="text-sm font-semibold hidden sm:block">{{ (auth.user?.full_name || "Account").split(" ")[0] }}</span>
                <UIcon name="i-heroicons-chevron-down" class="text-[#888888]" />
              </button>
              <div v-if="menuOpen" class="absolute right-0 top-12 bg-[#141414] border border-white/[0.08] rounded-2xl shadow-xl shadow-black/50 w-56 overflow-hidden">
                <div class="px-4 py-3 border-b border-white/[0.08]">
                  <p class="text-sm font-semibold text-white">{{ auth.user?.full_name }}</p>
                  <p class="text-xs text-[#888888] truncate">{{ auth.user?.email }}</p>
                </div>
                <NuxtLink to="/dashboard/bookings" class="flex items-center gap-2 px-4 py-3 text-sm text-[#888888] hover:text-white hover:bg-[#1a1a1a] transition-colors">
                  <UIcon name="i-heroicons-ticket" /> My Bookings
                </NuxtLink>
                <NuxtLink to="/manage" class="flex items-center gap-2 px-4 py-3 text-sm text-[#888888] hover:text-white hover:bg-[#1a1a1a] transition-colors">
                  <UIcon name="i-heroicons-building-storefront" /> Manage venues
                </NuxtLink>
                <button class="w-full flex items-center gap-2 px-4 py-3 text-sm text-[#888888] hover:text-white hover:bg-[#1a1a1a] transition-colors" @click="onLogout">
                  <UIcon name="i-heroicons-arrow-right-on-rectangle" /> Sign out
                </button>
              </div>
            </div>
          </template>
          <template v-else>
            <NuxtLink to="/login" class="text-sm font-semibold text-[#888888] hover:text-white transition-colors px-3 py-2">Log in</NuxtLink>
            <NuxtLink to="/register" class="bg-[#c9ff47] text-black text-sm font-bold px-4 py-2 rounded-full hover:bg-[#d9ff6b] transition-colors">Sign up</NuxtLink>
          </template>
          <template #fallback>
            <NuxtLink to="/login" class="text-sm font-semibold text-[#888888] hover:text-white transition-colors px-3 py-2">Log in</NuxtLink>
            <NuxtLink to="/register" class="bg-[#c9ff47] text-black text-sm font-bold px-4 py-2 rounded-full hover:bg-[#d9ff6b] transition-colors">Sign up</NuxtLink>
          </template>
        </ClientOnly>
      </div>

      <button
        class="md:hidden grid place-items-center w-10 h-10 -mr-2 rounded-lg text-[#888888] hover:bg-[#1a1a1a]"
        aria-label="Toggle menu"
        @click="mobileOpen = !mobileOpen"
      >
        <UIcon :name="mobileOpen ? 'i-heroicons-x-mark' : 'i-heroicons-bars-3'" class="text-2xl" />
      </button>
    </div>

    <!-- Mobile menu -->
    <div v-if="mobileOpen" class="md:hidden glass-nav border-t border-white/[0.08]">
      <div class="max-w-7xl mx-auto px-6 py-3 flex flex-col gap-1">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="px-3 py-3 rounded-lg font-medium transition-colors"
          :class="isActive(link.to) ? 'text-black bg-[#c9ff47]' : 'text-[#c4c4c4] hover:bg-[#1a1a1a]'"
        >
          {{ link.label }}
        </NuxtLink>
        <div class="h-px bg-white/[0.08] my-2" />
        <ClientOnly>
          <template v-if="auth.isAuthenticated">
            <NuxtLink to="/dashboard/bookings" class="px-3 py-3 rounded-lg font-medium text-[#c4c4c4] hover:bg-[#1a1a1a]">My Bookings</NuxtLink>
            <NuxtLink to="/manage" class="px-3 py-3 rounded-lg font-medium text-[#c4c4c4] hover:bg-[#1a1a1a]">Manage venues</NuxtLink>
            <button class="text-left px-3 py-3 rounded-lg font-medium text-[#c4c4c4] hover:bg-[#1a1a1a]" @click="onLogout">Sign out</button>
          </template>
          <template v-else>
            <NuxtLink to="/login" class="px-3 py-3 rounded-lg font-medium text-[#c4c4c4] hover:bg-[#1a1a1a]">Log in</NuxtLink>
            <NuxtLink to="/register" class="mt-1 px-3 py-3 rounded-lg font-bold text-center bg-[#c9ff47] text-black">Sign up</NuxtLink>
          </template>
        </ClientOnly>
      </div>
    </div>
  </header>
</template>
