/* ──────────────────────────────────────────────────────────────────
 * features.js — Notebook + RAG, Audio transcription, YouTube
 * summarizer, Image-to-image edit, and Workflow chains.
 * All endpoints require authentication.
 * ────────────────────────────────────────────────────────────────── */

const express = require('express');
const { pool } = require('../db/index');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
router.use(authenticateToken);

const HF_KEY = () => process.env.HF_API_KEY || '';
const GROQ_KEY = () => process.env.GROQ_API_KEY || ''; // optional; falls back gracefully

// ════════════════════════════════════════════════════════════════════
// DOCUMENTS / NOTEBOOK / RAG
// ════════════════════════════════════════════════════════════════════

// Naive but effective text chunker
function chunkText(text, size = 800, overlap = 100) {
  const out = [];
  const cleaned = String(text || '').replace(/\s+/g, ' ').trim();
  if (!cleaned) return out;
  let i = 0;
  while (i < cleaned.length) {
    out.push(cleaned.slice(i, i + size));
    i += size - overlap;
  }
  return out;
}

// Embed a list of texts via HF Inference (sentence-transformers MiniLM, free)
async function embedBatch(texts) {
  const url = 'https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2';
  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), 60000);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + HF_KEY() },
      body: JSON.stringify({ inputs: texts, options: { wait_for_model: true } }),
      signal: ctrl.signal,
    });
    clearTimeout(to);
    if (!res.ok) {
      const t = await res.text();
      console.error('[RAG] embed error ' + res.status + ': ' + t.slice(0, 200));
      return null;
    }
    const data = await res.json();
    // Expected: [[float, float, ...], ...] — one vector per input
    if (!Array.isArray(data) || !Array.isArray(data[0])) {
      console.error('[RAG] embed unexpected shape: ' + JSON.stringify(data).slice(0, 200));
      return null;
    }
    return data;
  } catch (e) {
    console.error('[RAG] embed exception: ' + e.message);
    return null;
  }
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

// Extract text from various file types (PDF, txt, simple)
async function extractDocumentText(buffer, mime) {
  if (mime === 'application/pdf') {
    try {
      const pdfParse = require('pdf-parse');
      const r = await pdfParse(buffer);
      return r.text || '';
    } catch (e) {
      console.error('[DOC] pdf-parse error: ' + e.message);
      return null;
    }
  }
  if (mime && (mime.startsWith('text/') || mime === 'application/json' || mime === 'application/xml')) {
    return buffer.toString('utf-8');
  }
  // Fallback: try utf-8 anyway
  return buffer.toString('utf-8').slice(0, 200000);
}

// POST /api/features/documents — upload doc and store + embed chunks
router.post('/documents', async (req, res) => {
  try {
    const { name, mime, data } = req.body || {};
    if (!data || typeof data !== 'string') {
      return res.status(400).json({ success: false, error: 'data (base64) required' });
    }
    const buf = Buffer.from(data, 'base64');
    if (buf.length > 15 * 1024 * 1024) {
      return res.status(413).json({ success: false, error: 'File too large (max 15 MB)' });
    }
    const text = await extractDocumentText(buf, mime || 'application/octet-stream');
    if (!text || text.trim().length < 30) {
      return res.status(400).json({ success: false, error: 'Could not extract text from this document.' });
    }

    const insertDoc = await pool.query(
      `INSERT INTO documents (user_id, name, mime, size, text_content)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, name, mime, size, created_at`,
      [req.user.id, String(name || 'document').slice(0, 200), mime || 'application/octet-stream', buf.length, text.slice(0, 500000)]
    );
    const doc = insertDoc.rows[0];

    // Chunk + embed (best-effort; if HF fails, the doc is still usable in notebook mode without RAG search)
    const chunks = chunkText(text, 800, 100).slice(0, 80); // cap total chunks
    const vectors = await embedBatch(chunks);
    if (vectors) {
      const inserts = chunks.map((c, i) => pool.query(
        `INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding)
         VALUES ($1, $2, $3, $4)`,
        [doc.id, i, c, JSON.stringify(vectors[i] || [])]
      ));
      await Promise.all(inserts);
      console.log('[RAG] Embedded ' + chunks.length + ' chunks for doc#' + doc.id);
    } else {
      // Save chunks without embeddings as plain text (notebook still works)
      const inserts = chunks.map((c, i) => pool.query(
        `INSERT INTO document_chunks (document_id, chunk_index, chunk_text)
         VALUES ($1, $2, $3)`,
        [doc.id, i, c]
      ));
      await Promise.all(inserts);
      console.log('[RAG] Stored ' + chunks.length + ' chunks (no embeddings) for doc#' + doc.id);
    }

    return res.status(201).json({
      success: true,
      document: { ...doc, chunks_count: chunks.length, embeddings_ok: !!vectors },
    });
  } catch (e) {
    console.error('[DOC] upload error: ' + e.message);
    return res.status(500).json({ success: false, error: 'Upload failed: ' + e.message });
  }
});

// GET /api/features/documents — list user's documents
router.get('/documents', async (req, res) => {
  try {
    const r = await pool.query(
      `SELECT d.id, d.name, d.mime, d.size, d.created_at,
              (SELECT COUNT(*)::int FROM document_chunks WHERE document_id = d.id) AS chunks_count
       FROM documents d
       WHERE d.user_id = $1
       ORDER BY d.created_at DESC`,
      [req.user.id]
    );
    return res.json({ success: true, documents: r.rows });
  } catch (e) {
    console.error('[DOC] list error: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// DELETE /api/features/documents/:id
router.delete('/documents/:id', async (req, res) => {
  try {
    await pool.query('DELETE FROM documents WHERE id=$1 AND user_id=$2', [req.params.id, req.user.id]);
    await pool.query('DELETE FROM notebook_bindings WHERE document_id=$1 AND user_id=$2', [req.params.id, req.user.id]);
    return res.json({ success: true });
  } catch (e) {
    console.error('[DOC] delete: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// PUT /api/features/notebook — bind a document to a session (notebook mode)
// Body: { session_id, document_id, mode: 'notebook' | 'rag' | null (to unbind) }
router.put('/notebook', async (req, res) => {
  try {
    const { session_id, document_id, mode } = req.body || {};
    if (!session_id) return res.status(400).json({ success: false, error: 'session_id required' });
    if (!document_id) {
      await pool.query('DELETE FROM notebook_bindings WHERE user_id=$1 AND session_id=$2', [req.user.id, session_id]);
      return res.json({ success: true, binding: null });
    }
    const m = (mode === 'rag') ? 'rag' : 'notebook';
    await pool.query(
      `INSERT INTO notebook_bindings (user_id, session_id, document_id, mode)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (user_id, session_id) DO UPDATE SET document_id = $3, mode = $4`,
      [req.user.id, session_id, document_id, m]
    );
    return res.json({ success: true, binding: { session_id, document_id, mode: m } });
  } catch (e) {
    console.error('[NOTEBOOK] bind: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// GET /api/features/notebook?session_id=...
router.get('/notebook', async (req, res) => {
  try {
    const sid = String(req.query.session_id || '');
    if (!sid) return res.json({ success: true, binding: null });
    const r = await pool.query(
      `SELECT nb.session_id, nb.document_id, nb.mode, d.name, d.mime
       FROM notebook_bindings nb
       JOIN documents d ON d.id = nb.document_id
       WHERE nb.user_id=$1 AND nb.session_id=$2`,
      [req.user.id, sid]
    );
    return res.json({ success: true, binding: r.rows[0] || null });
  } catch (e) {
    console.error('[NOTEBOOK] get: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// Internal helper used by the chat route to enrich the prompt with notebook/RAG context
async function getNotebookContext(userId, sessionId, userQuery) {
  try {
    const b = await pool.query(
      `SELECT document_id, mode FROM notebook_bindings
       WHERE user_id=$1 AND session_id=$2`, [userId, sessionId]
    );
    if (!b.rows.length) return null;
    const docId = b.rows[0].document_id;
    const mode = b.rows[0].mode;
    const doc = await pool.query('SELECT name, text_content FROM documents WHERE id=$1', [docId]);
    if (!doc.rows.length) return null;
    const docName = doc.rows[0].name;

    if (mode === 'rag') {
      // Retrieve top-3 chunks by cosine similarity
      const chunks = await pool.query(
        `SELECT chunk_text, embedding FROM document_chunks WHERE document_id=$1`, [docId]
      );
      const queryVec = await embedBatch([String(userQuery || '')]);
      if (!queryVec || !queryVec[0]) {
        // Fallback: include first 3 chunks
        const txt = chunks.rows.slice(0, 3).map((r) => r.chunk_text).join('\n\n');
        return { docName, mode, snippet: txt };
      }
      const q = queryVec[0];
      const scored = chunks.rows
        .map((r) => {
          let v = []; try { v = JSON.parse(r.embedding || '[]'); } catch (_) {}
          return { text: r.chunk_text, score: v.length ? cosine(q, v) : 0 };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, 4);
      const snippet = scored.map((s, i) => `[Chunk ${i + 1}, score=${s.score.toFixed(3)}]\n${s.text}`).join('\n\n');
      return { docName, mode, snippet };
    } else {
      // notebook: include up to ~6000 chars of the document directly
      const txt = (doc.rows[0].text_content || '').slice(0, 6000);
      return { docName, mode, snippet: txt };
    }
  } catch (e) {
    console.error('[NOTEBOOK] ctx: ' + e.message);
    return null;
  }
}

// ════════════════════════════════════════════════════════════════════
// AUDIO TRANSCRIPTION (Groq Whisper, free tier)
// ════════════════════════════════════════════════════════════════════
// Body: { audio: base64, mime: "audio/webm" | "audio/mp3" }
router.post('/transcribe', async (req, res) => {
  try {
    const { audio, mime } = req.body || {};
    if (!audio) return res.status(400).json({ success: false, error: 'audio (base64) required' });
    const key = GROQ_KEY();
    if (!key) return res.status(503).json({ success: false, error: 'Transcription service not configured (GROQ_API_KEY missing).' });
    const buf = Buffer.from(audio, 'base64');
    if (buf.length > 25 * 1024 * 1024) return res.status(413).json({ success: false, error: 'Audio too large (max 25 MB).' });

    const ext = (mime || 'audio/webm').split('/')[1] || 'webm';
    const filename = 'audio.' + ext;

    // Build multipart manually — Groq accepts whisper-large-v3 / whisper-large-v3-turbo
    const formData = new FormData();
    formData.append('file', new Blob([buf], { type: mime || 'audio/webm' }), filename);
    formData.append('model', 'whisper-large-v3-turbo');
    formData.append('response_format', 'json');

    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), 60000);
    const r = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + key },
      body: formData,
      signal: ctrl.signal,
    });
    clearTimeout(to);
    if (!r.ok) {
      const t = await r.text();
      console.error('[TRANSCRIBE] groq error: ' + r.status + ' ' + t.slice(0, 200));
      return res.status(502).json({ success: false, error: 'Transcription failed: ' + r.status });
    }
    const data = await r.json();
    return res.json({ success: true, text: data.text || '' });
  } catch (e) {
    console.error('[TRANSCRIBE] error: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// ════════════════════════════════════════════════════════════════════
// YOUTUBE SUMMARIZER — fetch transcript via public service then summarize via Mistral via n8n
// We use the youtube-transcript JSON public service (no API key needed).
// ════════════════════════════════════════════════════════════════════
function extractYouTubeId(url) {
  if (!url) return null;
  const patterns = [
    /(?:youtu\.be\/|v=|\/embed\/|\/v\/)([a-zA-Z0-9_-]{11})/,
    /^([a-zA-Z0-9_-]{11})$/,
  ];
  for (const p of patterns) {
    const m = String(url).match(p);
    if (m) return m[1];
  }
  return null;
}

router.post('/youtube-transcript', async (req, res) => {
  try {
    const { url } = req.body || {};
    const id = extractYouTubeId(url);
    if (!id) return res.status(400).json({ success: false, error: 'Could not extract YouTube video id from URL.' });

    // Try the public timetext endpoint (works for videos with auto/CC captions)
    // Fallback: youtubetranscript.com style API
    const endpoints = [
      'https://youtubetotranscript.com/transcript?v=' + id + '&lang=en',
      'https://www.youtube.com/api/timedtext?v=' + id + '&lang=en&fmt=json3',
    ];

    let transcript = null;
    for (const ep of endpoints) {
      try {
        const r = await fetch(ep, { signal: AbortSignal.timeout ? AbortSignal.timeout(15000) : undefined });
        if (!r.ok) continue;
        const ct = r.headers.get('content-type') || '';
        if (ct.includes('json')) {
          const data = await r.json();
          if (data.events && Array.isArray(data.events)) {
            transcript = data.events.flatMap((e) => (e.segs || []).map((s) => s.utf8 || '')).join(' ').trim();
          } else if (Array.isArray(data) && data[0] && data[0].text) {
            transcript = data.map((d) => d.text).join(' ');
          } else if (typeof data === 'object' && data.transcript) {
            transcript = data.transcript;
          }
        } else {
          // HTML scraping fallback — extract visible text
          const html = await r.text();
          const stripped = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
          if (stripped.length > 200) transcript = stripped.slice(0, 50000);
        }
        if (transcript && transcript.length > 50) break;
      } catch (_) {}
    }

    if (!transcript) {
      return res.status(404).json({ success: false, error: 'No transcript available for this video.' });
    }

    return res.json({
      success: true,
      video_id: id,
      transcript: transcript.slice(0, 60000),
      length: transcript.length,
    });
  } catch (e) {
    console.error('[YT] error: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// ════════════════════════════════════════════════════════════════════
// IMAGE-TO-IMAGE EDIT (HF FLUX schnell with init image, fal-ai img2img)
// Body: { image: base64, prompt: string, mime: 'image/jpeg' | ... }
// ════════════════════════════════════════════════════════════════════
router.post('/image-edit', async (req, res) => {
  try {
    const { image, prompt, mime } = req.body || {};
    if (!image || !prompt) return res.status(400).json({ success: false, error: 'image + prompt required' });
    const buf = Buffer.from(image, 'base64');
    if (buf.length > 8 * 1024 * 1024) return res.status(413).json({ success: false, error: 'Image too large (max 8 MB).' });

    const dataUrl = 'data:' + (mime || 'image/jpeg') + ';base64,' + image;

    // fal-ai supports image-to-image via dedicated FLUX img2img endpoint
    const url = 'https://router.huggingface.co/fal-ai/fal-ai/flux/dev/image-to-image';
    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), 90000);
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + HF_KEY() },
      body: JSON.stringify({
        prompt: String(prompt).slice(0, 800),
        image_url: dataUrl,
        strength: 0.85,
        num_inference_steps: 28,
      }),
      signal: ctrl.signal,
    });
    clearTimeout(to);

    if (!r.ok) {
      const t = await r.text();
      console.error('[IMG-EDIT] fal-ai error ' + r.status + ': ' + t.slice(0, 200));
      return res.status(502).json({ success: false, error: 'Image edit service failed: ' + r.status });
    }
    const data = await r.json();
    const outUrl = data && data.images && data.images[0] && data.images[0].url;
    if (!outUrl) {
      return res.status(502).json({ success: false, error: 'Image edit returned no result.' });
    }
    // Fetch and embed as data URL
    const imgRes = await fetch(outUrl);
    const ab = await imgRes.arrayBuffer();
    const ct = imgRes.headers.get('content-type') || 'image/jpeg';
    const out = 'data:' + ct + ';base64,' + Buffer.from(ab).toString('base64');
    return res.json({ success: true, image_url: out });
  } catch (e) {
    console.error('[IMG-EDIT] error: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

// ════════════════════════════════════════════════════════════════════
// WORKFLOW CHAINS
// ════════════════════════════════════════════════════════════════════

// CRUD
router.get('/workflows', async (req, res) => {
  try {
    const r = await pool.query(
      `SELECT id, name, steps, created_at, updated_at FROM workflows
       WHERE user_id=$1 ORDER BY updated_at DESC`,
      [req.user.id]
    );
    return res.json({
      success: true,
      workflows: r.rows.map((w) => ({ ...w, steps: safeJSON(w.steps) || [] })),
    });
  } catch (e) {
    console.error('[WF] list: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

router.post('/workflows', async (req, res) => {
  try {
    const { name, steps } = req.body || {};
    if (!name || !Array.isArray(steps)) {
      return res.status(400).json({ success: false, error: 'name + steps[] required' });
    }
    const r = await pool.query(
      `INSERT INTO workflows (user_id, name, steps) VALUES ($1, $2, $3)
       RETURNING id, name, steps, created_at, updated_at`,
      [req.user.id, String(name).slice(0, 120), JSON.stringify(steps)]
    );
    return res.status(201).json({ success: true, workflow: { ...r.rows[0], steps } });
  } catch (e) {
    console.error('[WF] create: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

router.put('/workflows/:id', async (req, res) => {
  try {
    const { name, steps } = req.body || {};
    const r = await pool.query(
      `UPDATE workflows SET name=$1, steps=$2, updated_at=NOW()
       WHERE id=$3 AND user_id=$4
       RETURNING id, name, steps, created_at, updated_at`,
      [String(name).slice(0, 120), JSON.stringify(steps || []), req.params.id, req.user.id]
    );
    if (!r.rows.length) return res.status(404).json({ success: false, error: 'Not found' });
    return res.json({ success: true, workflow: { ...r.rows[0], steps } });
  } catch (e) {
    console.error('[WF] update: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

router.delete('/workflows/:id', async (req, res) => {
  try {
    await pool.query('DELETE FROM workflows WHERE id=$1 AND user_id=$2', [req.params.id, req.user.id]);
    return res.json({ success: true });
  } catch (e) {
    console.error('[WF] delete: ' + e.message);
    return res.status(500).json({ success: false, error: 'Internal error' });
  }
});

function safeJSON(s) {
  try { return JSON.parse(s); } catch (_) { return null; }
}

module.exports = { router, getNotebookContext };
