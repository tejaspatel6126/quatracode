/**
 * ui.js — Shared UI utilities.
 *
 * XSS RULE: Use textContent / createElement — NEVER innerHTML with untrusted data.
 * URL RULE:  Validate scheme before building any <a> href.
 */
'use strict';

/* ── Safe DOM helpers ─────────────────────────────────────────────────────── */
const UI = (() => {

  /** Safely set element text content (XSS-safe). */
  function setText(el, text) {
    if (!el) return;
    el.textContent = text ?? '';
  }

  /** Get element by ID. */
  function $id(id) { return document.getElementById(id); }

  /** Show / hide element. */
  function show(el) { if (el) el.classList.remove('hidden'); }
  function hide(el) { if (el) el.classList.add('hidden'); }
  function toggle(el, visible) { visible ? show(el) : hide(el); }

  /* ── Alerts ──────────────────────────────────────────────────────────── */
  function showAlert(el, message, type = 'error') {
    if (!el) return;
    el.className = `alert alert-${type} visible`;
    el.textContent = message;
  }
  function hideAlert(el) {
    if (!el) return;
    el.className = 'alert';
    el.textContent = '';
  }

  /* ── Toast ───────────────────────────────────────────────────────────── */
  function toast(message, type = 'info', durationMs = 3500) {
    let container = $id('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = message;        // XSS-safe
    container.appendChild(t);
    setTimeout(() => t.remove(), durationMs);
  }

  /* ── Severity / status helpers ───────────────────────────────────────── */
  const SEV_CLASSES = { CRITICAL:'critical', HIGH:'high', MEDIUM:'medium', LOW:'low', INFO:'info' };
  const STATUS_CLASSES = {
    created:'queued', validating:'running', queued:'queued',
    scanning:'running', analyzing:'running', scoring:'running',
    ai_processing:'running', completed:'completed', failed:'failed', cancelled:'cancelled',
  };

  function severityBadge(severity) {
    const sev = (severity || '').toUpperCase();
    const cls = SEV_CLASSES[sev] || 'info';
    const span = document.createElement('span');
    span.className = `badge badge-${cls}`;
    span.textContent = sev || 'INFO';
    return span;
  }

  function statusBadge(status) {
    const cls = STATUS_CLASSES[status] || 'queued';
    const span = document.createElement('span');
    span.className = `badge badge-${cls}`;
    span.textContent = statusLabel(status);
    return span;
  }

  function statusLabel(status) {
    const labels = {
      created:'Created', validating:'Validating', queued:'Queued',
      scanning:'Running', analyzing:'Analysing', scoring:'Scoring',
      ai_processing:'Processing', completed:'Completed', failed:'Failed', cancelled:'Cancelled',
    };
    return labels[status] || (status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown');
  }

  function isRunning(status) {
    return ['created','validating','queued','scanning','analyzing','scoring','ai_processing'].includes(status);
  }

  /* ── Risk level helpers ──────────────────────────────────────────────── */
  function riskLevelClass(level) {
    return (level || '').toLowerCase().replace('_', '_');
  }
  function riskLevelLabel(level) {
    const map = { VERY_LOW:'Very Low', LOW:'Low', MEDIUM:'Medium', HIGH:'High', CRITICAL:'Critical' };
    return map[(level||'').toUpperCase()] || level || 'Unknown';
  }
  function riskColor(level) {
    const map = { CRITICAL:'var(--critical-text)', HIGH:'var(--high-text)', MEDIUM:'var(--medium-text)',
                  LOW:'var(--low-text)', VERY_LOW:'var(--low-text)' };
    return map[(level||'').toUpperCase()] || 'var(--text-primary)';
  }

  /* ── Date formatting ─────────────────────────────────────────────────── */
  function formatDate(iso) {
    if (!iso) return '—';
    try {
      return new Intl.DateTimeFormat('en-GB', { dateStyle:'medium', timeStyle:'short' }).format(new Date(iso));
    } catch { return iso; }
  }
  function duration(start, end) {
    if (!start || !end) return '—';
    const ms = new Date(end) - new Date(start);
    if (isNaN(ms) || ms < 0) return '—';
    const s = Math.floor(ms / 1000);
    if (s < 60) return `${s}s`;
    return `${Math.floor(s/60)}m ${s%60}s`;
  }

  /* ── URL safety ──────────────────────────────────────────────────────── */
  const SAFE_SCHEMES = new Set(['http:', 'https:']);
  function safeUrl(raw) {
    if (!raw || typeof raw !== 'string') return null;
    try {
      const u = new URL(raw);
      return SAFE_SCHEMES.has(u.protocol) ? raw : null;
    } catch { return null; }
  }
  function safeLink(raw, text) {
    const href = safeUrl(raw);
    if (!href) {
      const span = document.createElement('span');
      span.className = 'text-muted text-xs';
      span.textContent = '[unsafe URL]';
      return span;
    }
    const a = document.createElement('a');
    a.href    = href;
    a.target  = '_blank';
    a.rel     = 'noopener noreferrer';
    a.className = 'reference-link';
    a.textContent = text || href;   // XSS-safe
    return a;
  }

  /* ── Loading / empty states ──────────────────────────────────────────── */
  function loadingState(msg = 'Loading…') {
    const div = document.createElement('div');
    div.className = 'loading-state';
    const sp = document.createElement('span');
    sp.className = 'spinner';
    sp.setAttribute('aria-hidden', 'true');
    const t = document.createElement('span');
    t.textContent = msg;
    div.appendChild(sp); div.appendChild(t);
    return div;
  }
  function emptyState(icon, title, desc, actionEl) {
    const div = document.createElement('div');
    div.className = 'empty-state';
    div.innerHTML = ''; // we build manually
    const i = document.createElement('div');
    i.className = 'empty-state-icon'; i.setAttribute('aria-hidden','true'); i.textContent = icon;
    const h = document.createElement('div');
    h.className = 'empty-state-title'; h.textContent = title;
    const d = document.createElement('p');
    d.className = 'empty-state-desc';  d.textContent = desc;
    div.appendChild(i); div.appendChild(h); div.appendChild(d);
    if (actionEl) div.appendChild(actionEl);
    return div;
  }

  /* ── Sidebar mobile toggle ───────────────────────────────────────────── */
  function initSidebar() {
    const sidebar  = $id('sidebar');
    const overlay  = $id('sidebar-overlay');
    const toggle   = $id('menu-toggle');
    if (!sidebar || !overlay || !toggle) return;

    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('visible');
    });
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('visible');
    });
  }

  /* ── Populate sidebar user info ──────────────────────────────────────── */
  function populateSidebarUser(user) {
    const nameEl  = $id('sidebar-username');
    const emailEl = $id('sidebar-email');
    const avatarEl = $id('sidebar-avatar');
    if (!user) return;
    if (nameEl)   nameEl.textContent  = user.email?.split('@')[0] || 'User';
    if (emailEl)  emailEl.textContent = user.email || '';
    if (avatarEl) avatarEl.textContent = (user.email || 'U').charAt(0).toUpperCase();
  }

  return {
    $id, setText, show, hide, toggle,
    showAlert, hideAlert, toast,
    severityBadge, statusBadge, statusLabel, isRunning,
    riskLevelClass, riskLevelLabel, riskColor,
    formatDate, duration,
    safeUrl, safeLink,
    loadingState, emptyState,
    initSidebar, populateSidebarUser,
  };
})();
