/**
 * SecureAudit — Frontend API client foundation.
 *
 * Centralised fetch wrapper used by all pages.
 * No fetch() calls are scattered across HTML files.
 * All DOM updates use textContent — never innerHTML with untrusted data.
 */

'use strict';

// ── Configuration ─────────────────────────────────────────────────────────────
const API_CONFIG = {
  baseUrl: '/api/v1',
  timeoutMs: 10_000,
};

// ── Core API client ──────────────────────────────────────────────────────────
const ApiClient = (() => {

  /**
   * Perform a fetch with a timeout.
   * @param {string} path  - API path relative to baseUrl
   * @param {RequestInit} options
   * @returns {Promise<{ok: boolean, status: number, data: any}>}
   */
  async function request(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

    try {
      const response = await fetch(`${API_CONFIG.baseUrl}${path}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
      });

      const data = await response.json().catch(() => null);
      return { ok: response.ok, status: response.status, data };
    } catch (err) {
      if (err.name === 'AbortError') {
        return { ok: false, status: 0, data: null, error: 'Request timed out' };
      }
      return { ok: false, status: 0, data: null, error: 'Network error' };
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    /** GET /api/v1/health */
    getHealth() {
      return request('/health');
    },

    /** GET /api/v1/health/ready */
    getReady() {
      return request('/health/ready');
    },
  };
})();

// ── Status widget ─────────────────────────────────────────────────────────────
const StatusWidget = (() => {
  const card      = document.getElementById('status-card');
  const label     = document.getElementById('status-label');
  const detail    = document.getElementById('status-detail');

  function setState(state, labelText, detailText) {
    if (!card) return;
    card.className = `status-card ${state}`;
    // Safe DOM APIs — never innerHTML with untrusted data
    if (label)  label.textContent  = labelText;
    if (detail) detail.textContent = detailText;
  }

  async function check() {
    setState('checking', 'Checking API status\u2026', '');

    const result = await ApiClient.getHealth();

    if (result.ok && result.data?.success) {
      setState('ok', '\u2713 API is healthy', `HTTP ${result.status} \u00B7 GET /api/v1/health`);
    } else {
      const msg = result.error || `HTTP ${result.status}`;
      setState('error', '\u26A0 API is unavailable', msg);
    }
  }

  return { check };
})();

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  StatusWidget.check();
});
