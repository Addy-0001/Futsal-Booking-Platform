import { defineStore } from "pinia";

// JWT in localStorage via Pinia. localStorage is client-only — every access is
// guarded by import.meta.client, so SSR never touches it.
const ACCESS = "booksall_access";
const REFRESH = "booksall_refresh";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: null,
    refreshToken: null,
    user: null,
  }),

  getters: {
    isAuthenticated: (s) => !!s.accessToken,
  },

  actions: {
    /** Read tokens from localStorage on the client (called by the auth.client plugin). */
    hydrateFromStorage() {
      if (!import.meta.client) return;
      this.accessToken = localStorage.getItem(ACCESS);
      this.refreshToken = localStorage.getItem(REFRESH);
    },

    setTokens(access, refresh) {
      this.accessToken = access;
      this.refreshToken = refresh;
      if (import.meta.client) {
        localStorage.setItem(ACCESS, access);
        localStorage.setItem(REFRESH, refresh);
      }
    },

    setUser(user) {
      this.user = user;
    },

    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      if (import.meta.client) {
        localStorage.removeItem(ACCESS);
        localStorage.removeItem(REFRESH);
      }
    },
  },
});
