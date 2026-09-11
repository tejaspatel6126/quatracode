/**
 * api.js — Centralised API client.
 *
 * Rules:
 *  - All fetch() calls go through here — never scattered in page files.
 *  - Every request has an AbortController timeout.
 *  - 401 → redirect to login (centralised).
 *  - Never exposes secrets or tokens to localStorage.
 *  - JSON parse failures handled gracefully.
 */
'use strict';

const API_BASE   = '/api/v1';
const TIMEOUT_MS = 15_000;

const ApiClient = (() => {

  /* ── Core request ──────────────────────────────────────────────────────── */
  async function request(method, path, body = null, opts = {}) {
    const ctrl  = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), opts.timeout ?? TIMEOUT_MS);

    const headers = { 'Content-Type': 'application/json' };
    const init = { method, headers, signal: ctrl.signal, credentials: 'same-origin' };
    if (body !== null) init.body = JSON.stringify(body);

    let response, data;
    try {
      response = await fetch(`${API_BASE}${path}`, init);
      data = await response.json().catch(() => null);
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') return { ok: false, status: 0, data: null, error: 'Request timed out.' };
      return { ok: false, status: 0, data: null, error: 'Network error — check your connection.' };
    } finally {
      clearTimeout(timer);
    }

    // Centralised 401 handling → redirect to login
    if (response.status === 401 && !opts.skipAuthRedirect) {
      Auth.clearSession();
      window.location.href = '/login.html';
      return { ok: false, status: 401, data: null, error: 'Session expired.' };
    }

    return { ok: response.ok, status: response.status, data };
  }

  /* ── HTTP helpers ──────────────────────────────────────────────────────── */
  const get    = (path, opts)       => request('GET',    path, null, opts);
  const post   = (path, body, opts) => request('POST',   path, body, opts);
  const del    = (path, opts)       => request('DELETE', path, null, opts);

  /* ── Error message extractor ───────────────────────────────────────────── */
  function errorMessage(result) {
    if (result.error) return result.error;
    const d = result.data;
    if (!d) return `HTTP ${result.status}`;
    if (d.error?.message) return d.error.message;
    if (d.detail) {
      if (typeof d.detail === 'string') return d.detail;
      if (Array.isArray(d.detail)) return d.detail.map(e => e.msg || e).join('; ');
    }
    if (d.message) return d.message;
    return `HTTP ${result.status}`;
  }

  /* ── Auth endpoints ────────────────────────────────────────────────────── */
  const auth = {
    login:  (email, password) => post('/auth/login',  { email, password }, { skipAuthRedirect: true }),
    logout: ()                => post('/auth/logout',  {}, { skipAuthRedirect: true }),
    me:     ()                => get('/auth/me',            { skipAuthRedirect: true }),
  };

  /* ── Scan endpoints ────────────────────────────────────────────────────── */
  const scans = {
    create:    (target_url) => post('/scans',       { target_url }),
    get:       (id)         => get(`/scans/${id}`),
    results:   (id)         => get(`/scans/${id}/results`),
    aiSummary: (id)         => get(`/scans/${id}/ai-summary`, { timeout: 30_000 }),
    list:      (page = 1, per_page = 20) => get(`/scans?page=${page}&per_page=${per_page}`),
    cancel:    (id)         => del(`/scans/${id}`),
  };

  /* ── Health ────────────────────────────────────────────────────────────── */
  const health = {
    check: () => get('/health', { skipAuthRedirect: true }),
  };

  return { get, post, del, errorMessage, auth, scans, health };
})();
