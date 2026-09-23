require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { Pool } = require('pg');
const fs = require('fs');

// shared/ lives at /app/shared in Docker and ../../shared in local dev
function findShared() {
  for (const c of [path.join(__dirname, 'shared'), path.join(__dirname, '..', '..', 'shared')]) {
    if (fs.existsSync(path.join(c, 'llm', 'index.js'))) return c;
  }
  throw new Error('shared/ directory not found');
}
const shared = require(path.join(findShared(), 'llm'));

// ── DB pool (shared with main app DB, read-mostly here) ──────────────
const pool = new Pool({
  host: process.env.DB_HOST || 'postgre_container',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'mydatabase',
  user: process.env.DB_USER || 'tidiane',
  password: process.env.DB_PASSWORD || 'changeme',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
pool.on('error', (e) => console.error('[ADMIN-DB] pool error:', e.message));

const JWT_SECRET = process.env.JWT_SECRET || 'change_me_in_env';
const PORT = process.env.PORT || 7040;
const app = express();

// Behind the Caddy reverse proxy (mounted under /admin): trust the first
// proxy hop so rate-limiting and req.ip use the real client IP.
app.set('trust proxy', 1);

// ── Middleware ────────────────────────────────────────────────────────
app.use(helmet({ contentSecurityPolicy: false, crossOriginEmbedderPolicy: false }));
app.use(cors({ origin: true, credentials: true, methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'] }));
app.use(express.json({ limit: '20mb' }));
app.use(express.urlencoded({ extended: true, limit: '20mb' }));
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 500 }));

// No-cache for static assets so updates show immediately
app.use(express.static(path.join(__dirname, 'public'), {
  etag: false, lastModified: false,
  setHeaders: (res) => {
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
  },
}));

// ── Auth helper ───────────────────────────────────────────────────────
function requireAdmin(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ success: false, error: 'No token.' });
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    if (!payload.is_admin) return res.status(403).json({ success: false, error: 'Admin access required.' });
    req.admin = payload;
    next();
  } catch (e) {
    return res.status(401).json({ success: false, error: 'Invalid token.' });
  }
}

function signToken(user) {
  return jwt.sign(
    { id: user.id, email: user.email, name: user.name, surname: user.surname, is_admin: !!user.is_admin },
    JWT_SECRET,
    { expiresIn: '12h' }
  );
}

// ── Health ────────────────────────────────────────────────────────────
app.get('/api/health', (_req, res) => {
  res.json({ success: true, service: 'AstroBot Admin', port: PORT, timestamp: new Date().toISOString() });
});

// ── AUTH ──────────────────────────────────────────────────────────────
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body || {};
    if (!email || !password) {
      return res.status(400).json({ success: false, error: 'Email and password are required.' });
    }
    const r = await pool.query(
      'SELECT id, name, surname, email, password_hash, avatar, is_admin, status FROM users WHERE email = $1',
      [String(email).toLowerCase().trim()]
    );
    if (r.rows.length === 0) return res.status(401).json({ success: false, error: 'Invalid credentials.' });
    const u = r.rows[0];
    if (!u.is_admin) return res.status(403).json({ success: false, error: 'This account is not an administrator.' });
    if (u.status === 'suspended') return res.status(403).json({ success: false, error: 'Account suspended.' });
    const ok = await bcrypt.compare(password, u.password_hash);
    if (!ok) return res.status(401).json({ success: false, error: 'Invalid credentials.' });
    await pool.query('UPDATE users SET last_login = NOW() WHERE id = $1', [u.id]);
    return res.json({
      success: true,
      token: signToken(u),
      user: { id: u.id, name: u.name, surname: u.surname, email: u.email, avatar: u.avatar || null, is_admin: true },
    });
  } catch (err) {
    console.error('[ADMIN] Login error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// ── ME (current admin profile) ─────────────────────────────────────────
app.get('/api/me', requireAdmin, async (req, res) => {
  const r = await pool.query(
    'SELECT id, name, surname, email, avatar, is_admin, status, last_login, created_at FROM users WHERE id = $1',
    [req.admin.id]
  );
  if (r.rows.length === 0) return res.status(404).json({ success: false, error: 'Not found.' });
  return res.json({ success: true, user: r.rows[0] });
});

app.put('/api/me/profile', requireAdmin, async (req, res) => {
  try {
    const { name, surname } = req.body || {};
    if (!name || !surname || name.trim().length < 2 || surname.trim().length < 2) {
      return res.status(400).json({ success: false, error: 'Name and surname must be at least 2 chars.' });
    }
    const r = await pool.query(
      'UPDATE users SET name=$1, surname=$2 WHERE id=$3 RETURNING id, name, surname, email, avatar, is_admin',
      [name.trim(), surname.trim(), req.admin.id]
    );
    const u = r.rows[0];
    return res.json({ success: true, token: signToken(u), user: u });
  } catch (e) {
    console.error('[ADMIN] /me/profile:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

app.put('/api/me/password', requireAdmin, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body || {};
    if (!currentPassword || !newPassword) {
      return res.status(400).json({ success: false, error: 'Both passwords required.' });
    }
    if (newPassword.length < 8) {
      return res.status(400).json({ success: false, error: 'New password must be at least 8 chars.' });
    }
    const r = await pool.query('SELECT password_hash FROM users WHERE id=$1', [req.admin.id]);
    const ok = await bcrypt.compare(currentPassword, r.rows[0].password_hash);
    if (!ok) return res.status(401).json({ success: false, error: 'Current password is incorrect.' });
    const hash = await bcrypt.hash(newPassword, 12);
    await pool.query('UPDATE users SET password_hash=$1 WHERE id=$2', [hash, req.admin.id]);
    return res.json({ success: true });
  } catch (e) {
    console.error('[ADMIN] /me/password:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

app.put('/api/me/avatar', requireAdmin, async (req, res) => {
  try {
    const { avatar } = req.body || {};
    if (avatar === null || avatar === '' || typeof avatar === 'undefined') {
      await pool.query('UPDATE users SET avatar=NULL WHERE id=$1', [req.admin.id]);
      return res.json({ success: true, avatar: null });
    }
    if (typeof avatar !== 'string' || !avatar.startsWith('data:image/')) {
      return res.status(400).json({ success: false, error: 'avatar must be data:image/* URL.' });
    }
    if (avatar.length > 3 * 1024 * 1024) {
      return res.status(413).json({ success: false, error: 'Avatar too large.' });
    }
    await pool.query('UPDATE users SET avatar=$1 WHERE id=$2', [avatar, req.admin.id]);
    return res.json({ success: true, avatar });
  } catch (e) {
    console.error('[ADMIN] /me/avatar:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// ── STATS (dashboard) ─────────────────────────────────────────────────
app.get('/api/stats', requireAdmin, async (_req, res) => {
  try {
    const usersTotal     = (await pool.query('SELECT COUNT(*)::int AS c FROM users')).rows[0].c;
    const usersActive    = (await pool.query("SELECT COUNT(*)::int AS c FROM users WHERE status='active'")).rows[0].c;
    const usersSuspended = (await pool.query("SELECT COUNT(*)::int AS c FROM users WHERE status='suspended'")).rows[0].c;
    const usersAdmins    = (await pool.query('SELECT COUNT(*)::int AS c FROM users WHERE is_admin=TRUE')).rows[0].c;
    const messagesTotal  = (await pool.query('SELECT COUNT(*)::int AS c FROM conversations')).rows[0].c;
    const sessionsTotal  = (await pool.query('SELECT COUNT(DISTINCT session_id)::int AS c FROM conversations')).rows[0].c;
    const imagesTotal    = (await pool.query('SELECT COUNT(*)::int AS c FROM conversations WHERE image_url IS NOT NULL')).rows[0].c;
    const pdfsTotal      = (await pool.query('SELECT COUNT(*)::int AS c FROM conversations WHERE pdf_url IS NOT NULL')).rows[0].c;
    const docsTotal      = (await pool.query('SELECT COUNT(*)::int AS c FROM documents')).rows[0].c;

    // Messages per day for the last 30 days
    const perDayQ = await pool.query(`
      SELECT DATE(created_at) AS d, COUNT(*)::int AS c
      FROM conversations
      WHERE created_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(created_at)
      ORDER BY d ASC
    `);
    const perDay = perDayQ.rows.map((r) => ({ date: r.d, count: r.c }));

    // Top users (by message count)
    const topUsersQ = await pool.query(`
      SELECT u.id, u.name, u.surname, u.email, COUNT(c.id)::int AS messages
      FROM users u
      LEFT JOIN conversations c ON c.user_id = u.id
      GROUP BY u.id, u.name, u.surname, u.email
      ORDER BY messages DESC
      LIMIT 10
    `);

    // Recent signups
    const recentSignupsQ = await pool.query(`
      SELECT id, name, surname, email, created_at, status
      FROM users
      ORDER BY created_at DESC
      LIMIT 8
    `);

    // Estimated tokens (~ message length / 4)
    const tokensEstQ = await pool.query(`
      SELECT COALESCE(SUM(LENGTH(message) + LENGTH(COALESCE(response,''))) / 4, 0)::bigint AS t
      FROM conversations
    `);

    return res.json({
      success: true,
      stats: {
        users: { total: usersTotal, active: usersActive, suspended: usersSuspended, admins: usersAdmins },
        messages: messagesTotal,
        sessions: sessionsTotal,
        images: imagesTotal,
        pdfs: pdfsTotal,
        documents: docsTotal,
        tokens_estimated: Number(tokensEstQ.rows[0].t || 0),
        per_day: perDay,
        top_users: topUsersQ.rows,
        recent_signups: recentSignupsQ.rows,
      },
    });
  } catch (e) {
    console.error('[ADMIN] /stats:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// ── USERS ─────────────────────────────────────────────────────────────
app.get('/api/users', requireAdmin, async (req, res) => {
  try {
    const q = String(req.query.q || '').toLowerCase().trim();
    const where = q ? "WHERE LOWER(u.name||' '||u.surname||' '||u.email) LIKE $1" : '';
    const params = q ? ['%' + q + '%'] : [];
    const r = await pool.query(`
      SELECT u.id, u.name, u.surname, u.email, u.avatar, u.is_admin, u.status,
             u.last_login, u.created_at,
             (SELECT COUNT(*)::int FROM conversations WHERE user_id = u.id) AS message_count,
             (SELECT COUNT(DISTINCT session_id)::int FROM conversations WHERE user_id = u.id) AS session_count
      FROM users u
      ${where}
      ORDER BY u.created_at DESC
    `, params);
    return res.json({ success: true, users: r.rows });
  } catch (e) {
    console.error('[ADMIN] /users:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Create new user (admin-only)
app.post('/api/users', requireAdmin, async (req, res) => {
  try {
    const { name, surname, email, password, is_admin } = req.body || {};
    if (!name || !surname || !email || !password) {
      return res.status(400).json({ success: false, error: 'All fields required.' });
    }
    if (password.length < 8) {
      return res.status(400).json({ success: false, error: 'Password must be at least 8 chars.' });
    }
    const exists = await pool.query('SELECT id FROM users WHERE email=$1', [email.toLowerCase().trim()]);
    if (exists.rows.length) return res.status(409).json({ success: false, error: 'Email already in use.' });
    const hash = await bcrypt.hash(password, 12);
    const r = await pool.query(
      `INSERT INTO users (name, surname, email, password_hash, is_admin, status)
       VALUES ($1,$2,$3,$4,$5,'active')
       RETURNING id, name, surname, email, is_admin, status, created_at`,
      [name.trim(), surname.trim(), email.toLowerCase().trim(), hash, !!is_admin]
    );
    return res.status(201).json({ success: true, user: r.rows[0] });
  } catch (e) {
    console.error('[ADMIN] POST /users:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Get user detail
app.get('/api/users/:id', requireAdmin, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const r = await pool.query(
      `SELECT id, name, surname, email, avatar, is_admin, status, last_login, created_at
       FROM users WHERE id=$1`,
      [id]
    );
    if (!r.rows.length) return res.status(404).json({ success: false, error: 'User not found.' });
    return res.json({ success: true, user: r.rows[0] });
  } catch (e) {
    console.error('[ADMIN] GET /users/:id:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Update user (status / is_admin / name / email)
app.put('/api/users/:id', requireAdmin, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const { status, is_admin, name, surname, email } = req.body || {};
    const sets = [];
    const params = [];
    let i = 1;
    if (typeof status === 'string') { sets.push('status=$' + i++); params.push(status); }
    if (typeof is_admin === 'boolean') { sets.push('is_admin=$' + i++); params.push(is_admin); }
    if (typeof name === 'string')    { sets.push('name=$' + i++);    params.push(name.trim()); }
    if (typeof surname === 'string') { sets.push('surname=$' + i++); params.push(surname.trim()); }
    if (typeof email === 'string')   { sets.push('email=$' + i++);   params.push(email.toLowerCase().trim()); }
    if (sets.length === 0) return res.status(400).json({ success: false, error: 'Nothing to update.' });
    params.push(id);
    const r = await pool.query(
      `UPDATE users SET ${sets.join(', ')} WHERE id=$${i}
       RETURNING id, name, surname, email, is_admin, status`, params
    );
    if (!r.rows.length) return res.status(404).json({ success: false, error: 'User not found.' });
    return res.json({ success: true, user: r.rows[0] });
  } catch (e) {
    console.error('[ADMIN] PUT /users/:id:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Reset user password
app.post('/api/users/:id/reset-password', requireAdmin, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const { newPassword } = req.body || {};
    if (!newPassword || newPassword.length < 8) {
      return res.status(400).json({ success: false, error: 'Password must be at least 8 chars.' });
    }
    const hash = await bcrypt.hash(newPassword, 12);
    const r = await pool.query('UPDATE users SET password_hash=$1 WHERE id=$2 RETURNING id', [hash, id]);
    if (!r.rows.length) return res.status(404).json({ success: false, error: 'User not found.' });
    return res.json({ success: true });
  } catch (e) {
    console.error('[ADMIN] reset-password:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Delete user
app.delete('/api/users/:id', requireAdmin, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (id === req.admin.id) {
      return res.status(400).json({ success: false, error: 'Cannot delete your own admin account.' });
    }
    await pool.query('DELETE FROM users WHERE id=$1', [id]);
    return res.json({ success: true });
  } catch (e) {
    console.error('[ADMIN] DELETE /users/:id:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// Conversations of a specific user
app.get('/api/users/:id/conversations', requireAdmin, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const r = await pool.query(
      `SELECT id, message, response, session_id, image_url, pdf_filename, attachment, created_at
       FROM conversations
       WHERE user_id=$1
       ORDER BY created_at DESC
       LIMIT 200`,
      [id]
    );
    // Group into sessions (already most-recent first)
    const sessions = {};
    for (const c of r.rows) {
      const sid = c.session_id || 'no-session';
      if (!sessions[sid]) sessions[sid] = { session_id: sid, last_at: c.created_at, messages: [] };
      sessions[sid].messages.push(c);
    }
    const sessionsArr = Object.values(sessions).sort((a, b) => new Date(b.last_at) - new Date(a.last_at));
    return res.json({ success: true, sessions: sessionsArr });
  } catch (e) {
    console.error('[ADMIN] /users/:id/conversations:', e.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// ── AI PROVIDER (engine selection, keys, models, tests) ───────────────
app.use('/api/ai', requireAdmin, require('./routes/ai')({ pool, shared }));

// ── SPA fallback ──────────────────────────────────────────────────────
app.get('*', (req, res) => {
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ success: false, error: 'API not found.' });
  }
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ── Start ─────────────────────────────────────────────────────────────
// Make sure the AI tables exist even if the admin boots before the main app.
pool.connect().then(async (c) => {
  try { await shared.schema.ensureAiSchema(c); } catch (e) { console.error('[ADMIN] AI schema:', e.message); } finally { c.release(); }
}).catch((e) => console.error('[ADMIN] DB not reachable yet:', e.message));

app.listen(PORT, '0.0.0.0', () => {
  console.log('\n[ADMIN] Dashboard listening on port ' + PORT);
  console.log('[ADMIN] DB:', process.env.DB_HOST + '/' + process.env.DB_NAME);
});
