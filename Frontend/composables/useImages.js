// Curated, verified Unsplash photo IDs (futsal / football / pitch).
const ACTION = [
  "1509077613385-f89402467146",
  "1630420598913-44208d36f9af",
  "1676444920926-c8a084ec4003",
  "1622862259519-f6aab1c6168a",
  "1606925797300-0b35e9d1794e",
  "1544698310-74ea9d1c8258",
];

const COURTS = [
  "1521217078329-f8fc1becab68",
  "1553627220-92f0446b6a5f",
  "1630420598771-dd52ab08c8cb",
];

const DETAIL = [
  "1587384474964-3a06ce1ce699",
  "1702467430182-f955bb8ced5b",
  "1529900672901-908be5302554",
];

const ALL = [...ACTION, ...COURTS, ...DETAIL];

/** Build a sized, optimized Unsplash CDN URL. */
export function stockImage(id, w = 800, h, q = 80) {
  const dims = `w=${w}${h ? `&h=${h}` : ""}`;
  return `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&q=${q}&${dims}`;
}

/** Stable pick from a pool, seeded by a string (e.g. venue id) so it doesn't flicker. */
function pick(pool, seed = "") {
  let n = 0;
  for (let i = 0; i < seed.length; i++) n = (n + seed.charCodeAt(i)) % pool.length;
  return pool[n];
}

export const useImages = () => ({
  stockImage,
  action: (i = 0, w = 1200, h) => stockImage(ACTION[i % ACTION.length], w, h),
  court: (i = 0, w = 1200, h) => stockImage(COURTS[i % COURTS.length], w, h),
  detail: (i = 0, w = 1200, h) => stockImage(DETAIL[i % DETAIL.length], w, h),
  venueFallback: (seed = "", w = 800, h = 500) =>
    stockImage(pick([...COURTS, ...ACTION], seed), w, h),
  all: ALL,
});
