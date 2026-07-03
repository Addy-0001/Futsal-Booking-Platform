// Runs once on client boot: restore tokens from localStorage and load the user.
// Client-only (.client suffix) because localStorage doesn't exist during SSR.
export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  auth.hydrateFromStorage();
  if (auth.accessToken && !auth.user) {
    try {
      await useAuth().fetchMe();
    } catch {
      auth.logout();
    }
  }
});
