/* ──────────────────────────────────────────────────────────────────
 * shared/llm/client.js — one tiny HTTP client for every provider.
 *   listModels(providerId, { apiKey, baseUrl })            → [{id,label}]
 *   chat(providerId, { apiKey, baseUrl, model, messages }) → { text, raw }
 *   testEngine(providerId, { apiKey, baseUrl, model })     → { ok, ms, error? }
 * Errors are thrown as Error('provider_http_<status> — <body>') so the
 * admin UI can show exactly what the provider said.
 * ────────────────────────────────────────────────────────────────── */
const catalog = require('./catalog');

const DEFAULT_TIMEOUT = 45000;

function trimSlash(u) { return String(u || '').replace(/\/+$/, ''); }

async function http(url, { method = 'GET', headers = {}, body, timeout = DEFAULT_TIMEOUT } = {}) {
  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), timeout);
  let res;
  try {
    res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: ctrl.signal,
    });
  } catch (e) {
    clearTimeout(to);
    const why = e.name === 'AbortError' ? 'timeout after ' + timeout + ' ms' : (e.cause && e.cause.message) || e.message;
    throw new Error('provider_unreachable — ' + why);
  }
  clearTimeout(to);
  const text = await res.text();
  if (!res.ok) throw new Error('provider_http_' + res.status + ' — ' + text.slice(0, 300));
  try { return JSON.parse(text); } catch (_) { return { _raw: text }; }
}

function authHeaders(p, apiKey) {
  if (p.api === 'anthropic') return { 'x-api-key': apiKey || '', 'anthropic-version': '2023-06-01' };
  return apiKey ? { Authorization: 'Bearer ' + apiKey } : {};
}

function resolveBase(p, baseUrl) {
  const b = trimSlash(baseUrl || p.baseUrl);
  if (!b) throw new Error('base_url_required — this provider needs a base URL.');
  return b;
}

// ── models ─────────────────────────────────────────────────────────
async function listModels(providerId, { apiKey, baseUrl } = {}) {
  const p = catalog.get(providerId);
  if (!p) throw new Error('unknown_provider');
  if (p.keyRequired && !apiKey) throw new Error('api_key_required');

  if (p.staticModels) {
    // Validate the key with the cheapest possible call, then return the list.
    await chat(providerId, { apiKey, baseUrl, model: p.staticModels[0], messages: [{ role: 'user', content: 'ping' }], maxTokens: 1 });
    return p.staticModels.map((id) => ({ id, label: id }));
  }

  const base = resolveBase(p, baseUrl);
  let items = [];

  if (p.api === 'anthropic') {
    const d = await http(base + '/v1/models?limit=1000', { headers: authHeaders(p, apiKey) });
    items = (d.data || []).map((m) => ({ id: m.id, label: m.display_name || m.id }));
  } else if (p.api === 'gemini') {
    const d = await http(base + '/models?pageSize=200&key=' + encodeURIComponent(apiKey));
    items = (d.models || [])
      .filter((m) => (m.supportedGenerationMethods || []).includes('generateContent'))
      .map((m) => ({ id: String(m.name).replace(/^models\//, ''), label: m.displayName || m.name }));
  } else if (p.api === 'cohere') {
    const d = await http(base + '/v2/models?endpoint=chat&page_size=100', { headers: authHeaders(p, apiKey) });
    items = (d.models || []).map((m) => ({ id: m.name, label: m.name }));
  } else if (p.api === 'ollama') {
    const d = await http(base + '/api/tags', { headers: authHeaders(p, apiKey) });
    items = (d.models || []).map((m) => ({ id: m.name || m.model, label: m.name || m.model }));
  } else {
    const d = await http(base + '/models', { headers: authHeaders(p, apiKey) });
    const arr = Array.isArray(d) ? d : (d.data || d.models || []);
    items = arr
      .filter((m) => !p.filter || p.filter(m.id || m.name, m))
      .map((m) => ({ id: m.id || m.name, label: m.name && m.name !== m.id ? m.name : (m.id || m.name) }));
  }

  const seen = new Set();
  return items
    .filter((m) => m.id && !seen.has(m.id) && seen.add(m.id))
    .sort((a, b) => a.id.localeCompare(b.id));
}

// ── chat ───────────────────────────────────────────────────────────
async function chat(providerId, { apiKey, baseUrl, model, messages, maxTokens = 4096, temperature = 0.7, timeout } = {}) {
  const p = catalog.get(providerId);
  if (!p) throw new Error('unknown_provider');
  if (!model) throw new Error('model_required');
  const base = resolveBase(p, baseUrl);

  if (p.api === 'anthropic') {
    const system = messages.filter((m) => m.role === 'system').map((m) => m.content).join('\n\n');
    const turns = messages.filter((m) => m.role !== 'system').map((m) => ({ role: m.role, content: m.content }));
    const d = await http(base + '/v1/messages', {
      method: 'POST', headers: authHeaders(p, apiKey), timeout,
      body: { model, max_tokens: maxTokens, temperature, ...(system ? { system } : {}), messages: turns },
    });
    const text = (d.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('');
    return { text, raw: d };
  }

  // Everyone else speaks the OpenAI chat-completions dialect.
  let url;
  if (p.api === 'gemini') url = base + '/openai/chat/completions';
  else if (p.api === 'cohere') url = base + '/compatibility/v1/chat/completions';
  else if (p.api === 'ollama') url = base + '/v1/chat/completions';
  else url = base + '/chat/completions';

  const d = await http(url, {
    method: 'POST', headers: authHeaders(p, apiKey), timeout,
    body: { model, messages, max_tokens: maxTokens, temperature },
  });
  const choice = d.choices && d.choices[0];
  let text = choice && choice.message ? choice.message.content : '';
  if (Array.isArray(text)) text = text.map((c) => (typeof c === 'string' ? c : c.text || '')).join('');
  return { text: String(text || ''), raw: d };
}

async function testEngine(providerId, { apiKey, baseUrl, model }) {
  const t0 = Date.now();
  try {
    const r = await chat(providerId, {
      apiKey, baseUrl, model, maxTokens: 20, temperature: 0, timeout: 30000,
      messages: [{ role: 'user', content: 'Reply with the single word OK.' }],
    });
    return { ok: true, ms: Date.now() - t0, sample: r.text.slice(0, 60) };
  } catch (e) {
    return { ok: false, ms: Date.now() - t0, error: e.message };
  }
}

module.exports = { listModels, chat, testEngine };
