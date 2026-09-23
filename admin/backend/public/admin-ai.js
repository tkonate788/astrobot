/* ════════════════════════════════════════════════════════════════════
   ASTROBOT ADMIN — "AI Provider" page
   Depends on admin.js globals: req(), toast(), escapeHtml(), $()
   ════════════════════════════════════════════════════════════════════ */
(function () {
  const state = { catalog: [], engines: [], active: null, settings: null, modal: null };

  const byId = (id) => state.catalog.find((p) => p.id === id) || null;
  const fmtDate = (d) => (d ? new Date(d).toLocaleString() : '—');

  function logo(p, size) {
    const s = size || 40;
    if (!p) return `<div class="ai-logo" style="width:${s}px;height:${s}px;background:#334155">?</div>`;
    return `<div class="ai-logo" style="width:${s}px;height:${s}px;background:${p.color}">${escapeHtml(p.badge)}</div>`;
  }
  function n8nLogo(size) {
    const s = size || 40;
    return `<div class="ai-logo" style="width:${s}px;height:${s}px;background:#ea4b71">n8n</div>`;
  }
  function engineLogo(e, size) {
    return e.provider === 'n8n' ? n8nLogo(size) : logo(byId(e.provider), size);
  }
  function engineName(e) {
    if (e.provider === 'n8n') return 'n8n (existing workflow — fallback)';
    const p = byId(e.provider);
    return e.label && e.label !== (p && p.label) ? e.label : (p ? p.label : e.provider);
  }
  function testLine(e) {
    if (e.last_test_ok === true) return `<div class="ai-status ok">&#10003; Last test passed <span class="ai-muted">· ${fmtDate(e.last_test_at)}</span></div>`;
    if (e.last_test_ok === false) return `<div class="ai-status err">&#10007; ${escapeHtml(e.last_test_error || 'Test failed')}</div>`;
    return `<div class="ai-status muted">Not tested yet</div>`;
  }

  // ── data ───────────────────────────────────────────────────────────
  async function load() {
    const [cat, eng, set, rec] = await Promise.all([
      req('/ai/catalog'), req('/ai/engines'), req('/ai/settings'), req('/ai/recent'),
    ]);
    if (cat && cat.success) state.catalog = cat.providers;
    if (eng && eng.success) { state.engines = eng.engines; state.active = eng.active; }
    if (set && set.success) state.settings = set;
    render();
    renderRecent(rec && rec.success ? rec.items : []);
  }
  async function reloadEngines() {
    const eng = await req('/ai/engines');
    if (eng && eng.success) { state.engines = eng.engines; state.active = eng.active; render(); }
  }

  // ── render ─────────────────────────────────────────────────────────
  function render() {
    renderCurrent();
    renderEngines();
    renderCatalog();
    renderFallback();
    renderPrompt();
  }

  function renderCurrent() {
    const a = state.active;
    const el = $('aiCurrent');
    if (!a) {
      el.innerHTML = `<div class="ai-current-label">ENGINE IN USE RIGHT NOW</div>
        <div class="ai-current-row"><div class="ai-current-name">No engine selected</div>
        <span class="pill pill-suspended">chat offline</span></div>`;
      return;
    }
    el.innerHTML = `
      <div class="ai-current-label">ENGINE IN USE RIGHT NOW</div>
      <div class="ai-current-row">
        ${engineLogo(a, 48)}
        <div class="ai-current-text">
          <div class="ai-current-name">${escapeHtml(engineName(a))}</div>
          <div class="ai-current-model">${escapeHtml(a.model || (a.provider === 'n8n' ? 'Mistral via n8n workflow' : '—'))}</div>
        </div>
        <span class="pill pill-active">in service</span>
      </div>`;
  }

  function engineRow(e) {
    const p = byId(e.provider);
    const meta = [];
    if (e.model) meta.push(`<span>${escapeHtml(e.model)}</span>`);
    if (e.key_hint) meta.push(`<span>key ${escapeHtml(e.key_hint)}</span>`);
    if (e.base_url && p && p.baseUrlEditable) meta.push(`<span>${escapeHtml(e.base_url)}</span>`);
    if (e.provider === 'n8n') meta.push(`<span>${escapeHtml(e.base_url || 'N8N_WEBHOOK from env')}</span>`);
    return `
      <div class="ai-engine ${e.is_active ? 'is-active' : ''}" data-id="${e.id}">
        ${engineLogo(e, 44)}
        <div class="ai-engine-body">
          <div class="ai-engine-title">${escapeHtml(engineName(e))}
            ${e.is_active ? '<span class="pill pill-active">in service</span>' : ''}</div>
          <div class="ai-engine-meta">${meta.join('<i>·</i>')}</div>
          ${testLine(e)}
        </div>
        <div class="ai-engine-actions">
          <button class="btn btn-ghost btn-sm" data-act="test" data-id="${e.id}">&#9889; Test</button>
          ${e.is_active ? '' : `<button class="btn btn-primary btn-sm" data-act="use" data-id="${e.id}">&#10003; Use this one</button>`}
          <button class="row-icon-btn" title="Edit" data-act="edit" data-id="${e.id}">&#9998;</button>
          ${e.provider === 'n8n' ? '' : `<button class="row-icon-btn danger" title="Remove" data-act="del" data-id="${e.id}">&#128465;</button>`}
        </div>
      </div>`;
  }

  function renderEngines() {
    const list = state.engines.filter((e) => e.provider !== 'n8n');
    $('aiEngines').innerHTML = list.length
      ? list.map(engineRow).join('')
      : `<div class="ai-empty">No provider configured yet — the chat runs on the n8n fallback. Add one below.</div>`;
  }

  function renderFallback() {
    const n8n = state.engines.find((e) => e.provider === 'n8n');
    $('aiFallback').innerHTML = n8n ? engineRow(n8n) : '';
  }

  function renderCatalog() {
    $('aiCatalog').innerHTML = state.catalog.map((p) => `
      <button class="ai-card" data-provider="${p.id}">
        ${logo(p, 40)}
        <div class="ai-card-text">
          <div class="ai-card-name">${escapeHtml(p.label)}</div>
          <div class="ai-card-sub">${p.keyRequired ? 'API key required' : 'Free, no key'}</div>
        </div>
        <span class="ai-card-plus">+</span>
      </button>`).join('');
  }

  function renderPrompt() {
    const s = state.settings;
    if (!s) return;
    const ta = $('aiPromptText');
    ta.value = s.system_prompt || s.default_prompt || '';
    $('aiPromptState').textContent = s.system_prompt
      ? 'Custom prompt · saved ' + fmtDate(s.updated_at)
      : 'Default prompt (same contract as the n8n workflow)';
  }

  function renderRecent(items) {
    const tb = $('aiRecentBody');
    if (!items.length) { tb.innerHTML = '<tr><td colspan="4" class="ai-muted">No conversation yet.</td></tr>'; return; }
    tb.innerHTML = items.map((c) => `
      <tr>
        <td>${escapeHtml((c.name || '') + ' ' + (c.surname || '')).trim() || escapeHtml(c.email || '—')}</td>
        <td class="ai-ellipsis" title="${escapeHtml(c.message)}">${escapeHtml(String(c.message || '').slice(0, 90))}</td>
        <td><code class="ai-code">${escapeHtml(c.engine || 'n8n')}</code></td>
        <td class="ai-muted">${fmtDate(c.created_at)}</td>
      </tr>`).join('');
  }

  // ── actions ────────────────────────────────────────────────────────
  async function testEngine(id, btn) {
    const old = btn.innerHTML; btn.disabled = true; btn.innerHTML = 'Testing…';
    const r = await req(`/ai/engines/${id}/test`, { method: 'POST' });
    btn.disabled = false; btn.innerHTML = old;
    if (r && r.success) {
      toast(r.test.ok ? `Test passed in ${r.test.ms} ms` : 'Test failed: ' + r.test.error, r.test.ok ? 'success' : 'error');
      await reloadEngines();
    } else toast((r && r.error) || 'Test failed', 'error');
  }
  async function useEngine(id) {
    const r = await req(`/ai/engines/${id}/activate`, { method: 'POST' });
    if (r && r.success) { toast('Engine switched — applies to the next message', 'success'); await reloadEngines(); }
    else toast((r && r.error) || 'Could not switch', 'error');
  }
  async function deleteEngine(id) {
    const e = state.engines.find((x) => x.id === id);
    if (!confirm(`Remove "${engineName(e)}"?${e.is_active ? ' The chat will fall back to n8n.' : ''}`)) return;
    const r = await req(`/ai/engines/${id}`, { method: 'DELETE' });
    if (r && r.success) { toast('Engine removed', 'info'); await reloadEngines(); }
    else toast((r && r.error) || 'Could not remove', 'error');
  }

  $('aiEngines').addEventListener('click', onEngineAction);
  $('aiFallback').addEventListener('click', onEngineAction);
  function onEngineAction(ev) {
    const b = ev.target.closest('[data-act]'); if (!b) return;
    const id = parseInt(b.dataset.id);
    if (b.dataset.act === 'test') testEngine(id, b);
    else if (b.dataset.act === 'use') useEngine(id);
    else if (b.dataset.act === 'edit') openModal({ engine: state.engines.find((x) => x.id === id) });
    else if (b.dataset.act === 'del') deleteEngine(id);
  }
  $('aiCatalog').addEventListener('click', (ev) => {
    const c = ev.target.closest('.ai-card'); if (!c) return;
    openModal({ provider: byId(c.dataset.provider) });
  });
  $('aiRefreshBtn').addEventListener('click', load);

  // ── system prompt card ─────────────────────────────────────────────
  $('aiPromptToggle').addEventListener('click', () => {
    const body = $('aiPromptBody'); body.hidden = !body.hidden;
    $('aiPromptChevron').style.transform = body.hidden ? '' : 'rotate(180deg)';
  });
  $('aiPromptSave').addEventListener('click', async () => {
    const r = await req('/ai/settings', { method: 'PUT', body: { system_prompt: $('aiPromptText').value } });
    if (r && r.success) { toast(r.reset ? 'Prompt reset to default' : 'Prompt saved', 'success'); const s = await req('/ai/settings'); if (s && s.success) { state.settings = s; renderPrompt(); } }
    else toast((r && r.error) || 'Save failed', 'error');
  });
  $('aiPromptReset').addEventListener('click', async () => {
    if (!confirm('Reset the instructions to the default prompt?')) return;
    const r = await req('/ai/settings', { method: 'PUT', body: { system_prompt: '' } });
    if (r && r.success) { toast('Prompt reset to default', 'info'); const s = await req('/ai/settings'); if (s && s.success) { state.settings = s; renderPrompt(); } }
  });

  // ── modal (add / edit) ─────────────────────────────────────────────
  const M = {
    el: () => $('aiModal'),
    close: () => { $('aiModal').classList.remove('show'); state.modal = null; },
  };
  $('aiModalClose').addEventListener('click', M.close);
  $('aiModalCancel').addEventListener('click', M.close);
  $('aiModal').addEventListener('click', (e) => { if (e.target === $('aiModal')) M.close(); });

  function openModal({ provider, engine }) {
    const p = provider || byId(engine.provider);
    const isN8n = engine && engine.provider === 'n8n';
    state.modal = { p, engine, models: [], model: engine ? engine.model : null, validated: false };

    $('aiModalLogo').innerHTML = isN8n ? n8nLogo(40) : logo(p, 40);
    $('aiModalTitle').textContent = isN8n ? 'n8n workflow' : (engine ? 'Edit ' + engineName(engine) : p.label);
    $('aiModalSub').textContent = isN8n ? 'Fallback engine' : (engine ? 'Change the model, the key or the URL' : 'Setup in 3 steps');
    $('aiModalNote').hidden = !(p && p.note) || isN8n;
    $('aiModalNote').textContent = p && p.note ? p.note : '';

    // step 1 — key + url
    const keyBlock = $('aiKeyBlock');
    keyBlock.hidden = isN8n || !(p.keyRequired || p.id === 'custom');
    $('aiKeyInput').value = '';
    $('aiKeyInput').placeholder = engine && engine.has_key ? `Leave empty to keep the current key (${engine.key_hint})` : (p.keyRequired ? 'Paste your API key' : 'Optional');
    $('aiKeyDocs').hidden = !(p && p.docsUrl);
    if (p && p.docsUrl) $('aiKeyDocs').href = p.docsUrl;
    const urlBlock = $('aiUrlBlock');
    urlBlock.hidden = !(isN8n || (p && p.baseUrlEditable));
    $('aiUrlLabel').textContent = isN8n ? 'Webhook URL' : 'Base URL';
    $('aiUrlInput').value = engine ? (engine.base_url || '') : (p ? p.baseUrl : '');
    $('aiUrlInput').placeholder = isN8n ? 'http://host:5678/webhook/astrobot' : 'https://host/v1';

    // step 2 — models
    const modelsBlock = $('aiModelsBlock');
    modelsBlock.hidden = isN8n;
    $('aiModelSearch').value = '';
    $('aiModelList').innerHTML = '';
    $('aiManualModel').hidden = !(p && p.allowManualModel);
    $('aiManualModelInput').value = engine && engine.model ? engine.model : '';
    setStatus('');
    if (engine && !isN8n) $('aiSelectedModel').textContent = engine.model || '—';
    else $('aiSelectedModel').textContent = '—';

    // step 3 — label
    $('aiLabelInput').value = engine && engine.label ? engine.label : (p ? p.label : '');
    $('aiLabelBlock').hidden = isN8n;

    $('aiModalSaveUse').hidden = !!(engine && engine.is_active);
    $('aiModalSave').textContent = engine ? 'Save changes' : 'Save';
    M.el().classList.add('show');

    // auto-load models when editing (uses the stored key) or when no key is needed
    if (!isN8n && (engine || !p.keyRequired)) validateAndList();
  }

  function setStatus(msg, kind) {
    const s = $('aiKeyStatus');
    s.textContent = msg || '';
    s.className = 'ai-status ' + (kind || 'muted');
  }

  async function validateAndList() {
    const m = state.modal; if (!m) return;
    const key = $('aiKeyInput').value.trim();
    const url = $('aiUrlInput').value.trim();
    if (m.p.keyRequired && !key && !(m.engine && m.engine.has_key)) { setStatus('Paste your API key first.', 'muted'); return; }
    setStatus('Checking…', 'muted');
    $('aiCheckBtn').disabled = true;
    const body = { provider: m.p.id, api_key: key || undefined, base_url: url || undefined, engine_id: m.engine ? m.engine.id : undefined };
    const r = await req('/ai/engines/validate', { method: 'POST', body });
    $('aiCheckBtn').disabled = false;
    if (r && r.success) {
      m.models = r.models; m.validated = true;
      setStatus(`✓ ${m.p.keyRequired ? 'Key valid — ' : ''}${r.count} model${r.count > 1 ? 's' : ''} available`, 'ok');
      renderModelList();
    } else {
      m.models = []; m.validated = false;
      setStatus('✗ ' + ((r && r.error) || 'Validation failed'), 'err');
      renderModelList();
    }
  }
  $('aiCheckBtn').addEventListener('click', validateAndList);
  $('aiKeyInput').addEventListener('change', () => { if ($('aiKeyInput').value.trim()) validateAndList(); });
  $('aiUrlInput').addEventListener('change', () => { const m = state.modal; if (m && (!m.p.keyRequired || $('aiKeyInput').value.trim() || m.engine)) validateAndList(); });

  function renderModelList() {
    const m = state.modal; if (!m) return;
    const q = $('aiModelSearch').value.trim().toLowerCase();
    const items = m.models.filter((x) => !q || x.id.toLowerCase().includes(q) || String(x.label).toLowerCase().includes(q));
    $('aiModelList').innerHTML = items.length
      ? items.map((x) => `<button class="ai-model ${x.id === m.model ? 'sel' : ''}" data-model="${escapeHtml(x.id)}">
            <span>${escapeHtml(x.id)}</span>${x.label && x.label !== x.id ? `<small>${escapeHtml(x.label)}</small>` : ''}</button>`).join('')
      : `<div class="ai-muted" style="padding:10px">${m.models.length ? 'No model matches your search.' : 'Models will appear here once the key is validated.'}</div>`;
  }
  $('aiModelSearch').addEventListener('input', renderModelList);
  $('aiModelList').addEventListener('click', (ev) => {
    const b = ev.target.closest('.ai-model'); if (!b) return;
    state.modal.model = b.dataset.model;
    $('aiSelectedModel').textContent = b.dataset.model;
    $('aiManualModelInput').value = b.dataset.model;
    renderModelList();
  });
  $('aiManualModelInput').addEventListener('input', () => {
    state.modal.model = $('aiManualModelInput').value.trim() || null;
    $('aiSelectedModel').textContent = state.modal.model || '—';
  });

  async function save(activate) {
    const m = state.modal; if (!m) return;
    const isN8n = m.engine && m.engine.provider === 'n8n';
    const key = $('aiKeyInput').value.trim();
    const url = $('aiUrlInput').value.trim();
    const label = $('aiLabelInput').value.trim();
    const model = isN8n ? null : (m.model || $('aiManualModelInput').value.trim());
    if (!isN8n && !model) { toast('Pick a model first', 'error'); return; }
    if (!m.engine && m.p.keyRequired && !key) { toast('API key required', 'error'); return; }

    let r;
    if (m.engine) {
      r = await req(`/ai/engines/${m.engine.id}`, { method: 'PUT', body: { model, api_key: key || undefined, base_url: $('aiUrlBlock').hidden ? undefined : url, label } });
      if (r && r.success && activate) r = await req(`/ai/engines/${m.engine.id}/activate`, { method: 'POST' });
    } else {
      r = await req('/ai/engines', { method: 'POST', body: { provider: m.p.id, api_key: key || undefined, base_url: url || undefined, model, label, activate: !!activate } });
    }
    if (r && r.success) {
      toast(activate ? 'Saved and now in service' : 'Saved', 'success');
      M.close();
      await reloadEngines();
    } else toast((r && r.error) || 'Save failed', 'error');
  }
  $('aiModalSave').addEventListener('click', () => save(false));
  $('aiModalSaveUse').addEventListener('click', () => save(true));

  window.loadAiPage = load;
})();
