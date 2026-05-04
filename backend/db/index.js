const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host: process.env.DB_HOST || 'postgre_container',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'mydatabase',
  user: process.env.DB_USER || 'tidiane',
  password: process.env.DB_PASSWORD || 'changeme',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => {
  console.error('[DB] Unexpected pool error:', err.message);
});

const initDB = async () => {
  const client = await pool.connect();
  try {
    console.log('[DB] Connected to PostgreSQL successfully.');

    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        surname VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        message TEXT NOT NULL,
        response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // ── Idempotent migrations: add session + media columns if missing ──
    const CONV_COLUMN_ADDS = [
      ['session_id',   'VARCHAR(255)'],
      ['image_url',    'TEXT'],         // data URL of bot-generated image
      ['pdf_url',      'TEXT'],         // data URL of bot-generated PDF
      ['pdf_filename', 'VARCHAR(255)'],
      ['attachment',   'TEXT'],         // JSON: { name, mime, size, dataUrl }
    ];
    for (const [col, type] of CONV_COLUMN_ADDS) {
      await client.query(
        `ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ${col} ${type};`
      );
    }

    // Add user avatar column (data URL of cropped profile photo)
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar TEXT;`);

    // Admin / status columns
    const USER_COLUMN_ADDS = [
      ['is_admin',   'BOOLEAN DEFAULT FALSE'],
      ['status',     "VARCHAR(20) DEFAULT 'active'"], // 'active' | 'suspended'
      ['last_login', 'TIMESTAMP'],
    ];
    for (const [col, type] of USER_COLUMN_ADDS) {
      await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS ${col} ${type};`);
    }

    // Tags on conversations (per-session tag/folder)
    await client.query(`ALTER TABLE conversations ADD COLUMN IF NOT EXISTS session_tag VARCHAR(80);`);

    // Documents table for Notebook + RAG
    await client.query(`
      CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        mime VARCHAR(100),
        size INTEGER,
        text_content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    await client.query(`
      CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER,
        chunk_text TEXT,
        embedding TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc ON document_chunks(document_id);`);

    // Notebook session bindings (which doc is active for which session)
    await client.query(`
      CREATE TABLE IF NOT EXISTS notebook_bindings (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        session_id VARCHAR(255) NOT NULL,
        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
        mode VARCHAR(20) DEFAULT 'notebook',
        PRIMARY KEY (user_id, session_id)
      );
    `);

    // Workflow chains (saved multi-step prompt pipelines)
    await client.query(`
      CREATE TABLE IF NOT EXISTS workflows (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(120) NOT NULL,
        steps TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // ── Seed admin account ────────────────────────────────────────────
    // Idempotent: ensures the canonical admin always exists with the
    // credentials defined via env vars (ADMIN_EMAIL, ADMIN_PASSWORD).
    // If the user already existed with a different password, we overwrite
    // it — this account is reserved for admin use.
    const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@astrobot.local';
    const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'changeme123';
    const bcrypt = require('bcryptjs');
    const existing = await client.query('SELECT id FROM users WHERE email = $1', [ADMIN_EMAIL]);
    const hash = await bcrypt.hash(ADMIN_PASSWORD, 12);
    if (existing.rows.length === 0) {
      await client.query(
        `INSERT INTO users (name, surname, email, password_hash, is_admin, status)
         VALUES ($1, $2, $3, $4, TRUE, 'active')`,
        ['Tidiane', 'Konaté', ADMIN_EMAIL, hash]
      );
      console.log('[DB] Admin account created:', ADMIN_EMAIL);
    } else {
      await client.query(
        `UPDATE users SET is_admin = TRUE, status = 'active', password_hash = $1 WHERE id = $2`,
        [hash, existing.rows[0].id]
      );
      console.log('[DB] Admin account ensured (admin role + canonical password reset):', ADMIN_EMAIL);
    }

    console.log('[DB] All tables, columns, indexes & admin seed initialized.');
  } catch (err) {
    console.error('[DB] Error initializing tables:', err.message);
    throw err;
  } finally {
    client.release();
  }
};

module.exports = { pool, initDB };
