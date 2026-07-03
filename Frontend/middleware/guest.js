// Keeps already-authenticated users off the login/register pages.
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (auth.isAuthenticated) {
    const next = to.query.next || "/dashboard/bookings";
    return navigateTo(next);
  }
});
