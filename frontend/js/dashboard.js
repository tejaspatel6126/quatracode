/**
 * dashboard.js — Dashboard page logic.
 *
 * Rules:
 *  - Risk scores and severities come from backend only.
 *  - No client-side calculations.
 *  - Controlled polling on in-progress scans (max iterations, cleanup).
 *  - textContent only for untrusted data (XSS-safe).
 */
'use strict';

(async () => {
  /* ── Auth guard ─────────────────────────────────────────────────────── */
  const user = await Auth.requireAuth();
  if (!user) return;
  UI.populateSidebarUser(user);
  UI.initSidebar();

  UI.$id('logout-btn').addEventListener('click', () => Auth.logout());

  /* ── Quick scan form ────────────────────────────────────────────────── */
  const qBtn   = UI.$id('quick-scan-btn');
  const qUrl   = UI.$id('quick-url');
  const qAlert = UI.$id('quick-alert');
  let   submitting = false;

  qBtn.addEventListener('click', async () => {
    if (submitting) return;
    UI.hideAlert(qAlert);

    const url = qUrl.value.trim();
    if (!url) {
      UI.showAlert(qAlert, 'Please enter a target URL.', 'error');
      qUrl.focus();
      return;
    }
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      UI.showAlert(qAlert, 'URL must start with http:// or https://', 'error');
      qUrl.focus();
      return;
    }

    submitting = true;
    qBtn.disabled = true;
    qBtn.classList.add('btn-loading');
    UI.setText(qBtn, 'Creating scan…');

    const r = await ApiClient.scans.create(url);

    submitting = false;
    qBtn.disabled = false;
    qBtn.classList.remove('btn-loading');
    UI.setText(qBtn, 'Start Scan');

    if (r.ok && r.data?.data?.scan_id) {
      const id = r.data.data.scan_id;
      window.location.href = `/scan.html?id=${encodeURIComponent(id)}`;
    } else {
      UI.showAlert(qAlert, ApiClient.errorMessage(r), 'error');
    }
  });

  /* ── Load recent scans ──────────────────────────────────────────────── */
  await loadRecentScans();

  async function loadRecentScans() {
    const container = UI.$id('recent-scans-container');
    const r = await ApiClient.scans.list(1, 10);

    if (!r.ok) {
      container.replaceChildren(
        UI.emptyState('⚠', 'Could not load scans', ApiClient.errorMessage(r))
      );
      return;
    }

    const scans = r.data?.data?.scans || [];
    const meta  = r.data?.data?.meta  || {};

    // Stats
    updateStats(meta);

    if (!scans.length) {
      const cta = document.createElement('a');
      cta.href = '/scan.html'; cta.className = 'btn btn-primary btn-sm';
      cta.textContent = 'Start your first scan';
      container.replaceChildren(
        UI.emptyState('🔍', 'No scans yet', 'Run a security scan to see results here.', cta)
      );
      return;
    }

    container.replaceChildren(buildScansTable(scans));
  }

  function updateStats(meta) {
    UI.setText(UI.$id('stat-total'),     meta.total ?? '—');
    UI.setText(UI.$id('stat-completed'), meta.completed ?? '—');
    UI.setText(UI.$id('stat-running'),   meta.running ?? '—');
    UI.setText(UI.$id('stat-failed'),    meta.failed ?? '—');
  }

  function buildScansTable(scans) {
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap';

    const tbl = document.createElement('table');
    tbl.setAttribute('aria-label', 'Recent scans');

    // Header
    const thead = tbl.createTHead();
    const hrow  = thead.insertRow();
    ['Target', 'Status', 'Risk', 'Findings', 'Started', ''].forEach(h => {
      const th = document.createElement('th');
      th.textContent = h;
      hrow.appendChild(th);
    });

    // Body
    const tbody = tbl.createTBody();
    scans.forEach(scan => {
      const row = tbody.insertRow();
      row.style.cursor = 'pointer';
      row.addEventListener('click', () => {
        window.location.href = `/scan.html?id=${encodeURIComponent(scan.scan_id || scan.id)}`;
      });

      // Target
      const td0 = row.insertCell();
      td0.style.fontFamily = 'var(--font-mono)';
      td0.style.fontSize   = '0.8rem';
      td0.textContent = scan.target_hostname || scan.target_url || '—';

      // Status
      const td1 = row.insertCell();
      td1.appendChild(UI.statusBadge(scan.status));

      // Risk
      const td2 = row.insertCell();
      if (scan.security_score != null) {
        const score = document.createElement('span');
        score.style.fontWeight = '600';
        score.style.color = UI.riskColor(scan.risk_level);
        score.textContent = `${Math.round(scan.security_score)} / 100`;
        td2.appendChild(score);
      } else { td2.textContent = '—'; }

      // Findings
      const td3 = row.insertCell();
      td3.textContent = scan.total_findings ?? '—';

      // Date
      const td4 = row.insertCell();
      td4.textContent = UI.formatDate(scan.started_at || scan.created_at);
      td4.style.color = 'var(--text-muted)';
      td4.style.fontSize = '0.8125rem';

      // Link
      const td5 = row.insertCell();
      const a = document.createElement('a');
      a.href = `/scan.html?id=${encodeURIComponent(scan.scan_id || scan.id)}`;
      a.className = 'btn btn-ghost btn-sm';
      a.textContent = 'View';
      a.addEventListener('click', e => e.stopPropagation());
      td5.appendChild(a);
    });

    wrap.appendChild(tbl);
    return wrap;
  }
})();
