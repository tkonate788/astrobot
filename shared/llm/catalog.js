/* ──────────────────────────────────────────────────────────────────
 * shared/llm/catalog.js — the providers an admin can plug in.
 *
 * `api` decides which HTTP adapter client.js uses:
 *   openai     → GET {base}/models, POST {base}/chat/completions, Bearer key
 *   anthropic  → GET /v1/models + POST /v1/messages, x-api-key
 *   gemini     → native model listing, OpenAI-compatible chat endpoint
 *   cohere     → native model listing, OpenAI-compatible chat endpoint
 *   ollama     → GET {base}/api/tags, OpenAI-compatible chat endpoint
 *   n8n        → the original webhook workflow (fallback), handled by the router
 * ────────────────────────────────────────────────────────────────── */

const NON_CHAT = /(embed|embedding|whisper|tts|speech|audio|transcri|moderation|dall-e|image|realtime|guard|rerank|ocr|search-preview|babbage|davinci|instruct$)/i;

const PROVIDERS = [
  {
    id: 'openai', label: 'OpenAI', api: 'openai', badge: 'AI', color: '#10a37f',
    baseUrl: 'https://api.openai.com/v1', keyRequired: true,
    docsUrl: 'https://platform.openai.com/api-keys',
    filter: (id) => /^(gpt|o[1-9]|chatgpt)/i.test(id) && !NON_CHAT.test(id),
  },
  {
    id: 'anthropic', label: 'Anthropic (Claude)', api: 'anthropic', badge: '✱', color: '#d97757',
    baseUrl: 'https://api.anthropic.com', keyRequired: true,
    docsUrl: 'https://console.anthropic.com/settings/keys',
  },
  {
    id: 'mistral', label: 'Mistral AI', api: 'openai', badge: 'M', color: '#f59e0b',
    baseUrl: 'https://api.mistral.ai/v1', keyRequired: true,
    docsUrl: 'https://console.mistral.ai/api-keys',
    note: 'The model the original n8n workflow used.',
    filter: (id, raw) => (raw && raw.capabilities ? raw.capabilities.completion_chat !== false : true) && !NON_CHAT.test(id),
  },
  {
    id: 'gemini', label: 'Google Gemini', api: 'gemini', badge: '✦', color: '#4285f4',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta', keyRequired: true,
    docsUrl: 'https://aistudio.google.com/apikey',
  },
  {
    id: 'groq', label: 'Groq', api: 'openai', badge: 'GQ', color: '#f55036',
    baseUrl: 'https://api.groq.com/openai/v1', keyRequired: true,
    docsUrl: 'https://console.groq.com/keys',
    filter: (id) => !NON_CHAT.test(id),
  },
  {
    id: 'deepseek', label: 'DeepSeek', api: 'openai', badge: 'DS', color: '#4d6bfe',
    baseUrl: 'https://api.deepseek.com/v1', keyRequired: true,
    docsUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    id: 'xai', label: 'xAI (Grok)', api: 'openai', badge: 'X', color: '#111111',
    baseUrl: 'https://api.x.ai/v1', keyRequired: true,
    docsUrl: 'https://console.x.ai',
    filter: (id) => !NON_CHAT.test(id),
  },
  {
    id: 'openrouter', label: 'OpenRouter (multi-provider gateway)', api: 'openai', badge: 'OR', color: '#6366f1',
    baseUrl: 'https://openrouter.ai/api/v1', keyRequired: true,
    docsUrl: 'https://openrouter.ai/keys',
    // /models is public: verify the key separately (free call, 401 on bad key)
    authCheckUrl: 'https://openrouter.ai/api/v1/auth/key',
  },
  {
    id: 'together', label: 'Together AI', api: 'openai', badge: 'TA', color: '#0ea5e9',
    baseUrl: 'https://api.together.xyz/v1', keyRequired: true,
    docsUrl: 'https://api.together.ai/settings/api-keys',
    filter: (id, raw) => !raw || !raw.type || raw.type === 'chat',
  },
  {
    id: 'cohere', label: 'Cohere', api: 'cohere', badge: 'CO', color: '#39594d',
    baseUrl: 'https://api.cohere.com', keyRequired: true,
    docsUrl: 'https://dashboard.cohere.com/api-keys',
  },
  {
    id: 'perplexity', label: 'Perplexity', api: 'openai', badge: 'PX', color: '#20808d',
    baseUrl: 'https://api.perplexity.ai', keyRequired: true,
    docsUrl: 'https://www.perplexity.ai/settings/api',
    // No /models endpoint: static list, the key is validated with a tiny chat call.
    staticModels: ['sonar', 'sonar-pro', 'sonar-reasoning', 'sonar-reasoning-pro', 'sonar-deep-research'],
  },
  {
    id: 'huggingface', label: 'Hugging Face (Inference Providers)', api: 'openai', badge: 'HF', color: '#b8860b',
    baseUrl: 'https://router.huggingface.co/v1', keyRequired: true,
    docsUrl: 'https://huggingface.co/settings/tokens',
    note: 'Same token as HF_API_KEY (image generation). Models are served by partner providers.',
    // /v1/models is public: verify the token separately (free call, 401 on bad token)
    authCheckUrl: 'https://huggingface.co/api/whoami-v2',
    filter: (id) => !NON_CHAT.test(id),
  },
  {
    id: 'ollama', label: 'Ollama (local, on the server)', api: 'ollama', badge: 'OL', color: '#1f2937',
    baseUrl: 'http://host.docker.internal:11434', keyRequired: false, baseUrlEditable: true,
    docsUrl: 'https://ollama.com/download',
    free: true, note: 'Runs on your own machine/server, no API key. Set the URL where Ollama listens.',
  },
  {
    id: 'custom', label: 'Other (OpenAI-compatible API)', api: 'openai', badge: '?', color: '#6b7280',
    baseUrl: '', keyRequired: false, baseUrlEditable: true, allowManualModel: true,
    docsUrl: null,
    free: true, note: 'Any provider exposing /v1/models and /v1/chat/completions (LM Studio, vLLM, Azure-style gateways...).',
  },
];

const BY_ID = Object.fromEntries(PROVIDERS.map((p) => [p.id, p]));

/** Public, serialisable catalog (functions stripped). */
function publicCatalog() {
  return PROVIDERS.map(({ filter, ...rest }) => rest);
}

function get(id) { return BY_ID[id] || null; }

module.exports = { PROVIDERS, get, publicCatalog };
