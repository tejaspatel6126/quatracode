/**
 * auth.js — Client-side authentication state.
 *
 * Rules:
 *  - Follows HttpOnly cookie architecture — JS reads no raw token.
 *  - Only non-sensitive display data (email, id) stored in sessionStorage.
 *  - On 401 → clear session + redirect (handled in api.js).
 *  - All protected pages call Auth.requireAuth() on load.
 */
'use strict';

const Auth = (() => {
  const SESSION_KEY = 'sa_user';

  function saveSession(user) {
    // Only store safe display info — never passwords, tokens, or cookies
    const safe = { id: user.id, email: user.email };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(safe));
  }

  function getSession() {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
  }

  /** Redirect to login if backend reports no active session. */
  async function requireAuth() {
    const result = await ApiClient.auth.me();
    if (!result.ok || !result.data?.data?.user) {
      clearSession();
      window.location.href = '/login.html';
      return null;
    }
    const user = result.data.data.user;
    saveSession(user);
    return user;
  }

  /** Login flow — returns { ok, error } */
  async function login(email, password) {
    const result = await ApiClient.auth.login(email, password);
    if (result.ok && result.data?.data?.user) {
      saveSession(result.data.data.user);
      return { ok: true };
    }
    return { ok: false, error: ApiClient.errorMessage(result) };
  }

  /** Logout flow */
  async function logout() {
    await ApiClient.auth.logout();
    clearSession();
    window.location.href = '/login.html';
  }

  return { requireAuth, login, logout, getSession, saveSession, clearSession };
})();
