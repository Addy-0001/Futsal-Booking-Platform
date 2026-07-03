# Booksall — Frontend Design & Build Guideline (Nuxt SSR)

**Stack decision:** Nuxt 3 (Vue 3, `<script setup>`), **full SSR** (`ssr: true`), **Tailwind CSS + Nuxt UI**, **Pinia** for state, **JWT in localStorage** via Pinia. Talks to the Django/DRF backend (see `BACKEND_DESIGN.md`).
**Primary goal of SSR here:** SEO + fast first paint on public pages (venue listings, venue detail, landing, policy pages).

---

## 1. Guiding principles

- **Server renders the public, client owns the private.** Venue discovery, landing, and policy pages must be fully server-rendered and crawlable. Authenticated dashboard pages render their shell on the server and hydrate data on the client.
- **`useFetch`/`useAsyncData` for anything that must appear in the HTML.** Never fetch SEO-critical content in `onMounted` — crawlers won't see it.
- **The server never trusts the client for price or availability.** The Nuxt app sends a court + slot; Django computes the price and enforces the booking rules (see backend §5).
- **Type the API surface.** Generate TS types from the backend's OpenAPI schema (drf-spectacular) so frontend and backend can't silently drift.
- **One API layer.** All calls go through a single `$api` wrapper (auth header, base URL, error normalization) — components never call `$fetch` raw.

---

## 2. The SSR + localStorage caveat (read this first)

You chose **full SSR** with **JWT in localStorage via Pinia**. These two have a known interaction you must design around: **`localStorage` does not exist on the server**, so on the very first server render the user's token is unavailable. Practical consequences and the pattern that makes it work cleanly:

- **Public/SEO pages** (venues, landing, policies) don't need auth — they SSR fully with no token. SEO is unaffected. ✅
- **Authenticated pages** (my bookings, dashboard, team) can't fetch user-scoped data during SSR because there's no token server-side. Handle them as **SSR shell + client-side data fetch**:
  - Render the page layout/skeleton on the server.
  - In a Pinia action, read the token from `localStorage` on the client (guard with `import.meta.client`), then fetch the protected data after hydration.
  - Use `useAsyncData(..., { server: false })` for protected calls so Nuxt doesn't try them during SSR.
- **Avoid hydration mismatches:** never read `localStorage` directly in template/setup that runs on both server and client. Read it inside `onMounted`, a client-only plugin, or behind `import.meta.client`. Wrap auth-dependent UI in `<ClientOnly>` where needed.
- **Auth guard:** middleware checks `auth.isAuthenticated`; since the token is client-only, mark protected route middleware to run on the client, or redirect after mount. Public route SSR stays untouched.

> If you later want protected pages to SSR with data (and harden against XSS), the standard upgrade is mirroring the access token into an `httpOnly` cookie so Nuxt's server has it. Not required now — noted so the structure below stays compatible.

---

## 3. Project structure

```
booksall-web/
  nuxt.config.ts
  app.vue
  assets/css/            # tailwind entry, base styles
  components/
    ui/                  # thin wrappers over Nuxt UI where needed
    venue/               # VenueCard, VenueFilters, AvailabilityGrid
    booking/             # SlotPicker, BookingSummary, BookingStatusBadge
    team/                # TeamCard, ChallengeModal
  composables/
    useApi.ts            # $api wrapper (base URL, auth header, errors)
    useAuth.ts           # login/logout/refresh helpers over the store
    useSeo.ts            # helper to set title/meta/OG/JSON-LD per page
  layouts/
    default.vue          # public shell (header/footer, SEO nav)
    dashboard.vue        # authenticated shell
  middleware/
    auth.client.ts       # protect dashboard routes (client-side)
    guest.client.ts      # redirect logged-in users away from /login
  pages/                 # file-based routing (URLs below)
  plugins/
    api.ts               # provide $api
    auth.client.ts       # hydrate token from localStorage on client boot
  stores/
    auth.ts              # Pinia: token, user, login/logout/refresh
    booking.ts
  server/                # (optional) Nuxt server routes if you proxy later
  types/                 # generated API types + domain types
  nuxt.config.ts
```

---

## 4. nuxt.config.ts (key settings)

```ts
export default defineNuxtConfig({
  ssr: true,                       // full SSR
  modules: [
    '@nuxt/ui',                    // Tailwind + Headless UI + icons
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxtjs/sitemap',             // sitemap.xml for SEO
    '@nuxtjs/robots',              // robots.txt
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE,   // https://api.booksall.com
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL,   // https://booksall.com
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      // global defaults; pages override via useSeoMeta
    },
  },
  nitro: {
    compressPublicAssets: true,
  },
})
```

Set `NUXT_PUBLIC_API_BASE` per environment. **During SSR, fetches run from the Nuxt server**, so the API base must be reachable server-side (internal URL ok); for client calls it must be publicly reachable. If those differ, expose both and pick by `import.meta.server`.

---

## 5. SEO — the reason for SSR

This is the payoff; treat it as a first-class feature, not an afterthought.

**Per-page meta** with `useSeoMeta` (reactive, SSR-rendered):

```vue
<script setup lang="ts">
const { data: venue } = await useFetch(() => `/api/futsals/${route.params.slug}`)
useSeoMeta({
  title: () => `${venue.value?.name} — Book a futsal in ${venue.value?.city} | Booksall`,
  description: () => venue.value?.description,
  ogTitle: () => venue.value?.name,
  ogImage: () => venue.value?.cover_image,
  ogType: 'website',
  twitterCard: 'summary_large_image',
})
</script>
```

**Structured data (JSON-LD)** so venues can appear as rich results — emit `SportsActivityLocation` / `LocalBusiness` per venue via `useHead({ script: [{ type: 'application/ld+json', innerHTML: ... }] })`.

**Must-haves:**
- Canonical URLs (`useHead` link rel=canonical) to avoid duplicate-content from filters/query params.
- `@nuxtjs/sitemap` driven by the venues API so every venue URL is indexed; submit to Google Search Console.
- `@nuxtjs/robots` allowing public pages, disallowing `/dashboard`, `/login`, API-ish routes.
- Semantic HTML + real `<h1>` per page; image `alt`; meaningful link text.
- Clean, slug-based URLs (see §6) — never expose UUIDs in public URLs; use `slug` for SEO and resolve to UUID server-side.

---

## 6. Routing / URL plan

| URL | Render | Notes |
|---|---|---|
| `/` | SSR | Landing, SEO-heavy |
| `/futsals` | SSR | Venue search/listing, filters via query params (kept canonical) |
| `/futsals/[slug]` | SSR | Venue detail + availability preview — primary SEO page |
| `/teams`, `/teams/[slug]` | SSR | Public team pages |
| `/matches` | SSR | Open matches board (replaces FB groups) |
| `/privacy`, `/terms`, `/cookies` | SSR/SSG | Policy pages from backend `legal` app |
| `/login`, `/register` | SSR shell | Forms; `guest` middleware |
| `/dashboard/**` | SSR shell + client data | Bookings, profile, team mgmt — protected |

Public pages use slugs; protected/API operations use the UUID returned by the API.

---

## 7. API integration layer

`composables/useApi.ts` — single wrapper used everywhere:

```ts
export const useApi = () => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()
  return $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (auth.accessToken) {
        options.headers = { ...options.headers, Authorization: `Bearer ${auth.accessToken}` }
      }
    },
    async onResponseError({ response }) {
      if (response.status === 401) await auth.tryRefresh()   // rotate refresh token
      // normalize DRF error envelope here → consistent shape for UI
    },
  })
}
```

- Wrap SEO-critical GETs in `useFetch`/`useAsyncData` (so they SSR + dedupe + cache).
- Wrap protected GETs in `useAsyncData(key, fn, { server: false })` per §2.
- Mutations (POST/PATCH) call `$api` directly inside event handlers, never in setup.
- Generate `types/api.ts` from the backend OpenAPI schema (`openapi-typescript`) and type every call.

---

## 8. Auth flow (Pinia + localStorage)

`stores/auth.ts` holds `accessToken`, `refreshToken`, `user`.

```
register → POST /auth/register → email verification notice
login    → POST /auth/login → {access, refresh} → store in Pinia + localStorage (client only)
boot     → plugins/auth.client.ts reads tokens from localStorage → fetches /auth/me
refresh  → on 401, POST /auth/refresh with refresh token → rotate; on fail → logout
logout   → clear store + localStorage + (call backend blacklist endpoint)
```

Rules:
- All `localStorage` access guarded by `import.meta.client` or inside `auth.client.ts` plugin / `onMounted`.
- Protected route middleware (`auth.client.ts`) checks `isAuthenticated`; redirects to `/login?next=...` on the client.
- Never render user-specific data in server HTML (no token there anyway) — keeps SSR cache-safe and avoids leaking one user's data into another's cached page.

---

## 9. Core feature UIs (where the real work is)

- **AvailabilityGrid** (`components/venue/`): fetch a court's slots for a date, render the fixed-grid slots (backend §5.5), color by state (free / your-pending / booked). Selecting a free slot opens BookingSummary.
- **BookingSummary**: shows server-computed price (never compute price client-side), confirms → POST creates a `PENDING_APPROVAL` booking → show "awaiting venue approval" state. Poll or use the notification feed for status changes.
- **SlotPicker / reschedule**: same grid, pre-selects current slot; submit goes through the backend's cancel-and-rebook transaction.
- **Booking status**: badge component mapping the backend lifecycle (pending/approved/rejected/cancelled/expired/completed).
- **Matches board**: list + create open match; join button.
- **Teams + challenges**: team page, challenge modal → maps to the backend "war" flow.

Optimistic UI is fine for non-critical actions, but **booking creation must wait for the server response** — the exclusion constraint is the source of truth and the slot may have just been taken.

---

## 10. Performance & quality

- Lazy-load heavy/below-fold components (`defineAsyncComponent` / `Lazy` prefix).
- `<NuxtImg>` (add `@nuxt/image`) for responsive, optimized venue images — big SEO + LCP win.
- Cache stable SSR responses at the edge via Nitro `routeRules` (e.g. `/futsals` with short `swr`) without breaking freshness on booking pages.
- Lighthouse budget in CI; target good LCP/CLS on venue pages.
- ESLint + Prettier + `vue-tsc` typecheck in CI; Vitest for composables, Playwright for the booking happy-path.

---

## 11. How to get started

**Phase 0 — scaffold**
`npx nuxi init booksall-web`; add `@nuxt/ui`, `@pinia/nuxt`, `@vueuse/nuxt`, sitemap, robots. Set runtimeConfig + env. Build `default.vue` + `dashboard.vue` layouts and the `$api` wrapper.

**Phase 1 — public SEO pages**
Landing, `/futsals` listing, `/futsals/[slug]` detail with `useFetch` + `useSeoMeta` + JSON-LD + sitemap. This is the SSR/SEO core — get it indexable first.

**Phase 2 — auth**
Pinia auth store, login/register, `auth.client.ts` boot plugin, protected middleware, `/auth/me` hydration. Mind the §2 localStorage rules.

**Phase 3 — booking**
AvailabilityGrid → BookingSummary → create booking → status tracking. Wire reschedule/cancel.

**Phase 4 — social**
Matches board, then teams + challenges.

**Phase 5 — polish**
`@nuxt/image`, route rules/caching, policy pages, analytics events, Lighthouse pass, Search Console submission.

### This week
1. `nuxi init`, wire Nuxt UI + Tailwind, build the two layouts and `$api`.
2. Ship `/futsals` and `/futsals/[slug]` fully SSR with meta + JSON-LD against the (even mocked) venues API — proves the SEO pipeline end to end.
3. Generate TS types from the backend OpenAPI schema so the contract is locked.

---

## 12. Key packages

`nuxt`, `@nuxt/ui`, `@pinia/nuxt`, `pinia`, `@vueuse/nuxt`, `@nuxtjs/sitemap`, `@nuxtjs/robots`, `@nuxt/image`, `openapi-typescript` (dev), `vitest`, `@playwright/test`, `eslint`, `prettier`, `vue-tsc`.

---

*Note on your choices: full SSR + localStorage tokens means authenticated pages render their shell on the server and hydrate user data on the client (§2) — public SEO pages are unaffected and fully crawlable, which is the point of choosing SSR here. If you later want protected pages server-rendered with data, mirror the access token into an httpOnly cookie; the structure above already supports that without a rewrite.*
