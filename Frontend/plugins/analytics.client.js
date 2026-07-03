// Fire-and-forget first-party page-view tracking. Client-only.
export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();
  const auth = useAuthStore();
  const router = useRouter();

  function sessionId() {
    let s = localStorage.getItem("booksall_sid");
    if (!s) {
      s = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
      localStorage.setItem("booksall_sid", s);
    }
    return s;
  }

  function track(path) {
    const headers = {};
    if (auth.accessToken) headers.Authorization = `Bearer ${auth.accessToken}`;
    $fetch(`${config.public.apiBase}/api/events/`, {
      method: "POST",
      headers,
      body: { name: "page_view", path, session_id: sessionId() },
    }).catch(() => {});
  }

  router.afterEach((to) => track(to.fullPath));
  track(router.currentRoute.value.fullPath);
});
