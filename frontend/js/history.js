/**
 * history.js — Scan history with backend pagination.
 *
 * Rules:
 *  - Uses backend pagination — never downloads full history.
 *  - textContent throughout (XSS-safe).
 *  - Handles loading, empty, error states.
 */
'use strict';

(async () => {
  const user = await Auth.requireAuth();
  if (!user) return;
  UI.populateSidebarUser(user);
  UI.initSidebar();
  UI.$id('logout-btn').addEventListener('click', () => Auth.logout());

  const container  = UI.$id('history-container');
  const alertEl    = UI.$id('history-alert');
  const prevBtn    = UI.$id('prev-btn');
  const nextBtn    = UI.$id('next-btn');
  const pageInfo   = UI.$id('pagination-info');
  const countEl    = UI.$id('history-count');

  const PER_PAGE = 20;
  let currentPage = 1;
  let totalPages  = 1;

  prevBtn.addEventListener('click', () => { if (currentPage > 1) loadPage(currentPage - 1); });
  nextBtn.addEventListener('click', () => { if (currentPage < totalPages) loadPage(currentPage + 1); });

  await loadPage(1);

  async function loadPage(page) {
    container.replaceChildren(UI.loadingState('Loading scan history…'));
    UI.hideAlert(alertEl);

    const r = await ApiClient.scans.list(page, PER_PAGE);

    if (!r.ok) {
      UI.showAlert(alertEl, `Failed to load history: ${ApiClient.errorMessage(r)}`, 'error');
      container.replaceChildren();
      return;
    }

    const scans = r.data?.data?.scans || [];
    const meta  = r.data?.data?.meta  || {};
    const total     = meta.total      || scans.length;
    totalPages       = meta.total_pages || Math.ceil(total / PER_PAGE) || 1;
    currentPage      = meta.page        || page;

    // Count label
    UI.setText(countEl, total ? `${total} scan${total !== 1 ? 's' : ''}` : '');

    // Pagination controls
    UI.setText(pageInfo, total
      ? `Page ${currentPage} of ${totalPages}`
      : '');
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    if (!scans.length) {
      const cta = document.createElement('a');
      cta.href = '/scan.html'; cta.className = 'btn btn-primary btn-sm';
      cta.textContent = 'Start your first scan';
      container.replaceChildren(
        UI.emptyState('📋', 'No scans yet', 'Your scan history will appear here.', cta)
      );
      return;
    }

    container.replaceChildren(buildTable(scans));
  }

  function buildTable(scans) {
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap';

    const tbl = document.createElement('table');
    tbl.setAttribute('aria-label', 'Scan history');

    const thead = tbl.createTHead();
    const hrow  = thead.insertRow();
    ['Target', 'Status', 'Risk Score', 'Findings', 'Started', 'Duration', ''].forEach(h => {
      const th = document.createElement('th'); th.textContent = h; hrow.appendChild(th);
    });

    const tbody = tbl.createTBody();
    scans.forEach(scan => {
      const row = tbody.insertRow();
      row.style.cursor = 'pointer';
      const href = `/scan.html?id=${encodeURIComponent(scan.scan_id || scan.id)}`;
      row.addEventListener('click', () => { window.location.href = href; });

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
        const s = document.createElement('span');
        s.style.fontWeight = '600';
        s.style.color = UI.riskColor(scan.risk_level);
        s.textContent = `${Math.round(scan.security_score)} / 100`;
        td2.appendChild(s);
      } else { td2.textContent = '—'; }

      // Findings
      const td3 = row.insertCell();
      td3.textContent = scan.total_findings ?? '—';

      // Started
      const td4 = row.insertCell();
      td4.textContent = UI.formatDate(scan.started_at || scan.created_at);
      td4.style.color = 'var(--text-muted)'; td4.style.fontSize = '0.8rem';

      // Duration
      const td5 = row.insertCell();
      td5.textContent = UI.duration(scan.started_at, scan.completed_at);
      td5.style.color = 'var(--text-muted)'; td5.style.fontSize = '0.8rem';

      // View link
      const td6 = row.insertCell();
      const a = document.createElement('a');
      a.href = href; a.className = 'btn btn-ghost btn-sm';
      a.textContent = 'View';
      a.addEventListener('click', e => e.stopPropagation());
      td6.appendChild(a);
    });

    wrap.appendChild(tbl);
    return wrap;
  }
})();
