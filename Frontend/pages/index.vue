<script setup>
const api = useApi();
const img = useImages();
const { data: futsals } = await useAsyncData("home-futsals", () => api("/api/futsals/", { query: { page_size: 6 } }));
const { data: teams } = await useAsyncData("home-teams", () => api("/api/teams/", { query: { page_size: 6 } }));
const { data: matches } = await useAsyncData("home-matches", () => api("/api/matches/", { query: { status: "OPEN", page_size: 4 } }));
useSeoMeta({
    title: "Booksall — Book futsals & find matches across Nepal",
    description: "Reserve futsal courts online in seconds, find open matches, and challenge other teams. " +
        "Live availability, transparent pricing, no more Facebook-group hunting.",
    ogTitle: "Booksall — Book futsals & find matches across Nepal",
    ogDescription: "Reserve futsal courts, find matches, and challenge teams.",
    ogType: "website",
});
const search = ref("");
function goSearch() {
    navigateTo({ path: "/futsals", query: search.value ? { search: search.value } : {} });
}
const cities = [
    { name: "Kathmandu", img: img.action(0, 600, 600) },
    { name: "Lalitpur", img: img.court(0, 600, 600) },
    { name: "Bhaktapur", img: img.action(1, 600, 600) },
    { name: "Pokhara", img: img.court(2, 600, 600) },
];
const steps = [
    { icon: "i-heroicons-magnifying-glass", title: "Find your pitch", text: "Browse futsals near you with photos, live slots, and clear pricing." },
    { icon: "i-heroicons-calendar-days", title: "Book in seconds", text: "Pick a slot, confirm, and the venue approves it. Pay at the futsal." },
    { icon: "i-heroicons-user-group", title: "Find your game", text: "Join open matches or build a team and challenge rivals." },
];
const benefits = [
    { icon: "i-heroicons-bolt", title: "Real-time availability", text: "See exactly which slots are open — no calls, no double-bookings." },
    { icon: "i-heroicons-banknotes", title: "Transparent pricing", text: "Morning, evening and weekend rates shown upfront. No surprises." },
    { icon: "i-heroicons-shield-check", title: "Confirmed bookings", text: "Every booking is approved by the venue, so your slot is yours." },
    { icon: "i-heroicons-users", title: "A real community", text: "Find players for a pickup game or run your own team's season." },
];
const testimonials = [
    { name: "Aayush Shrestha", role: "Plays in Kathmandu", quote: "Booking used to mean ten phone calls. Now I grab a slot in 30 seconds and show up to play.", initials: "AS" },
    { name: "Sneha Gurung", role: "Team captain", quote: "The team challenges are addictive. We've played five clubs we'd never have found otherwise.", initials: "SG" },
    { name: "Bibek Tamang", role: "Futsal owner, Lalitpur", quote: "Approvals and pricing are finally in one place. My evenings book out without me lifting a finger.", initials: "BT" },
];
const faqs = [
    { icon: "i-heroicons-calendar-days", label: "How do I book a futsal?", content: "Pick a venue, choose an open slot on your date, and confirm. The venue approves your request and you pay in cash at the futsal." },
    { icon: "i-heroicons-arrow-path", label: "Can I cancel or reschedule?", content: "Yes — cancel anytime before play, or move to another open slot. The venue re-approves the new time." },
    { icon: "i-heroicons-user-group", label: "What are open matches?", content: "Players post pickup games with a time and number of spots. Join one to get a full squad without scrolling Facebook groups." },
    { icon: "i-heroicons-trophy", label: "How do team challenges work?", content: "Create a team, invite players, then challenge another team. The opponent captain accepts and you record the result afterwards." },
    { icon: "i-heroicons-banknotes", label: "Does Booksall cost anything?", content: "Browsing, matchmaking, and team features are free. You only pay the venue's court fee when you book." },
    { icon: "i-heroicons-building-storefront", label: "I run a futsal — can I list it?", content: "Yes. Register, add your venue, courts, and pricing, then approve bookings from your manager dashboard. Listing is free." },
];
const openFaq = ref(0);
function toggleFaq(i) {
    openFaq.value = openFaq.value === i ? -1 : i;
}
const fade = (delay = 0) => ({
    initial: { opacity: 0, y: 24 },
    visibleOnce: { opacity: 1, y: 0, transition: { duration: 600, delay } },
});
function matchTime(iso) {
    return new Date(iso).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
</script>

<template>
  <div>
    <!-- SECTION: Hero -->
    <section class="relative overflow-hidden bg-mesh-lime">
      <div class="absolute -top-24 -right-24 w-[28rem] h-[28rem] rounded-full bg-[#c9ff47]/10 blur-3xl animate-float-slow" />
      <div class="absolute top-40 -left-24 w-80 h-80 rounded-full bg-[#c9ff47]/[0.07] blur-3xl animate-float" />
      <div class="absolute -bottom-20 right-1/3 w-72 h-72 rounded-full bg-[#c9ff47]/[0.06] blur-3xl" />

      <UContainer class="relative py-20 md:py-28">
        <div class="grid lg:grid-cols-2 gap-12 items-center">
          <div v-motion :initial="{ opacity: 0, y: 24 }" :enter="{ opacity: 1, y: 0, transition: { duration: 700 } }">
            <span class="inline-flex items-center gap-2 rounded-full bg-[#c9ff47]/10 border border-[#c9ff47]/30 px-3 py-1 mb-6">
              <span class="w-2 h-2 rounded-full bg-[#c9ff47] animate-pulse" />
              <span class="text-xs font-semibold text-[#c9ff47] tracking-widest uppercase">Live availability</span>
            </span>
            <h1 class="font-display text-6xl md:text-7xl font-black leading-[0.95] tracking-tight uppercase text-[#f0f0f0]">
              Book the pitch.<br />
              <span class="text-[#c9ff47]">Find the game.</span>
            </h1>
            <p class="mt-5 text-lg text-[#8f8f8f] max-w-lg">
              Live court availability, fair pricing, and a community of players and teams —
              all in one bright, simple place.
            </p>

            <div class="mt-7 flex w-full max-w-md rounded-2xl border border-white/[0.08] bg-[#141414] p-1.5 shadow-sm focus-within:ring-2 focus-within:ring-[#c9ff47]/60">
              <input
                v-model="search"
                type="text"
                placeholder="Search by venue or city…"
                class="flex-1 bg-transparent px-3 text-[#e5e5e5] placeholder-[#666666] focus:outline-none"
                @keyup.enter="goSearch"
              />
              <UButton color="primary" size="lg" icon="i-heroicons-magnifying-glass" @click="goSearch">
                Search
              </UButton>
            </div>

            <div class="mt-6 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-[#888888]">
              <span class="inline-flex items-center gap-1.5"><UIcon name="i-heroicons-check-circle" class="text-[#c9ff47]" /> Free to join</span>
              <span class="inline-flex items-center gap-1.5"><UIcon name="i-heroicons-check-circle" class="text-[#c9ff47]" /> Instant slots</span>
              <span class="inline-flex items-center gap-1.5"><UIcon name="i-heroicons-check-circle" class="text-[#c9ff47]" /> Pay at venue</span>
            </div>
          </div>

          <!-- Photo collage -->
          <div class="relative h-[26rem] hidden lg:block" v-motion :initial="{ opacity: 0, scale: 0.96 }" :enter="{ opacity: 1, scale: 1, transition: { duration: 700, delay: 150 } }">
            <img :src="img.action(0, 520, 640)" alt="Players on a futsal pitch" class="absolute left-0 top-4 w-56 h-72 object-cover rounded-3xl shadow-xl rotate-[-4deg]" loading="eager" />
            <img :src="img.court(0, 520, 520)" alt="Futsal court" class="absolute right-2 top-0 w-52 h-52 object-cover rounded-3xl shadow-xl rotate-[3deg]" loading="eager" />
            <img :src="img.action(2, 520, 520)" alt="Futsal action" class="absolute right-6 bottom-0 w-56 h-60 object-cover rounded-3xl shadow-xl rotate-[-2deg]" loading="lazy" />
            <div class="absolute left-10 bottom-6 bg-[#141414] rounded-2xl shadow-lg px-4 py-3 rotate-[2deg]">
              <p class="text-xs text-[#888888]">Tonight, 7:00 PM</p>
              <p class="font-display font-semibold text-[#f0f0f0]">3 slots left</p>
            </div>
          </div>
        </div>

        <!-- Stat strip -->
        <div class="mt-14 grid grid-cols-3 gap-4 max-w-xl">
          <div>
            <p class="font-display text-3xl font-bold text-[#c9ff47]">{{ futsals?.count ?? "—" }}</p>
            <p class="text-sm text-[#888888]">Venues listed</p>
          </div>
          <div>
            <p class="font-display text-3xl font-bold text-[#c9ff47]">{{ teams?.count ?? "—" }}</p>
            <p class="text-sm text-[#888888]">Teams playing</p>
          </div>
          <div>
            <p class="font-display text-3xl font-bold text-[#c9ff47]">{{ matches?.count ?? "—" }}</p>
            <p class="text-sm text-[#888888]">Open matches</p>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: Popular cities -->
    <section class="py-12">
      <UContainer>
        <h2 class="font-display text-2xl font-bold text-[#f0f0f0] mb-6">Find a pitch in your city</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <NuxtLink
            v-for="c in cities" :key="c.name"
            :to="{ path: '/futsals', query: { city: c.name } }"
            class="group relative h-32 md:h-40 rounded-2xl overflow-hidden"
          >
            <img :src="c.img" :alt="c.name" class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" loading="lazy" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
            <span class="absolute bottom-3 left-3 font-display font-semibold text-white text-lg">{{ c.name }}</span>
          </NuxtLink>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: How it works -->
    <section class="py-16 md:py-24 bg-[#1a1a1a]/60">
      <UContainer>
        <div class="max-w-2xl">
          <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">From "where do we play?" to kickoff</h2>
          <p class="mt-3 text-[#8f8f8f] text-lg">Three steps, a few taps, you're on the pitch.</p>
        </div>
        <div class="mt-12 grid gap-6 md:grid-cols-3">
          <div v-for="(s, i) in steps" :key="s.title"
            v-motion :initial="fade(i * 100).initial" :visible-once="fade(i * 100).visibleOnce"
            class="rounded-3xl bg-[#141414] p-7 shadow-sm">
            <div class="w-12 h-12 rounded-2xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47] mb-5">
              <UIcon :name="s.icon" class="text-2xl" />
            </div>
            <p class="font-display text-sm font-semibold text-[#c9ff47] mb-1">Step {{ i + 1 }}</p>
            <h3 class="font-display text-xl font-semibold text-[#f0f0f0]">{{ s.title }}</h3>
            <p class="mt-2 text-[#8f8f8f] leading-relaxed">{{ s.text }}</p>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: Featured futsals -->
    <section class="py-16 md:py-24">
      <UContainer>
        <div class="flex items-end justify-between gap-4 mb-8">
          <div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Featured futsals</h2>
            <p class="mt-2 text-[#8f8f8f]">Explore venues — sign in when you're ready to book.</p>
          </div>
          <UButton to="/futsals" color="primary" variant="soft" trailing-icon="i-heroicons-arrow-right" class="hidden sm:flex">
            View all
          </UButton>
        </div>
        <div v-if="futsals?.results?.length" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="(v, i) in futsals.results" :key="v.id"
            v-motion :initial="fade((i % 3) * 80).initial" :visible-once="fade((i % 3) * 80).visibleOnce">
            <VenueCard :venue="v" />
          </div>
        </div>
        <p v-else class="text-[#888888]">No venues listed yet — check back soon.</p>
      </UContainer>
    </section>

    <!-- SECTION: Why Booksall (image + benefits) -->
    <section class="py-16 md:py-24 bg-[#111111]/60">
      <UContainer>
        <div class="grid lg:grid-cols-2 gap-12 items-center">
          <div class="relative" v-motion :initial="fade().initial" :visible-once="fade().visibleOnce">
            <img :src="img.action(4, 900, 700)" alt="Futsal players celebrating" class="rounded-3xl shadow-xl w-full object-cover aspect-[4/3]" loading="lazy" />
            <div class="absolute -bottom-5 -right-3 bg-[#141414] rounded-2xl shadow-lg px-5 py-4 hidden sm:block">
              <p class="font-display text-2xl font-bold text-[#c9ff47]">4.8★</p>
              <p class="text-xs text-[#888888]">player rating</p>
            </div>
          </div>
          <div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Everything you need to just play</h2>
            <p class="mt-3 text-[#8f8f8f] text-lg">No more group chats, no more guesswork. Booksall puts the whole game in your pocket.</p>
            <div class="mt-8 grid sm:grid-cols-2 gap-5">
              <div v-for="b in benefits" :key="b.title" class="flex gap-3">
                <div class="shrink-0 w-10 h-10 rounded-xl bg-[#141414] grid place-items-center text-[#c9ff47] shadow-sm">
                  <UIcon :name="b.icon" class="text-xl" />
                </div>
                <div>
                  <h3 class="font-semibold text-[#f0f0f0]">{{ b.title }}</h3>
                  <p class="text-sm text-[#8f8f8f] mt-0.5">{{ b.text }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: Open matches -->
    <section v-if="matches?.results?.length" class="py-16 md:py-24">
      <UContainer>
        <div class="flex items-end justify-between gap-4 mb-8">
          <div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Games looking for players</h2>
            <p class="mt-2 text-[#8f8f8f]">Jump into an open match near you.</p>
          </div>
          <UButton to="/matches" color="primary" variant="soft" trailing-icon="i-heroicons-arrow-right" class="hidden sm:flex">
            All matches
          </UButton>
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <NuxtLink v-for="m in matches.results" :key="m.id" to="/matches"
            class="group flex items-center justify-between rounded-2xl border border-white/[0.08] bg-[#141414] p-5 hover:border-[#c9ff47]/40 hover:shadow-md transition-all">
            <div>
              <p class="font-display text-lg font-semibold text-[#f0f0f0]">{{ m.format }} match</p>
              <p class="mt-1 text-sm text-[#888888]">{{ matchTime(m.proposed_start) }}<template v-if="m.city"> · {{ m.city }}</template></p>
            </div>
            <span class="inline-flex items-center gap-1.5 rounded-full bg-[#1a1a1a] text-[#c9ff47] px-3 py-1 text-sm font-semibold">
              {{ m.joined_count }}/{{ m.max_players }}
            </span>
          </NuxtLink>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: Teams -->
    <section v-if="teams?.results?.length" class="py-16 md:py-24 bg-[#1a1a1a]/60">
      <UContainer>
        <div class="flex items-end justify-between gap-4 mb-8">
          <div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Teams to watch</h2>
            <p class="mt-2 text-[#8f8f8f]">Build a squad, challenge rivals, climb the ladder.</p>
          </div>
          <UButton to="/teams" color="primary" variant="soft" trailing-icon="i-heroicons-arrow-right" class="hidden sm:flex">
            All teams
          </UButton>
        </div>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="(t, i) in teams.results" :key="t.id"
            v-motion :initial="fade((i % 3) * 80).initial" :visible-once="fade((i % 3) * 80).visibleOnce">
            <TeamCard :team="t" />
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: Testimonials -->
    <section class="py-16 md:py-24">
      <UContainer>
        <h2 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0] text-center">Loved by players & venues</h2>
        <p class="mt-3 text-[#8f8f8f] text-center max-w-xl mx-auto">Real games, real teams, across the Valley.</p>
        <div class="mt-12 grid gap-6 md:grid-cols-3">
          <div v-for="(t, i) in testimonials" :key="t.name"
            v-motion :initial="fade(i * 80).initial" :visible-once="fade(i * 80).visibleOnce"
            class="rounded-3xl border border-white/[0.06] bg-[#141414] p-7 shadow-sm">
            <div class="flex gap-1 text-amber-400 mb-4">
              <UIcon v-for="n in 5" :key="n" name="i-heroicons-star-solid" />
            </div>
            <p class="text-[#c4c4c4] leading-relaxed">"{{ t.quote }}"</p>
            <div class="mt-6 flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-[#1e1e1e] text-[#c9ff47] grid place-items-center font-semibold">{{ t.initials }}</div>
              <div>
                <p class="font-semibold text-[#f0f0f0] text-sm">{{ t.name }}</p>
                <p class="text-xs text-[#888888]">{{ t.role }}</p>
              </div>
            </div>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: FAQ -->
    <section class="relative py-16 md:py-28 bg-[#111111] overflow-hidden">
      <div class="absolute -top-32 right-0 w-[26rem] h-[26rem] rounded-full bg-[#c9ff47]/[0.05] blur-3xl" />
      <UContainer class="relative">
        <div class="grid lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-10 lg:gap-16 items-start">
          <!-- Left: heading + support CTA -->
          <div class="lg:sticky lg:top-24" v-motion :initial="fade().initial" :visible-once="fade().visibleOnce">
            <span class="inline-flex items-center gap-2 rounded-full bg-[#c9ff47]/10 border border-[#c9ff47]/30 px-3 py-1 mb-5">
              <UIcon name="i-heroicons-chat-bubble-left-right" class="text-[#c9ff47] text-sm" />
              <span class="text-xs font-semibold text-[#c9ff47] tracking-widest uppercase">FAQ</span>
            </span>
            <h2 class="font-display text-4xl md:text-5xl font-black uppercase tracking-tight leading-[1.02] text-[#f0f0f0]">
              Got questions?<br /><span class="text-[#c9ff47]">We've got answers.</span>
            </h2>
            <p class="mt-4 text-[#8f8f8f] text-lg max-w-md">
              Everything you need to know about booking courts, joining matches, and running your team.
            </p>
            <div class="mt-8 rounded-3xl border border-white/[0.08] bg-[#141414] p-6">
              <p class="font-display font-semibold text-[#f0f0f0]">Still stuck?</p>
              <p class="mt-1 text-sm text-[#8f8f8f]">Our team answers within a day.</p>
              <UButton to="/support" color="primary" variant="soft" trailing-icon="i-heroicons-arrow-right" class="mt-4">
                Contact support
              </UButton>
            </div>
          </div>

          <!-- Right: accordion -->
          <div class="space-y-3">
            <div
              v-for="(f, i) in faqs" :key="f.label"
              v-motion :initial="fade(i * 60).initial" :visible-once="fade(i * 60).visibleOnce"
              class="rounded-2xl border transition-colors duration-300"
              :class="openFaq === i ? 'border-[#c9ff47]/40 bg-[#161616]' : 'border-white/[0.07] bg-[#141414] hover:border-white/[0.16]'"
            >
              <button
                type="button"
                class="flex w-full items-center gap-4 px-5 py-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9ff47]/60 rounded-2xl"
                :aria-expanded="openFaq === i"
                @click="toggleFaq(i)"
              >
                <span
                  class="shrink-0 w-10 h-10 rounded-xl grid place-items-center transition-colors duration-300"
                  :class="openFaq === i ? 'bg-[#c9ff47] text-black' : 'bg-[#1e1e1e] text-[#c9ff47]'"
                >
                  <UIcon :name="f.icon" class="text-xl" />
                </span>
                <span class="flex-1 font-display text-base md:text-lg font-semibold" :class="openFaq === i ? 'text-[#c9ff47]' : 'text-[#f0f0f0]'">
                  {{ f.label }}
                </span>
                <UIcon
                  name="i-heroicons-plus"
                  class="shrink-0 text-xl text-[#8f8f8f] transition-transform duration-300"
                  :class="openFaq === i ? 'rotate-45 text-[#c9ff47]' : ''"
                />
              </button>
              <div
                class="grid transition-[grid-template-rows] duration-300 ease-out"
                :class="openFaq === i ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
              >
                <div class="overflow-hidden">
                  <p class="px-5 pb-5 pl-[4.75rem] text-[#8f8f8f] leading-relaxed">{{ f.content }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- SECTION: CTA (vibrant) -->
    <section class="py-16">
      <UContainer>
        <div class="relative overflow-hidden rounded-[2rem] bg-[#c9ff47] px-8 py-16 md:py-20 text-center">
          <h2 class="font-display text-5xl md:text-6xl font-black uppercase tracking-tight text-black">Ready to play?</h2>
          <p class="mt-4 text-black/70 max-w-xl mx-auto text-lg font-medium">
            Create a free account to book courts, join matches, and run your team.
          </p>
          <div class="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <NuxtLink
              to="/register"
              class="inline-flex items-center justify-center rounded-full bg-black px-7 py-3 text-base font-bold text-white transition-transform hover:scale-[1.03]"
            >
              Get started — it's free
            </NuxtLink>
            <NuxtLink
              to="/futsals"
              class="inline-flex items-center justify-center rounded-full border-2 border-black/70 px-7 py-3 text-base font-bold text-black transition-colors hover:bg-black hover:text-[#c9ff47]"
            >
              Browse futsals
            </NuxtLink>
          </div>
        </div>
      </UContainer>
    </section>
  </div>
</template>
