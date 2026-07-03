// Protects authenticated routes. Tokens are client-only (localStorage), so the
// check runs after hydration on the client and redirects guests to /login.
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    return navigateTo(`/login?next=${encodeURIComponent(to.fullPath)}`);
  }
});
