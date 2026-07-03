// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  ssr: true, // full SSR for SEO

  modules: [
    "@nuxt/ui",
    "@pinia/nuxt",
    "@vueuse/nuxt",
    "@vueuse/motion/nuxt",
    "@nuxt/image",
    "@nuxtjs/sitemap",
    "@nuxtjs/robots",
  ],

  css: ["~/assets/css/main.css"],

  // Register ~/components by filename only (no directory prefix), so nested
  // components resolve by their short name — e.g. components/booking/CourtBooking.vue
  // is <CourtBooking>, not <BookingCourtBooking>. Without this, the booking panel
  // and availability grid silently fail to resolve and never render.
  components: [{ path: "~/components", pathPrefix: false }],

  // Force the dark neon-lime theme everywhere.
  colorMode: {
    preference: "dark",
    fallback: "dark",
  },

  imports: {
    dirs: ["stores"],
  },

  runtimeConfig: {
    // Server-only. Optional — enables dynamic Unsplash image search.
    unsplashAccessKey: process.env.NUXT_UNSPLASH_ACCESS_KEY || "",
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || "http://localhost:3000",
    },
  },

  site: {
    url: process.env.NUXT_PUBLIC_SITE_URL || "http://localhost:3000",
    name: "Booksall",
  },

  robots: {
    disallow: ["/dashboard", "/manage", "/login", "/register", "/verify-email", "/reset-password"],
  },

  app: {
    head: {
      htmlAttrs: { lang: "en", class: "dark" },
      titleTemplate: "%s",
      meta: [{ name: "viewport", content: "width=device-width, initial-scale=1" }],
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&display=swap",
        },
      ],
    },
  },

  nitro: { compressPublicAssets: true },

  ui: { global: true },
});
