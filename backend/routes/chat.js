const express = require('express');
const PDFDocument = require('pdfkit');
const { createWorker } = require('tesseract.js');
const { pool } = require('../db/index');
const { authenticateToken } = require('../middleware/auth');
const { getNotebookContext } = require('./features');
const llmRouter = require('../services/llmRouter');

const router = express.Router();

// All routes require authentication
router.use(authenticateToken);

// ── Tesseract OCR worker (lazily created, reused across requests) ─
let _ocrWorker = null;
let _ocrWorkerPromise = null;
async function getOcrWorker() {
  if (_ocrWorker) return _ocrWorker;
  if (_ocrWorkerPromise) return _ocrWorkerPromise;
  _ocrWorkerPromise = (async () => {
    try {
      const worker = await createWorker(['eng', 'fra']);
      _ocrWorker = worker;
      console.log('[OCR] Tesseract worker ready (eng+fra)');
      return worker;
    } catch (e) {
      console.error('[OCR] Failed to create worker:', e.message);
      _ocrWorkerPromise = null;
      throw e;
    }
  })();
  return _ocrWorkerPromise;
}

async function extractImageText(base64Data) {
  try {
    const worker = await getOcrWorker();
    const buf = Buffer.from(base64Data, 'base64');
    const { data } = await worker.recognize(buf);
    const text = (data && data.text ? data.text : '').trim();
    // Filter out garbage OCR (confidence too low, or just whitespace)
    if (!text || text.length < 5) return null;
    return text;
  } catch (e) {
    console.error('[OCR] Recognize error:', e.message);
    return null;
  }
}

// ── Image visual caption via HuggingFace (fallback when no text in image) ──
async function describeImageWithHF(base64Data, mime) {
  try {
    const binary = Buffer.from(base64Data, 'base64');
    const endpoints = [
      'https://router.huggingface.co/hf-inference/models/Salesforce/blip-image-captioning-large',
      'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large',
    ];
    for (const url of endpoints) {
      try {
        const ctrl = new AbortController();
        const to = setTimeout(() => ctrl.abort(), 20000);
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.HF_API_KEY || ''}`,
            'Content-Type': mime || 'image/jpeg',
          },
          body: binary,
          signal: ctrl.signal,
        });
        clearTimeout(to);
        if (!res.ok) continue;
        const data = await res.json();
        if (Array.isArray(data) && data[0] && data[0].generated_text) return data[0].generated_text;
        if (data && data.generated_text) return data.generated_text;
      } catch (_) { /* try next */ }
    }
    return null;
  } catch (e) {
    console.error('[HF caption] error:', e.message);
    return null;
  }
}

// ── Build a PDF buffer from markdown-ish content ───────────────────
function buildPdfBuffer({ title, content, author }) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: 'A4',
        margins: { top: 64, bottom: 64, left: 64, right: 64 },
        info: {
          Title: title || 'AstroBot Report',
          Author: author || 'AstroBot',
          Creator: 'AstroBot V2',
        },
      });
      const chunks = [];
      doc.on('data', (c) => chunks.push(c));
      doc.on('end', () => resolve(Buffer.concat(chunks)));
      doc.on('error', reject);

      // Header bar
      doc.rect(0, 0, doc.page.width, 44).fill('#0d1b35');
      doc.fillColor('#00d4ff').font('Helvetica-Bold').fontSize(14)
        .text('ASTROBOT', 64, 16, { align: 'left' });
      doc.fillColor('#ffffff').font('Helvetica').fontSize(9)
        .text(new Date().toLocaleString(), 0, 18, { align: 'right', width: doc.page.width - 64 });

      // Title
      doc.moveDown(3);
      doc.fillColor('#000').font('Helvetica-Bold').fontSize(22)
        .text(title || 'AstroBot Report', { align: 'left' });
      doc.moveDown(0.3);
      doc.strokeColor('#00d4ff').lineWidth(1.2)
        .moveTo(64, doc.y).lineTo(doc.page.width - 64, doc.y).stroke();
      doc.moveDown(0.8);

      // Body — lightweight markdown handling: **bold**, headings ##/###, bullets "- "
      doc.font('Helvetica').fontSize(11).fillColor('#1a1a1a');
      const lines = String(content || '').split(/\r?\n/);
      for (const raw of lines) {
        const line = raw || '';
        if (!line.trim()) { doc.moveDown(0.5); continue; }

        if (/^###\s+/.test(line)) {
          doc.moveDown(0.4);
          doc.font('Helvetica-Bold').fontSize(12).fillColor('#0d47a1')
            .text(line.replace(/^###\s+/, ''));
          doc.font('Helvetica').fontSize(11).fillColor('#1a1a1a');
          continue;
        }
        if (/^##\s+/.test(line)) {
          doc.moveDown(0.5);
          doc.font('Helvetica-Bold').fontSize(14).fillColor('#0d1b35')
            .text(line.replace(/^##\s+/, ''));
          doc.font('Helvetica').fontSize(11).fillColor('#1a1a1a');
          continue;
        }
        if (/^#\s+/.test(line)) {
          doc.moveDown(0.6);
          doc.font('Helvetica-Bold').fontSize(16).fillColor('#000')
            .text(line.replace(/^#\s+/, ''));
          doc.font('Helvetica').fontSize(11).fillColor('#1a1a1a');
          continue;
        }
        const bulletMatch = line.match(/^\s*[-*]\s+(.*)$/);
        if (bulletMatch) {
          doc.text('• ' + bulletMatch[1], { indent: 12 });
          continue;
        }

        // Inline bold **...** — split and render
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        if (parts.length > 1) {
          parts.forEach((part, i) => {
            const isBold = /^\*\*([^*]+)\*\*$/.test(part);
            const text = isBold ? part.slice(2, -2) : part;
            if (isBold) doc.font('Helvetica-Bold');
            else doc.font('Helvetica');
            doc.text(text, { continued: i < parts.length - 1 });
          });
          doc.moveDown(0.1);
          doc.font('Helvetica');
        } else {
          doc.text(line);
        }
      }

      // Footer
      const range = doc.bufferedPageRange();
      for (let i = range.start; i < range.start + range.count; i++) {
        doc.switchToPage(i);
        doc.fontSize(8).fillColor('#888')
          .text(
            'Generated by AstroBot · Page ' + (i - range.start + 1) + ' / ' + range.count,
            64,
            doc.page.height - 40,
            { align: 'center', width: doc.page.width - 128 }
          );
      }

      doc.end();
    } catch (e) {
      reject(e);
    }
  });
}

// Persona instructions appended to the user prompt (since the n8n workflow's
// system message is static, we inject the persona into the user-visible message
// as a discreet instruction — Mistral treats it as a sub-role directive).
const PERSONA_PROMPTS = {
  default: null,
  formal:    '[Respond in a formal, professional tone. Use precise vocabulary and full sentences.]',
  casual:    '[Respond in a relaxed, friendly, conversational tone — like a helpful friend.]',
  teacher:   '[Respond as a patient teacher: explain concepts step by step, use analogies, and check understanding.]',
  dev:       '[Respond as a senior software engineer: technical, concise, code-first, mention trade-offs.]',
  poet:      '[Respond with poetic flair — imagery, rhythm, and metaphor, while still answering the question.]',
  scientist: '[Respond as a rigorous scientist: cite facts, use neutral language, acknowledge uncertainty.]',
};

// POST /api/chat/message
router.post('/message', async (req, res) => {
  try {
    const { message, session_id, audio, attachment, attachments, persona } = req.body;
    const userId = req.user.id;

    // Normalize attachments input — support both single `attachment` and `attachments` array
    const attList = Array.isArray(attachments) && attachments.length > 0
      ? attachments
      : (attachment && typeof attachment === 'object' && attachment.data ? [attachment] : []);
    const hasAttachment = attList.length > 0;

    if ((!message || message.trim().length === 0) && !hasAttachment) {
      return res.status(400).json({ success: false, error: 'Message cannot be empty.' });
    }
    if (message && message.trim().length > 4000) {
      return res.status(400).json({ success: false, error: 'Message is too long. Maximum 4000 characters.' });
    }
    // Validate each attachment size
    for (const a of attList) {
      if (!a || !a.data || typeof a.data !== 'string') {
        return res.status(400).json({ success: false, error: 'Malformed attachment.' });
      }
      if (a.data.length > 14 * 1024 * 1024) {
        return res.status(413).json({ success: false, error: 'One of the attachments exceeds 10 MB.' });
      }
    }

    // Fetch last 15 messages for conversation context (ordered oldest→newest)
    const historyResult = await pool.query(
      `SELECT message, response FROM conversations
       WHERE user_id = $1
       ORDER BY created_at DESC LIMIT 15`,
      [userId]
    );
    const conversationHistory = historyResult.rows.reverse().map(r => ({
      role_user: r.message,
      role_assistant: r.response
    }));

    let botResponse = null;
    let imageUrl = null;

    // Build the effective message sent to n8n. Includes:
    //   (a) persona directive if chosen
    //   (b) user's text
    //   (c) per-attachment metadata + OCR/caption analysis for images
    let effectiveMessage = (message || '').trim();

    const personaDirective = persona && PERSONA_PROMPTS[persona] ? PERSONA_PROMPTS[persona] : null;
    if (personaDirective) {
      effectiveMessage = personaDirective + '\n\n' + effectiveMessage;
    }

    if (hasAttachment) {
      const parts = [];
      for (let idx = 0; idx < attList.length; idx++) {
        const att = attList[idx];
        const mime = String(att.mime || '');
        const isImg = mime.startsWith('image/');
        const sizeKb = att.size ? Math.round(att.size / 1024) + ' KB' : 'unknown size';
        const header = `[Attachment ${idx + 1}/${attList.length} — ${isImg ? 'Image' : 'File'} "${att.name}" · ${mime} · ${sizeKb}]`;

        let analysis = '';
        if (isImg) {
          const [ocrText, caption] = await Promise.all([
            extractImageText(att.data),
            describeImageWithHF(att.data, mime),
          ]);
          if (ocrText) {
            const snippet = ocrText.length > 3000 ? ocrText.slice(0, 3000) + '\n... [truncated]' : ocrText;
            analysis += `\n[OCR text extracted (via Tesseract):\n"""\n${snippet}\n"""]`;
          }
          if (caption) analysis += `\n[Visual description (via BLIP): ${caption}]`;
          if (!ocrText && !caption) analysis += '\n[Note: Could not extract text or visual description.]';
        }
        parts.push(header + analysis);
      }

      const userText = effectiveMessage
        ? effectiveMessage
        : 'The user sent attachment(s) without any written message.';
      effectiveMessage = `${userText}\n\n${parts.join('\n\n')}`.trim();
    }

    // ── Notebook / RAG context (if a document is bound to this session) ──
    try {
      const ctx = await getNotebookContext(userId, session_id || `user_${userId}`, message || '');
      if (ctx && ctx.snippet) {
        const header = ctx.mode === 'rag'
          ? `[Document context (RAG retrieval from "${ctx.docName}") — answer using these passages whenever relevant:]`
          : `[Notebook document "${ctx.docName}" attached as permanent context — refer to it for the user's questions:]`;
        effectiveMessage = `${effectiveMessage}\n\n${header}\n"""\n${ctx.snippet}\n"""\n`;
      }
    } catch (e) {
      console.error('[CHAT] notebook ctx error:', e.message);
    }

    // ── Ask the active engine (admin-selected provider, or the n8n workflow) ──
    let engineUsed = 'n8n';
    try {
      const n8nPayload = {
        user_id: userId,
        user_name: req.user.name,
        user_surname: req.user.surname,
        user_email: req.user.email,
        message: effectiveMessage,
        session_id: session_id || `user_${userId}`,
        audio: audio || null,
        // First attachment (backward-compat with existing n8n workflow)
        attachment: hasAttachment
          ? {
              name: String(attList[0].name || 'file').slice(0, 200),
              mime: String(attList[0].mime || 'application/octet-stream').slice(0, 100),
              size: Number(attList[0].size || 0),
              data: attList[0].data,
            }
          : null,
        // Full array for workflows that support multiple
        attachments: hasAttachment ? attList.map((a) => ({
          name: String(a.name || 'file').slice(0, 200),
          mime: String(a.mime || 'application/octet-stream').slice(0, 100),
          size: Number(a.size || 0),
          data: a.data,
        })) : [],
        persona: persona || 'default',
        conversation_history: conversationHistory,
      };
      const result = await llmRouter.generateReply({
        user: req.user,
        effectiveMessage,
        conversationHistory,
        n8nPayload,
      });
      botResponse = result.text;
      imageUrl = result.imageUrl || null;
      engineUsed = result.engine;
      if (result.fallback) console.warn('[CHAT] provider failed, answered by n8n fallback');
    } catch (engineErr) {
      console.error('[CHAT] engine error:', engineErr.message);
      botResponse = "I'm currently offline from my main systems. Please check back shortly, Commander.";
    }

    // Check if AI wants to generate an image/pdf
    let parsedAIResponse = null;
    try {
      const cleaned = botResponse.replace(/```json/g, '').replace(/```/g, '').trim();
      parsedAIResponse = JSON.parse(cleaned);
    } catch (e) {
      parsedAIResponse = null;
    }

    // Debug: log what came back from the AI (truncated)
    const logSnippet = typeof botResponse === 'string'
      ? botResponse.slice(0, 200).replace(/\n/g, ' ')
      : '';
    console.log('[CHAT] n8n raw response (first 200): ' + logSnippet);
    if (parsedAIResponse) {
      console.log('[CHAT] parsed action=' + (parsedAIResponse.action || 'none')
        + ', has_pdf_content=' + !!parsedAIResponse.pdf_content
        + ', pdf_content_len=' + (parsedAIResponse.pdf_content ? String(parsedAIResponse.pdf_content).length : 0));
    }

    // ── Heuristic PDF trigger ─────────────────────────────────────
    // If the AI forgot to set action:"generate_pdf" but the user's request
    // and the bot's acknowledgment both indicate a PDF, force the action.
    const responseText =
      (parsedAIResponse && parsedAIResponse.response) ||
      (typeof botResponse === 'string' ? botResponse : '') ||
      '';

    const userAsksPdf = /\b(pdf|rapport|document|fiche|exporte?r?|telecharger|t[eé]l[eé]charger)\b/i
      .test((message || '').toLowerCase());
    const botAcksPdf = /voici ton pdf|here'?s your pdf|pdf (est )?pr[eê]t|your pdf is ready|t[eé]l[eé]charger? ci-dessous|download it below/i
      .test(responseText);

    if (userAsksPdf && botAcksPdf) {
      if (!parsedAIResponse) parsedAIResponse = {};
      if (parsedAIResponse.action !== 'generate_pdf') {
        parsedAIResponse.action = 'generate_pdf';
        console.log('[PDF] Heuristic trigger activated (user asked + bot acknowledged, but action was missing)');
      }
    }

    // ── Heuristic IMAGE trigger ───────────────────────────────────
    // Same idea for image generation: if user asks for an image and the bot
    // says it's generating but didn't set the action, force it.
    const userAsksImage = /\b(image|dessin|dessine|illustration|generer?\s+.{0,20}(image|photo)|generate.{0,20}(image|picture)|draw|dessiner?|photo\s+de|picture of)\b/i
      .test((message || '').toLowerCase());
    const botAcksImage = /je g[eé]n[eè]re (l'?image|une image)|g[eé]n[eé]ration.{0,20}image|generating.{0,20}image|un instant.{0,10}[.!…]|voici.{0,5}(ton|votre).{0,5}image|here'?s your image/i
      .test(responseText);

    if (userAsksImage && botAcksImage) {
      if (!parsedAIResponse) parsedAIResponse = {};
      if (parsedAIResponse.action !== 'generate_image') {
        parsedAIResponse.action = 'generate_image';
        console.log('[IMAGE] Heuristic trigger activated (user asked + bot acknowledged, but action was missing)');
      }
      // Provide a default prompt if AI omitted image_prompt
      if (!parsedAIResponse.image_prompt) {
        // Strip common request phrasing to extract the subject
        parsedAIResponse.image_prompt = String(message || '')
          .replace(/g[eé]n[eè]re?\s*(une\s+|moi\s+|une?\s+)?(image|photo|illustration|dessin)\s*(de|du|d'|sur)?/gi, '')
          .replace(/can you (generate|make|draw|create)\s*(an?\s+)?(image|picture|illustration)\s*(of)?/gi, '')
          .replace(/dessine(-moi)?\s*/gi, '')
          .replace(/draw(\s+me)?\s*/gi, '')
          .trim() || 'beautiful digital artwork';
        console.log('[IMAGE] Using fallback prompt: "' + parsedAIResponse.image_prompt + '"');
      }
    }

    let pdfDataUrl = null;
    let pdfFilename = null;

    if (parsedAIResponse && parsedAIResponse.action === 'generate_pdf') {
      // Resolve pdf content: use what the AI provided, else fall back to the last
      // SUBSTANTIVE assistant message in history (skipping short acks like
      // "Voici ton PDF...").
      let pdfContent = parsedAIResponse.pdf_content;
      const pdfTitle = parsedAIResponse.pdf_title || 'AstroBot Report';

      function stripJsonWrap(s) {
        if (!s) return s;
        try {
          const cleaned = String(s).replace(/```json/g, '').replace(/```/g, '').trim();
          const p = JSON.parse(cleaned);
          if (p && typeof p.response === 'string') return p.response;
        } catch (_) {}
        return s;
      }

      if (!pdfContent || String(pdfContent).trim().length < 40) {
        // Walk history from most recent to oldest, skipping short ack messages
        let found = null;
        for (let i = conversationHistory.length - 1; i >= 0; i--) {
          const raw = conversationHistory[i].role_assistant;
          if (!raw) continue;
          const unwrapped = stripJsonWrap(raw).trim();
          // Skip short / ack-like messages ("Voici ton PDF...", etc.)
          if (unwrapped.length < 120) continue;
          if (/voici ton pdf|here'?s your pdf|your pdf is ready/i.test(unwrapped)) continue;
          found = unwrapped;
          break;
        }
        if (found) {
          pdfContent = found;
          console.log('[PDF] Using fallback content from history (' + pdfContent.length + ' chars)');
        } else {
          console.log('[PDF] No substantive history message found for fallback');
        }
      }

      if (pdfContent && String(pdfContent).trim().length >= 20) {
        botResponse = parsedAIResponse.response || 'Your PDF is ready, Commander.';
        try {
          const buf = await buildPdfBuffer({
            title: pdfTitle,
            content: String(pdfContent),
            author: `${req.user.name} ${req.user.surname}`,
          });
          pdfDataUrl = 'data:application/pdf;base64,' + buf.toString('base64');
          pdfFilename =
            String(pdfTitle)
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-|-$/g, '')
              .slice(0, 60) || 'astrobot-report';
          pdfFilename += '.pdf';
          console.log('[PDF] Generated: ' + pdfFilename + ' (' + Math.round(buf.length / 1024) + ' KB)');
        } catch (pdfErr) {
          console.error('[PDF] Generation error:', pdfErr.message);
          botResponse = 'Commander, I had trouble generating the PDF. Please try again.';
        }
      } else {
        console.warn('[PDF] Action=generate_pdf but no content resolvable');
        botResponse =
          parsedAIResponse.response ||
          "Commander, I'd need a bit more context about what to include in the PDF. Ask me first, then request the document.";
      }
    } else if (parsedAIResponse && parsedAIResponse.action === 'generate_image' && parsedAIResponse.image_prompt) {
      botResponse = parsedAIResponse.response || "I'm generating the image for you, Commander...";
      const prompt = String(parsedAIResponse.image_prompt).slice(0, 800);
      console.log('[IMAGE] Calling image provider with prompt: "' + prompt.slice(0, 120) + '"');
      const hfKey = process.env.HF_API_KEY || '';

      // Ordered list of providers (first success wins). SDXL is deprecated,
      // so FLUX.1-schnell is the primary. fal-ai flux schnell is the fallback.
      const providers = [
        {
          name: 'FLUX.1-schnell (hf-inference)',
          url: 'https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell',
          body: { inputs: prompt },
          responseType: 'binary',
        },
        {
          name: 'FLUX schnell (fal-ai)',
          url: 'https://router.huggingface.co/fal-ai/fal-ai/flux/schnell',
          body: { prompt: prompt },
          responseType: 'url',
        },
      ];

      for (const p of providers) {
        try {
          const ctrl = new AbortController();
          const to = setTimeout(() => ctrl.abort(), 60000);
          const res = await fetch(p.url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${hfKey}` },
            body: JSON.stringify(p.body),
            signal: ctrl.signal,
          });
          clearTimeout(to);

          if (!res.ok) {
            const errText = await res.text();
            console.error('[IMAGE] ' + p.name + ' HTTP ' + res.status + ': ' + errText.slice(0, 200));
            continue;
          }

          if (p.responseType === 'binary') {
            const ct = res.headers.get('content-type') || 'image/jpeg';
            if (ct.includes('application/json')) {
              const txt = await res.text();
              console.error('[IMAGE] ' + p.name + ' returned JSON: ' + txt.slice(0, 200));
              continue;
            }
            const buf = await res.arrayBuffer();
            imageUrl = 'data:' + ct + ';base64,' + Buffer.from(buf).toString('base64');
            console.log('[IMAGE] Generated via ' + p.name + ' (' + Math.round(buf.byteLength / 1024) + ' KB)');
            break;
          } else if (p.responseType === 'url') {
            const data = await res.json();
            const imgUrl = data && data.images && data.images[0] && data.images[0].url;
            if (!imgUrl) { console.error('[IMAGE] ' + p.name + ': no url in response'); continue; }
            // Fetch the image and embed as data URL so it doesn't expire
            const imgRes = await fetch(imgUrl, { signal: AbortSignal.timeout ? AbortSignal.timeout(30000) : undefined });
            if (!imgRes.ok) { console.error('[IMAGE] fal-ai CDN fetch failed: ' + imgRes.status); continue; }
            const buf = await imgRes.arrayBuffer();
            const ct = imgRes.headers.get('content-type') || 'image/jpeg';
            imageUrl = 'data:' + ct + ';base64,' + Buffer.from(buf).toString('base64');
            console.log('[IMAGE] Generated via ' + p.name + ' (' + Math.round(buf.byteLength / 1024) + ' KB, proxied)');
            break;
          }
        } catch (err) {
          console.error('[IMAGE] ' + p.name + ' error: ' + err.message);
        }
      }

      if (!imageUrl) {
        botResponse =
          "Commander, I tried to generate the image but my art systems are offline right now. " +
          "The prompt was: \"" + prompt.slice(0, 120) + "\". " +
          "Try again in a moment, or rephrase your request.";
      }
    } else if (parsedAIResponse && parsedAIResponse.response) {
      // AI returned valid JSON with response field — use it directly
      botResponse = parsedAIResponse.response;
    }

    // Persist user attachment metadata + first-attachment data URL so that
    // when the user revisits the session, the image/file preview is restored.
    let attachmentJson = null;
    if (hasAttachment) {
      const a0 = attList[0];
      try {
        attachmentJson = JSON.stringify({
          name: a0.name,
          mime: a0.mime,
          size: a0.size,
          dataUrl: 'data:' + a0.mime + ';base64,' + a0.data,
          count: attList.length, // for indication if multiple
        });
      } catch (_) { attachmentJson = null; }
    }

    // Save conversation to DB
    const result = await pool.query(
      `INSERT INTO conversations
         (user_id, message, response, session_id, image_url, pdf_url, pdf_filename, attachment, engine)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       RETURNING id, message, response, session_id, image_url, pdf_url, pdf_filename, attachment, created_at`,
      [
        userId,
        (message && message.trim()) ||
          (hasAttachment
            ? `[Attachment: ${attList.map(a => a.name).join(', ')}]`
            : ''),
        botResponse,
        session_id || null,
        imageUrl,
        pdfDataUrl,
        pdfFilename,
        attachmentJson,
        engineUsed,
      ]
    );

    const conversation = result.rows[0];

    return res.status(200).json({
      success: true,
      data: {
        id: conversation.id,
        message: conversation.message,
        response: conversation.response,
        image_url: imageUrl,
        pdf_url: pdfDataUrl,
        pdf_filename: pdfFilename,
        session_id: conversation.session_id,
        createdAt: conversation.created_at,
      },
    });
  } catch (err) {
    console.error('[CHAT] Message error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

// DELETE /api/chat/:id
router.delete('/:id', async (req, res) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;
    const result = await pool.query(
      'DELETE FROM conversations WHERE id = $1 AND user_id = $2 RETURNING id',
      [id, userId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Conversation not found.' });
    }
    return res.status(200).json({ success: true });
  } catch (err) {
    console.error('[CHAT] Delete error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

// Helper: parse stored attachment JSON safely
function parseAttachment(raw) {
  if (!raw) return null;
  try {
    const o = typeof raw === 'string' ? JSON.parse(raw) : raw;
    return o && typeof o === 'object' ? o : null;
  } catch (_) { return null; }
}

// GET /api/chat/history
router.get('/history', async (req, res) => {
  try {
    const userId = req.user.id;

    const result = await pool.query(
      `SELECT id, message, response, image_url, pdf_url, pdf_filename, attachment, created_at
       FROM conversations
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT 50`,
      [userId]
    );

    // Return in chronological order (oldest first)
    const conversations = result.rows.reverse();

    return res.status(200).json({
      success: true,
      data: conversations.map((c) => ({
        id: c.id,
        message: c.message,
        response: c.response,
        image_url: c.image_url || null,
        pdf_url: c.pdf_url || null,
        pdf_filename: c.pdf_filename || null,
        attachment: parseAttachment(c.attachment),
        createdAt: c.created_at,
      })),
      count: conversations.length,
    });
  } catch (err) {
    console.error('[CHAT] History error:', err.message);
    return res.status(500).json({
      success: false,
      error: 'Internal server error. Please try again later.',
    });
  }
});

// PUT /api/chat/sessions/:session_id/tag — set/clear a tag (folder) for a session
router.put('/sessions/:session_id/tag', async (req, res) => {
  try {
    const userId = req.user.id;
    const { session_id } = req.params;
    const { tag } = req.body || {};
    const cleaned = (typeof tag === 'string' && tag.trim()) ? tag.trim().slice(0, 80) : null;
    await pool.query(
      `UPDATE conversations SET session_tag = $1
       WHERE user_id = $2 AND session_id = $3`,
      [cleaned, userId, session_id]
    );
    return res.json({ success: true, tag: cleaned });
  } catch (err) {
    console.error('[CHAT] tag update error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// GET /api/chat/tags — distinct tags used by current user
router.get('/tags', async (req, res) => {
  try {
    const r = await pool.query(
      `SELECT DISTINCT session_tag FROM conversations
       WHERE user_id = $1 AND session_tag IS NOT NULL
       ORDER BY session_tag ASC`,
      [req.user.id]
    );
    return res.json({ success: true, tags: r.rows.map((x) => x.session_tag) });
  } catch (err) {
    console.error('[CHAT] tags list error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal error.' });
  }
});

// GET /api/chat/sessions
router.get('/sessions', async (req, res) => {
  try {
    const userId = req.user.id;

    const result = await pool.query(
      `SELECT DISTINCT ON (session_id) session_id, message, created_at,
        (SELECT session_tag FROM conversations c2
         WHERE c2.session_id = conversations.session_id AND c2.user_id = $1
           AND c2.session_tag IS NOT NULL LIMIT 1) AS session_tag
       FROM conversations
       WHERE user_id = $1 AND session_id IS NOT NULL
       ORDER BY session_id, created_at ASC`,
      [userId]
    );

    // Sort by created_at DESC (most recent session first)
    const sessions = result.rows.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    return res.status(200).json({
      success: true,
      data: sessions.map((s) => ({
        session_id: s.session_id,
        first_message: s.message,
        tag: s.session_tag || null,
        createdAt: s.created_at,
      })),
    });
  } catch (err) {
    console.error('[CHAT] Sessions error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

// GET /api/chat/session/:session_id
router.get('/session/:session_id', async (req, res) => {
  try {
    const userId = req.user.id;
    const { session_id } = req.params;

    const result = await pool.query(
      `SELECT id, message, response, image_url, pdf_url, pdf_filename, attachment, created_at
       FROM conversations
       WHERE user_id = $1 AND session_id = $2
       ORDER BY created_at ASC`,
      [userId, session_id]
    );

    return res.status(200).json({
      success: true,
      data: result.rows.map((c) => ({
        id: c.id,
        message: c.message,
        response: c.response,
        image_url: c.image_url || null,
        pdf_url: c.pdf_url || null,
        pdf_filename: c.pdf_filename || null,
        attachment: parseAttachment(c.attachment),
        createdAt: c.created_at,
      })),
    });
  } catch (err) {
    console.error('[CHAT] Session messages error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});


// GET /api/chat/export/:session_id?format=pdf|md|json
router.get('/export/:session_id', async (req, res) => {
  try {
    const userId = req.user.id;
    const { session_id } = req.params;
    const format = (req.query.format || 'md').toLowerCase();

    const r = await pool.query(
      `SELECT id, message, response, created_at
       FROM conversations
       WHERE user_id = $1 AND session_id = $2
       ORDER BY created_at ASC`,
      [userId, session_id]
    );
    if (r.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'No conversation to export.' });
    }

    const who = `${req.user.name} ${req.user.surname}`;
    const when = new Date().toLocaleString();

    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', `attachment; filename="astrobot-${session_id}.json"`);
      return res.send(JSON.stringify({
        session_id,
        exported_at: new Date().toISOString(),
        user: who,
        messages: r.rows.map((c) => ({
          user: c.message,
          bot: c.response,
          at: c.created_at,
        })),
      }, null, 2));
    }

    if (format === 'md') {
      const lines = [`# AstroBot Conversation`, ``, `**User:** ${who}  `, `**Exported:** ${when}  `, `**Session:** ${session_id}`, ``, `---`, ``];
      for (const c of r.rows) {
        lines.push(`### 🧑 ${who}`);
        lines.push('');
        lines.push(c.message || '');
        lines.push('');
        lines.push(`### 🤖 AstroBot`);
        lines.push('');
        lines.push(c.response || '');
        lines.push('');
        lines.push('---');
        lines.push('');
      }
      res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
      res.setHeader('Content-Disposition', `attachment; filename="astrobot-${session_id}.md"`);
      return res.send(lines.join('\n'));
    }

    // PDF (default)
    const content = r.rows
      .map((c) => `## 🧑 ${who}\n\n${c.message || ''}\n\n## 🤖 AstroBot\n\n${c.response || ''}\n\n---\n`)
      .join('\n');
    const buf = await buildPdfBuffer({
      title: 'AstroBot Conversation',
      content,
      author: who,
    });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="astrobot-${session_id}.pdf"`);
    return res.send(buf);
  } catch (err) {
    console.error('[EXPORT] error:', err.message);
    return res.status(500).json({ success: false, error: 'Export failed.' });
  }
});

// DELETE /api/chat/sessions/:session_id
router.delete('/sessions/:session_id', async (req, res) => {
  try {
    const userId = req.user.id;
    const { session_id } = req.params;
    const result = await pool.query(
      'DELETE FROM conversations WHERE session_id = $1 AND user_id = $2 RETURNING id',
      [session_id, userId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Session not found.' });
    }
    return res.status(200).json({ success: true, deleted: result.rows.length });
  } catch (err) {
    console.error('[CHAT] Session delete error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

module.exports = router;
