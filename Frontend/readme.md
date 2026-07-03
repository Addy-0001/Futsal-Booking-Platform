# Booksall — Frontend (Nuxt 3, SSR)

Nuxt 3 SSR app for Booksall. See `../Documentation/FRONTEND_DESIGN.md` for the full design.

## Built so far

**Public + SEO (SSR):** landing, venue list (`/futsals`), venue detail (`/futsals/[slug]`)
with `useSeoMeta` + JSON-LD (`SportsActivityLocation`), custom error page, policy pages.

**Auth:** login, register, email verification, forgot/reset password — wired to the DRF
JWT endpoints. `composables/useAuth.ts` orchestrates; `composables/useApi.ts` injects the
token and silently refreshes once on 401. `stores/auth.ts` holds tokens in localStorage
(client-guarded). `plugins/auth.client.ts` restores the session on boot. `middleware/auth.ts`
protects the dashboard; `middleware/guest.ts` keeps signed-in users off auth pages.

**Booking:** `AvailabilityGrid` (reads `/api/availability/`), `CourtBooking` (court + date +
grid + confirm modal → `POST /api/bookings/`), integrated into the venue detail page
(client-only, so SSR/SEO is unaffected). `BookingStatusBadge` maps the backend lifecycle.

**Dashboard (protected):** `/dashboard/bookings` (list + cancel), `/dashboard/profile`.

**Venue staff (protected):** `/manage/approvals` (approve/reject pending bookings at venues
you manage), `/manage` (your venues + create), `/manage/[slug]` (add courts, operating
hours, dynamic price rules, and upload venue/court photos). Staff scope is filtered by
`my_role` / the booking's `futsal` id; the backend enforces the actual permissions.

**Matchmaking & teams:** `/matches` (browse open matches, host, join/leave/cancel),
`/teams` (browse + create), `/teams/[slug]` (squad, invite by email, accept/leave, and the
team-vs-team challenge flow: propose, accept/decline, record result).

**Images:** futsals and courts can each have multiple photos. Cards show a cover image,
the venue detail page shows a gallery + per-court thumbnails, and staff upload via multipart
on `/manage/[slug]`.

**Legal / support / analytics:** policy pages (`/privacy`, `/terms`, `/cookies`) render from
the backend `legal` app (versioned); a cookie-consent banner records consent; `/support` files
tickets to the backend; a client-only plugin sends page-view events to `/api/events/`.

## Design system

Bright, vibrant, photo-rich. White / soft-tint surfaces (`emerald-50`, `lime-50`) with
**emerald + lime** accents and a gradient CTA — no dark sections. Headings use **Space
Grotesk** (`font-display`), body **Inter** (Google Fonts in `nuxt.config.ts`). Tokens in
`app.config.ts` (`primary: emerald`) and `assets/css/main.css` (`.text-gradient`,
reduced-motion guard). Scroll/entrance motion via `@vueuse/motion` (`v-motion`).

### Imagery (Unsplash)
- `composables/useImages.ts` — a curated set of verified Unsplash futsal/football photos
  with a sizing helper (`stockImage`) and a deterministic `venueFallback(seed)` so every
  venue/court has a real photo even without an upload. Works with zero config.
- `server/api/unsplash.get.ts` + `NUXT_UNSPLASH_ACCESS_KEY` — optional dynamic Unsplash
  search (key stays server-side, results cached 1h). Without a key, the curated set is used.

The homepage is fully browsable logged-out (hero search, popular cities, featured futsals,
open matches, teams, testimonials, FAQ); booking/joining/creating redirect to sign-in.

## Setup

```bash
cd Frontend
cp .env.example .env       # point NUXT_PUBLIC_API_BASE at the Django API (default :8000)
npm install
npm run dev                # http://localhost:3000  (Django must be running on :8000)
```

Other scripts: `npm run build` (SSR build), `npm run preview`, `npm run typecheck`.

## Structure

```
nuxt.config.ts        modules, SSR, runtimeConfig (apiBase/siteUrl), robots, site
app.config.ts         Nuxt UI theme (primary = green)
composables/useApi.ts single $fetch wrapper (baseURL + JWT header injection)
stores/auth.ts        Pinia auth store (JWT in localStorage, client-guarded)
types/api.ts          domain types mirroring the DRF serializers
layouts/              default (public) + dashboard (authenticated shell)
components/venue/      VenueCard
pages/                index, futsals/index, futsals/[slug], policies, auth stubs
error.vue             custom error / 404 screen
```

## How data flows (SSR)

Public pages fetch via `useAsyncData` + `useApi()` so content is in the crawlable HTML.
The API base must be reachable from the Nuxt **server** during SSR (not just the browser).

## Notes on auth (next pass)

Tokens live in `localStorage` via Pinia — client-only, so SSR renders public pages
token-free (see FRONTEND_DESIGN §2). Authenticated/dashboard pages will render their
shell on the server and hydrate user data on the client. All `localStorage` access is
guarded by `import.meta.client`.

## Next

- Reschedule UI (backend endpoint already exists)
- Manage staff roles (grant owner/manager) on `/manage/[slug]`
- Dynamic sitemap entries sourced from the venues API
- Generate `types/api.ts` from the backend OpenAPI schema (`openapi-typescript`)
- Teams & matchmaking (after backend Phase 4)
