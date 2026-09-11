/**
 * scan.js — Scan page logic.
 *
 * Handles:
 *  - New scan form (with duplicate-submit prevention)
 *  - Controlled polling (max 120 iterations × 5s = 10 min)
 *  - Result rendering (risk score, findings, raw scanner data)
 *  - AI Explanation section (Phase 08)
 *  - Finding detail modal with AI explanations
 *  - XSS-safe rendering (textContent throughout)
 *  - Polling cleanup on page unload
 */
'use strict';

(async () => {
  /* ── Auth ───────────────────────────────────────────────────────────── */
  const user = await Auth.requireAuth();
  if (!user) return;
  UI.populateSidebarUser(user);
  UI.initSidebar();
  UI.$id('logout-btn').addEventListener('click', () => Auth.logout());

  /* ── Elements ───────────────────────────────────────────────────────── */
  const newSection    = UI.$id('new-scan-section');
  const statusSection = UI.$id('status-section');
  const resultsSection= UI.$id('results-section');
  const startBtn      = UI.$id('start-scan-btn');
  const targetInput   = UI.$id('target-url');
  const scanAlert     = UI.$id('scan-alert');
  const cancelBtn     = UI.$id('cancel-btn');
  const newScanBtn    = UI.$id('new-scan-btn');

  /* ── Routing: ?id= means show existing scan ─────────────────────────── */
  const params = new URLSearchParams(location.search);
  const scanId = params.get('id');

  if (scanId) {
    showScanById(scanId);
  } else {
    UI.show(newSection);
  }

  /* ── New scan form ──────────────────────────────────────────────────── */
  let submitting = false;

  startBtn?.addEventListener('click', async () => {
    if (submitting) return;
    UI.hideAlert(scanAlert);

    const url = targetInput?.value.trim() || '';
    if (!url) {
      UI.showAlert(scanAlert, 'Please enter a target URL.', 'error');
      targetInput?.focus();
      return;
    }
    if (!/^https?:\/\//i.test(url)) {
      UI.showAlert(scanAlert, 'URL must start with https:// or http://', 'error');
      targetInput?.focus();
      return;
    }

    submitting = true;
    startBtn.disabled = true;
    startBtn.classList.add('btn-loading');
    UI.setText(startBtn, 'Creating scan…');

    const r = await ApiClient.scans.create(url);

    submitting = false;
    startBtn.disabled = false;
    startBtn.classList.remove('btn-loading');
    UI.setText(startBtn, 'Start Scan');

    if (r.ok && (r.data?.data?.scan_id || r.data?.data?.id)) {
      const id = r.data.data.scan_id || r.data.data.id;
      history.replaceState(null, '', `?id=${encodeURIComponent(id)}`);
      UI.hide(newSection);
      showScanById(id);
    } else {
      const msg = ApiClient.errorMessage(r);
      UI.showAlert(scanAlert, mapApiError(msg), 'error');
    }
  });

  newScanBtn?.addEventListener('click', () => {
    stopPolling();
    history.replaceState(null, '', '/scan.html');
    UI.hide(statusSection);
    UI.hide(resultsSection);
    UI.show(newSection);
    if (targetInput) targetInput.value = '';
  });

  /* ── Polling ─────────────────────────────────────────────────────────── */
  const POLL_INTERVAL_MS = 4000;
  const POLL_MAX         = 150;   // 150 × 4s = 10 min max
  let pollTimer   = null;
  let pollCount   = 0;
  let currentScanId = null;

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }
  window.addEventListener('beforeunload', stopPolling);

  async function showScanById(id) {
    currentScanId = id;
    UI.hide(newSection);
    const scan = await fetchScanStatus(id);
    if (!scan) return;

    if (UI.isRunning(scan.status)) {
      renderStatusView(scan);
      startPolling(id);
    } else {
      await renderResults(id, scan);
    }
  }

  async function fetchScanStatus(id) {
    const r = await ApiClient.scans.get(id);
    if (!r.ok) {
      UI.show(newSection);
      UI.showAlert(scanAlert, `Scan not found: ${ApiClient.errorMessage(r)}`, 'error');
      return null;
    }
    return r.data?.data?.scan || r.data?.data || null;
  }

  function startPolling(id) {
    pollCount = 0;
    pollTimer = setInterval(async () => {
      pollCount++;
      if (pollCount > POLL_MAX) {
        stopPolling();
        UI.setText(UI.$id('status-text'), 'Scan is taking longer than expected. Refresh to check.');
        return;
      }
      const scan = await fetchScanStatus(id);
      if (!scan) { stopPolling(); return; }

      if (!UI.isRunning(scan.status)) {
        stopPolling();
        UI.hide(statusSection);
        await renderResults(id, scan);
      } else {
        renderStatusView(scan);
      }
    }, POLL_INTERVAL_MS);
  }

  function renderStatusView(scan) {
    UI.hide(newSection);
    UI.hide(resultsSection);
    UI.show(statusSection);

    const badgeWrap = UI.$id('status-badge-wrap');
    if (badgeWrap) {
      badgeWrap.replaceChildren(UI.statusBadge(scan.status));
    }
    UI.setText(UI.$id('status-text'), statusDescription(scan.status));
    UI.setText(UI.$id('status-target'), scan.target_url || scan.target_hostname || '');
  }

  function statusDescription(status) {
    const d = {
      created:      'Scan created, waiting to start…',
      validating:   'Validating target URL…',
      queued:       'Queued for scanning…',
      scanning:     'Scanning security configuration…',
      analyzing:    'Analysing results…',
      scoring:      'Calculating risk score…',
      ai_processing:'Generating AI explanations…',
    };
    return d[status] || `Status: ${status}`;
  }

  /* ── Cancel ──────────────────────────────────────────────────────────── */
  cancelBtn?.addEventListener('click', async () => {
    if (!currentScanId) return;
    stopPolling();
    cancelBtn.disabled = true;
    await ApiClient.scans.cancel(currentScanId);
    cancelBtn.disabled = false;
    window.location.href = '/history.html';
  });

  /* ── Render completed results ─────────────────────────────────────────── */
  // AI explanation data keyed by finding_code — populated after AI call
  let _aiExplanations = {};

  async function renderResults(id, scan) {
    UI.hide(newSection);
    UI.hide(statusSection);
    UI.show(resultsSection);

    // Page heading
    UI.setText(UI.$id('page-heading'), 'Scan Results');
    UI.setText(UI.$id('results-heading'), scan.target_hostname || scan.target_url || 'Results');
    UI.setText(UI.$id('results-meta'),
      `${UI.statusLabel(scan.status)} · ${UI.formatDate(scan.started_at)} · ${UI.duration(scan.started_at, scan.completed_at)}`
    );

    // Fetch full results
    const rr = await ApiClient.scans.results(id);
    const results = (rr.ok ? rr.data?.data : null) || {};
    const risk     = results.risk || {};
    const findings = results.findings || [];

    // Risk panel (backend values only — no JS calculation)
    renderRiskPanel(risk, scan);

    // Findings
    renderFindings(findings);

    // Raw scanner sections
    renderScannerDetails(results, scan);

    // AI Summary (Phase 08) — loaded async, won't block deterministic content
    renderAISummarySection(id, findings);
  }

  function renderRiskPanel(risk, scan) {
    const score    = risk.score ?? scan.security_score ?? null;
    const level    = risk.risk_level || scan.risk_level || null;
    const counts   = risk.severity_counts || {};

    const dial = UI.$id('risk-dial');
    if (dial && level) {
      dial.className = `risk-score-dial level-${(level||'').toLowerCase()}`;
    }
    UI.setText(UI.$id('risk-number'), score != null ? Math.round(score) : '—');
    UI.setText(UI.$id('risk-level-label'), UI.riskLevelLabel(level));
    UI.setText(UI.$id('risk-level-desc'),
      score != null ? `Overall risk score: ${Math.round(score)} / 100` : 'Score not yet available.'
    );

    // Severity counts
    const row = UI.$id('severity-row');
    if (row) {
      row.replaceChildren();
      [['CRITICAL','critical'],['HIGH','high'],['MEDIUM','medium'],['LOW','low'],['INFO','info']].forEach(([key, cls]) => {
        const n = counts[key] ?? (scan[`${cls}_count`] ?? 0);
        const wrap = document.createElement('div');
        wrap.className = 'sev-count';
        const dot = document.createElement('span');
        dot.className = `sev-dot ${cls}`; dot.setAttribute('aria-hidden','true');
        const label = document.createElement('span');
        label.className = 'sev-label'; label.textContent = key.charAt(0) + key.slice(1).toLowerCase();
        const num = document.createElement('span');
        num.className = 'sev-num'; num.textContent = n;
        wrap.appendChild(dot); wrap.appendChild(label); wrap.appendChild(num);
        row.appendChild(wrap);
      });
    }
  }

  function renderFindings(findings) {
    const container = UI.$id('findings-container');
    const countDesc = UI.$id('findings-count-desc');
    if (!container) return;

    UI.setText(countDesc, findings.length
      ? `${findings.length} finding${findings.length !== 1 ? 's' : ''} identified`
      : 'No findings — all checks passed.');

    if (!findings.length) {
      container.replaceChildren(
        UI.emptyState('✓', 'No findings', 'All security checks passed for this target.')
      );
      return;
    }

    const list = document.createElement('div');
    list.className = 'finding-list';

    findings.forEach(f => {
      const item = buildFindingItem(f);
      list.appendChild(item);
    });

    container.replaceChildren(list);
  }

  function buildFindingItem(f) {
    const sev = (f.severity || 'INFO').toLowerCase();
    const item = document.createElement('div');
    item.className = 'finding-item';
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');
    item.setAttribute('aria-label', `View details for: ${f.title}`);

    const bar = document.createElement('div');
    bar.className = `finding-sev-bar ${sev}`;

    const body = document.createElement('div');
    body.className = 'finding-body';

    const title = document.createElement('div');
    title.className = 'finding-title';
    title.textContent = f.title || f.finding_id || 'Finding'; // XSS-safe

    const meta = document.createElement('div');
    meta.className = 'finding-meta';
    meta.appendChild(UI.severityBadge(f.severity));
    const cat = document.createElement('span');
    cat.className = 'finding-category';
    cat.textContent = (f.category || '').replace(/_/g, ' ');
    meta.appendChild(cat);

    body.appendChild(title);
    body.appendChild(meta);

    const action = document.createElement('div');
    action.className = 'finding-action';
    const btn = document.createElement('button');
    btn.className = 'btn btn-ghost btn-sm';
    btn.textContent = 'Details';
    btn.setAttribute('aria-label', `View details for ${f.title}`);
    action.appendChild(btn);

    item.appendChild(bar);
    item.appendChild(body);
    item.appendChild(action);

    // Open modal
    const open = () => openFindingModal(f);
    item.addEventListener('click', open);
    item.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') open(); });

    return item;
  }

  /* ── Finding detail modal ─────────────────────────────────────────────── */
  const modal      = UI.$id('finding-modal');
  const modalClose = UI.$id('modal-close');
  const modalTitle = UI.$id('modal-title');
  const modalBody  = UI.$id('modal-body');

  modalClose?.addEventListener('click', closeModal);
  modal?.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  function closeModal() {
    if (modal) modal.classList.remove('open');
  }

  function openFindingModal(f) {
    if (!modal || !modalBody) return;
    UI.setText(modalTitle, f.title || 'Finding');

    modalBody.replaceChildren();

    // Header: badge + category
    const hdr = document.createElement('div');
    hdr.style.display = 'flex'; hdr.style.gap = 'var(--space-3)';
    hdr.style.marginBottom = 'var(--space-4)'; hdr.style.flexWrap = 'wrap';
    hdr.appendChild(UI.severityBadge(f.severity));
    const cat = document.createElement('span');
    cat.className = 'text-muted text-xs';
    cat.style.alignSelf = 'center';
    cat.textContent = (f.category || '').replace(/_/g, ' ');
    hdr.appendChild(cat);
    modalBody.appendChild(hdr);

    // Description
    if (f.description) {
      addSection(modalBody, 'Description', () => {
        const p = document.createElement('p');
        p.className = 'finding-description';
        p.textContent = f.description; // XSS-safe
        return p;
      });
    }

    // Evidence
    if (f.evidence?.length) {
      addSection(modalBody, 'Evidence', () => {
        const wrap = document.createElement('div');
        wrap.style.display = 'flex';
        wrap.style.flexDirection = 'column';
        wrap.style.gap = 'var(--space-2)';
        f.evidence.forEach(ev => {
          const box = document.createElement('div');
          box.className = 'evidence-box';
          box.textContent = ev.detail ? `${ev.observed}\n${ev.detail}` : ev.observed; // XSS-safe
          wrap.appendChild(box);
        });
        return wrap;
      });
    }

    // Remediation
    if (f.remediation) {
      addSection(modalBody, 'Recommended Remediation', () => {
        const box = document.createElement('div');
        box.className = 'remediation-box';
        box.textContent = f.remediation; // XSS-safe
        return box;
      });
    }

    // AI Explanation (Phase 08) — only if available
    const aiExpl = _aiExplanations[f.finding_id || f.check_id || ''];
    if (aiExpl) {
      addSection(modalBody, '🤖 AI Explanation', () => {
        const wrap = document.createElement('div');
        wrap.className = 'ai-explanation-block';

        const statusBadge = document.createElement('span');
        statusBadge.className = 'ai-status-badge';
        statusBadge.textContent = aiExpl.ai_status === 'GENERATED' ? 'AI-generated' : 'Deterministic fallback';
        wrap.appendChild(statusBadge);

        const fields = [
          ['Summary',        aiExpl.summary],
          ['Why it matters', aiExpl.why_it_matters],
          ['Potential impact', aiExpl.impact],
          ['Recommendation', aiExpl.recommendation],
          ['Plain language',  aiExpl.owner_explanation],
        ];
        fields.forEach(([label, text]) => {
          if (!text) return;
          const row = document.createElement('div');
          row.className = 'ai-field-row';
          const lbl = document.createElement('div');
          lbl.className = 'ai-field-label';
          lbl.textContent = label;  // XSS-safe
          const val = document.createElement('div');
          val.className = 'ai-field-value';
          val.textContent = text;   // XSS-safe — never innerHTML
          row.appendChild(lbl);
          row.appendChild(val);
          wrap.appendChild(row);
        });

        const disclaimer = document.createElement('p');
        disclaimer.className = 'ai-disclaimer';
        disclaimer.textContent = 'AI-generated explanation. Security findings and risk scores are determined by the security analysis engine.';
        wrap.appendChild(disclaimer);

        return wrap;
      });
    }

    // References
    if (f.references?.length) {
      addSection(modalBody, 'References', () => {
        const list = document.createElement('div');
        list.className = 'reference-list';
        f.references.forEach(ref => {
          list.appendChild(UI.safeLink(ref, ref)); // URL-safe
        });
        return list;
      });
    }

    modal.classList.add('open');
    modalClose?.focus();
  }

  function addSection(parent, label, contentFn) {
    const sec = document.createElement('div');
    sec.className = 'finding-section';
    sec.style.marginTop = 'var(--space-4)';
    sec.style.paddingTop = 'var(--space-4)';
    sec.style.borderTop = '1px solid var(--border)';
    const lbl = document.createElement('div');
    lbl.className = 'finding-section-label';
    lbl.textContent = label;
    sec.appendChild(lbl);
    sec.appendChild(contentFn());
    parent.appendChild(sec);
  }

  /* ── Raw scanner detail sections ──────────────────────────────────────── */
  function renderScannerDetails(results, scan) {
    const container = UI.$id('scanner-details');
    if (!container) return;
    container.replaceChildren();

    const raw = results.raw_observations || results.scanner_results || {};

    // TLS
    if (raw.tls?.available) addTlsSection(container, raw.tls);
    // Certificate
    if (raw.certificate?.available) addCertSection(container, raw.certificate);
    // Headers
    if (raw.headers?.available) addHeaderSection(container, raw.headers);
    // Cookies
    if (raw.cookies?.available && raw.cookies.cookies?.length) addCookieSection(container, raw.cookies);
    // Redirects
    if (raw.redirects?.available) addRedirectSection(container, raw.redirects);
    // Network (Nmap)
    if (raw.network?.available) addNetworkSection(container, raw.network);
  }

  function makeResultSection(iconText, titleText) {
    const sec = document.createElement('div');
    sec.className = 'result-section';
    const hdr = document.createElement('div');
    hdr.className = 'result-section-header';
    const icon = document.createElement('span');
    icon.className = 'result-section-icon'; icon.setAttribute('aria-hidden','true'); icon.textContent = iconText;
    const t = document.createElement('span');
    t.className = 'result-section-title'; t.textContent = titleText;
    hdr.appendChild(icon); hdr.appendChild(t);
    const body = document.createElement('div');
    body.className = 'result-section-body';
    sec.appendChild(hdr); sec.appendChild(body);
    return { sec, body };
  }

  function checkRow(label, value, cls = '') {
    const row = document.createElement('div');
    row.className = 'check-row';
    const l = document.createElement('span'); l.className = 'check-label'; l.textContent = label;
    const v = document.createElement('span'); v.className = `check-value ${cls}`; v.textContent = value;
    row.appendChild(l); row.appendChild(v);
    return row;
  }

  function addTlsSection(container, tls) {
    const { sec, body } = makeResultSection('🔒', 'TLS Protocol');
    body.appendChild(checkRow('TLS Version', tls.version || '—'));
    body.appendChild(checkRow('TLS 1.0', tls.tls_1_0 ? 'Supported' : 'Disabled',
      tls.tls_1_0 ? 'check-fail' : 'check-pass'));
    body.appendChild(checkRow('TLS 1.1', tls.tls_1_1 ? 'Supported' : 'Disabled',
      tls.tls_1_1 ? 'check-fail' : 'check-pass'));
    body.appendChild(checkRow('TLS 1.2', tls.tls_1_2 ? 'Supported' : 'Not detected',
      tls.tls_1_2 ? 'check-pass' : 'check-warn'));
    body.appendChild(checkRow('TLS 1.3', tls.tls_1_3 ? 'Supported' : 'Not detected',
      tls.tls_1_3 ? 'check-pass' : 'check-warn'));
    body.appendChild(checkRow('Cipher Suite', tls.cipher_suite || '—'));
    container.appendChild(sec);
  }

  function addCertSection(container, cert) {
    const { sec, body } = makeResultSection('📜', 'TLS Certificate');
    body.appendChild(checkRow('Subject CN', cert.subject?.commonName || '—'));
    body.appendChild(checkRow('Issuer',     cert.issuer?.commonName  || cert.issuer?.organizationName || '—'));
    body.appendChild(checkRow('Valid From', UI.formatDate(cert.not_before)));
    body.appendChild(checkRow('Valid Until',UI.formatDate(cert.not_after)));
    body.appendChild(checkRow('Days Remaining', cert.days_until_expiry != null ? `${cert.days_until_expiry} days` : '—',
      cert.days_until_expiry != null && cert.days_until_expiry < 30 ? 'check-warn' : 'check-pass'));
    body.appendChild(checkRow('Hostname Match', cert.hostname_validation === 'match' ? 'Valid' : cert.hostname_validation || '—',
      cert.hostname_validation === 'match' ? 'check-pass' : 'check-fail'));
    body.appendChild(checkRow('Self-Signed', cert.is_self_signed ? 'Yes' : 'No',
      cert.is_self_signed ? 'check-fail' : 'check-pass'));
    if (cert.san_domains?.length) {
      body.appendChild(checkRow('SANs', cert.san_domains.join(', ')));
    }
    container.appendChild(sec);
  }

  function addHeaderSection(container, headers) {
    const { sec, body } = makeResultSection('🛡', 'Security Headers');
    const checks = [
      ['HSTS',                headers.hsts?.present],
      ['Content-Security-Policy', headers.csp?.present],
      ['X-Content-Type-Options',  headers.x_content_type_options?.present],
      ['Frame Protection',        headers.frame_protection?.x_frame_options_present || headers.frame_protection?.csp_frame_ancestors_present],
      ['Referrer-Policy',         headers.referrer_policy?.present],
      ['Permissions-Policy',      headers.permissions_policy?.present],
    ];
    checks.forEach(([label, present]) => {
      body.appendChild(checkRow(label,
        present ? 'Present' : 'Missing',
        present ? 'check-pass' : 'check-fail'));
    });
    container.appendChild(sec);
  }

  function addCookieSection(container, cookies) {
    const { sec, body } = makeResultSection('🍪', `Cookies (${cookies.cookies.length})`);
    cookies.cookies.slice(0, 20).forEach(c => {
      const row = document.createElement('div');
      row.className = 'check-row';
      const name = document.createElement('span');
      name.className = 'check-label check-value'; name.style.fontFamily = 'var(--font-mono)';
      name.textContent = c.name; // XSS-safe
      const attrs = document.createElement('span');
      attrs.className = 'text-muted text-xs';
      attrs.style.display = 'flex'; attrs.style.gap = '0.4rem';
      [['Secure', c.secure], ['HttpOnly', c.http_only], ['SameSite', c.same_site]].forEach(([label, val]) => {
        const s = document.createElement('span');
        s.textContent = val ? `${label}${typeof val === 'string' && val !== 'true' ? '='+val : ''}` : '';
        if (!s.textContent) return;
        s.style.color = 'var(--low-text)';
        attrs.appendChild(s);
      });
      row.appendChild(name);
      row.appendChild(attrs);
      body.appendChild(row);
    });
    container.appendChild(sec);
  }

  function addRedirectSection(container, redirects) {
    const { sec, body } = makeResultSection('↩', 'Redirect Chain');
    body.appendChild(checkRow('HTTP→HTTPS Redirect',
      redirects.https_redirect_observed ? 'Yes' : 'No',
      redirects.https_redirect_observed ? 'check-pass' : 'check-fail'));
    body.appendChild(checkRow('Redirect Count', redirects.redirect_count ?? '—'));
    if (redirects.final_url) {
      body.appendChild(checkRow('Final URL', redirects.final_url));
    }
    container.appendChild(sec);
  }

  function addNetworkSection(container, network) {
    const { sec, body } = makeResultSection('🌐', 'Network Discovery');
    if (!network.ports?.length) {
      const p = document.createElement('p');
      p.className = 'text-muted text-sm';
      p.textContent = 'No open ports discovered on scanned port set.';
      body.appendChild(p);
    } else {
      const wrap = document.createElement('div');
      wrap.className = 'table-wrap port-table-wrap';
      const tbl = document.createElement('table');
      tbl.setAttribute('aria-label', 'Discovered ports');
      const hdr = tbl.createTHead().insertRow();
      ['Port', 'Protocol', 'State', 'Service'].forEach(h => {
        const th = document.createElement('th'); th.textContent = h; hdr.appendChild(th);
      });
      const tb = tbl.createTBody();
      network.ports.forEach(p => {
        const r = tb.insertRow();
        [p.port, p.protocol || 'tcp', p.state, p.service_name || '—'].forEach(v => {
          const td = r.insertCell(); td.textContent = v ?? '—'; // XSS-safe
        });
        if (p.state === 'open') r.cells[0].innerHTML = '';
        // rebuild port cell safely
        const portCell = r.cells[0];
        const pb = document.createElement('span');
        pb.className = 'port-badge'; pb.textContent = p.port;
        portCell.replaceChildren(pb);
      });
      wrap.appendChild(tbl);
      body.appendChild(wrap);
    }
    if (network.nmap_version) {
      const note = document.createElement('p');
      note.className = 'text-muted text-xs';
      note.style.marginTop = 'var(--space-2)';
      note.textContent = `Nmap ${network.nmap_version} · ${UI.formatDate(network.scanned_at)}`;
      body.appendChild(note);
    }
    container.appendChild(sec);
  }

  /* ── Error mapping ────────────────────────────────────────────────────── */
  function mapApiError(msg) {
    if (!msg) return 'An error occurred.';
    if (/private|internal|loopback|ssrf|blocked|unsafe/i.test(msg))
      return 'This target cannot be scanned. Only public HTTPS/HTTP URLs are supported.';
    if (/invalid url|malformed/i.test(msg))
      return 'The URL appears to be invalid. Check the format and try again.';
    if (/rate limit|429/i.test(msg))
      return 'Too many requests. Please wait a moment and try again.';
    return msg;
  }

})();
