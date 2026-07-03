// Optional dynamic Unsplash search proxy.
// Set NUXT_UNSPLASH_ACCESS_KEY to enable; otherwise the frontend falls back to the
// curated set in composables/useImages.js. Keeps the access key server-side only.
const cache = new Map();
const TTL = 1000 * 60 * 60; // 1h

export default defineEventHandler(async (event) => {
  const { unsplashAccessKey } = useRuntimeConfig();
  const { query = "futsal", count = "12" } = getQuery(event);

  if (!unsplashAccessKey) {
    return { configured: false, results: [] };
  }

  const key = `${query}:${count}`;
  const hit = cache.get(key);
  if (hit && Date.now() - hit.at < TTL) return hit.data;

  try {
    const res = await $fetch("https://api.unsplash.com/search/photos", {
      query: { query, per_page: count, orientation: "landscape", content_filter: "high" },
      headers: { Authorization: `Client-ID ${unsplashAccessKey}` },
    });
    const data = {
      configured: true,
      results: (res.results || []).map((p) => ({
        url: p.urls?.regular,
        thumb: p.urls?.small,
        alt: p.alt_description || query,
        credit: p.user?.name,
        creditUrl: p.user?.links?.html,
      })),
    };
    cache.set(key, { at: Date.now(), data });
    return data;
  } catch {
    return { configured: true, results: [], error: true };
  }
});
