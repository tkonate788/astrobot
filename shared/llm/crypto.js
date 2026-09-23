/* ──────────────────────────────────────────────────────────────────
 * shared/llm/crypto.js — at-rest encryption for provider API keys.
 * AES-256-GCM; key derived from AI_KEYS_SECRET (or JWT_SECRET) so both
 * the main app and the admin service can read what the other wrote.
 * ────────────────────────────────────────────────────────────────── */
const crypto = require('crypto');

function masterKey() {
  const secret = process.env.AI_KEYS_SECRET || process.env.JWT_SECRET || 'change_me_in_env';
  return crypto.createHash('sha256').update('astrobot-ai-keys:' + secret).digest();
}

function encrypt(plain) {
  if (plain === null || plain === undefined || plain === '') return null;
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', masterKey(), iv);
  const enc = Buffer.concat([cipher.update(String(plain), 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return 'v1:' + iv.toString('base64') + ':' + tag.toString('base64') + ':' + enc.toString('base64');
}

function decrypt(blob) {
  if (!blob) return null;
  const [v, ivB, tagB, dataB] = String(blob).split(':');
  if (v !== 'v1') throw new Error('unknown key blob version');
  const decipher = crypto.createDecipheriv('aes-256-gcm', masterKey(), Buffer.from(ivB, 'base64'));
  decipher.setAuthTag(Buffer.from(tagB, 'base64'));
  return Buffer.concat([decipher.update(Buffer.from(dataB, 'base64')), decipher.final()]).toString('utf8');
}

/** "sk-abc…wxyz" style hint that never reveals the key. */
function hint(plain) {
  if (!plain) return null;
  const s = String(plain);
  if (s.length <= 10) return s.slice(0, 2) + '…';
  return s.slice(0, 6) + '…' + s.slice(-4);
}

module.exports = { encrypt, decrypt, hint };
