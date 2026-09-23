/* ──────────────────────────────────────────────────────────────────
 * backend/services/llmRouter.js — picks the engine an admin activated
 * in the dashboard and produces the assistant's raw reply.
 *
 *   - engine "n8n"  → the original webhook workflow (unchanged payload)
 *   - any provider  → direct API call through shared/llm/client with the
 *                     same JSON contract, automatic fallback to n8n on error
 *
 * chat.js keeps parsing `text` exactly as before, so image/PDF actions and
 * the heuristics keep working whichever engine answered.
 * ────────────────────────────────────────────────────────────────── */
const path = require('path');
const fs = require('fs');
const { pool } = require('../db/index');

function findShared() {
  for (const c of [path.join(__dirname, '..', 'shared'), path.join(__dirname, '..', '..', 'shared')]) {
    if (fs.existsSync(path.join(c, 'llm', 'index.js'))) return c;
  }
  throw new Error('shared/ directory not found');
}
const { catalog, client, crypto, prompt } = require(path.join(findShared(), 'llm'));

const DEFAULT_N8N = 'http://76.13.62.195:5678/webhook/astrobot';

async function getActiveEngine() {
  try {
    const r = await pool.query(
      `SELECT * FROM ai_providers WHERE is_active = TRUE ORDER BY updated_at DESC LIMIT 1`
    );
    return r.rows[0] || null;
  } catch (e) {
    console.error('[LLM] active engine lookup failed:', e.message);
    return null;
  }
}

async function getSystemPromptTemplate() {
  try {
    const r = await pool.query(`SELECT value FROM app_settings WHERE key = 'system_prompt'`);
    const v = r.rows[0] && r.rows[0].value;
    return v && v.trim() ? v : prompt.DEFAULT_SYSTEM_PROMPT;
  } catch (_) {
    return prompt.DEFAULT_SYSTEM_PROMPT;
  }
}

function engineLabel(row) {
  if (!row || row.provider === 'n8n') return 'n8n';
  return row.provider + ':' + (row.model || '?');
}

// ── n8n (original behaviour) ───────────────────────────────────────
async function callN8n(webhookUrl, payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 45000);
  let res;
  try {
    res = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) throw new Error('n8n_http_' + res.status);
  const data = await res.json();
  const text =
    data.response || data.message || data.output || data.text || data.answer ||
    (Array.isArray(data) && data[0] && (data[0].response || data[0].output)) ||
    JSON.stringify(data);
  return { text, imageUrl: data.image_url || data.image || null };
}

// ── direct provider ────────────────────────────────────────────────
async function callProvider(row, { user, effectiveMessage, conversationHistory }) {
  const template = await getSystemPromptTemplate();
  const messages = [{ role: 'system', content: prompt.renderPrompt(template, user) }];
  for (const h of conversationHistory || []) {
    if (h.role_user) messages.push({ role: 'user', content: String(h.role_user) });
    if (h.role_assistant) messages.push({ role: 'assistant', content: String(h.role_assistant) });
  }
  messages.push({ role: 'user', content: effectiveMessage });

  const r = await client.chat(row.provider, {
    apiKey: row.api_key_enc ? crypto.decrypt(row.api_key_enc) : null,
    baseUrl: row.base_url,
    model: row.model,
    messages,
    maxTokens: 4096,
    temperature: 0.7,
    timeout: 60000,
  });
  return { text: r.text, imageUrl: null };
}

async function recordFailure(row, err) {
  try {
    await pool.query(
      `UPDATE ai_providers SET last_test_ok = FALSE, last_test_error = $1, last_test_at = NOW() WHERE id = $2`,
      [String(err && err.message || err).slice(0, 500), row.id]
    );
  } catch (_) { /* best effort */ }
}

/**
 * Returns { text, imageUrl, engine, fallback }.
 * Throws only if every path failed (caller shows the "offline" message).
 */
async function generateReply({ user, effectiveMessage, conversationHistory, n8nPayload }) {
  const engine = await getActiveEngine();
  const n8nUrl =
    (engine && engine.provider === 'n8n' && engine.base_url) || process.env.N8N_WEBHOOK || DEFAULT_N8N;

  if (!engine || engine.provider === 'n8n') {
    const r = await callN8n(n8nUrl, n8nPayload);
    return { ...r, engine: 'n8n', fallback: false };
  }

  const label = engineLabel(engine);
  if (!catalog.get(engine.provider)) {
    console.error('[LLM] unknown provider in DB:', engine.provider);
  } else {
    try {
      const r = await callProvider(engine, { user, effectiveMessage, conversationHistory });
      return { ...r, engine: label, fallback: false };
    } catch (e) {
      console.error('[LLM] ' + label + ' failed, falling back to n8n:', e.message);
      await recordFailure(engine, e);
    }
  }
  const r = await callN8n(process.env.N8N_WEBHOOK || DEFAULT_N8N, n8nPayload);
  return { ...r, engine: label + ' -> fallback:n8n', fallback: true };
}

module.exports = { generateReply, getActiveEngine, engineLabel };
