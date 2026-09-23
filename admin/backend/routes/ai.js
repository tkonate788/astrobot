/* ──────────────────────────────────────────────────────────────────
 * admin/backend/routes/ai.js — "AI Provider" admin API.
 *
 *   GET    /catalog                    provider catalog (logos, docs links…)
 *   GET    /engines                    configured engines (keys masked)
 *   POST   /engines/validate           check a key / URL → list of models
 *   POST   /engines                    save a new engine
 *   PUT    /engines/:id                change model / key / URL / label
 *   DELETE /engines/:id                remove (n8n fallback cannot be removed)
 *   POST   /engines/:id/test           live round-trip test
 *   POST   /engines/:id/activate       make it the engine used by the chat
 *   GET    /settings                   system prompt (+ default)
 *   PUT    /settings                   save / reset system prompt
 *   GET    /recent                     last conversations with the engine used
 * Mounted in server.js under /api/ai behind requireAdmin.
 * ────────────────────────────────────────────────────────────────── */
const express = require('express');

module.exports = function createAiRouter({ pool, shared }) {
  const { catalog, client, crypto, prompt } = shared;
  const router = express.Router();

  const publicRow = (r) => ({
    id: r.id,
    provider: r.provider,
    label: r.label,
    key_hint: r.key_hint,
    has_key: !!r.api_key_enc,
    base_url: r.base_url,
    model: r.model,
    is_active: !!r.is_active,
    last_test_ok: r.last_test_ok,
    last_test_at: r.last_test_at,
    last_test_error: r.last_test_error,
    created_at: r.created_at,
    updated_at: r.updated_at,
  });

  async function getRow(id) {
    const r = await pool.query('SELECT * FROM ai_providers WHERE id = $1', [id]);
    return r.rows[0] || null;
  }

  async function ensureN8nRow() {
    const r = await pool.query(`SELECT * FROM ai_providers WHERE provider = 'n8n' LIMIT 1`);
    if (r.rows.length) return r.rows[0];
    const ins = await pool.query(
      `INSERT INTO ai_providers (provider, label, base_url, is_active)
       VALUES ('n8n', 'n8n (existing workflow — fallback)', $1, FALSE) RETURNING *`,
      [process.env.N8N_WEBHOOK || null]
    );
    return ins.rows[0];
  }

  async function testN8n(webhookUrl) {
    const t0 = Date.now();
    try {
      const ctrl = new AbortController();
      const to = setTimeout(() => ctrl.abort(), 30000);
      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 0, user_name: 'Admin', user_surname: 'Test', user_email: 'admin@test',
          message: 'Reply with the single word OK.', session_id: 'admin_engine_test',
          audio: null, attachment: null, attachments: [], persona: 'default', conversation_history: [],
        }),
        signal: ctrl.signal,
      });
      clearTimeout(to);
      const body = await res.text();
      if (!res.ok) return { ok: false, ms: Date.now() - t0, error: 'n8n_http_' + res.status + ' — ' + body.slice(0, 200) };
      return { ok: true, ms: Date.now() - t0, sample: body.slice(0, 60) };
    } catch (e) {
      return { ok: false, ms: Date.now() - t0, error: 'n8n_unreachable — ' + e.message };
    }
  }

  async function storeTest(id, t) {
    await pool.query(
      `UPDATE ai_providers SET last_test_ok = $1, last_test_at = NOW(), last_test_error = $2 WHERE id = $3`,
      [t.ok, t.ok ? null : t.error, id]
    );
  }

  // ── catalog ──────────────────────────────────────────────────────
  router.get('/catalog', (_req, res) => {
    res.json({ success: true, providers: catalog.publicCatalog() });
  });

  // ── list ─────────────────────────────────────────────────────────
  router.get('/engines', async (_req, res) => {
    try {
      await ensureN8nRow();
      const r = await pool.query('SELECT * FROM ai_providers ORDER BY created_at ASC');
      const rows = r.rows.map(publicRow);
      const active = rows.find((x) => x.is_active) || null;
      res.json({ success: true, engines: rows, active, n8n_default_url: process.env.N8N_WEBHOOK || null });
    } catch (e) {
      console.error('[AI] list:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── validate key / url → models ──────────────────────────────────
  router.post('/engines/validate', async (req, res) => {
    try {
      const { provider, api_key, base_url, engine_id } = req.body || {};
      const p = catalog.get(provider);
      if (!p) return res.status(400).json({ success: false, error: 'Unknown provider.' });

      let apiKey = (api_key || '').trim() || null;
      let baseUrl = (base_url || '').trim() || null;
      if (!apiKey && engine_id) {
        const row = await getRow(parseInt(engine_id));
        if (row && row.api_key_enc) apiKey = crypto.decrypt(row.api_key_enc);
        if (!baseUrl && row) baseUrl = row.base_url;
      }
      if (p.keyRequired && !apiKey) return res.status(400).json({ success: false, error: 'API key required.' });

      const models = await client.listModels(provider, { apiKey, baseUrl });
      if (!models.length && !p.allowManualModel) {
        return res.status(422).json({ success: false, error: 'The key is valid but no chat model was returned.' });
      }
      res.json({ success: true, models, count: models.length });
    } catch (e) {
      res.status(400).json({ success: false, error: e.message });
    }
  });

  // ── create ───────────────────────────────────────────────────────
  router.post('/engines', async (req, res) => {
    try {
      const { provider, api_key, base_url, model, label, activate } = req.body || {};
      const p = catalog.get(provider);
      if (!p) return res.status(400).json({ success: false, error: 'Unknown provider.' });
      if (!model) return res.status(400).json({ success: false, error: 'Model required.' });
      const apiKey = (api_key || '').trim() || null;
      if (p.keyRequired && !apiKey) return res.status(400).json({ success: false, error: 'API key required.' });
      const baseUrl = (base_url || '').trim() || (p.baseUrlEditable ? p.baseUrl : null) || null;

      const ins = await pool.query(
        `INSERT INTO ai_providers (provider, label, api_key_enc, key_hint, base_url, model, is_active)
         VALUES ($1, $2, $3, $4, $5, $6, FALSE) RETURNING *`,
        [provider, (label || p.label).slice(0, 120), apiKey ? crypto.encrypt(apiKey) : null,
         crypto.hint(apiKey), baseUrl, String(model).slice(0, 160)]
      );
      const row = ins.rows[0];
      if (activate) {
        await pool.query('UPDATE ai_providers SET is_active = (id = $1), updated_at = NOW()', [row.id]);
        row.is_active = true;
      }
      res.status(201).json({ success: true, engine: publicRow(row) });
    } catch (e) {
      console.error('[AI] create:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── update ───────────────────────────────────────────────────────
  router.put('/engines/:id', async (req, res) => {
    try {
      const row = await getRow(parseInt(req.params.id));
      if (!row) return res.status(404).json({ success: false, error: 'Not found.' });
      const { api_key, base_url, model, label } = req.body || {};
      const sets = [];
      const params = [];
      let i = 1;
      if (typeof model === 'string' && model.trim()) { sets.push(`model=$${i++}`); params.push(model.trim().slice(0, 160)); }
      if (typeof label === 'string' && label.trim()) { sets.push(`label=$${i++}`); params.push(label.trim().slice(0, 120)); }
      if (typeof base_url === 'string') { sets.push(`base_url=$${i++}`); params.push(base_url.trim() || null); }
      if (typeof api_key === 'string' && api_key.trim()) {
        sets.push(`api_key_enc=$${i++}`); params.push(crypto.encrypt(api_key.trim()));
        sets.push(`key_hint=$${i++}`); params.push(crypto.hint(api_key.trim()));
      }
      if (!sets.length) return res.status(400).json({ success: false, error: 'Nothing to update.' });
      sets.push('updated_at=NOW()', 'last_test_ok=NULL', 'last_test_error=NULL');
      params.push(row.id);
      const r = await pool.query(`UPDATE ai_providers SET ${sets.join(', ')} WHERE id=$${i} RETURNING *`, params);
      res.json({ success: true, engine: publicRow(r.rows[0]) });
    } catch (e) {
      console.error('[AI] update:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── delete ───────────────────────────────────────────────────────
  router.delete('/engines/:id', async (req, res) => {
    try {
      const row = await getRow(parseInt(req.params.id));
      if (!row) return res.status(404).json({ success: false, error: 'Not found.' });
      if (row.provider === 'n8n') return res.status(400).json({ success: false, error: 'The n8n fallback cannot be removed.' });
      await pool.query('DELETE FROM ai_providers WHERE id = $1', [row.id]);
      if (row.is_active) {
        // Never leave the chat without an engine: fall back to n8n.
        const n8n = await ensureN8nRow();
        await pool.query('UPDATE ai_providers SET is_active = (id = $1)', [n8n.id]);
      }
      res.json({ success: true });
    } catch (e) {
      console.error('[AI] delete:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── test ─────────────────────────────────────────────────────────
  router.post('/engines/:id/test', async (req, res) => {
    try {
      const row = await getRow(parseInt(req.params.id));
      if (!row) return res.status(404).json({ success: false, error: 'Not found.' });
      let t;
      if (row.provider === 'n8n') {
        t = await testN8n(row.base_url || process.env.N8N_WEBHOOK || '');
      } else {
        t = await client.testEngine(row.provider, {
          apiKey: row.api_key_enc ? crypto.decrypt(row.api_key_enc) : null,
          baseUrl: row.base_url,
          model: row.model,
        });
      }
      await storeTest(row.id, t);
      res.json({ success: true, test: t, engine: publicRow(await getRow(row.id)) });
    } catch (e) {
      console.error('[AI] test:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── activate ─────────────────────────────────────────────────────
  router.post('/engines/:id/activate', async (req, res) => {
    try {
      const row = await getRow(parseInt(req.params.id));
      if (!row) return res.status(404).json({ success: false, error: 'Not found.' });
      await pool.query('UPDATE ai_providers SET is_active = (id = $1), updated_at = CASE WHEN id = $1 THEN NOW() ELSE updated_at END', [row.id]);
      res.json({ success: true, engine: publicRow(await getRow(row.id)) });
    } catch (e) {
      console.error('[AI] activate:', e.message);
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── system prompt ────────────────────────────────────────────────
  router.get('/settings', async (_req, res) => {
    try {
      const r = await pool.query(`SELECT value, updated_at FROM app_settings WHERE key = 'system_prompt'`);
      res.json({
        success: true,
        system_prompt: r.rows[0] ? r.rows[0].value : null,
        updated_at: r.rows[0] ? r.rows[0].updated_at : null,
        default_prompt: prompt.DEFAULT_SYSTEM_PROMPT,
      });
    } catch (e) {
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  router.put('/settings', async (req, res) => {
    try {
      const v = typeof req.body.system_prompt === 'string' ? req.body.system_prompt.trim() : '';
      if (!v || v === prompt.DEFAULT_SYSTEM_PROMPT.trim()) {
        await pool.query(`DELETE FROM app_settings WHERE key = 'system_prompt'`);
        return res.json({ success: true, system_prompt: null, reset: true });
      }
      await pool.query(
        `INSERT INTO app_settings (key, value, updated_at) VALUES ('system_prompt', $1, NOW())
         ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()`,
        [v.slice(0, 20000)]
      );
      res.json({ success: true, system_prompt: v });
    } catch (e) {
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  // ── recent conversations ─────────────────────────────────────────
  router.get('/recent', async (_req, res) => {
    try {
      const r = await pool.query(
        `SELECT c.id, c.message, c.engine, c.created_at, u.name, u.surname, u.email
         FROM conversations c LEFT JOIN users u ON u.id = c.user_id
         ORDER BY c.created_at DESC LIMIT 12`
      );
      res.json({ success: true, items: r.rows });
    } catch (e) {
      res.status(500).json({ success: false, error: 'Internal error.' });
    }
  });

  return router;
};
