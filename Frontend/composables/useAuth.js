// Orchestrates auth API calls and keeps the Pinia store in sync.
export const useAuth = () => {
  const auth = useAuthStore();
  const api = useApi();

  async function login(email, password) {
    const data = await api("/api/auth/login/", {
      method: "POST",
      body: { email, password },
    });
    auth.setTokens(data.access, data.refresh);
    auth.setUser(data.user);
    return data;
  }

  async function register(payload) {
    return api("/api/auth/register/", { method: "POST", body: payload });
  }

  async function fetchMe() {
    const user = await api("/api/auth/me/");
    auth.setUser(user);
    return user;
  }

  async function logout() {
    try {
      if (auth.refreshToken) {
        await api("/api/auth/logout/", { method: "POST", body: { refresh: auth.refreshToken } });
      }
    } catch {
      // ignore — we clear locally regardless
    }
    auth.logout();
  }

  async function requestPasswordReset(email) {
    return api("/api/auth/password-reset/", { method: "POST", body: { email } });
  }

  async function confirmPasswordReset(uid, token, new_password) {
    return api("/api/auth/password-reset/confirm/", {
      method: "POST",
      body: { uid, token, new_password },
    });
  }

  async function verifyEmail(uid, token) {
    return api("/api/auth/verify-email/", { method: "POST", body: { uid, token } });
  }

  return {
    login,
    register,
    fetchMe,
    logout,
    requestPasswordReset,
    confirmPasswordReset,
    verifyEmail,
  };
};
