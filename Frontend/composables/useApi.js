// Single API wrapper. Pages/components never call $fetch raw — always useApi().
// Attaches the JWT when present, and silently refreshes once on a 401 (rotating
// refresh tokens), de-duplicating concurrent refreshes.
let refreshing = null;

export const useApi = () => {
  const config = useRuntimeConfig();
  const auth = useAuthStore();

  const raw = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (auth.accessToken) {
        const headers = new Headers(options.headers);
        headers.set("Authorization", `Bearer ${auth.accessToken}`);
        options.headers = headers;
      }
    },
  });

  async function doRefresh() {
    if (!auth.refreshToken) return false;
    try {
      const data = await raw("/api/auth/refresh/", {
        method: "POST",
        body: { refresh: auth.refreshToken },
      });
      auth.setTokens(data.access, data.refresh ?? auth.refreshToken);
      return true;
    } catch {
      auth.logout();
      return false;
    }
  }

  return async function api(url, opts = {}) {
    try {
      return await raw(url, opts);
    } catch (err) {
      const status = err?.response?.status ?? err?.statusCode;
      const isAuthCall = String(url).includes("/api/auth/");
      if (status === 401 && auth.refreshToken && !isAuthCall) {
        refreshing = refreshing ?? doRefresh();
        const ok = await refreshing;
        refreshing = null;
        if (ok) return await raw(url, opts);
      }
      throw err;
    }
  };
};

/** Pull a readable message out of the DRF uniform error envelope. */
export function apiErrorMessage(err, fallback = "Something went wrong.") {
  const detail = err?.data?.error?.detail ?? err?.response?._data?.error?.detail;
  if (!detail) return err?.data?.detail || fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return String(detail[0]);
  if (typeof detail === "object") {
    const first = Object.values(detail)[0];
    return Array.isArray(first) ? String(first[0]) : String(first);
  }
  return fallback;
}
