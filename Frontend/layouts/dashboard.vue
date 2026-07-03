<script setup>
// Authenticated app shell. The site-wide navbar stays visible at the top
// (so you're never stranded without a way back to the main site), with a
// second, account-specific nav below it: sidebar on desktop, scrollable
// pill nav on mobile.
const auth = useAuthStore();
const route = useRoute();
const { logout } = useAuth();
const nav = [
    { label: "My Bookings", to: "/dashboard/bookings", icon: "i-heroicons-calendar-days" },
    { label: "Invoices", to: "/dashboard/invoices", icon: "i-heroicons-document-text" },
    { label: "Support", to: "/dashboard/tickets", icon: "i-heroicons-lifebuoy" },
    { label: "Manager dashboard", to: "/manage", icon: "i-heroicons-chart-bar" },
    { label: "Bookings", to: "/manage/bookings", icon: "i-heroicons-inbox-arrow-down" },
    { label: "Profile", to: "/dashboard/profile", icon: "i-heroicons-user-circle" },
];
const MANAGE_SUBROUTES = ["/manage/approvals", "/manage/bookings"];
const isActive = (to) => to === "/manage" ? route.path === "/manage" || (route.path.startsWith("/manage/") && !MANAGE_SUBROUTES.includes(route.path))
    : route.path === to || route.path.startsWith(to + "/");
const initials = computed(() => {
    const n = auth.user?.full_name || auth.user?.email || "";
    return n.split(/[\s@.]+/).filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "U";
});
async function onLogout() {
    await logout();
    await navigateTo("/");
}
</script>

<template>
  <div class="min-h-screen bg-[#111111] text-[#f0f0f0]">
    <SiteNavbar />

    <div class="pt-16">
      <div class="mx-auto max-w-7xl md:grid md:grid-cols-[260px_1fr]">
        <!-- Sidebar (desktop) -->
        <aside class="hidden md:flex flex-col gap-2 sticky top-16 h-[calc(100vh-4rem)] bg-ink bg-ink-gradient px-4 py-6 overflow-hidden">
          <div class="bg-pitch-dots absolute inset-0 opacity-50 pointer-events-none" />

          <nav class="relative flex-1 space-y-1.5 mt-1">
            <NuxtLink
              v-for="n in nav"
              :key="n.to"
              :to="n.to"
              class="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all"
              :class="isActive(n.to)
                ? 'bg-white/10 text-white shadow-inner ring-1 ring-volt-300/30'
                : 'text-[#8f8f8f]/70 hover:bg-white/5 hover:text-white'"
            >
              <UIcon :name="n.icon" class="text-xl transition-colors" :class="isActive(n.to) ? 'text-volt-300' : 'text-[#8f8f8f]/60 group-hover:text-volt-300'" />
              {{ n.label }}
            </NuxtLink>
          </nav>

          <ClientOnly>
            <div class="relative rounded-2xl bg-white/5 ring-1 ring-white/10 p-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="auth.user?.avatar"
                  :src="auth.user.avatar"
                  alt=""
                  class="w-9 h-9 rounded-full object-cover shrink-0"
                />
                <div v-else class="w-9 h-9 rounded-full surface-volt text-ink-950 grid place-items-center text-sm font-bold shrink-0">
                  {{ initials }}
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium truncate text-white">{{ auth.user?.full_name || "Player" }}</p>
                  <p class="text-xs text-[#8f8f8f]/50 truncate">{{ auth.user?.email }}</p>
                </div>
              </div>
              <UButton block color="gray" variant="soft" size="xs" class="mt-3" @click="onLogout">
                Sign out
              </UButton>
            </div>
          </ClientOnly>
        </aside>

        <!-- Content -->
        <div class="min-w-0">
          <!-- Mobile pill nav -->
          <div class="md:hidden sticky top-16 z-30 bg-ink bg-ink-gradient text-white">
            <div class="flex gap-2 overflow-x-auto no-scrollbar px-4 py-3">
              <NuxtLink
                v-for="n in nav"
                :key="n.to"
                :to="n.to"
                class="shrink-0 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
                :class="isActive(n.to) ? 'surface-volt text-ink-950' : 'bg-white/10 text-[#8f8f8f]/80'"
              >
                <UIcon :name="n.icon" />
                {{ n.label }}
              </NuxtLink>
            </div>
          </div>

          <main class="px-4 md:px-8 py-6 md:py-10">
            <slot />
          </main>
        </div>
      </div>
    </div>
  </div>
</template>
