/* ──────────────────────────────────────────────────────────────────
 * shared/llm/schema.js — idempotent DDL for the AI-provider feature.
 * Called by both services on boot (CREATE IF NOT EXISTS only).
 * ────────────────────────────────────────────────────────────────── */
async function ensureAiSchema(client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS ai_providers (
      id SERIAL PRIMARY KEY,
      provider VARCHAR(40) NOT NULL,          -- catalog id: openai, mistral, n8n, custom…
      label VARCHAR(120),
      api_key_enc TEXT,                       -- AES-GCM blob, never returned to clients
      key_hint VARCHAR(40),
      base_url TEXT,
      model VARCHAR(160),
      is_active BOOLEAN DEFAULT FALSE,
      last_test_ok BOOLEAN,
      last_test_at TIMESTAMP,
      last_test_error TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  `);
  await client.query(`
    CREATE TABLE IF NOT EXISTS app_settings (
      key VARCHAR(80) PRIMARY KEY,
      value TEXT,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  `);
  await client.query(`ALTER TABLE conversations ADD COLUMN IF NOT EXISTS engine VARCHAR(200);`);

  // Seed the n8n fallback engine once; it stays the active engine until an
  // admin picks another one, so existing behaviour is unchanged.
  const n8n = await client.query(`SELECT id FROM ai_providers WHERE provider = 'n8n' LIMIT 1`);
  if (n8n.rows.length === 0) {
    const anyActive = await client.query(`SELECT 1 FROM ai_providers WHERE is_active LIMIT 1`);
    await client.query(
      `INSERT INTO ai_providers (provider, label, base_url, is_active)
       VALUES ('n8n', 'n8n (existing workflow — fallback)', $1, $2)`,
      [process.env.N8N_WEBHOOK || null, anyActive.rows.length === 0]
    );
  }
}

module.exports = { ensureAiSchema };
