#!/usr/bin/env python3
"""
AstroBot — Speaker Notes / Talking Points generator.

Produces a printable PDF that mirrors the 32-slide deck and gives
each presenter the exact lines they should say, in English, with a
suggested time allocation. One slide per page, designed to be printed
and held during the 15-minute talk.

Run:
    python presentation/build_speaker_notes.py

Output:
    presentation/AstroBot_Speaker_Notes.pdf
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = Path(__file__).resolve().parent / "AstroBot_Speaker_Notes.pdf"

# ─── Brand palette (matches the deck) ────────────────────────────────
NAVY = HexColor("#0F1A35")
PURPLE = HexColor("#7B2CBF")
CYAN = HexColor("#06B6D4")
GOLD = HexColor("#F9C94D")
LIGHT = HexColor("#F6F7FB")
INK = HexColor("#141B2D")
INK_SOFT = HexColor("#404A66")
WHITE = HexColor("#FFFFFF")
GREEN_OK = HexColor("#16A34A")
LINE = HexColor("#D6D9E0")


# ─── Speaker assignments ─────────────────────────────────────────────
SIDI = "Sidi Mohamed Sall"
TIDIANE = "Tidiane Konaté"
AHMED = "Ahmed Essalem"
SAAD = "Saad Ibrahim Houssein"
ALL = "Anyone (opening)"


# ─── Slide-by-slide notes ────────────────────────────────────────────
# Each entry: (slide_no, title, presenter, presenter_color, time_seconds, body)
# body is a list of (kind, content) tuples where:
#   - ('say', text)  : a paragraph to read out loud
#   - ('cue', text)  : a stage direction or quick beat
#   - ('hint', text) : a tip to remember
NOTES = [
    (1, "Cover · AstroBot", SIDI, PURPLE, 15, [
        ('cue', "Open with a smile. The whole jury is watching this slide while you settle in."),
        ('say', "Good morning. We are presenting AstroBot — an intelligent conversational AI assistant — our graduation project for course MFBP 402. We are four engineers, our advisor is Assist. Prof. Dr. Yücel Tekin, and over the next fifteen minutes we will walk you through the project in four parts."),
        ('hint', "Speak slowly on this slide — your nerves are highest now."),
    ]),

    (2, "Meet the Team", SIDI, PURPLE, 30, [
        ('cue', "Look at each photo as you name the person."),
        ('say', "First, our team. Tidiane Konaté led the architecture, backend and deployment work. I — Sidi Mohamed Sall — focused on the product vision and user experience. Ahmed Essalem built the AI integration layer and all the multimodal features. And Saad Ibrahim Houssein owned testing, the frontend polish, and our admin dashboard."),
        ('say', "Our advisor — Assist. Prof. Dr. Yücel Tekin — supported us throughout the four months of the project."),
    ]),

    (3, "Agenda", SIDI, PURPLE, 30, [
        ('say', "The presentation has four parts. I will start by introducing the problem we set out to solve and the goals we set for ourselves. Tidiane will then take you through the system architecture and our design choices."),
        ('say', "Ahmed will demonstrate the implementation — the chat experience and all the AI-powered features. And Saad will close with the admin dashboard, our test suite, and how we deployed everything to production."),
        ('cue', "End with: \"Let's begin.\" Pause. Click."),
    ]),

    (4, "Part 01 — Introduction & Vision", SIDI, PURPLE, 10, [
        ('cue', "Brief beat after this slide appears."),
        ('say', "Part one — introduction and vision."),
    ]),

    (5, "The Problem", SIDI, PURPLE, 50, [
        ('say', "AI assistants today are powerful but fragmented. If you want to chat with a model, generate an image, transcribe an audio file and analyse a PDF — that is four different apps with four different subscriptions."),
        ('say', "Most useful features are paywalled, which puts students and small teams off-side. Conversations are throwaway: flat lists with no folders, no tags, no notebook context, no way to export a record. And multi-step prompt pipelines are either rebuilt from scratch every single time, or hidden inside closed agents."),
        ('say', "We saw this gap and decided to fill it."),
    ]),

    (6, "Project Objectives", SIDI, PURPLE, 50, [
        ('say', "From those pain points we set six concrete objectives. One — unify all modalities — text, image, audio, OCR, document Q and A — in a single chat surface. Two — stay free for our users, by combining free-tier APIs with self-hosted models."),
        ('say', "Three — make sessions persistent, with folders, tags, notebooks and exports. Four — show our work: workflows are saved, replayable and visible, including the n8n graph that drives the agent. Five — ship a real MVP, live, dockerised, on a real server. And six — ground every choice in academic rigor."),
    ]),

    (7, "Users & First Impression", SIDI, PURPLE, 70, [
        ('cue', "Gesture toward the landing page screenshot on the slide."),
        ('say', "This is our public landing page. It is where the product introduces itself: a single chat bar, a friendly mascot, and a quick path to register or to try the demo."),
        ('say', "We built AstroBot for four user groups: students preparing reports and code, developers exploring multimodal AI, knowledge workers doing document Q and A, and anyone tired of switching between ten browser tabs to do their AI work."),
        ('say', "The MVP scope was deliberately ambitious: a public chat, an authenticated chat, an admin dashboard with real metrics, twelve AI-powered features — all of which Ahmed will demonstrate later — and production deployment on a real virtual machine."),
        ('cue', "Hand off cleanly: \"Now I'll hand over to Tidiane for the architecture.\""),
    ]),

    (8, "Part 02 — Architecture & Design", TIDIANE, CYAN, 10, [
        ('cue', "Take the clicker. Brief beat."),
        ('say', "Thank you, Sidi. Part two — architecture and design."),
    ]),

    (9, "Context Diagram", TIDIANE, CYAN, 40, [
        ('cue', "Point at the AstroBot Platform box in the centre."),
        ('say', "Before the architecture itself, a step back: who interacts with AstroBot, and what flows in and out?"),
        ('say', "Two human actors. The end user on the left — they chat, upload images and PDFs, and listen to replies. The administrator on the bottom-left — they run the dashboard, manage accounts and audit activity."),
        ('say', "Four external services on the right. Mistral Cloud is the language model behind every reply. HuggingFace handles image generation, captioning and embeddings. Groq Whisper turns voice into text. SerpAPI gives the AI agent live web search."),
        ('say', "Everything outside the central box is out of our control and reached over HTTPS only — that is the system boundary."),
        ('hint', "Keep it under one minute — this slide just frames the next one."),
    ]),

    (10, "Use-Case Diagram", TIDIANE, CYAN, 40, [
        ('cue', "Point at the End User actor, then the Administrator actor."),
        ('say', "This is what the two actors can actually do. The end user, on the left: register and log in with JWT, chat in seven personas, generate or edit images, ask questions over a PDF in RAG or notebook mode, speak a message via Whisper, read an image with OCR and BLIP, generate a PDF report on demand, save tag search and export sessions, and compose multi-step workflow chains."),
        ('say', "The administrator, on the right: log in to the admin dashboard, view KPIs and activity charts, search suspend reactivate delete or create users, reset a user's password, and inspect any user's conversation history."),
        ('say', "Every use case here also goes through our JWT authentication and role gate — there is no public action that skips the security layer."),
        ('cue', "Transition: \"Now let me show how all of this is structured internally.\""),
    ]),

    (11, "System Architecture", TIDIANE, CYAN, 60, [
        ('say', "AstroBot runs as three Docker services on a shared private network. The main app on port three thousand — the public chat surface, built on Express with JWT auth and Helmet security headers."),
        ('say', "A separate admin dashboard on port seven thousand forty — completely isolated from the public app, protected by an admin role claim. And n8n on port five-six-seven-eight — the workflow orchestrator that talks to Mistral."),
        ('say', "They share PostgreSQL — but as a client only — and they share access to external APIs: HuggingFace for image generation and captioning, Groq for audio transcription, SerpAPI for web search inside the agent."),
        ('say', "Three reasons for this shape. One: we reuse an existing PostgreSQL container — no extra database to operate. Two: all AI traffic exits through n8n, so we can tune prompts and tools without redeploying. And three: the admin lives in its own service, so a public-facing exploit can never reach the dashboard process."),
    ]),

    (12, "Technology Stack", TIDIANE, CYAN, 30, [
        ('say', "Boring, well-supported building blocks at every layer. Vanilla HTML, CSS and JavaScript on the frontend — no framework, fast and maintainable. Node version eighteen with Express, JWT, and bcrypt at twelve rounds for the backend."),
        ('say', "Mistral medium-latest as the chat model, HuggingFace for image and embedding inference, Groq Whisper for audio. Docker and docker-compose for the infrastructure, and Python for our deploy script."),
    ]),

    (13, "Database Schema", TIDIANE, CYAN, 30, [
        ('say', "Six tables, all created idempotently on every boot — no manual database admin work. Users for accounts and roles. Conversations for the chat history with media attachments."),
        ('say', "Documents and document_chunks for the RAG pipeline — chunks store cosine embeddings as text. Notebook bindings link a session to a document. And workflows store user-defined prompt chains as JSON. Migrations use ALTER TABLE ADD COLUMN IF NOT EXISTS, so the app self-heals on every redeploy."),
    ]),

    (14, "n8n LLM Orchestration", TIDIANE, CYAN, 50, [
        ('cue', "Point at the workflow screenshot."),
        ('say', "This is the n8n workflow that powers every chat message. Each request comes in through a webhook, then a Switch node splits audio from text. Audio goes through a self-hosted Whisper transcriber."),
        ('say', "Text gets enriched with the user's name and conversation history, then it hits the AI Agent — Mistral medium-latest. The agent has access to two tools: SerpAPI for live web search, capped at two calls per request, and a Think scratchpad for chain-of-thought reasoning."),
        ('say', "The agent's reply is parsed as JSON, which lets the backend trigger image generation or PDF generation when needed. The whole graph is visual — we can iterate on prompts without redeploying anything."),
    ]),

    (15, "Security & Resilience", TIDIANE, CYAN, 40, [
        ('say', "Defence in depth across four pillars. Authentication: JWT with seven-day expiry, bcrypt password hashing at twelve rounds, hard admin gate via a JWT claim."),
        ('say', "Network: Helmet HTTP security headers, CORS allow-list, no-cache on static assets to prevent stale CSS bugs on iOS Safari. Rate limits: twenty per fifteen minutes on auth, thirty per minute on chat, five hundred per fifteen minutes on admin."),
        ('say', "And operational hygiene: secrets only in gitignored env files, file uploads capped at ten megabytes, idempotent migrations and an admin re-seed at boot — so a fresh VM is always one command away from a working install."),
        ('cue', "Hand off: \"Now Ahmed will demonstrate what we built on top of this.\""),
    ]),

    (16, "Part 03 — Implementation", AHMED, GOLD, 10, [
        ('cue', "Take the clicker."),
        ('say', "Thanks, Tidiane. Part three — implementation."),
    ]),

    (17, "Chat Experience", AHMED, GOLD, 30, [
        ('cue', "Point at the screenshot."),
        ('say', "This is the authenticated chat. Mistral medium-latest, fifteen-message context window per session, persona directives prepended to the system prompt. Replies stream word-by-word for a smooth feel."),
        ('say', "Markdown, KaTeX math, code highlighting and Mermaid diagrams all render inside the same bubble. Multi-language detection across ten languages. And seven personas — default, formal, casual, teacher, developer, poet, scientist — each tunes the model's tone."),
    ]),

    (18, "Rich Content Rendering", AHMED, GOLD, 25, [
        ('say', "A bot bubble is a tiny IDE. Markdown for structured replies. LaTeX math, both inline and block, rendered with KaTeX."),
        ('say', "Code highlighting across one hundred and eighty languages, with one-click copy buttons. And Mermaid diagrams — flow charts, sequence diagrams, ER models — straight from the model's text output."),
    ]),

    (19, "AI Image Generation", AHMED, GOLD, 30, [
        ('say', "Image generation runs on FLUX.1-schnell via the HuggingFace router — a four-step diffusion model on the free tier. If HuggingFace rate-limits or times out, we automatically fall back to fal-ai."),
        ('say', "We also support image-to-image — drop in a photo, ask for an anime version, FLUX dev returns it. Every generated image is stored as a data URL on the conversation row, so it survives reloads."),
    ]),

    (20, "On-Demand PDF Reports", AHMED, GOLD, 25, [
        ('say', "PDF reports are composed server-side with PDFKit. The trick: the LLM sometimes promises a report without flagging the action — so the backend re-parses every reply, and if it acknowledges a PDF, we force the generation."),
        ('say', "The output appears as a download card right inside the chat bubble — name, size badge, one-click download — and is persisted for re-download anytime."),
    ]),

    (21, "OCR & Visual Understanding", AHMED, GOLD, 30, [
        ('say', "Drop in any image, we'll read it AND describe it. Tesseract.js does OCR in English and French, server-side. BLIP from HuggingFace generates captions when there is no text."),
        ('say', "Both signals are concatenated to the prompt before the LLM sees it. This unlocks real use cases: forms, screenshots of error messages, scanned identity documents, or in this example, a Green Card lottery confirmation that the AI happily explains."),
    ]),

    (22, "Document Q&A — RAG & Notebook", AHMED, GOLD, 50, [
        ('say', "Document Q and A has two modes. The pipeline is the same: upload a PDF, parse with pdf-parse, chunk into eight-hundred-character pieces with one-hundred-character overlap, embed with MiniLM-L6-v2, retrieve the top four chunks by cosine similarity, inject into the prompt."),
        ('say', "Notebook mode keeps the first six thousand characters of the document in context on every message — best for short, thesis-sized PDFs. RAG mode picks the four most relevant chunks per question — that is how we make two-hundred-page books answerable in real time."),
        ('say', "Both modes share the same chat surface — the user only switches a toggle."),
    ]),

    (23, "Productivity Tools", AHMED, GOLD, 30, [
        ('say', "Six productivity features that other AI apps usually skip. Workflow chains — saved multi-step prompt sequences. Folders and tags on sessions, color-coded, searchable across the full history."),
        ('say', "Three exports per conversation: PDF, Markdown, JSON. A YouTube summarizer — paste a URL, get a transcript-grounded summary inside the chat. Audio transcription via Groq Whisper. And a built-in image cropper for profile photos."),
        ('cue', "Hand off: \"Now Saad will show how we operate the system.\""),
    ]),

    (24, "Part 04 — Admin · Testing · Deployment", SAAD, GREEN_OK, 10, [
        ('cue', "Take the clicker."),
        ('say', "Thanks, Ahmed. Part four — admin, testing and deployment."),
    ]),

    (25, "Admin Dashboard", SAAD, GREEN_OK, 25, [
        ('say', "The admin dashboard is a second Express service, on port seven thousand forty, totally isolated from the public app. It surfaces real-time KPIs — users, messages, sessions, tokens, images, PDFs, documents — plus two charts: daily activity over thirty days and a user-status doughnut."),
        ('say', "Recent signups and top users are panels above the fold. Login refuses any account that is not is_admin equals true."),
    ]),

    (26, "User Management", SAAD, GREEN_OK, 25, [
        ('say', "From this table we manage every account. Search and filter by status or role, see sessions, messages, last login, joined date."),
        ('say', "Lifecycle actions: suspend, reactivate, reset password, delete — with self-delete blocked. Admins can also create new accounts directly from the UI, regular or admin. All non-admin tokens are rejected before any state is read."),
    ]),

    (27, "Conversation Audit", SAAD, GREEN_OK, 20, [
        ('say', "Click any user to see their full conversation history, grouped by session. Profile metadata at the top, a sessions list with previews, and a drill-down to the full message-and-response trace."),
        ('say', "We built this so we can answer a 'what did this user ask?' request in seconds — useful for debugging and for compliance."),
    ]),

    (28, "Testing — 66 Integration Tests", SAAD, GREEN_OK, 30, [
        ('say', "Quality is enforced by sixty-six integration tests in test_all dot py — one command, runs against the live server, no mocks."),
        ('say', "Ten categories: health checks, static asset headers, auth flows, admin CRUD, the main chat round-trip through n8n and Mistral, sessions and tags, all three export formats, document and RAG endpoints, and validation — bad inputs return clean four hundreds, never five hundreds."),
    ]),

    (29, "Production Deployment", SAAD, GREEN_OK, 30, [
        ('say', "Deployment is one command — python deploy dot py. Five remote steps: tar up the project, SFTP it to the VM, untar in place, docker compose up dash d build, and a healthcheck verifies both services."),
        ('say', "The result: two containers — astrobot two point zero and astrobot-admin one point zero — running alongside our existing PostgreSQL and n8n containers, on a shared docker network. The app is live right now at the URLs you see — feel free to test it during the questions."),
    ]),

    (30, "Lessons Learned & What's Next", SAAD, GREEN_OK, 25, [
        ('say', "A few lessons. iOS Safari held onto stale CSS for hours — we kill it with Cache-Control no-store. LLMs sometimes promise a PDF without flagging it — we re-parse every reply and force the action when needed."),
        ('say', "Idempotent migrations let the app self-heal on every boot. And one deploy script beats git pull over SSH — no more half-deployed states."),
        ('say', "What's next: a mobile-first PWA, two-way voice mode, more OCR languages, fully self-hosted Whisper, and a workflow marketplace where users share and rate prompt chains."),
    ]),

    (31, "Key Takeaways", SAAD, GREEN_OK, 20, [
        ('say', "Four numbers to remember. Twelve AI-powered features, all in one place. Sixty-six integration tests, all green, runnable in one command. Three Dockerised services, reproducible from a fresh VM. Four engineers, four months, no feature dropped along the way."),
        ('say', "AstroBot is not a demo — it is a working product, running live as we speak."),
    ]),

    (32, "Thank You — Q&A", SAAD, GREEN_OK, 30, [
        ('say', "Thank you for your attention. AstroBot is live at the URLs on the screen — feel free to log in during the questions."),
        ('say', "The source code is on GitHub. We — Tidiane, Sidi, Ahmed and myself — and our advisor Assist. Prof. Dr. Yücel Tekin, are happy to take your questions."),
        ('cue', "Stand still. Smile. Wait for the first question."),
    ]),
]


# ─── Styles ──────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()['BodyText']
    return {
        'big_title': ParagraphStyle(
            'big_title', parent=base, fontName='Helvetica-Bold',
            fontSize=28, leading=32, textColor=NAVY,
            alignment=TA_LEFT, spaceAfter=4),
        'sub_title': ParagraphStyle(
            'sub_title', parent=base, fontName='Helvetica-Oblique',
            fontSize=12, leading=16, textColor=INK_SOFT,
            alignment=TA_LEFT, spaceAfter=10),
        'slide_no': ParagraphStyle(
            'slide_no', parent=base, fontName='Helvetica-Bold',
            fontSize=10, leading=12, textColor=WHITE,
            alignment=TA_CENTER),
        'presenter': ParagraphStyle(
            'presenter', parent=base, fontName='Helvetica-Bold',
            fontSize=10, leading=12, textColor=WHITE,
            alignment=TA_CENTER),
        'time_chip': ParagraphStyle(
            'time_chip', parent=base, fontName='Helvetica-Bold',
            fontSize=10, leading=12, textColor=NAVY,
            alignment=TA_CENTER),
        'section_label': ParagraphStyle(
            'section_label', parent=base, fontName='Helvetica-Bold',
            fontSize=11, leading=14, textColor=PURPLE,
            spaceBefore=8, spaceAfter=4),
        'say': ParagraphStyle(
            'say', parent=base, fontName='Times-Roman',
            fontSize=14, leading=20, textColor=INK,
            alignment=TA_LEFT, spaceAfter=10),
        'cue': ParagraphStyle(
            'cue', parent=base, fontName='Helvetica-Oblique',
            fontSize=11, leading=15, textColor=INK_SOFT,
            alignment=TA_LEFT, spaceAfter=6,
            leftIndent=12, borderColor=PURPLE,
            borderWidth=0, borderPadding=0),
        'hint': ParagraphStyle(
            'hint', parent=base, fontName='Helvetica-Oblique',
            fontSize=10, leading=14, textColor=GREEN_OK,
            alignment=TA_LEFT, spaceAfter=6, leftIndent=12),
        'cover_title': ParagraphStyle(
            'cover_title', parent=base, fontName='Helvetica-Bold',
            fontSize=42, leading=46, textColor=WHITE,
            alignment=TA_LEFT, spaceAfter=4),
        'cover_subtitle': ParagraphStyle(
            'cover_subtitle', parent=base, fontName='Helvetica-Oblique',
            fontSize=18, leading=22, textColor=GOLD,
            alignment=TA_LEFT, spaceAfter=20),
        'cover_para': ParagraphStyle(
            'cover_para', parent=base, fontName='Helvetica',
            fontSize=12, leading=18, textColor=LIGHT,
            alignment=TA_LEFT, spaceAfter=8),
        'toc_h': ParagraphStyle(
            'toc_h', parent=base, fontName='Helvetica-Bold',
            fontSize=14, leading=18, textColor=PURPLE,
            alignment=TA_LEFT, spaceAfter=4),
        'toc_row': ParagraphStyle(
            'toc_row', parent=base, fontName='Helvetica',
            fontSize=11, leading=15, textColor=INK,
            alignment=TA_LEFT),
    }


# ─── Page templates ──────────────────────────────────────────────────
def cover_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Solid navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # Magenta accent strip on the left
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, 12 * mm, h, fill=1, stroke=0)
    # Gold underline near title area
    canvas.setFillColor(GOLD)
    canvas.rect(20 * mm, h - 95 * mm, 60 * mm, 2 * mm, fill=1, stroke=0)
    canvas.restoreState()


def slide_page_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Light page bg with thin top color band based on the active slide
    band_color = doc._current_band or PURPLE
    canvas.setFillColor(band_color)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=1, stroke=0)
    # Footer rule
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)
    # Footer text
    canvas.setFillColor(INK_SOFT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(15 * mm, 7 * mm, "AstroBot · Speaker Notes · Graduation Project 2026")
    canvas.drawRightString(
        w - 15 * mm, 7 * mm,
        f"Slide {doc._current_slide_no} of 32")
    canvas.restoreState()


def toc_page_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(PURPLE)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)
    canvas.setFillColor(INK_SOFT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(15 * mm, 7 * mm, "AstroBot · Speaker Notes · Graduation Project 2026")
    canvas.drawRightString(w - 15 * mm, 7 * mm, "Outline")
    canvas.restoreState()


# ─── Story builders ─────────────────────────────────────────────────
def make_header_table(slide_no, title, presenter, color, time_s, styles):
    """Small banner: slide number, title, presenter chip, time chip."""
    no_para = Paragraph(f"<b>SLIDE {slide_no}</b>", styles['slide_no'])
    presenter_para = Paragraph(presenter, styles['presenter'])
    time_para = Paragraph(_fmt_time(time_s), styles['time_chip'])

    data = [[no_para, "", presenter_para, time_para]]
    tbl = Table(data, colWidths=[24 * mm, 95 * mm, 38 * mm, 18 * mm], rowHeights=[10 * mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), NAVY),
        ('BACKGROUND', (2, 0), (2, 0), color),
        ('BACKGROUND', (3, 0), (3, 0), GOLD),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return tbl


def _fmt_time(seconds: int) -> str:
    if seconds >= 60:
        m, s = divmod(seconds, 60)
        return f"{m}m {s:02d}s"
    return f"{seconds}s"


def build_slide_page(slide_no, title, presenter, color, time_s, body, styles):
    flow = []
    flow.append(make_header_table(slide_no, title, presenter, color, time_s, styles))
    flow.append(Spacer(1, 8 * mm))
    flow.append(Paragraph(_escape(title), styles['big_title']))
    flow.append(Paragraph(_escape(_subtitle_for(presenter, color)),
                          styles['sub_title']))

    flow.append(Paragraph("WHAT TO SAY", styles['section_label']))
    for kind, content in body:
        if kind == 'say':
            flow.append(Paragraph(_escape(content), styles['say']))
        elif kind == 'cue':
            flow.append(Paragraph(
                f'<font color="#7B2CBF"><b>CUE</b></font> &nbsp; '
                f'<i>{_escape(content)}</i>',
                styles['cue']))
        elif kind == 'hint':
            flow.append(Paragraph(
                f'<font color="#16A34A"><b>TIP</b></font> &nbsp; '
                f'{_escape(content)}',
                styles['hint']))

    return flow


def _subtitle_for(presenter, color):
    return f"Speaker — {presenter}"


def _escape(text: str) -> str:
    """Escape minimal XML for reportlab Paragraphs."""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def build_cover_page(styles):
    flow = []
    # Vertical spacer to push content lower
    flow.append(Spacer(1, 60 * mm))
    flow.append(Paragraph("AstroBot", styles['cover_title']))
    flow.append(Paragraph(
        "Speaker Notes · 15-Minute Presentation",
        styles['cover_subtitle']))
    flow.append(Paragraph(
        "Talking points for every slide, who says what,<br/>"
        "and a suggested time per slide.",
        styles['cover_para']))
    flow.append(Spacer(1, 20 * mm))
    flow.append(Paragraph(
        "<b>Tidiane Konaté</b> &nbsp;·&nbsp; "
        "<b>Sidi Mohamed Sall</b> &nbsp;·&nbsp; "
        "<b>Ahmed Essalem</b> &nbsp;·&nbsp; "
        "<b>Saad Ibrahim Houssein</b>",
        styles['cover_para']))
    flow.append(Paragraph(
        "Advisor — Assist. Prof. Dr. Yücel Tekin",
        styles['cover_para']))
    flow.append(Paragraph(
        "OSTIM Technical University &nbsp;·&nbsp; MFBP 402 Graduation Project &nbsp;·&nbsp; May 2026",
        styles['cover_para']))
    return flow


def build_outline_page(styles):
    flow = []
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph("Outline & Timing", styles['big_title']))
    flow.append(Paragraph(
        "How the 15 minutes break down between the four presenters.",
        styles['sub_title']))

    sections = [
        ("Opening · Slides 1 – 3", ALL, "1 min 15 s", PURPLE,
         "Cover · Team · Agenda."),
        ("Part 1 · Slides 4 – 7", SIDI, "3 min 00 s", PURPLE,
         "Section divider · Problem · Objectives · Users."),
        ("Part 2 · Slides 8 – 15", TIDIANE, "4 min 50 s", CYAN,
         "Section divider · Context diagram · Use-case diagram · Architecture · Tech stack · Database · n8n · Security."),
        ("Part 3 · Slides 16 – 23", AHMED, "4 min 00 s", GOLD,
         "Section divider · Chat · Markdown · Image gen · PDF · OCR · RAG · Productivity."),
        ("Part 4 · Slides 24 – 31", SAAD, "3 min 00 s", GREEN_OK,
         "Section divider · Admin · Users · Audit · Testing · Deploy · Lessons · Takeaways."),
        ("Closing · Slide 32", SAAD, "30 s", PURPLE,
         "Thank you & Q&A — but Q&A itself is on top of the 15 minutes."),
    ]
    rows = [["Block", "Speaker", "Length", "Slides covered"]]
    for label, who, length, _, slides in sections:
        rows.append([
            Paragraph(f"<b>{label}</b>", styles['toc_row']),
            Paragraph(who, styles['toc_row']),
            Paragraph(length, styles['toc_row']),
            Paragraph(slides, styles['toc_row']),
        ])
    tbl = Table(rows, colWidths=[55 * mm, 45 * mm, 25 * mm, 55 * mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('LEADING', (0, 0), (-1, 0), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, LINE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
    ]))
    flow.append(tbl)

    flow.append(Spacer(1, 8 * mm))
    flow.append(Paragraph("How to use this booklet", styles['section_label']))
    bullets = [
        "Each slide gets one page. Print double-sided to halve the page count.",
        "Black serif paragraphs are the actual lines to say — read them aloud at least twice before the talk.",
        ('Italic gray paragraphs marked <font color="#7B2CBF"><b>CUE</b></font> are stage directions: '
         'when to point, when to pause, how to hand off.'),
        ('Italic green paragraphs marked <font color="#16A34A"><b>TIP</b></font> are reminders and confidence boosters.'),
        "Time chips on each header sum to 15 minutes for the talk itself — Q&amp;A is on top.",
    ]
    for b in bullets:
        flow.append(Paragraph(
            f"&bull;&nbsp;&nbsp;{b}",
            ParagraphStyle('bul', parent=styles['toc_row'],
                           leftIndent=10, spaceAfter=4)))
    return flow


# ─── Doc builder ────────────────────────────────────────────────────
class _Doc(BaseDocTemplate):
    """A doc that exposes per-page state (slide number / band color)
    so onPage callbacks can read them."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_slide_no = 1
        self._current_band = PURPLE


def build_pdf(path: Path):
    styles = make_styles()
    doc = _Doc(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
        title="AstroBot Speaker Notes",
        author="Tidiane Konaté · Sidi Mohamed Sall · Ahmed Essalem · Saad Ibrahim Houssein",
    )

    cover_frame = Frame(
        20 * mm, 18 * mm,
        A4[0] - 38 * mm, A4[1] - 36 * mm,
        leftPadding=0, bottomPadding=0,
        rightPadding=0, topPadding=0,
        showBoundary=0, id='cover')
    body_frame = Frame(
        18 * mm, 18 * mm,
        A4[0] - 36 * mm, A4[1] - 36 * mm,
        leftPadding=0, bottomPadding=0,
        rightPadding=0, topPadding=0,
        showBoundary=0, id='body')

    cover_tpl = PageTemplate(id='cover', frames=[cover_frame], onPage=cover_bg)
    toc_tpl = PageTemplate(id='toc', frames=[body_frame], onPage=toc_page_bg)
    slide_tpl = PageTemplate(id='slide', frames=[body_frame], onPage=slide_page_bg)
    doc.addPageTemplates([cover_tpl, toc_tpl, slide_tpl])

    story = []
    # Cover page
    story.extend(build_cover_page(styles))
    story.append(NextPageTemplate('toc'))
    story.append(PageBreak())
    # Outline page
    story.extend(build_outline_page(styles))
    story.append(NextPageTemplate('slide'))
    story.append(PageBreak())

    # 30 slide pages
    for i, (no, title, presenter, color, time_s, body) in enumerate(NOTES):
        # Inject per-page state by intercepting via a side-effect flowable
        story.append(_StateFlowable(no, color))
        story.extend(build_slide_page(no, title, presenter, color, time_s, body, styles))
        if i < len(NOTES) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Wrote {path}  ({path.stat().st_size / 1024:.0f} KB)")


# ─── Helper flowable that just updates doc state ────────────────────
class _StateFlowable(Flowable):
    """Zero-size placeholder; on draw we mutate the doc state so the
    onPage callbacks can read the right slide number / accent color."""
    def __init__(self, slide_no, band):
        super().__init__()
        self.slide_no = slide_no
        self.band = band

    def wrap(self, _aw, _ah):
        return (0, 0)

    def draw(self):
        try:
            self.canv._doctemplate._current_slide_no = self.slide_no
            self.canv._doctemplate._current_band = self.band
        except Exception:
            pass


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(OUTPUT)
