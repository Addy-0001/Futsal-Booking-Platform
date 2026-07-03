<script setup>
const year = new Date().getFullYear();
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[#0a0a0a] text-[#f0f0f0]">
    <SiteNavbar />

    <main class="flex-1 pt-16">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="relative bg-[#0a0a0a] border-t border-white/[0.08] text-[#888888]">
      <div class="max-w-7xl mx-auto px-6 py-16">
        <div class="grid gap-10 md:grid-cols-4">
          <div class="md:col-span-2 max-w-sm">
            <NuxtLink to="/" class="font-display text-2xl font-black tracking-tight uppercase text-white">
              BOOKS<span class="text-[#c9ff47]">ALL</span>
            </NuxtLink>
            <p class="mt-4 leading-relaxed">
              Book futsals and find matches across Nepal — live availability, fair pricing,
              and a community that plays.
            </p>
            <div class="mt-6 flex items-center gap-3">
              <a
                v-for="s in ['i-heroicons-globe-alt', 'i-heroicons-chat-bubble-left-right', 'i-heroicons-envelope']"
                :key="s"
                href="#"
                class="grid place-items-center w-10 h-10 rounded-xl bg-[#141414] border border-white/[0.08] hover:bg-[#c9ff47] hover:text-black hover:border-transparent transition-colors"
              >
                <UIcon :name="s" class="text-lg" />
              </a>
            </div>
          </div>

          <div>
            <h4 class="eyebrow text-[#c9ff47] mb-4">Play</h4>
            <ul class="space-y-2.5 text-sm">
              <li><NuxtLink to="/futsals" class="hover:text-[#c9ff47] transition-colors">Find a futsal</NuxtLink></li>
              <li><NuxtLink to="/matches" class="hover:text-[#c9ff47] transition-colors">Open matches</NuxtLink></li>
              <li><NuxtLink to="/teams" class="hover:text-[#c9ff47] transition-colors">Teams</NuxtLink></li>
            </ul>
          </div>

          <div>
            <h4 class="eyebrow text-[#c9ff47] mb-4">Company</h4>
            <ul class="space-y-2.5 text-sm">
              <li><NuxtLink to="/support" class="hover:text-[#c9ff47] transition-colors">Support</NuxtLink></li>
              <li><NuxtLink to="/privacy" class="hover:text-[#c9ff47] transition-colors">Privacy</NuxtLink></li>
              <li><NuxtLink to="/terms" class="hover:text-[#c9ff47] transition-colors">Terms</NuxtLink></li>
              <li><NuxtLink to="/cookies" class="hover:text-[#c9ff47] transition-colors">Cookies</NuxtLink></li>
            </ul>
          </div>
        </div>

        <div class="mt-12 pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-[#666666]">
          <span>© {{ year }} Booksall. Made for futsal in Nepal.</span>
          <span class="inline-flex items-center gap-2"><span class="live-dot" /> All systems live</span>
        </div>
      </div>
    </footer>
  </div>
</template>
