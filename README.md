# 🚀 AstroBot

> Your intelligent space-themed AI assistant — university graduation project.

AstroBot is a full-stack AI chat application built around an **n8n workflow** that
routes messages through Mistral, with a layered set of features on top:
image generation, OCR, retrieval-augmented generation (RAG), audio transcription,
PDF report generation, image-to-image edits, and a separate admin dashboard.

---

## 🏗️ Architecture

```
                       ┌────────────────────────┐
                       │    User browser        │
                       └─────────┬──────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐      ┌────────▼──────────┐    ┌───────▼────────┐
│   Main app     │      │  Admin dashboard  │    │     n8n        │
│  Express :3000 │      │   Express :7040   │    │    :5678       │
│  Public chat   │      │  Admin / stats /  │    │ Mistral cloud  │
└───────┬────────┘      │  user management  │    │ SerpAPI · Think│
        │               └─────────┬─────────┘    └───────┬────────┘
        │                         │                      │
        └───────────┬─────────────┘                      │
                    │                                    │
            ┌───────▼────────┐                  ┌────────▼─────────┐
            │   PostgreSQL   │                  │  HuggingFace     │
            │ (shared)       │                  │ FLUX · BLIP ·    │
            │ users · convs ·│                  │ MiniLM · TrOCR   │
            │ docs · workflows                  └──────────────────┘
            └────────────────┘
```

Three Docker services on the same private network:

| Service          | Port | Image                  | Purpose                                         |
|------------------|------|------------------------|-------------------------------------------------|
| `astrobot`       | 3000 | `astrobot:2.0.0`       | Main user-facing chat app                       |
| `astrobot-admin` | 7040 | `astrobot-admin:1.0.0` | Admin dashboard (stats, user mgmt, settings)    |
| n8n              | 5678 | `n8n` (external)       | LLM workflow orchestration                      |

---

## ✨ Features

### Chat experience
- **Mistral Medium** via n8n with conversation history (last 15 messages)
- Markdown rendering with **GitHub-flavored** support
- **KaTeX** for LaTeX math (`$E=mc^2$`, `$$\int_0^\infty$$`)
- **highlight.js** for code syntax highlighting
- **Mermaid** diagrams (flowcharts, sequence, ER, etc.)
- **Streaming-style** word-by-word reveal animation
- Multi-language detection (FR / EN / ES / DE / AR / ZH / JA / KO / RU / EL)
- Theme toggle dark / light
- UI density: comfortable / compact
- 7 personas (default, formal, casual, teacher, dev, poet, scientist)

### Multimedia
- 🎨 **Image generation** via FLUX.1-schnell (HuggingFace, free) with fal-ai fallback
- 📄 **PDF report generation** via pdfkit (typed responses)
- 🖼️ **Image-to-image edit** via FLUX dev (style transfer, "make this anime", …)
- 📎 **File / image attachments** with drag-and-drop, multi-attach
- 🔊 **OCR** for images via Tesseract.js (EN / FR)
- 🤖 **Visual captioning** via BLIP for non-text images
- 🎙 **Audio transcription** via Groq Whisper (optional, free key)
- 🗣 **Text-to-speech** for bot replies (Web Speech API, browser-native)

### Productivity
- 📚 **Notebook mode** — pin a PDF as permanent context for a session
- 🔍 **Document Q&A (RAG)** — chunk + embed via MiniLM, cosine similarity retrieval
- 🎬 **YouTube summarizer** — fetch transcript + summarize
- 🔁 **Workflow chains** — saved multi-step prompt sequences
- 🏷️ **Tags / folders** on sessions with color-coded filters
- 🔎 **Search** in chat history
- 📤 **Export** session as PDF / Markdown / JSON
- ✏️ **Edit & resend** your messages
- 🔄 **Regenerate** bot responses
- ⏹ **Stop generation** mid-stream
- 🛡 **Profile photo** with built-in cropper (rotate / zoom / flip)

### Admin dashboard (port 7040)
- 🔐 Admin-only login (regular users get 403)
- 📊 Real-time stats: users / messages / sessions / tokens / images / PDFs / docs
- 📈 Charts (Chart.js): daily activity, user status breakdown
- 👥 User management: list, search, suspend/activate, reset password, delete
- ➕ **Admin can create new accounts** (regular or admin)
- 📜 Browse any user's full conversation history grouped by session
- 👤 Self-service settings: profile, password, photo

---

## 🚀 Quick start

### Requirements
- Docker + Docker Compose
- An existing PostgreSQL container on a Docker network (we connect to it as a client)
- An external n8n container with the AstroBot workflow imported
- A HuggingFace API token (free at https://huggingface.co/settings/tokens)
- Optional: Groq API key for audio transcription (free at https://console.groq.com/keys)

### 1. Clone & configure

```bash
git clone https://github.com/tkonate788/astrobot.git
cd astrobot
cp docker/.env.example docker/.env
nano docker/.env       # fill in real values (see below)
```

The `docker/.env` file holds all secrets and never gets committed:

| Variable        | Example                                | Notes                          |
|-----------------|----------------------------------------|--------------------------------|
| `JWT_SECRET`    | `<random 32+ chars>`                   | Sign user tokens               |
| `DB_HOST`       | `postgre_container`                    | Hostname on the docker network |
| `DB_PORT`       | `5432`                                 |                                |
| `DB_NAME`       | `astrobot`                             |                                |
| `DB_USER`       | `astrobot_user`                        |                                |
| `DB_PASSWORD`   | `<strong password>`                    |                                |
| `N8N_WEBHOOK`   | `http://n8n:5678/webhook/astrobot`     | Your n8n entry point           |
| `HF_API_KEY`    | `hf_xxx...`                            | HuggingFace token              |
| `GROQ_API_KEY`  | `gsk_xxx...` (or empty)                | Optional, for transcription    |
| `ADMIN_EMAIL`   | `admin@example.com`                    | Seed admin login               |
| `ADMIN_PASSWORD`| `<strong password>`                    | Seed admin password            |

### 2. Build & run

```bash
cd docker
docker compose up -d --build
```

Both services come up:
- Main app: http://localhost:3000
- Admin dashboard: http://localhost:7040

The admin account is auto-seeded on first run using `ADMIN_EMAIL` / `ADMIN_PASSWORD`
from `docker/.env`. Sign in once and start exploring.

### 3. Verify

```bash
# Run the comprehensive test suite (66 tests)
python test_all.py
```

---

## 📁 Project layout

```
astrobot/
├── frontend/              # Static HTML / CSS / JS for the main app
│   ├── index.html         # Landing page with central chat bar
│   ├── chat.html          # Authenticated chat interface
│   ├── login.html
│   ├── register.html
│   ├── style.css
│   └── team/              # Developer photos for the About section
├── backend/
│   ├── server.js          # Express entry
│   ├── db/index.js        # Postgres pool + idempotent migrations
│   ├── middleware/auth.js
│   └── routes/
│       ├── auth.js        # Register / login / profile / avatar
│       ├── chat.js        # Messages + image gen + PDF + history
│       └── features.js    # Documents / RAG / YouTube / img-edit / workflows
├── admin/                 # Separate Express service (port 7040)
│   ├── backend/
│   │   ├── server.js
│   │   └── public/        # Admin dashboard UI (vanilla JS + Chart.js)
│   └── Dockerfile
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile         # Main app
│   └── .env.example       # Template for local secrets
├── deploy.py              # SSH + SCP + docker compose deployment
├── test_all.py            # Full integration test suite (66 tests)
└── README.md
```

---

## 🧪 Testing

```bash
# Set ASTROBOT_HOST / ASTROBOT_ADMIN_EMAIL / ASTROBOT_ADMIN_PASSWORD
# (or place them in .deploy.env), then:
python test_all.py
```

The suite covers:
- Service health (main + admin)
- Static asset serving with no-cache headers
- Admin auth (correct / wrong / missing token, role check)
- Admin endpoints (`/stats`, `/users`, CRUD, suspend/activate, reset-password)
- Main app auth (login, profile, avatar set + clear)
- Chat flow (n8n → Mistral round-trip)
- Tags, sessions, history, exports (PDF/MD/JSON)
- Features endpoints (documents, RAG bind/unbind, workflows CRUD, validation)

---

## 🛠 Tech stack

| Layer       | Tech                                                        |
|-------------|-------------------------------------------------------------|
| Frontend    | Vanilla HTML / CSS / JS (no framework)                      |
| Frontend libs | KaTeX, highlight.js, Mermaid, Cropper.js, Chart.js (admin) |
| Backend     | Node.js 18, Express 4, JWT, bcrypt, Helmet, rate-limit      |
| Storage     | PostgreSQL                                                  |
| AI / LLM    | Mistral via n8n, HuggingFace (FLUX, BLIP, MiniLM)           |
| Speech      | Tesseract.js (OCR), Groq Whisper (optional STT)             |
| Doc parsing | pdf-parse, pdfkit                                           |
| Container   | Docker + Docker Compose, Alpine Node 18                     |

---

## 🔒 Security notes

- All secrets live in `docker/.env` (gitignored). No keys committed to the repo.
- JWT-based auth (7-day expiry).
- Helmet headers + per-route rate limiting (auth: 20/15min, chat: 30/min).
- bcrypt password hashing with salt rounds = 12.
- Admin endpoints protected by an `is_admin` claim in the JWT.
- Static assets served with `Cache-Control: no-store` to keep updates fresh.
- File uploads capped at 10 MB each, 5 attachments max per message.

---

## 👥 Team

AstroBot is a **university graduation project** developed by:

- **Tidiane Konaté**
- **Sidi Mohamed Sall**
- **Ahmed Essalem**
- **Saad Ibrahim Houssein**

— 2026
