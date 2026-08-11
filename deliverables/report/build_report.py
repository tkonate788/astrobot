#!/usr/bin/env python3
"""
AstroBot — Capstone Project Report generator.

Builds the graduation/capstone report (.docx) following the OSTIM Technical
University "Capstone Project Report" template that the project advisor asked
the team to use (cover → APPROVAL → ACKNOWLEDGEMENTS → ABSTRACT (TR/EN) →
TABLE OF CONTENTS / LIST OF TABLES / FIGURES / SYMBOLS → numbered sections
1. Introduction … 12. Conclusion → REFERENCES → CURRICULUM VITAE → 13.
Appendices).

UML-ish diagrams (context, use-case, architecture, class/ER, sequence,
state) are drawn with Pillow into `report/assets/diagrams/` on first run.

Run:
    python report/build_report.py

Output:
    report/AstroBot_Graduation_Report.docx
"""

from __future__ import annotations

import os
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
ASSETS = REPORT_DIR / "assets"
DIAGRAMS = ASSETS / "diagrams"
SCREENSHOTS = ROOT / "assets" / "screenshots"
BACKEND = ROOT / "backend"
OUTPUT = REPORT_DIR / "AstroBot_Graduation_Report.docx"

# ── Project metadata ───────────────────────────────────────────────
PROJECT_TITLE = ("ASTROBOT — AN INTELLIGENT CONVERSATIONAL AI ASSISTANT WITH "
                 "MULTIMODAL CAPABILITIES, RETRIEVAL-AUGMENTED GENERATION AND "
                 "WEB-BASED WORKFLOW INTEGRATION")
SHORT_TITLE = "AstroBot"
GITHUB_URL = "https://github.com/tkonate788/astrobot"
DEPLOY_URL = "http://76.13.62.195:3000"
ADMIN_URL = "http://76.13.62.195:7040"
UNIVERSITY = "OSTIM TECHNICAL UNIVERSITY"
FACULTY = "FACULTY OF ENGINEERING"
DEPARTMENT = "Department of Computer Engineering"
COURSE = "MFBP 402 — Graduation Project II"
DATE_LINE = "May 2026"
ADVISOR = "Assist. Prof. Dr. Yücel TEKİN"
ADVISOR_PLAIN = "Yücel TEKİN"

STUDENTS = [
    ("220201838", "TIDIANE KONATE"),
    ("210208992", "SIDI MOHAMED SALL"),
    ("220201992", "AHMED ESSALEM"),
    ("210201983", "SAAD IBRAHIM HOUSSEIN"),
]

# Tidiane's CV details (provided). Other members → blank CV pages.
CV_TIDIANE = {
    "full_name": "Tidiane KONATÉ",
    "nationality": "Malian (Mali)",
    "birth": "—",
    "email": "Tkonate788@gmail.com  ·  220201838@ostimteknik.edu.tr",
    "education": [
        ("High School", "Lycée Privé d'Excellence (LPE), Mali — Scientific Baccalaureate", "2021"),
        ("Turkish Language Training", "Yozgat Bozok University (YOBU), Turkey", "2022"),
        ("Undergraduate", "OSTIM Technical University, Ankara — Computer Engineering", "2026 (expected)"),
    ],
    "experience": [
        ("INEDIIA — Lille, France (Remote)", "Applied GenAI / LLMOps Intern — designing and deploying "
         "AI-powered automation workflows with n8n, integrating LLM APIs into business processes, "
         "containerised service deployment with Docker, end-to-end GenAI pipelines.", "2025 – present"),
    ],
    "expertise": [
        "Applied Generative AI & LLM APIs",
        "AI workflow automation & orchestration (n8n)",
        "DevOps / LLMOps — Docker, webhooks, API integration",
        "Software development — C, C++, Python, C#",
        "Operating systems & networking",
    ],
    "languages": [
        ("French", "Native"),
        ("English", "Advanced (B2)"),
        ("Turkish", "Intermediate (B1)"),
        ("Bambara", "Fluent"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_SIDI = {
    "full_name": "Sidi Mohamed SALL",
    "nationality": "Malian (Mali)",
    "birth": "Bamako, Mali",
    "email": "Sidimohamedsall5@gmail.com  ·  210208992@ostimteknik.edu.tr",
    "education": [
        ("High School", "Lycée Complexe Scolaire Kanouté Aïssé, Bamako, Mali", "2020"),
        ("English Language Proficiency", "OSTIM Technical University, Ankara", "2021"),
        ("Undergraduate", "OSTIM Technical University, Ankara — Software Engineering",
         "2026 (expected)"),
    ],
    "experience": [],
    "expertise": [
        "Product vision, user experience and interface design",
        "Front-end development with HTML, CSS and JavaScript",
        "Software engineering — analysis, design and documentation",
        "Team collaboration and agile project work",
    ],
    "languages": [
        ("French", "Native"),
        ("English", "Advanced (B2)"),
        ("Turkish", "Intermediate (B1)"),
        ("Bambara", "Fluent"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_AHMED = {
    "full_name": "Ahmed ESSALEM",
    "nationality": "Mauritanian (Mauritania)",
    "birth": "Mauritania",
    "email": "220201992@ostimteknik.edu.tr",
    "education": [
        ("Undergraduate", "OSTIM Technical University, Ankara — Computer Engineering",
         "2026 (expected)"),
    ],
    "experience": [
        ("OSTIM Technical University", "C#: Advanced Object-Oriented Programming "
         "(OOP), multi-module application development, scripting, automation, API "
         "integration and back-end development.", "2026"),
        ("Datacamp", "Python: Advanced Object-Oriented Programming (OOP), "
         "multi-module application development, scripting, automation, API "
         "integration and back-end development.", "2024"),
        ("Smart SA Company", "Database Management — SQL databases, data modelling, "
         "CRUD operations and database integration in applications.", "2025"),
        ("Smart SA Company", "Web Technologies — frontend and backend development, "
         "responsive web applications and API-based systems.", "2024"),
    ],
    "expertise": [
        "Computer Engineering: systems architecture, software development life cycle "
        "(SDLC), problem solving, debugging and application optimisation.",
        "Python Programming: advanced OOP, multi-module applications, scripting, "
        "automation, API integration and back-end development.",
        "C# Programming: advanced OOP, multi-module applications and back-end "
        "development.",
        "Software Engineering: application design, clean code practices, version "
        "control with Git/GitHub, testing and documentation.",
        "Database Management: SQL databases, data modelling and integration.",
        "Web Technologies: responsive web applications and API-based systems.",
        "Team Collaboration & Problem Solving: agile teamwork, technical "
        "communication and analytical thinking.",
    ],
    "languages": [
        ("Arabic", "Fluent"),
        ("French", "Fluent"),
        ("Turkish", "Advanced (C1)"),
        ("English", "Advanced (C1)"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_SAAD = {
    "full_name": "Saad Ibrahim HOUSSEIN",
    "nationality": "Djiboutian (Djibouti)",
    "birth": "Djibouti",
    "email": "saadgodin2@gmail.com  ·  210201983@ostimteknik.edu.tr",
    "education": [
        ("Undergraduate", "OSTIM Technical University, Ankara — Software Engineering",
         "2026 (expected)"),
    ],
    "experience": [
        ("Datacomp", "Flutter Development — cross-platform mobile and web application "
         "development using Dart, responsive UI/UX design, state management, Firebase "
         "integration and REST API connectivity.", "2024"),
        ("Datacomp", "Database Management — SQL databases, data modelling, CRUD "
         "operations and database integration in applications.", "2025"),
        ("Datacomp", "Web Technologies — frontend and backend development, responsive "
         "web applications and API-based systems.", "2024"),
    ],
    "expertise": [
        "Computer Engineering: systems architecture, software development life cycle "
        "(SDLC), problem solving, debugging and application optimisation.",
        "Python Programming: advanced OOP, multi-module applications, scripting, "
        "automation, API integration and back-end development.",
        "Flutter Development: cross-platform mobile and web apps with Dart, "
        "responsive UI/UX, state management, Firebase and REST APIs.",
        "Software Engineering: application design, clean code practices, version "
        "control with Git/GitHub, testing and documentation.",
        "Database Management: SQL databases, data modelling and integration.",
        "Web Technologies: responsive web applications and API-based systems.",
        "Team Collaboration & Problem Solving: agile teamwork, technical "
        "communication and analytical thinking.",
    ],
    "languages": [
        ("Somali", "Fluent"),
        ("Arabic", "Fluent"),
        ("French", "Fluent"),
        ("Turkish", "Advanced (C1)"),
        ("English", "Upper-Intermediate (B2)"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


# ════════════════════════════════════════════════════════════════════════
# DIAGRAM GENERATION  (Pillow)  →  report/assets/diagrams/*.png
# ════════════════════════════════════════════════════════════════════════

FDIR = Path("C:/Windows/Fonts")


def _f(name, size):
    try:
        return ImageFont.truetype(str(FDIR / name), size)
    except OSError:
        return ImageFont.load_default()


def FB(s): return _f("segoeuib.ttf", s)     # bold
def FS(s): return _f("seguisb.ttf", s)      # semibold
def FR(s): return _f("segoeui.ttf", s)      # regular
def FM(s): return _f("consola.ttf", s)      # mono

INK = (28, 36, 56)
SOFT = (96, 108, 132)
NAVY = (15, 26, 53)
LINE = (170, 180, 196)
BLUE = (37, 99, 235)
GREEN = (22, 163, 74)
ORANGE = (217, 119, 6)
PURPLE = (124, 58, 191)
CYAN = (8, 145, 178)
RED = (185, 28, 28)
BGCARD = (246, 248, 252)


def _box(d, x, y, w, h, title, sub=None, *, color=BLUE, fill=(255, 255, 255),
         ts=26, ss=20, radius=12):
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill,
                        outline=color, width=3)
    f1 = FB(ts)
    bb = d.textbbox((0, 0), title, font=f1)
    tw = bb[2] - bb[0]
    ty = y + (h * 0.5 - (bb[3] - bb[1])) if sub is None else y + h * 0.20
    d.text((x + (w - tw) / 2, ty), title, font=f1, fill=NAVY)
    if sub:
        f2 = FR(ss)
        bb2 = d.textbbox((0, 0), sub, font=f2)
        d.text((x + (w - (bb2[2] - bb2[0])) / 2, y + h * 0.58), sub, font=f2, fill=SOFT)


def _actor(d, cx, cy, label, *, scale=1.0, color=INK):
    # stick figure
    s = 26 * scale
    d.ellipse((cx - s * 0.45, cy - s * 1.4, cx + s * 0.45, cy - s * 0.5), outline=color, width=3)
    d.line((cx, cy - s * 0.5, cx, cy + s * 0.7), fill=color, width=3)
    d.line((cx - s * 0.8, cy, cx + s * 0.8, cy), fill=color, width=3)
    d.line((cx, cy + s * 0.7, cx - s * 0.7, cy + s * 1.7), fill=color, width=3)
    d.line((cx, cy + s * 0.7, cx + s * 0.7, cy + s * 1.7), fill=color, width=3)
    f = FS(22)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, cy + s * 2.0), label, font=f, fill=INK)


def _arrow(d, x1, y1, x2, y2, *, color=SOFT, w=3, two_way=False, dashed=False):
    if dashed:
        # crude dashed line
        import math
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy)
        n = max(1, int(ln / 16))
        for i in range(n):
            if i % 2 == 0:
                a = i / n
                b = min(1.0, (i + 1) / n)
                d.line((x1 + dx * a, y1 + dy * a, x1 + dx * b, y1 + dy * b), fill=color, width=w)
    else:
        d.line((x1, y1, x2, y2), fill=color, width=w)
    # arrowhead at end
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    al = 16
    for s in (-0.5, 0.5):
        ax = x2 - al * math.cos(ang - s)
        ay = y2 - al * math.sin(ang - s)
        d.line((x2, y2, ax, ay), fill=color, width=w)
    if two_way:
        ang2 = math.atan2(y1 - y2, x1 - x2)
        for s in (-0.5, 0.5):
            ax = x1 - al * math.cos(ang2 - s)
            ay = y1 - al * math.sin(ang2 - s)
            d.line((x1, y1, ax, ay), fill=color, width=w)


def _label_mid(d, x1, y1, x2, y2, text, *, size=18, color=SOFT, dy=-22):
    f = FR(size)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    bb = d.textbbox((0, 0), text, font=f)
    # white halo
    pad = 4
    d.rectangle((mx - (bb[2] - bb[0]) / 2 - pad, my + dy - pad,
                 mx + (bb[2] - bb[0]) / 2 + pad, my + dy + (bb[3] - bb[1]) + pad),
                fill=(255, 255, 255))
    d.text((mx - (bb[2] - bb[0]) / 2, my + dy), text, font=f, fill=color)


def _canvas(w, h):
    img = Image.new("RGB", (w, h), (255, 255, 255))
    return img, ImageDraw.Draw(img)


def gen_context_diagram(path):
    W, H = 1600, 1100
    img, d = _canvas(W, H)
    # central system box
    cx, cy = W // 2, H // 2
    bw, bh = 520, 200
    _box(d, cx - bw // 2, cy - bh // 2, bw, bh, "AstroBot Platform",
         "Web app · Admin · n8n orchestrator", color=BLUE, fill=(238, 244, 252), ts=34, ss=22)
    # actors left
    _actor(d, 200, 320, "End User")
    _actor(d, 200, 780, "Administrator")
    # external systems right
    _box(d, W - 470, 180, 380, 110, "Mistral Cloud", "LLM inference", color=PURPLE, fill=BGCARD, ts=24, ss=18)
    _box(d, W - 470, 360, 380, 110, "HuggingFace", "FLUX · BLIP · MiniLM", color=CYAN, fill=BGCARD, ts=24, ss=18)
    _box(d, W - 470, 540, 380, 110, "Groq Whisper", "Audio transcription", color=GREEN, fill=BGCARD, ts=24, ss=18)
    _box(d, W - 470, 720, 380, 110, "SerpAPI", "Live web search", color=ORANGE, fill=BGCARD, ts=24, ss=18)
    _box(d, W - 470, 900, 380, 110, "PostgreSQL", "Shared database", color=RED, fill=BGCARD, ts=24, ss=18)
    # arrows users -> system
    _arrow(d, 270, 320, cx - bw // 2 - 10, cy - 40, two_way=True)
    _label_mid(d, 270, 320, cx - bw // 2 - 10, cy - 40, "chat / files / requests", dy=-26)
    _arrow(d, 270, 780, cx - bw // 2 - 10, cy + 40, two_way=True)
    _label_mid(d, 270, 780, cx - bw // 2 - 10, cy + 40, "manage users / view stats", dy=8)
    # arrows system -> externals
    for ty in (235, 415, 595, 775, 955):
        _arrow(d, cx + bw // 2 + 10, cy + (ty - cy) * 0.35, W - 470 - 10, ty, two_way=True)
    img.save(path)


def gen_usecase_diagram(path):
    W, H = 1600, 1200
    img, d = _canvas(W, H)
    # system boundary
    d.rounded_rectangle((360, 60, 1240, H - 60), radius=24, outline=BLUE, width=3)
    d.text((400, 80), "AstroBot", font=FB(30), fill=NAVY)
    cases = [
        ("Register / Log in", 200), ("Send chat message", 290),
        ("Generate image", 380), ("Edit image (img-to-img)", 470),
        ("Analyse image (OCR / caption)", 560), ("Ask questions over a PDF (RAG)", 650),
        ("Transcribe audio", 740), ("Generate PDF report", 830),
        ("Run saved workflow chain", 920), ("Export conversation", 1010),
        ("Manage own profile / avatar", 1100),
    ]
    for label, y in cases:
        ew, eh = 600, 64
        ex = 800 - ew // 2
        d.ellipse((ex, y - eh // 2, ex + ew, y + eh // 2), fill=(248, 250, 253), outline=SOFT, width=2)
        f = FR(22)
        bb = d.textbbox((0, 0), label, font=f)
        d.text((800 - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - 2), label, font=f, fill=INK)
    # admin-only ovals
    admin_cases = [("Review stats dashboard", 360), ("Manage user accounts", 470),
                   ("Audit conversation history", 580), ("Create new account", 690)]
    for label, y in admin_cases:
        ew, eh = 540, 64
        ex = 1430 - ew // 2 if False else 1500 - ew  # not used
    # actors
    _actor(d, 150, 560, "End User", scale=1.4)
    _actor(d, 1450, 600, "Administrator", scale=1.4)
    # associations
    for _, y in cases:
        _arrow(d, 220, 560 + (y - 560) * 0.45, 800 - 600 // 2 - 6, y, color=LINE, w=2)
    # admin associations to a few of the same cases + admin ones (we'll just
    # connect the admin actor to the boundary generally)
    _arrow(d, 1390, 600, 1240 + 6, 560, color=LINE, w=2)
    f = FR(20)
    d.text((1300, 720), "(admin extends:\n stats · users ·\n audit · create)", font=f, fill=SOFT)
    img.save(path)


def gen_architecture_diagram(path):
    W, H = 1600, 1180
    img, d = _canvas(W, H)
    # client tier
    _box(d, W // 2 - 300, 50, 600, 110, "Client (Browser)", "Public chat UI · Admin dashboard UI",
         color=BLUE, fill=(238, 244, 252), ts=30, ss=22)
    # app tier — two services
    _box(d, 120, 280, 620, 150, "AstroBot — Main App", "Express · port 3000 · JWT · Helmet · rate-limit",
         color=GREEN, fill=BGCARD, ts=28, ss=20)
    _box(d, 860, 280, 620, 150, "AstroBot — Admin Service", "Express · port 7040 · is_admin gate",
         color=ORANGE, fill=BGCARD, ts=28, ss=20)
    # orchestration tier
    _box(d, W // 2 - 320, 560, 640, 150, "n8n Workflow Orchestrator", "port 5678 · AI Agent (Mistral) · SerpAPI · Think · Whisper branch",
         color=PURPLE, fill=BGCARD, ts=28, ss=20)
    # data + external tier
    _box(d, 80, 860, 470, 130, "PostgreSQL", "shared relational store",
         color=RED, fill=BGCARD, ts=28, ss=20)
    _box(d, 600, 860, 460, 130, "HuggingFace Router", "FLUX · BLIP · MiniLM · fal-ai",
         color=CYAN, fill=BGCARD, ts=28, ss=20)
    _box(d, 1110, 860, 410, 130, "External APIs", "Mistral · Groq · SerpAPI",
         color=NAVY, fill=BGCARD, ts=28, ss=20)
    # arrows
    _arrow(d, W // 2 - 150, 160, 430, 280, two_way=True)
    _arrow(d, W // 2 + 150, 160, 1170, 280, two_way=True)
    _arrow(d, 430, 430, W // 2 - 150, 560, two_way=True)   # main app -> n8n
    _arrow(d, 380, 430, 300, 850, two_way=True)            # main app -> postgres
    _arrow(d, 1170, 430, W // 2 + 150, 560, two_way=True)  # admin -> n8n
    _arrow(d, 1170, 430, 1300, 850, two_way=True)          # admin -> postgres? -> show admin to DB
    _arrow(d, W // 2 - 150, 710, 820, 850, two_way=True)   # n8n -> HF
    _arrow(d, W // 2 + 150, 710, 1300, 850, two_way=True)  # n8n -> external APIs
    img.save(path)


def gen_er_diagram(path):
    W, H = 1600, 1100
    img, d = _canvas(W, H)

    def entity(x, y, name, fields, *, color=BLUE):
        w = 360
        rh = 34
        h = 50 + rh * len(fields)
        d.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=(255, 255, 255), outline=color, width=3)
        d.rectangle((x, y, x + w, y + 46), fill=color)
        f1 = FB(24)
        bb = d.textbbox((0, 0), name, font=f1)
        d.text((x + (w - (bb[2] - bb[0])) / 2, y + 8), name, font=f1, fill=(255, 255, 255))
        fr = FM(20)
        for i, fld in enumerate(fields):
            d.text((x + 18, y + 56 + i * rh), fld, font=fr, fill=INK)
        return (x, y, w, h)

    e_user = entity(70, 70, "users", ["id  PK", "name, surname", "email  UNIQUE", "password_hash",
                                      "is_admin, status", "avatar, last_login"], color=BLUE)
    e_conv = entity(620, 70, "conversations", ["id  PK", "user_id  FK", "message, response", "session_id, session_tag",
                                               "image_url, pdf_url", "attachment (JSON)"], color=GREEN)
    e_doc = entity(70, 560, "documents", ["id  PK", "user_id  FK", "name, mime, size", "text_content"], color=ORANGE)
    e_chunk = entity(620, 560, "document_chunks", ["id  PK", "document_id  FK", "chunk_index", "chunk_text", "embedding (TEXT)"], color=PURPLE)
    e_nb = entity(1180, 70, "notebook_bindings", ["user_id  FK", "session_id  PK", "document_id  FK", "mode"], color=CYAN)
    e_wf = entity(1180, 560, "workflows", ["id  PK", "user_id  FK", "name", "steps (JSON)"], color=RED)
    # relationships (simple lines with crow-foot-ish labels)
    _arrow(d, 430, 200, 620, 200, color=SOFT, w=3, two_way=True)
    _label_mid(d, 430, 200, 620, 200, "1 — *", dy=-26)
    _arrow(d, 250, 410, 250, 560, color=SOFT, w=3, two_way=True)
    _label_mid(d, 250, 410, 250, 560, "1 — *", dy=-26)
    _arrow(d, 430, 660, 620, 660, color=SOFT, w=3, two_way=True)
    _label_mid(d, 430, 660, 620, 660, "1 — *", dy=-26)
    _arrow(d, 250, 240, 250, 70, color=(255, 255, 255), w=1)  # noop spacing
    _arrow(d, 1180, 200, 980, 200, color=SOFT, w=3, two_way=True)
    _arrow(d, 1180, 660, 980, 660, color=SOFT, w=3, two_way=True)
    _arrow(d, 1360, 410, 1360, 560, color=(255, 255, 255), w=1)
    _arrow(d, 1180, 280, 250, 470, color=SOFT, w=2, dashed=True, two_way=True)  # user-notebook (rough)
    img.save(path)


def gen_sequence_diagram(path):
    W, H = 1600, 1200
    img, d = _canvas(W, H)
    lanes = [("User", 150), ("Main App\n(Express)", 470), ("PostgreSQL", 760), ("n8n / AI Agent", 1060), ("Mistral / HF", 1400)]
    top, bot = 110, H - 80
    for name, x in lanes:
        d.rounded_rectangle((x - 130, 40, x + 130, top), radius=10, fill=(238, 244, 252), outline=BLUE, width=3)
        f = FB(22)
        # multi-line title centred
        lines = name.split("\n")
        lh = 26
        ly = (top - 40 - lh * len(lines)) / 2 + 40
        for i, ln in enumerate(lines):
            bb = d.textbbox((0, 0), ln, font=f)
            d.text((x - (bb[2] - bb[0]) / 2, ly + i * lh), ln, font=f, fill=NAVY)
        # lifeline
        d.line((x, top, x, bot), fill=LINE, width=2)

    def msg(x1, x2, y, text, *, ret=False):
        color = SOFT if not ret else (150, 160, 178)
        w = 3 if not ret else 2
        _arrow(d, x1, y, x2, y, color=color, w=w, dashed=ret)
        f = FR(20)
        bb = d.textbbox((0, 0), text, font=f)
        tx = (x1 + x2) / 2 - (bb[2] - bb[0]) / 2
        d.rectangle((tx - 4, y - 28, tx + (bb[2] - bb[0]) + 4, y - 28 + (bb[3] - bb[1]) + 4), fill=(255, 255, 255))
        d.text((tx, y - 28), text, font=f, fill=INK)

    X = {n: x for n, x in lanes}
    a, b, c, e, f = X["User"], X["Main App\n(Express)"], X["PostgreSQL"], X["n8n / AI Agent"], X["Mistral / HF"]
    y = top + 70
    msg(a, b, y, "POST /api/chat/message (text + attachments, JWT)"); y += 90
    msg(b, c, y, "load last 15 messages of session"); y += 70
    msg(c, b, y, "conversation history", ret=True); y += 90
    msg(b, e, y, "POST n8n webhook (enriched prompt + OCR/BLIP + persona)"); y += 90
    msg(e, f, y, "chat completion (mistral-medium) / image / embed"); y += 70
    msg(f, e, y, "model response (JSON action contract)", ret=True); y += 90
    msg(e, b, y, "{ response, action: generate_image | generate_pdf }", ret=True); y += 90
    msg(b, c, y, "INSERT conversation row (+ image_url / pdf_url)"); y += 90
    msg(b, a, y, "200 OK — reply, media, metadata", ret=True)
    img.save(path)


def gen_state_diagram(path):
    W, H = 1600, 850
    img, d = _canvas(W, H)

    def state(cx, cy, label, *, color=BLUE):
        w, h = 280, 100
        d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), radius=30,
                            fill=(238, 244, 252), outline=color, width=3)
        f = FB(24)
        bb = d.textbbox((0, 0), label, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2 - 2), label, font=f, fill=NAVY)
        return (cx, cy)

    # initial dot
    d.ellipse((90, H // 2 - 16, 122, H // 2 + 16), fill=INK)
    s1 = state(330, H // 2, "Idle")
    s2 = state(700, H // 2, "Processing")
    s3 = state(1080, 250, "Awaiting tool /\nmedia")
    s4 = state(1080, 600, "Replied")
    # final
    d.ellipse((1430, H // 2 - 20, 1474, H // 2 + 20), outline=INK, width=4)
    d.ellipse((1438, H // 2 - 12, 1466, H // 2 + 12), fill=INK)

    _arrow(d, 122, H // 2, 330 - 140, H // 2, color=SOFT, w=3)
    _arrow(d, 470, H // 2, 560, H // 2, color=SOFT, w=3)
    _label_mid(d, 470, H // 2, 560, H // 2, "user sends message", dy=-30)
    _arrow(d, 760, H // 2 - 30, 1010, 290, color=SOFT, w=3)
    _label_mid(d, 760, H // 2 - 30, 1010, 290, "needs image / PDF / search", dy=-26)
    _arrow(d, 1010, 320, 760, H // 2 + 30, color=SOFT, w=3)
    _label_mid(d, 1010, 320, 760, H // 2 + 30, "tool result", dy=10)
    _arrow(d, 760, H // 2 + 20, 1010, 560, color=SOFT, w=3)
    _label_mid(d, 760, H // 2 + 20, 1010, 560, "answer ready", dy=-26)
    _arrow(d, 1080, 550, 1080, 360, color=(255, 255, 255), w=1)
    _arrow(d, 1180, 600, 1430, H // 2 + 10, color=SOFT, w=3)
    _arrow(d, 1180, 600, 1080, 300, color=(255, 255, 255), w=1)
    # Replied -> Idle (loop) and Replied -> final
    _arrow(d, 980, 600, 470, H // 2 + 36, color=SOFT, w=2, dashed=True)
    _label_mid(d, 980, 600, 470, H // 2 + 36, "next message", dy=14)
    img.save(path)


def gen_sprint_chart(path):
    """Simple Gantt-ish chart of the four sprints."""
    W, H = 1500, 700
    img, d = _canvas(W, H)
    sprints = [
        ("Sprint 1 — Foundations", 0, 2.5, "Repo · Docker · DB schema · JWT auth · base chat via n8n", BLUE),
        ("Sprint 2 — Conversational core", 2.5, 5.0, "Mistral agent · history · personas · Markdown/KaTeX/Mermaid · streaming UX", GREEN),
        ("Sprint 3 — Multimodal & RAG", 5.0, 8.0, "Image gen · img-to-img · OCR · BLIP · Whisper · RAG/Notebook · PDF", ORANGE),
        ("Sprint 4 — Admin, tests & deploy", 8.0, 11.0, "Admin dashboard · 66-test suite · deploy.py · hardening · docs", PURPLE),
    ]
    left = 70
    top = 120
    week_w = (W - left - 60) / 12.0
    row_h = 110
    # week ruler
    for wk in range(0, 13):
        x = left + wk * week_w
        d.line((x, top - 14, x, top + row_h * len(sprints) + 14), fill=(230, 234, 240), width=1)
        if wk % 2 == 0:
            d.text((x - 8, top - 44), f"W{wk}", font=FR(20), fill=SOFT)
    d.text((left, 40), "Project timeline (≈ 12 weeks)", font=FB(28), fill=NAVY)
    for i, (name, a, b, desc, color) in enumerate(sprints):
        y = top + i * row_h
        x1 = left + a * week_w
        x2 = left + b * week_w
        d.rounded_rectangle((x1, y + 14, x2, y + 64), radius=12, fill=color)
        d.text((x1 + 14, y - 12), name, font=FB(24), fill=NAVY)
        d.text((x1 + 14, y + 74), desc, font=FR(20), fill=SOFT)
    img.save(path)


def generate_all_diagrams():
    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    spec = {
        "context.png": gen_context_diagram,
        "usecase.png": gen_usecase_diagram,
        "architecture.png": gen_architecture_diagram,
        "er.png": gen_er_diagram,
        "sequence.png": gen_sequence_diagram,
        "state.png": gen_state_diagram,
        "sprints.png": gen_sprint_chart,
    }
    for name, fn in spec.items():
        out = DIAGRAMS / name
        fn(out)
        print(f"  diagram → {out.relative_to(ROOT)}")


# ════════════════════════════════════════════════════════════════════════
# WORD HELPERS
# ════════════════════════════════════════════════════════════════════════

TNR = "Times New Roman"
BLACK = RGBColor(0, 0, 0)


def _set_run(run, *, font=TNR, size=12, bold=False, italic=False, color=BLACK):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def para(doc, text="", *, size=12, bold=False, italic=False,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, color=BLACK, space_after=8,
         space_before=0, line_spacing=1.5, indent=None, font=TNR):
    p = doc.add_paragraph()
    p.alignment = align
    if text != "":
        r = p.add_run(text)
        _set_run(r, font=font, size=size, bold=bold, italic=italic, color=color)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = line_spacing
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    return p


def h1(doc, text):
    """Top-level numbered section heading, e.g. '1. Introduction'."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    _set_run(r, size=15, bold=True)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    _set_run(r, size=13, bold=True)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    _set_run(r, size=12, bold=True, italic=True)
    return p


def front_heading(doc, text):
    """Centred, bold, uppercase front-matter heading."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(18)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text.upper())
    _set_run(r, size=14, bold=True)
    return p


def bullet(doc, text, *, level=0, size=12):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.8 + level * 0.6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    _set_run(r, size=size)
    return p


def labelled(doc, label, text, *, size=12):
    """A justified paragraph beginning with a bold run, e.g. 'FR-1: ...'."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.8)
    r1 = p.add_run(label + "  ")
    _set_run(r1, size=size, bold=True)
    r2 = p.add_run(text)
    _set_run(r2, size=size)
    return p


def page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def add_figure(doc, image_path, caption, *, width_inches=6.0):
    image_path = str(image_path)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    if os.path.exists(image_path):
        p.add_run().add_picture(image_path, width=Inches(width_inches))
    else:
        r = p.add_run(f"[missing figure: {os.path.basename(image_path)}]")
        _set_run(r, italic=True, color=RGBColor(0xB0, 0x30, 0x30))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(14)
    r = cap.add_run(caption)
    _set_run(r, size=11, italic=True)


def add_table(doc, headers, rows, *, col_widths=None, caption=None, font_size=11):
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(8)
        cap.paragraph_format.space_after = Pt(4)
        r = cap.add_run(caption)
        _set_run(r, size=11, italic=True)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TAB_ALIGNMENT.CENTER if False else None
    hdr = t.rows[0].cells
    for j, htext in enumerate(headers):
        hdr[j].text = ""
        p = hdr[j].paragraphs[0]
        run = p.add_run(htext)
        _set_run(run, size=font_size, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for i, row in enumerate(rows):
        cells = t.rows[i + 1].cells
        for j, val in enumerate(row):
            cells[j].text = ""
            p = cells[j].paragraphs[0]
            run = p.add_run(str(val))
            _set_run(run, size=font_size)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(10)
    return t


def add_code_block(doc, code, *, size=8.5):
    """A monospace, light-shaded code excerpt."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.left_indent = Cm(0.4)
    pf = p.paragraph_format
    pf.line_spacing = 1.05
    # light shading
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F4F5F7")
    pPr.append(shd)
    for i, line in enumerate(code.rstrip("\n").split("\n")):
        if i > 0:
            r = p.add_run()
            r.add_break()
        r = p.add_run(line if line else " ")
        _set_run(r, font="Consolas", size=size, color=RGBColor(0x1C, 0x24, 0x38))
    return p


# ── Page-numbering / sections ──────────────────────────────────────
def _add_page_field(paragraph):
    run = paragraph.add_run()
    fc1 = OxmlElement("w:fldChar"); fc1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    fc2 = OxmlElement("w:fldChar"); fc2.set(qn("w:fldCharType"), "end")
    run._r.append(fc1); run._r.append(it); run._r.append(fc2)
    _set_run(run, size=11)


def _footer_pageno(section, *, align=WD_ALIGN_PARAGRAPH.CENTER, link_previous=False):
    section.footer.is_linked_to_previous = link_previous
    p = section.footer.paragraphs[0]
    p.text = ""
    p.alignment = align
    _add_page_field(p)


def _no_footer(section, *, link_previous=False):
    section.footer.is_linked_to_previous = link_previous
    section.footer.paragraphs[0].text = ""


def _set_pgnum_format(section, fmt, start=None):
    """fmt: 'decimal' | 'lowerRoman' | 'upperRoman' ..."""
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn("w:pgNumType"))
    if pgNumType is None:
        pgNumType = OxmlElement("w:pgNumType")
        sectPr.append(pgNumType)
    pgNumType.set(qn("w:fmt"), fmt)
    if start is not None:
        pgNumType.set(qn("w:start"), str(start))
    elif pgNumType.get(qn("w:start")) is not None:
        del pgNumType.attrib[qn("w:start")]


def _apply_a4(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.5)


# ════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS / LISTS  (manual, dotted leader)
# ════════════════════════════════════════════════════════════════════════

def _leader_line(doc, label, page, *, bold=False, indent=0.0, size=11):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(2)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(label)
    _set_run(r, size=size, bold=bold)
    ts = p.paragraph_format.tab_stops
    ts.add_tab_stop(Cm(14.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r2 = p.add_run("\t" + str(page))
    _set_run(r2, size=size, bold=bold)
    return p


# Page numbers verified against the rendered .docx (single page-numbering
# break: front matter in lowercase roman starting at i, body in arabic
# starting at 1).
TOC_ENTRIES = [
    ("TABLE OF CONTENTS", "iv", False, 0.0),
    ("LIST OF TABLES", "vi", False, 0.0),
    ("LIST OF FIGURES", "vii", False, 0.0),
    ("LIST OF SYMBOLS AND ABBREVIATIONS", "viii", False, 0.0),
    ("1.  Introduction", "1", True, 0.0),
    ("1.1.  Problem Statement", "1", False, 0.8),
    ("1.2.  Project Objectives", "1", False, 0.8),
    ("1.3.  Project Scope", "2", False, 0.8),
    ("1.4.  Report Organization", "2", False, 0.8),
    ("2.  General Concepts", "3", True, 0.0),
    ("2.1.  Domain Definition", "3", False, 0.8),
    ("2.2.  Technologies Used", "3", False, 0.8),
    ("2.3.  Fundamental Concepts", "3", False, 0.8),
    ("3.  Related Work", "5", True, 0.0),
    ("3.1.  Existing Systems", "5", False, 0.8),
    ("3.2.  Academic Studies", "5", False, 0.8),
    ("3.3.  Comparative Analysis", "5", False, 0.8),
    ("4.  Software Process Model", "7", True, 0.0),
    ("4.1.  Selected Software Development Model", "7", False, 0.8),
    ("4.2.  Definition of Scrum Roles", "7", False, 0.8),
    ("4.3.  Scrum Process", "7", False, 0.8),
    ("4.4.  Scrum Implementation in the Project", "8", False, 0.8),
    ("5.  Requirements Analysis", "9", True, 0.0),
    ("5.1.  Stakeholders", "9", False, 0.8),
    ("5.2.  User Requirements", "9", False, 0.8),
    ("5.2.1.  Functional Requirements", "9", False, 1.4),
    ("5.2.2.  Non-Functional Requirements", "9", False, 1.4),
    ("5.3.  System Specifications", "10", False, 0.8),
    ("6.  System Modeling", "12", True, 0.0),
    ("6.1.  Context Diagram", "12", False, 0.8),
    ("6.2.  Use Case Diagram", "12", False, 0.8),
    ("6.3.  Use Case Descriptions", "13", False, 0.8),
    ("6.4.  Sequence Diagrams", "14", False, 0.8),
    ("7.  System Architecture and Design", "16", True, 0.0),
    ("7.1.  System Architecture", "16", False, 0.8),
    ("7.2.  Structural Models", "17", False, 0.8),
    ("7.2.1.  Class / Entity-Relationship Diagram", "18", False, 1.4),
    ("7.2.2.  Inheritance (Generalization)", "18", False, 1.4),
    ("7.2.3.  Aggregation / Composition", "18", False, 1.4),
    ("7.3.  Behavioral Models", "18", False, 0.8),
    ("7.3.1.  Event-Driven Model", "18", False, 1.4),
    ("7.3.2.  State Diagram", "19", False, 1.4),
    ("8.  System Implementation", "20", True, 0.0),
    ("8.1.  Development Environment", "20", False, 0.8),
    ("8.2.  System Components", "20", False, 0.8),
    ("8.3.  Code Structure", "21", False, 0.8),
    ("9.  MVP Development", "23", True, 0.0),
    ("9.1.  MVP Definition", "23", False, 0.8),
    ("9.2.  Implemented Features", "23", False, 0.8),
    ("9.3.  System Interfaces", "24", False, 0.8),
    ("9.4.  System Demonstration", "27", False, 0.8),
    ("10.  Testing and Evaluation", "31", True, 0.0),
    ("10.1.  Testing Strategy", "31", False, 0.8),
    ("10.2.  Test Scenarios", "31", False, 0.8),
    ("10.3.  Test Results", "31", False, 0.8),
    ("11.  Results and Discussion", "33", True, 0.0),
    ("12.  Conclusion and Future Work", "34", True, 0.0),
    ("12.1.  Conclusion", "34", False, 0.8),
    ("12.2.  Future Work", "34", False, 0.8),
    ("REFERENCES", "35", True, 0.0),
    ("CURRICULUM VITAE", "36", True, 0.0),
    ("13.  Appendices", "44", True, 0.0),
    ("13.1.  Appendix A: Source Code", "44", False, 0.8),
    ("13.2.  Appendix B: Sprint Backlog", "47", False, 0.8),
    ("13.3.  Appendix C: User Guide", "48", False, 0.8),
]

# (num, caption, page)  — pages verified against the rendered .docx.
FIGURES = [
    ("Figure 6.1", "Context diagram of the AstroBot platform", "12"),
    ("Figure 6.2", "Use-case diagram (end user and administrator)", "13"),
    ("Figure 6.3", "Sequence diagram for a chat message round-trip", "14"),
    ("Figure 7.1", "System architecture (client / application / orchestration / data tiers)", "17"),
    ("Figure 7.2", "Entity-relationship model of the PostgreSQL schema", "17"),
    ("Figure 7.3", "State diagram of a conversation message", "19"),
    ("Figure 8.1", "n8n workflow that routes every message through Mistral", "21"),
    ("Figure 9.1", "Public landing page with the central chat bar", "24"),
    ("Figure 9.2", "Features section of the public application", "24"),
    ("Figure 9.3", "About page with the four-developer team", "25"),
    ("Figure 9.4", "Authenticated chat interface (welcome screen)", "25"),
    ("Figure 9.5", "Persona selector — seven selectable assistant personas", "25"),
    ("Figure 9.6", "Profile settings with an in-browser image cropper", "26"),
    ("Figure 9.7", "Admin dashboard — KPIs and activity charts", "26"),
    ("Figure 9.8", "Admin user-management table", "27"),
    ("Figure 9.9", "Admin self-service settings (profile and password)", "27"),
    ("Figure 9.10", "Markdown-rich reply rendered inside a bot bubble", "28"),
    ("Figure 9.11", "AI image generation example", "28"),
    ("Figure 9.12", "On-demand PDF report shown as a download card", "28"),
    ("Figure 9.13", "OCR analysis of an attached image", "29"),
    ("Figure 9.14", "Document Q&A — uploading and binding a PDF (notebook / RAG)", "29"),
    ("Figure 9.15", "Composing a reusable multi-step workflow chain", "30"),
    ("Figure 13.1", "Sprint timeline of the project", "47"),
]

TABLES = [
    ("Table 4.1", "Scrum roles and the team members who held them", "7"),
    ("Table 4.2", "Sprint plan and delivered increments", "8"),
    ("Table 5.1", "Functional requirements", "9"),
    ("Table 5.2", "Non-functional requirements", "9"),
    ("Table 5.3", "Selected REST endpoints and their responsibilities", "10"),
    ("Table 7.1", "Main database tables and their purpose", "17"),
    ("Table 8.1", "Third-party services used by AstroBot", "20"),
    ("Table 10.1", "Integration test suite — results by category", "31"),
]

SYMBOLS = [
    ("AI", "Artificial Intelligence"),
    ("API", "Application Programming Interface"),
    ("BLIP", "Bootstrapping Language-Image Pre-training (image captioning model)"),
    ("CRUD", "Create, Read, Update, Delete"),
    ("CSS", "Cascading Style Sheets"),
    ("DB", "Database"),
    ("ETA", "Estimated Time of Arrival (used generically)"),
    ("FR", "Functional Requirement"),
    ("HTML", "HyperText Markup Language"),
    ("HTTP", "HyperText Transfer Protocol"),
    ("JSON", "JavaScript Object Notation"),
    ("JWT", "JSON Web Token"),
    ("KaTeX", "LaTeX math typesetting library for the web"),
    ("LLM", "Large Language Model"),
    ("MVP", "Minimum Viable Product"),
    ("NFR", "Non-Functional Requirement"),
    ("OCR", "Optical Character Recognition"),
    ("ORM", "Object-Relational Mapping"),
    ("RAG", "Retrieval-Augmented Generation"),
    ("REST", "Representational State Transfer"),
    ("SQL", "Structured Query Language"),
    ("STT", "Speech-to-Text"),
    ("TTS", "Text-to-Speech"),
    ("UI / UX", "User Interface / User Experience"),
    ("UML", "Unified Modeling Language"),
    ("VM", "Virtual Machine"),
    ("VPS", "Virtual Private Server"),
]


# ════════════════════════════════════════════════════════════════════════
# DOCUMENT
# ════════════════════════════════════════════════════════════════════════

def build():
    print("[1/3] Generating diagrams ...")
    generate_all_diagrams()

    print("[2/3] Building document ...")
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = TNR
    style.font.size = Pt(12)

    # ─────────────────────────────────────────────────────────────────
    # SECTION A — cover + APPROVAL  (no page numbers)
    # ─────────────────────────────────────────────────────────────────
    sec_a = doc.sections[0]
    _apply_a4(sec_a)
    _no_footer(sec_a)

    # COVER  (kept to a single page)
    para(doc, "", space_after=10, line_spacing=1.0)
    para(doc, UNIVERSITY, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, FACULTY, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, "CAPSTONE PROJECT REPORT", size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=22, line_spacing=1.1)
    if (ASSETS / "ostim_logo_official.png").exists():
        pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.add_run().add_picture(str(ASSETS / "ostim_logo_official.png"), width=Inches(1.9))
        pp.paragraph_format.space_after = Pt(22)
    para(doc, PROJECT_TITLE, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         line_spacing=1.25, space_after=26)
    para(doc, "Project Team", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3, line_spacing=1.0)
    for sid, sname in STUDENTS:
        para(doc, f"{sname}    ({sid})", size=12, align=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=1, line_spacing=1.1)
    para(doc, "", space_after=12, line_spacing=1.0)
    para(doc, "Project Advisor", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.0)
    para(doc, ADVISOR, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, line_spacing=1.1)
    para(doc, "Undergraduate Project", size=12, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.0)
    para(doc, DEPARTMENT, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, COURSE, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, line_spacing=1.1)
    para(doc, DATE_LINE, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0, line_spacing=1.0)

    # APPROVAL
    page_break(doc)
    front_heading(doc, "APPROVAL")
    para(doc, f"This undergraduate capstone project, entitled “{SHORT_TITLE} — An Intelligent "
              f"Conversational AI Assistant with Multimodal Capabilities, Retrieval-Augmented "
              f"Generation and Web-Based Workflow Integration”, prepared by "
              f"{', '.join(s[1].title() for s in STUDENTS[:-1])} and {STUDENTS[-1][1].title()} "
              f"under the supervision of {ADVISOR}, has been examined by the committee and "
              f"accepted as an undergraduate capstone project in terms of scope and quality.",
         space_after=36)
    for role, name in [("Supervisor", ADVISOR),
                       ("Member", "Jury Member Name Surname"),
                       ("Member", "Jury Member Name Surname"),
                       ("Head of Department", "Head of Department Name Surname")]:
        para(doc, name, size=12, bold=True, space_after=2, line_spacing=1.2)
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(22)
        r1 = p.add_run(f"{role}   "); _set_run(r1, size=12)
        r2 = p.add_run(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ."); _set_run(r2, size=12)

    # ─────────────────────────────────────────────────────────────────
    # SECTION B — front matter (roman numerals, start at i)
    # ─────────────────────────────────────────────────────────────────
    sec_b = doc.add_section(WD_SECTION.NEW_PAGE)
    _apply_a4(sec_b)
    _set_pgnum_format(sec_b, "lowerRoman", start=1)
    _footer_pageno(sec_b)

    # ACKNOWLEDGEMENTS
    front_heading(doc, "ACKNOWLEDGEMENTS")
    para(doc, f"The authors gratefully acknowledge the guidance of our project advisor, "
              f"{ADVISOR}, whose feedback during reviews shaped both the scope and the quality "
              f"of this work. We thank the Department of Computer Engineering at OSTIM Technical "
              f"University for the resources made available throughout the project, and our "
              f"colleagues who took part in informal usability sessions and helped us refine the "
              f"interface and the assistant's behaviour. Finally, we thank the maintainers of the "
              f"open-source tools and free-tier services on which AstroBot is built.")

    # ABSTRACT (LOCAL LANGUAGE VERSION — Turkish)
    page_break(doc)
    front_heading(doc, "ÖZET")
    para(doc, "Bu çalışma, AstroBot adlı çok modlu yeteneklere sahip akıllı bir konuşma tabanlı "
              "yapay zekâ asistanının tasarımını ve gerçekleştirimini sunmaktadır. Proje, "
              "günümüz yapay zekâ araçlarının dağınıklığı sorununu ele alır: sohbet, görsel "
              "üretimi, belge arama, OCR ve ses dökümü genellikle ayrı uygulamalarda yer alır ve "
              "kullanıcılar en güncel modellere erişmek için birden çok ücretli aboneliğe ihtiyaç "
              "duyar. Önerilen sistem; herkese açık bir sohbet arayüzü, bir yönetici paneli ve "
              "her kullanıcı mesajını Mistral büyük dil modeline yönlendiren n8n tabanlı bir iş "
              "akışı düzenleyicisinden oluşur. Sistem; metin tabanlı sohbet, görsel üretimi, "
              "görselden görsele düzenleme, OCR ve görüntü altyazılama, ses dökümü, belgeler "
              "üzerinde soru-cevap (RAG), PDF rapor üretimi ve tekrar kullanılabilir iş akışı "
              "zincirleri gibi temel işlevleri içerir. Geliştirme süreci yinelemeli sprint'ler "
              "hâlinde yürütülmüş, gereksinimler son kullanıcı ve yönetici paydaşlarından elde "
              "edilmiştir. Çözüm Docker ile konteynerleştirilmiş, gerçek bir sunucu üzerinde "
              "dağıtılmış ve 66 entegrasyon testinden oluşan bir paketle doğrulanmıştır.",
         space_after=10)
    para(doc, "Anahtar Kelimeler: Konuşma tabanlı yapay zekâ, büyük dil modeli, RAG, "
              "çok modluluk, iş akışı düzenleme, MVP", size=12, italic=True)

    # ABSTRACT (English)
    page_break(doc)
    front_heading(doc, "ABSTRACT")
    para(doc, "This report presents the design and implementation of AstroBot, an intelligent "
              "conversational artificial-intelligence assistant with multimodal capabilities. The "
              "project targets the fragmentation of today's AI tooling: chat, image generation, "
              "document search, OCR and audio transcription typically live in separate "
              "applications, and users juggle several paid subscriptions to reach state-of-the-art "
              "models. The proposed system consists of a public chat interface, an administrative "
              "dashboard, and an n8n-based workflow orchestrator that routes every user message "
              "through a Mistral large-language model. The Minimum Viable Product delivers core "
              "functionality including text chat with conversation memory and personas, image "
              "generation and image-to-image editing, OCR and visual captioning, audio "
              "transcription, retrieval-augmented question answering over uploaded PDF documents, "
              "on-demand PDF report generation, and reusable workflow chains, alongside a separate "
              "admin service for statistics and user management. Development followed an "
              "iterative, Scrum-style process across four sprints, with requirements elicited from "
              "end-user and administrator stakeholders. The solution is containerised with Docker, "
              "deployed on a live virtual server, and validated by a 66-case integration test "
              "suite. Evaluation indicates that the system meets its acceptance criteria and "
              "fulfils the goal of bringing several AI modalities together behind a single, "
              "free-to-use web application.",
         space_after=10)
    para(doc, "Keywords: Conversational AI, large language model, retrieval-augmented "
              "generation, multimodal, workflow orchestration, MVP", size=12, italic=True)

    # TABLE OF CONTENTS
    page_break(doc)
    front_heading(doc, "TABLE OF CONTENTS")
    pg = doc.add_paragraph()
    pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True)
    pg.paragraph_format.space_after = Pt(4)
    for label, page, bold, indent in TOC_ENTRIES:
        _leader_line(doc, label, page, bold=bold, indent=indent)

    # LIST OF TABLES
    page_break(doc)
    front_heading(doc, "LIST OF TABLES")
    pg = doc.add_paragraph(); pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True); pg.paragraph_format.space_after = Pt(4)
    for num, label, page in TABLES:
        _leader_line(doc, f"{num}:  {label}", page)

    # LIST OF FIGURES
    page_break(doc)
    front_heading(doc, "LIST OF FIGURES")
    pg = doc.add_paragraph(); pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True); pg.paragraph_format.space_after = Pt(4)
    for num, label, page in FIGURES:
        _leader_line(doc, f"{num}:  {label}", page)

    # LIST OF SYMBOLS AND ABBREVIATIONS
    page_break(doc)
    front_heading(doc, "LIST OF SYMBOLS AND ABBREVIATIONS")
    for abbr, full in SYMBOLS:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        r1 = p.add_run(f"{abbr}  :  "); _set_run(r1, size=11, bold=True)
        r2 = p.add_run(full); _set_run(r2, size=11)

    # ─────────────────────────────────────────────────────────────────
    # SECTION C — body + CV + appendices  (arabic, start at 1)
    # ─────────────────────────────────────────────────────────────────
    sec_c = doc.add_section(WD_SECTION.NEW_PAGE)
    _apply_a4(sec_c)
    _set_pgnum_format(sec_c, "decimal", start=1)
    _footer_pageno(sec_c)

    _build_body(doc)
    _build_cv(doc)
    _build_appendices(doc)

    print("[3/3] Saving ...")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    sz = OUTPUT.stat().st_size / 1024
    print(f"\n✓ Report generated: {OUTPUT}")
    print(f"  Size: {sz:.1f} KB")


# ─── 1. Introduction … 12. Conclusion + REFERENCES ─────────────────────
def _build_body(doc):
    # ── 1. INTRODUCTION ───────────────────────────────────────────────
    h1(doc, "1.  Introduction")

    h2(doc, "1.1.  Problem Statement")
    para(doc, "Modern artificial-intelligence assistants are powerful but fragmented. A user who "
              "wants to chat with a model, generate an image, transcribe an audio recording, run "
              "optical character recognition on a screenshot, and ask questions over a PDF "
              "typically needs four or five different applications, each with its own account, "
              "interface, and — increasingly — its own paid subscription. State-of-the-art models "
              "sit behind paywalls that put students and small teams at a disadvantage, while "
              "self-hosting open models remains complex because every model has its own "
              "integration story. Conversations are also treated as disposable: most tools offer "
              "flat message lists with no folders, no tags, no way to pin a document as durable "
              "context, and no exportable record of what was discussed. Reusable multi-step prompt "
              "pipelines are either rebuilt from scratch every time or hidden inside closed "
              "agents. There is no single, affordable place that brings conversational AI, "
              "multimodal input, document understanding, and reusable workflows together.")

    h2(doc, "1.2.  Project Objectives")
    para(doc, "The objective of this project is to design, implement, and deploy a practical "
              "Minimum Viable Product that unifies these capabilities behind one free-to-use web "
              "application. Specific objectives are:")
    bullet(doc, "Provide a conversational chat surface backed by a large-language model, with "
                "per-session memory, multiple personas, and rich rendering of Markdown, mathematics, "
                "code, and diagrams.")
    bullet(doc, "Support multimodal input and output — image generation and image-to-image "
                "editing, OCR and visual captioning, and audio transcription.")
    bullet(doc, "Offer document understanding through retrieval-augmented generation over uploaded "
                "PDF files, plus a notebook mode that pins a document as durable context.")
    bullet(doc, "Make conversations persistent and exportable, with folders/tags, search, and PDF "
                "report generation.")
    bullet(doc, "Provide an administrative dashboard for statistics, user management, and "
                "conversation auditing, isolated from the public application.")
    bullet(doc, "Keep the system free to operate by combining free-tier APIs (Mistral, "
                "HuggingFace, Groq) and a self-hostable workflow engine, and ship it as a "
                "reproducible Docker deployment.")

    h2(doc, "1.3.  Project Scope")
    para(doc, "The project covers the end-to-end software-engineering pipeline for the MVP: "
              "requirements analysis, system modelling, architecture and design, implementation, "
              "testing, and deployment on a live server. In scope are the public chat application, "
              "the administrative dashboard, the n8n orchestration workflow, and the twelve-plus "
              "AI-powered features described in this report. Out of scope — and deferred to future "
              "work — are native mobile applications, a fine-tuned in-house model, billing and "
              "quota enforcement, and large-scale load testing. The system targets a single "
              "deployment environment rather than a multi-tenant SaaS offering.")

    h2(doc, "1.4.  Report Organization")
    para(doc, "Section 2 introduces the domain and the enabling technologies. Section 3 reviews "
              "existing systems and academic work and positions AstroBot among them. Section 4 "
              "describes the software process model. Section 5 presents the requirements analysis, "
              "and Section 6 the system models (context, use-case, and sequence diagrams). Section "
              "7 details the architecture and the structural and behavioural design. Section 8 "
              "covers the implementation; Section 9 the MVP, its features, interfaces, and a "
              "demonstration. Section 10 reports the testing and evaluation, Section 11 discusses "
              "the results, and Section 12 concludes with future work. The curriculum vitae of the "
              "team members and the appendices (source-code excerpts, sprint backlog, and a user "
              "guide) follow the references.")

    # ── 2. GENERAL CONCEPTS ───────────────────────────────────────────
    page_break(doc)
    h1(doc, "2.  General Concepts")

    h2(doc, "2.1.  Domain Definition")
    para(doc, "AstroBot belongs to the domain of conversational AI applications: software systems "
              "that expose a large-language model through a chat interface and orchestrate "
              "additional tools — image models, speech models, search, and retrieval — to answer "
              "user requests. The domain combines natural-language interaction design, web "
              "application engineering, and the operational concerns of calling external model "
              "APIs reliably and affordably. Within this domain the project sits at the "
              "intersection of an end-user productivity tool and a small operational platform with "
              "its own administration side.")

    h2(doc, "2.2.  Technologies Used")
    para(doc, "The solution stack is deliberately built from well-supported, mostly free building "
              "blocks:")
    bullet(doc, "Frontend — vanilla HTML, CSS and JavaScript (no framework), with KaTeX for "
                "mathematics, highlight.js for code, Mermaid for diagrams, Cropper.js for avatar "
                "cropping, and Chart.js in the admin dashboard.")
    bullet(doc, "Backend — Node.js 18 with Express 4, JSON Web Tokens for authentication, bcrypt "
                "for password hashing, Helmet for HTTP security headers, and express-rate-limit. "
                "Document and PDF handling use pdf-parse and PDFKit; OCR uses Tesseract.js.")
    bullet(doc, "AI and models — Mistral medium-latest as the chat model (reached through the n8n "
                "AI Agent), HuggingFace Inference for FLUX.1-schnell (image generation), BLIP "
                "(image captioning) and MiniLM-L6-v2 (sentence embeddings), Groq Whisper-large-v3 "
                "for transcription, and SerpAPI for live web search inside the agent.")
    bullet(doc, "Orchestration and infrastructure — n8n as the visual workflow engine, PostgreSQL "
                "(with the pgvector image, used as a plain relational store) for persistence, and "
                "Docker with Docker Compose for packaging and deployment. A Python script "
                "(deploy.py) performs the SSH/SFTP deployment to the server.")

    h2(doc, "2.3.  Fundamental Concepts")
    para(doc, "Several concepts recur throughout the report. A large-language model (LLM) is a "
              "neural network trained to predict text; given a conversation it produces a "
              "continuation, and with a system prompt and tools it can act as an agent. "
              "Retrieval-augmented generation (RAG) improves grounding by retrieving the most "
              "relevant chunks of a document — here ranked by cosine similarity over MiniLM "
              "embeddings — and inserting them into the prompt before the model answers. "
              "Workflow orchestration means describing a multi-step pipeline (receive a request, "
              "branch on its type, enrich it, call the model, post-process, respond) as a graph "
              "that can be edited without redeploying application code; AstroBot uses n8n for "
              "this. JSON Web Tokens carry a signed, time-limited identity claim so the stateless "
              "API can authorise requests, and an is_admin claim gates the administrative service. "
              "Containerization packages each service with its dependencies so the system is "
              "reproducible from a fresh virtual machine.")

    # ── 3. RELATED WORK ──────────────────────────────────────────────
    page_break(doc)
    h1(doc, "3.  Related Work")

    h2(doc, "3.1.  Existing Systems")
    para(doc, "General-purpose assistants such as ChatGPT, Claude, and Gemini provide strong "
              "conversational quality and, in their paid tiers, some multimodal features. However, "
              "advanced capabilities — large context windows, image generation, document analysis "
              "— are typically gated behind subscriptions, and the more specialised tasks (OCR, "
              "transcription, vector search over private documents, reproducible multi-step "
              "pipelines) are spread across separate products such as dedicated OCR services, "
              "speech-to-text APIs, and notebook-style RAG tools. Self-hosting alternatives (open "
              "models served locally) exist but require significant operational effort and "
              "rarely come with a polished, multi-feature interface out of the box.")

    h2(doc, "3.2.  Academic Studies")
    para(doc, "Research on retrieval-augmented generation has shown that grounding model outputs "
              "in retrieved passages reduces hallucination and improves factual accuracy on "
              "open-domain question answering, and that dense retrievers based on transformer "
              "embeddings with cosine similarity generally outperform sparse lexical baselines for "
              "this purpose. Work on LLM-based agents demonstrates that giving a model a small set "
              "of tools (search, a scratchpad for reasoning, a structured output contract) lets it "
              "decompose tasks reliably while keeping the surrounding system simple. On the "
              "engineering side, studies of agile software delivery report that iterative, "
              "feedback-driven development is well suited to projects whose requirements evolve as "
              "users try early versions — which is precisely the situation for a feature-rich "
              "assistant.")

    h2(doc, "3.3.  Comparative Analysis")
    para(doc, "Compared with the alternatives above, AstroBot emphasises three differentiators. "
              "First, breadth behind one surface: chat, image generation and editing, OCR and "
              "captioning, transcription, document RAG, notebook mode, PDF report generation, "
              "workflow chains, and an admin side are all reachable from a single application "
              "with a single account. Second, affordability: by combining free-tier model APIs "
              "with a self-hostable orchestration layer, the system is free to operate for the "
              "team and its users. Third, transparency and reproducibility: the orchestration "
              "logic is a visible n8n graph that can be tuned without redeploying code, the data "
              "model and deployment are documented, and the whole stack comes up from a single "
              "docker compose command. AstroBot does not attempt to beat frontier models on raw "
              "quality; it integrates accessible models well.")

    # ── 4. SOFTWARE PROCESS MODEL ────────────────────────────────────
    page_break(doc)
    h1(doc, "4.  Software Process Model")

    h2(doc, "4.1.  Selected Software Development Model")
    para(doc, "An iterative, Scrum-style agile model was selected. The set of desirable features "
              "for an AI assistant is large and evolves quickly as the team and informal testers "
              "use early versions, so a plan-driven waterfall process would have been a poor fit. "
              "The project was organised into four short sprints, each producing a working, "
              "testable increment of the product, with the most valuable and foundational items "
              "scheduled first.")

    h2(doc, "4.2.  Definition of Scrum Roles")
    para(doc, "Because the project was carried out by a four-person student team, the standard "
              "Scrum roles were mapped onto the team as shown in Table 4.1. The Product Owner role "
              "(prioritising the backlog, validating increments against acceptance criteria) "
              "was held primarily by the project lead in consultation with the advisor, who acted "
              "as the external stakeholder. The Scrum Master role (facilitating ceremonies, "
              "removing blockers) rotated informally but was anchored by the project lead. All "
              "four members formed the Development Team, each owning one or more feature domains.")
    add_table(doc,
              ["Scrum role", "Held by", "Main responsibilities"],
              [["Product Owner / Stakeholder", "Tidiane Konaté (with the advisor)",
                "Backlog priority, acceptance of increments, scope decisions"],
               ["Scrum Master", "Tidiane Konaté", "Sprint ceremonies, blocker removal, coordination"],
               ["Development Team — Architecture / Backend / Deployment", "Tidiane Konaté",
                "System architecture, REST API, n8n workflow, Docker, deployment"],
               ["Development Team — Vision / Product / UX", "Sidi Mohamed Sall",
                "Product framing, public interface design, usability sessions"],
               ["Development Team — AI / LLM / Multimodal", "Ahmed Essalem",
                "Model integration, image/OCR/audio features, RAG pipeline"],
               ["Development Team — QA / Frontend / Testing", "Saad Ibrahim Houssein",
                "Frontend polish, admin dashboard, integration test suite"]],
              col_widths=[5.0, 4.5, 6.0],
              caption="Table 4.1: Scrum roles and the team members who held them.")

    h2(doc, "4.3.  Scrum Process")
    para(doc, "Each sprint followed the usual ceremonies adapted to the team's size: a sprint "
              "planning meeting to select backlog items and define acceptance criteria, short "
              "stand-up synchronisations to surface progress and blockers, a sprint review in "
              "which the increment was demonstrated, and a brief retrospective to adjust the way "
              "of working. The product backlog was maintained as a list of user stories with "
              "priority and acceptance criteria; items not completed in a sprint were re-ranked "
              "for the next one. The advisor's review feedback fed directly into the backlog.")

    h2(doc, "4.4.  Scrum Implementation in the Project")
    para(doc, "The project was delivered in four sprints over roughly twelve weeks, as summarised "
              "in Table 4.2 and Figure 13.1 (in Appendix B). Sprint 1 established the foundations "
              "— repository, Docker Compose, database schema, JWT authentication, and a minimal "
              "chat path through n8n. Sprint 2 built the conversational core — the Mistral AI "
              "Agent, conversation history, personas, and the rich-content rendering and "
              "streaming-style reveal in the chat UI. Sprint 3 added the multimodal and retrieval "
              "features — image generation and image-to-image editing, OCR and BLIP captioning, "
              "Whisper transcription, RAG and notebook mode, and on-demand PDF reports. Sprint 4 "
              "delivered the administrative dashboard, the 66-case integration test suite, the "
              "deployment script, security hardening, and documentation.")
    add_table(doc,
              ["Sprint", "Weeks", "Goal", "Delivered increment"],
              [["1 — Foundations", "≈ 1–3", "Stand up the skeleton",
                "Repo, Docker Compose, PostgreSQL schema, JWT auth, base chat via n8n"],
               ["2 — Conversational core", "≈ 3–5", "Make the chat good",
                "Mistral AI Agent, conversation history, 7 personas, Markdown/KaTeX/highlight.js/Mermaid, streaming-style reveal"],
               ["3 — Multimodal & RAG", "≈ 5–8", "Add the AI features",
                "Image generation & img-to-img, OCR, BLIP captions, Whisper transcription, RAG & notebook mode, PDF report generation, workflow chains, tags/exports"],
               ["4 — Admin, tests & deploy", "≈ 8–11", "Operate & harden",
                "Admin dashboard (stats, users, audit), 66-case integration test suite, deploy.py, security hardening, documentation"]],
              col_widths=[3.4, 1.8, 3.6, 6.7],
              caption="Table 4.2: Sprint plan and delivered increments.")

    # ── 5. REQUIREMENTS ANALYSIS ─────────────────────────────────────
    page_break(doc)
    h1(doc, "5.  Requirements Analysis")

    h2(doc, "5.1.  Stakeholders")
    para(doc, "The primary stakeholders are the end users of the public application — students "
              "preparing reports and code, developers exploring multimodal AI, and knowledge "
              "workers who need question answering over their own documents — and the "
              "administrator, who operates the deployment, manages accounts, and audits usage. "
              "Secondary stakeholders include the project advisor, who acted as the external "
              "reviewer and shaped the scope, and the development team itself, which relied on a "
              "reproducible build and a fast deployment loop.")

    h2(doc, "5.2.  User Requirements")
    para(doc, "Requirements were gathered from the team's own use of comparable tools, short "
              "informal usability sessions with fellow students, and the advisor's reviews, then "
              "translated into prioritised backlog items with acceptance criteria and validated at "
              "sprint reviews. They are summarised below as functional and non-functional "
              "requirements.")

    h3(doc, "5.2.1.  Functional Requirements")
    para(doc, "The functional requirements are summarised in Table 5.1.")
    add_table(doc,
              ["ID", "Functional requirement"],
              [["FR-1", "A visitor can register an account; authenticated users can log in and out."],
               ["FR-2", "A user can send a text message and receive a model reply, with the last fifteen messages of the session kept as context."],
               ["FR-3", "A user can choose a persona that adjusts the assistant's tone."],
               ["FR-4", "A user can request an image from a text prompt and receive it inline in the conversation."],
               ["FR-5", "A user can upload an image and ask the assistant to edit it (image-to-image)."],
               ["FR-6", "A user can attach an image and have its text extracted (OCR) and/or described (captioning), with the result used as context."],
               ["FR-7", "A user can upload a PDF and ask questions answered from its content (RAG), or pin it as durable notebook context."],
               ["FR-8", "A user can record audio and have it transcribed to text."],
               ["FR-9", "A user can obtain a generated PDF report of a typed response."],
               ["FR-10", "A user can organise sessions with colour-coded tags, search the conversation history, and export a session as PDF, Markdown, or JSON."],
               ["FR-11", "A user can define and replay reusable multi-step workflow chains."],
               ["FR-12", "A user can manage their profile and avatar (with an in-browser cropper)."],
               ["FR-13", "An administrator can log in to a separate dashboard and view real-time statistics and activity charts."],
               ["FR-14", "An administrator can search, suspend, reactivate, reset the password of, delete, and create user accounts."],
               ["FR-15", "An administrator can browse any user's conversation history grouped by session."]],
              col_widths=[1.6, 13.3],
              caption="Table 5.1: Functional requirements.", font_size=10)

    h3(doc, "5.2.2.  Non-Functional Requirements")
    add_table(doc,
              ["ID", "Category", "Requirement"],
              [["NFR-1", "Performance", "Core chat and CRUD requests shall complete within an interactive latency budget under normal load; long model calls are bounded by the n8n agent's iteration cap."],
               ["NFR-2", "Security", "Passwords shall be stored hashed with bcrypt (12 salt rounds); sessions shall use signed JWTs with a 7-day expiry; the admin service shall reject any token without an is_admin claim."],
               ["NFR-3", "Security", "HTTP responses shall carry Helmet security headers; rate limiting shall apply (auth 20/15 min, chat 30/min, admin 500/15 min); uploads shall be capped at 10 MB and 5 attachments per message."],
               ["NFR-4", "Reliability", "The application shall self-heal on restart through idempotent database migrations and an admin re-seed; containers shall use restart policies so a host reboot recovers the system."],
               ["NFR-5", "Maintainability", "Orchestration logic shall live in a visible n8n workflow editable without redeploying code; the codebase shall be modular by feature domain."],
               ["NFR-6", "Portability", "The whole system shall come up from a single docker compose command and shall be deployable to a fresh virtual server with one script."],
               ["NFR-7", "Cost", "The system shall rely only on free-tier external APIs and self-hostable components."]],
              col_widths=[1.6, 2.6, 11.3],
              caption="Table 5.2: Non-functional requirements.")

    h2(doc, "5.3.  System Specifications")
    para(doc, "The backend exposes a REST API: authentication and profile endpoints under "
              "/api/auth, chat and history endpoints under /api/chat, and the document, RAG, "
              "transcription, image-edit, YouTube, and workflow endpoints under /api/features; "
              "the admin service exposes a parallel /api set. Selected endpoints are listed in "
              "Table 5.3. Every chat message is forwarded to the n8n webhook, which returns a JSON "
              "object carrying the reply text and an optional action (generate_image or "
              "generate_pdf). The persistent data entities are users, conversations (with optional "
              "image, PDF, and attachment fields), documents, document_chunks (with embeddings "
              "stored as text), notebook_bindings, and workflows; they are detailed in Section 7.")
    add_table(doc,
              ["Method & path", "Service", "Responsibility"],
              [["POST /api/auth/register · /login", "Main", "Account creation and login; issues a 7-day JWT."],
               ["PUT /api/auth/profile · /password · /avatar", "Main", "Update profile fields, change password, set/clear avatar."],
               ["POST /api/chat/message", "Main", "Core chat: OCR/BLIP on images, history + persona enrichment, n8n round-trip, image/PDF generation, persistence."],
               ["GET /api/chat/history · /sessions · /session/:id", "Main", "Conversation history, distinct sessions, and a single session's messages."],
               ["PUT /api/chat/sessions/:id/tag · GET /tags", "Main", "Folder/tag system over sessions."],
               ["GET /api/chat/export/:id?format=pdf|md|json", "Main", "Export a session in the chosen format."],
               ["POST /api/features/documents · PUT /notebook", "Main", "Upload a PDF (chunk + embed), bind it to a session in notebook or RAG mode."],
               ["POST /api/features/transcribe · /image-edit · /youtube-transcript", "Main", "Audio transcription (Whisper), image-to-image edit, YouTube summary."],
               ["GET/POST/PUT/DELETE /api/features/workflows", "Main", "CRUD for user-defined workflow chains."],
               ["GET /api/stats", "Admin", "Dashboard metrics: user/message/session/token/image/PDF/doc totals, daily activity, top users."],
               ["GET/POST/PUT/DELETE /api/users[/:id]", "Admin", "List, create, update (status/role), reset password, delete users; per-user conversations."]],
              col_widths=[6.0, 1.6, 7.3],
              caption="Table 5.3: Selected REST endpoints and their responsibilities.", font_size=10)

    # ── 6. SYSTEM MODELING ───────────────────────────────────────────
    page_break(doc)
    h1(doc, "6.  System Modeling")

    h2(doc, "6.1.  Context Diagram")
    para(doc, "Figure 6.1 shows the context model. The AstroBot platform (the public web app, the "
              "admin service, and the n8n orchestrator) is the system of interest. Two human "
              "actors interact with it: the end user, who sends chat messages, uploads files, and "
              "consumes replies and generated media, and the administrator, who manages accounts "
              "and reviews statistics. The platform integrates with several external systems: "
              "Mistral Cloud for LLM inference, the HuggingFace Inference router for image "
              "generation, captioning and embeddings, Groq Whisper for transcription, SerpAPI for "
              "live web search, and a shared PostgreSQL database for persistence.")
    add_figure(doc, DIAGRAMS / "context.png", "Figure 6.1: Context diagram of the AstroBot platform.", width_inches=6.2)

    h2(doc, "6.2.  Use Case Diagram")
    para(doc, "Figure 6.2 summarises the use cases. The end user can register and log in, send "
              "chat messages, generate and edit images, analyse images via OCR and captioning, "
              "ask questions over a PDF using RAG, transcribe audio, generate PDF reports, run "
              "saved workflow chains, export conversations, and manage their profile and avatar. "
              "The administrator additionally reviews the statistics dashboard, manages user "
              "accounts (search, suspend, reset, delete, create), and audits conversation "
              "history.")
    add_figure(doc, DIAGRAMS / "usecase.png", "Figure 6.2: Use-case diagram (end user and administrator).", width_inches=6.2)

    h2(doc, "6.3.  Use Case Descriptions")
    para(doc, "Two representative use cases are described below.")
    para(doc, "Send chat message — Actor: authenticated end user. Preconditions: the user holds a "
              "valid JWT and is on the chat page. Main flow: the user types a message, optionally "
              "attaches images, and submits; the backend runs OCR and captioning on any images, "
              "loads the last fifteen messages of the session, prepends the active persona "
              "directive and any notebook/RAG context, and forwards the enriched request to the "
              "n8n webhook; the n8n AI Agent calls Mistral (with optional SerpAPI search and a "
              "reasoning scratchpad) and returns a JSON reply; the backend triggers image or PDF "
              "generation if the reply requests it, persists the conversation row, and returns the "
              "reply and any media. Postconditions: the conversation history contains the new "
              "exchange. Alternative flows: if the model output cannot be parsed as the expected "
              "contract the backend falls back to treating the whole output as the reply text; "
              "rate-limit and validation errors return clear 4xx responses.")
    para(doc, "Ask questions over a PDF (RAG) — Actor: authenticated end user. Preconditions: the "
              "user has uploaded a PDF and bound it to the session in RAG mode. Main flow: on each "
              "question the backend embeds the question with MiniLM, retrieves the four most "
              "similar chunks of the document by cosine similarity, inserts them into the prompt, "
              "and proceeds as in the chat use case. Postconditions: the answer is grounded in the "
              "retrieved chunks. Alternative flow: in notebook mode the first six thousand "
              "characters of the document are used as context instead of retrieved chunks.")

    h2(doc, "6.4.  Sequence Diagrams")
    para(doc, "Figure 6.3 traces a chat message round-trip. The browser posts the message (with "
              "any attachments and the JWT) to the main app, which loads the session history from "
              "PostgreSQL, posts an enriched prompt to the n8n webhook, where the AI Agent calls "
              "Mistral (and, when needed, HuggingFace for images or embeddings); n8n returns a "
              "structured JSON response, the main app generates an image or PDF if requested, "
              "inserts the conversation row, and returns the reply, media, and metadata to the "
              "browser.")
    add_figure(doc, DIAGRAMS / "sequence.png", "Figure 6.3: Sequence diagram for a chat message round-trip.", width_inches=6.4)

    # ── 7. SYSTEM ARCHITECTURE AND DESIGN ────────────────────────────
    page_break(doc)
    h1(doc, "7.  System Architecture and Design")

    h2(doc, "7.1.  System Architecture")
    para(doc, "AstroBot follows a layered client–server architecture, shown in Figure 7.1, "
              "deployed as three Docker services on one private network. The client tier is the "
              "browser, serving the public chat UI and the admin dashboard UI from static assets. "
              "The application tier contains two independent Express services: the main app on "
              "port 3000 (public chat, JWT-authenticated, with Helmet and rate limiting) and the "
              "admin service on port 7040 (gated by an is_admin claim, completely separate from "
              "the public process). The orchestration tier is an n8n instance on port 5678 that "
              "hosts the AI Agent workflow and reaches Mistral, SerpAPI, a Think scratchpad, and a "
              "self-hosted Whisper transcriber. The data and external tier consists of a shared "
              "PostgreSQL container (used as a plain relational store), the HuggingFace Inference "
              "router (FLUX, BLIP, MiniLM, with a fal-ai fallback), and the external Mistral, "
              "Groq, and SerpAPI services. This shape was chosen so that the existing PostgreSQL "
              "container can be reused without operating a second database, all AI traffic exits "
              "through n8n so prompts and tools can be tuned without redeploying, and a "
              "public-facing exploit can never reach the admin process.")
    add_figure(doc, DIAGRAMS / "architecture.png", "Figure 7.1: System architecture (client / application / orchestration / data tiers).", width_inches=6.4)

    h2(doc, "7.2.  Structural Models")
    para(doc, "The static design is centred on the persistent data model rather than a deep class "
              "hierarchy: the backend is organised by feature modules (auth, chat, features) with "
              "controller, service, and data-access responsibilities, and the durable state lives "
              "in a small set of relational tables described below and in Figure 7.2.")
    add_table(doc,
              ["Table", "Purpose"],
              [["users", "Accounts: name, email, hashed password, is_admin, status, avatar, last_login."],
               ["conversations", "One row per message/response, with session_id, session_tag, and optional image_url, pdf_url, pdf_filename, and an attachment JSON blob."],
               ["documents", "Uploaded files for notebook/RAG: name, mime, size, extracted text_content."],
               ["document_chunks", "Per-document chunks for RAG: chunk_index, chunk_text, and an embedding stored as text."],
               ["notebook_bindings", "Which document is active for which session, and the mode (notebook | rag)."],
               ["workflows", "User-defined multi-step prompt chains, stored as a steps JSON array."]],
              col_widths=[3.6, 11.3],
              caption="Table 7.1: Main database tables and their purpose.")
    add_figure(doc, DIAGRAMS / "er.png", "Figure 7.2: Entity-relationship model of the PostgreSQL schema.", width_inches=6.4)

    h3(doc, "7.2.1.  Class / Entity-Relationship Diagram")
    para(doc, "Because the backend is JavaScript with direct SQL access rather than an "
              "object-oriented domain model, the structural design is best expressed as the "
              "entity-relationship diagram in Figure 7.2. A user owns many conversations, many "
              "documents, many notebook bindings, and many workflows (one-to-many in each case); "
              "a document owns many document chunks (one-to-many); and a notebook binding links a "
              "user's session to one document. Foreign keys cascade on delete so removing a user "
              "or a document removes its dependent rows.")

    h3(doc, "7.2.2.  Inheritance (Generalization)")
    para(doc, "The system uses very little inheritance by design. Conceptually the user type is "
              "specialised into a regular user and an administrator, but this specialisation is "
              "represented by a boolean is_admin flag on the single users table rather than by a "
              "subclass, which keeps the schema and the authorisation logic simple — the admin "
              "service simply requires is_admin to be true in the JWT.")

    h3(doc, "7.2.3.  Aggregation / Composition")
    para(doc, "Aggregation and composition appear in two places. A conversation session aggregates "
              "its individual message rows (they share a session_id but each row is independently "
              "meaningful), and a document composes its chunks: the chunks have no meaning outside "
              "their parent document and are deleted with it (composition, enforced by an "
              "ON DELETE CASCADE foreign key). Notebook bindings are association objects linking a "
              "session and a document with a mode attribute.")

    h2(doc, "7.3.  Behavioral Models")
    para(doc, "The dynamic design is event-driven at the orchestration boundary and state-based "
              "for an individual message.")

    h3(doc, "7.3.1.  Event-Driven Model")
    para(doc, "Every chat message is an event posted to the n8n webhook. Inside the workflow a "
              "Switch node routes the event by type (audio vs. text); the audio branch posts the "
              "file to a Whisper transcriber and rejoins the text branch; a code node enriches the "
              "payload with the user's name and conversation history; the AI Agent node consumes "
              "it and may itself emit tool-call events to SerpAPI (capped at two searches) and to "
              "a Think scratchpad before producing its JSON reply, which a final node extracts and "
              "returns. On the client, the bot reply is revealed word by word, an animation driven "
              "by a timer rather than by server-side streaming.")

    h3(doc, "7.3.2.  State Diagram")
    para(doc, "Figure 7.3 models the lifecycle of a single conversation message. From the Idle "
              "state, the user sending a message moves the session into Processing; if the model "
              "needs a tool or media generation the session enters Awaiting tool / media and "
              "returns to Processing when the result arrives; when the answer is ready the session "
              "moves to Replied; sending the next message returns it to Processing, and closing the "
              "session is the terminal transition.")
    add_figure(doc, DIAGRAMS / "state.png", "Figure 7.3: State diagram of a conversation message.", width_inches=6.2)

    # ── 8. SYSTEM IMPLEMENTATION ─────────────────────────────────────
    page_break(doc)
    h1(doc, "8.  System Implementation")

    h2(doc, "8.1.  Development Environment")
    para(doc, "Development used Git for version control with a public mirror on GitHub "
              f"({GITHUB_URL}), Visual Studio Code as the editor, Node.js 18 for the backend, and "
              "Docker Desktop / Docker Compose for running the services locally exactly as they "
              "run in production. The n8n workflow was developed in the n8n editor and exported as "
              "JSON kept in the repository. Deployment to the server is performed by a Python "
              "script (deploy.py) that packages the project, uploads it over SFTP, and runs "
              "docker compose up -d --build remotely; a 66-case Python integration suite "
              "(test_all.py) is run against the live deployment.")

    h2(doc, "8.2.  System Components")
    para(doc, "The MVP comprises four components. The main application (frontend + backend) serves "
              "the public chat UI and the REST API on port 3000. The admin service serves the "
              "dashboard UI and a parallel API on port 7040. The n8n instance on port 5678 hosts "
              "the orchestration workflow. The shared PostgreSQL container provides persistence. "
              "Beyond these, the system depends on several third-party services, summarised in "
              "Table 8.1. Figure 8.1 shows the n8n workflow that every message passes through.")
    add_table(doc,
              ["Service", "Used for", "How it is reached"],
              [["Mistral Cloud (mistral-medium-latest)", "Conversational LLM and the agent's reasoning", "Inside the n8n AI Agent node"],
               ["HuggingFace Inference router", "Image generation (FLUX.1-schnell), image captioning (BLIP), sentence embeddings (MiniLM-L6-v2)", "HTTPS from the backend / n8n"],
               ["fal-ai", "Fallback image generation and image-to-image editing", "HTTPS from the backend"],
               ["Groq (Whisper-large-v3-turbo)", "Audio transcription", "HTTPS from the backend / n8n audio branch"],
               ["SerpAPI", "Live web search available to the agent (capped at two calls per message)", "Inside the n8n AI Agent as a tool"],
               ["PostgreSQL (shared container)", "Persistent storage for all entities", "TCP on the private Docker network"]],
              col_widths=[4.6, 7.0, 3.3],
              caption="Table 8.1: Third-party services used by AstroBot.", font_size=10)
    add_figure(doc, SCREENSHOTS / "19n.png", "Figure 8.1: n8n workflow that routes every message through Mistral, with optional web search and reasoning tools.", width_inches=6.4)

    h2(doc, "8.3.  Code Structure")
    para(doc, "The repository is organised by component and, within the backend, by feature "
              "domain:")
    add_code_block(doc,
        "astrobot/\n"
        "├── frontend/                # static HTML / CSS / JS for the public app\n"
        "│   ├── index.html  chat.html  login.html  register.html\n"
        "│   ├── style.css   script.js\n"
        "│   └── team/                # developer photos for the About section\n"
        "├── backend/\n"
        "│   ├── server.js            # Express entry point, middleware, routes\n"
        "│   ├── db/index.js          # PostgreSQL pool + idempotent migrations + admin seed\n"
        "│   ├── middleware/auth.js   # JWT verification\n"
        "│   └── routes/\n"
        "│       ├── auth.js          # register / login / profile / avatar\n"
        "│       ├── chat.js          # messages, image gen, PDF, history, sessions, export\n"
        "│       └── features.js      # documents, RAG, notebook, transcribe, YouTube, img-edit, workflows\n"
        "├── admin/\n"
        "│   ├── backend/server.js    # separate Express service (port 7040)\n"
        "│   └── backend/public/      # admin dashboard UI (vanilla JS + Chart.js)\n"
        "├── docker/\n"
        "│   ├── docker-compose.yml   # the two AstroBot services on the n8n network\n"
        "│   ├── Dockerfile           # main app\n"
        "│   └── .env.example         # template for local secrets\n"
        "├── deploy.py                # SSH + SFTP + docker compose deployment\n"
        "├── test_all.py              # 66-case integration test suite\n"
        "└── README.md\n",
        size=8.5)
    para(doc, "Within the backend, each route module separates request handling from the "
              "operations it performs, and the database module owns all SQL and the schema "
              "migrations, so the schema can evolve safely on every redeploy. Representative code "
              "excerpts are given in Appendix A.")

    # ── 9. MVP DEVELOPMENT ───────────────────────────────────────────
    page_break(doc)
    h1(doc, "9.  MVP Development")

    h2(doc, "9.1.  MVP Definition")
    para(doc, "The MVP is defined as the smallest deployable system that delivers real value to "
              "end users and to an administrator: a working chat assistant with conversation "
              "memory, the multimodal and retrieval features listed below, persistent and "
              "exportable conversations, and a separate admin dashboard — all running on a real "
              "server and covered by an automated test suite. Anything beyond that (native mobile "
              "apps, billing, a fine-tuned model) is explicitly future work.")

    h2(doc, "9.2.  Implemented Features")
    para(doc, "The MVP implements the following capabilities:")
    bullet(doc, "Conversational chat — Mistral medium-latest via the n8n AI Agent, with a "
                "fifteen-message context window per session and seven selectable personas.")
    bullet(doc, "Rich content rendering — Markdown, KaTeX mathematics, highlight.js code "
                "highlighting, and Mermaid diagrams in the bot bubble, with a word-by-word reveal.")
    bullet(doc, "Image generation — FLUX.1-schnell through the HuggingFace router with a fal-ai "
                "fallback, plus image-to-image editing (style transfer) via FLUX dev.")
    bullet(doc, "OCR and visual understanding — Tesseract.js OCR (English and French) and BLIP "
                "captioning, with both signals added to the prompt before the model answers.")
    bullet(doc, "Document Q&A — retrieval-augmented generation over uploaded PDFs (chunking, "
                "MiniLM embeddings, top-4 cosine retrieval) and a notebook mode that pins the "
                "document as durable context.")
    bullet(doc, "Audio transcription — browser recording transcribed by Groq Whisper-large-v3.")
    bullet(doc, "PDF report generation — typed responses turned into a downloadable PDF (PDFKit), "
                "with a heuristic that forces generation when the model acknowledges a report.")
    bullet(doc, "Productivity tools — colour-coded session tags and search, conversation export "
                "(PDF / Markdown / JSON), a YouTube summariser, reusable workflow chains, and a "
                "profile/avatar editor with an in-browser cropper.")
    bullet(doc, "Administration — a separate dashboard with real-time KPIs and charts, user "
                "management (search, suspend, reactivate, reset password, delete, create), and "
                "per-user conversation auditing grouped by session.")

    h2(doc, "9.3.  System Interfaces")
    para(doc, "The public application opens on a landing page (Figure 9.1) with a central chat bar "
              "and a friendly mascot, a features section (Figure 9.2), and an about page with the "
              "team (Figure 9.3). After logging in the user reaches the chat interface (Figure "
              "9.4) with the session sidebar and attachment controls; a persona selector (Figure "
              "9.5) adjusts the assistant's tone, and a profile panel with an in-browser image "
              "cropper (Figure 9.6) manages the account. The administrator uses a separate "
              "dashboard with KPI tiles and activity charts (Figure 9.7), a user-management table "
              "(Figure 9.8), and a self-service settings panel (Figure 9.9).")
    add_figure(doc, SCREENSHOTS / "1.png", "Figure 9.1: Public landing page with the central chat bar.")
    add_figure(doc, SCREENSHOTS / "2.png", "Figure 9.2: Features section of the public application.")
    add_figure(doc, SCREENSHOTS / "3.png", "Figure 9.3: About page with the four-developer team.")
    add_figure(doc, SCREENSHOTS / "6.png", "Figure 9.4: Authenticated chat interface (welcome screen).")
    add_figure(doc, SCREENSHOTS / "7.png", "Figure 9.5: Persona selector — seven selectable assistant personas.", width_inches=4.5)
    add_figure(doc, SCREENSHOTS / "14.png", "Figure 9.6: Profile settings with an in-browser image cropper.", width_inches=3.6)
    add_figure(doc, SCREENSHOTS / "16a.png", "Figure 9.7: Admin dashboard — KPIs and activity charts.")
    add_figure(doc, SCREENSHOTS / "17a.png", "Figure 9.8: Admin user-management table.")
    add_figure(doc, SCREENSHOTS / "18a.png", "Figure 9.9: Admin self-service settings (profile and password).")

    h2(doc, "9.4.  System Demonstration")
    para(doc, "The features were demonstrated against the live deployment with representative "
              "scenarios: a Markdown-rich answer rendered in the chat bubble (Figure 9.10); "
              "generating an image from a prompt (Figure 9.11); turning a typed response into a "
              "downloadable PDF report (Figure 9.12); attaching a screenshot so the assistant "
              "reads its text via OCR and explains it (Figure 9.13); uploading a PDF and binding "
              "it as notebook/RAG context (Figure 9.14); and composing a reusable workflow chain "
              "(Figure 9.15). Audio transcription was demonstrated by recording a short clip and "
              "receiving the transcript inline.")
    add_figure(doc, SCREENSHOTS / "15.png", "Figure 9.10: Markdown-rich reply rendered inside a bot bubble.")
    add_figure(doc, SCREENSHOTS / "13.png", "Figure 9.11: AI image generation example.")
    add_figure(doc, SCREENSHOTS / "12.png", "Figure 9.12: On-demand PDF report shown as a download card.")
    add_figure(doc, SCREENSHOTS / "11.png", "Figure 9.13: OCR analysis of an attached image.")
    add_figure(doc, SCREENSHOTS / "8.png", "Figure 9.14: Document Q&A — uploading and binding a PDF (notebook / RAG).", width_inches=4.6)
    add_figure(doc, SCREENSHOTS / "10.png", "Figure 9.15: Composing a reusable multi-step workflow chain.", width_inches=4.6)

    # ── 10. TESTING AND EVALUATION ───────────────────────────────────
    page_break(doc)
    h1(doc, "10.  Testing and Evaluation")

    h2(doc, "10.1.  Testing Strategy")
    para(doc, "Testing combines integration testing of the running system with scenario-based "
              "acceptance checks. The primary instrument is test_all.py, a Python suite of 66 "
              "cases that runs against the live deployment (main app on port 3000 and admin "
              "service on port 7040), exercising real HTTP requests, the database, and the n8n "
              "round-trip rather than mocks. In addition, each backlog item was checked against "
              "its acceptance criteria at the corresponding sprint review, and informal usability "
              "sessions surfaced interface refinements.")

    h2(doc, "10.2.  Test Scenarios")
    para(doc, "Representative scenarios covered by the suite include: service health of both "
              "applications; static assets served with the correct no-cache headers; "
              "authentication flows (correct and wrong credentials, missing token, role check); "
              "the full admin CRUD surface (statistics, list, create, update, suspend/activate, "
              "reset-password, delete); main-app profile and avatar operations and password "
              "change; the chat round-trip through n8n and Mistral; session tags, history, "
              "session detail and deletion; all three export formats (PDF, Markdown, JSON); the "
              "document, RAG bind/unbind, and workflow-CRUD endpoints; and input validation "
              "(malformed requests returning clean 4xx responses rather than 5xx).")

    h2(doc, "10.3.  Test Results")
    para(doc, "All 66 cases pass against the live deployment. Table 10.1 summarises the results by "
              "category. The few issues discovered during development were addressed before this "
              "report — most notably stale static assets on iOS Safari (fixed with no-store cache "
              "headers) and the model occasionally acknowledging a PDF report without flagging the "
              "action (handled by re-parsing the reply and forcing generation). The main "
              "limitation of the evaluation is scale: testing was functional and small-scale "
              "rather than a load test, which is left to future work.")
    add_table(doc,
              ["Category", "Result"],
              [["Service health (main + admin)", "passed"],
               ["Static assets & no-cache headers", "passed"],
               ["Authentication & role checks", "passed"],
               ["Admin CRUD (stats, users, lifecycle)", "passed"],
               ["Main-app profile / avatar / password", "passed"],
               ["Chat round-trip (n8n → Mistral)", "passed"],
               ["Sessions, tags, history, deletion", "passed"],
               ["Exports (PDF / Markdown / JSON)", "passed"],
               ["Documents, RAG bind/unbind, workflows", "passed"],
               ["Input validation (clean 4xx)", "passed"],
               ["Total", "66 / 66 passed"]],
              col_widths=[8.5, 6.4],
              caption="Table 10.1: Integration test suite — results by category.")

    # ── 11. RESULTS AND DISCUSSION ───────────────────────────────────
    page_break(doc)
    h1(doc, "11.  Results and Discussion")
    para(doc, "The project produced a working, deployed Minimum Viable Product that meets its "
              "objectives: a single web application that brings conversational AI together with "
              "image generation and editing, OCR and captioning, audio transcription, "
              "retrieval-augmented question answering, notebook context, PDF report generation, "
              "and reusable workflow chains, plus a separate administrative dashboard — all built "
              "from free-tier APIs and self-hostable components, packaged with Docker, deployed on "
              "a live server, and covered by a 66-case integration test suite that passes in "
              "full. The Scrum-style process worked well for this kind of project: scheduling the "
              "foundations and the conversational core first meant every later sprint built on a "
              "stable base, and the advisor's reviews fed directly into the backlog. Routing all "
              "AI traffic through a visible n8n workflow proved valuable in practice — prompts, "
              "tool limits, and the audio branch were tuned several times without redeploying "
              "application code. The main limitations are the breadth-over-depth trade-off (the "
              "system integrates accessible models rather than competing with frontier ones), "
              "reliance on the availability and rate limits of free external services, and the "
              "small scale of the evaluation.")

    # ── 12. CONCLUSION AND FUTURE WORK ───────────────────────────────
    page_break(doc)
    h1(doc, "12.  Conclusion and Future Work")
    h2(doc, "12.1.  Conclusion")
    para(doc, "AstroBot demonstrates a complete software-engineering pipeline — requirements "
              "elicitation, modelling, architecture and design, implementation, testing, and "
              "deployment — applied to a practical problem: the fragmentation of everyday AI "
              "tooling. The resulting MVP is live, reproducible, and useful, and it establishes a "
              "clean baseline architecture (a public app, a separate admin service, and an n8n "
              "orchestration layer over a shared database) on which further capabilities can be "
              "added incrementally.")
    h2(doc, "12.2.  Future Work")
    para(doc, "Planned future work includes a mobile-first progressive web app with offline "
              "support and push notifications; a two-way voice mode (continuous transcription in, "
              "speech out); broader OCR language coverage and per-language persona tuning; moving "
              "all audio paths to a fully self-hosted Whisper service; a marketplace where users "
              "share and rate workflow chains; optional per-user quotas and billing for a "
              "multi-tenant deployment; and a larger-scale performance and reliability evaluation.")

    # ── REFERENCES ───────────────────────────────────────────────────
    page_break(doc)
    front_heading(doc, "REFERENCES")
    refs = [
        "P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, 2020.",
        "V. Karpukhin et al., “Dense Passage Retrieval for Open-Domain Question Answering,” Proc. EMNLP, 2020.",
        "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” Proc. EMNLP-IJCNLP, 2019.",
        "S. Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” Proc. ICLR, 2023.",
        "K. Schwaber and J. Sutherland, “The Scrum Guide,” 2020. [Online]. Available: https://scrumguides.org",
        "Mistral AI, “Mistral models documentation.” [Online]. Available: https://docs.mistral.ai",
        "HuggingFace, “Inference API documentation.” [Online]. Available: https://huggingface.co/docs/api-inference",
        "n8n GmbH, “n8n documentation.” [Online]. Available: https://docs.n8n.io",
        "PostgreSQL Global Development Group, “PostgreSQL 16 documentation.” [Online]. Available: https://www.postgresql.org/docs/",
        "Docker Inc., “Docker documentation.” [Online]. Available: https://docs.docker.com",
        "OpenJS Foundation, “Express 4.x API reference.” [Online]. Available: https://expressjs.com",
        f"AstroBot source repository. [Online]. Available: {GITHUB_URL}",
    ]
    for i, r in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.9)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(f"[{i}]  {r}")
        _set_run(run, size=11)


# ─── CURRICULUM VITAE pages ────────────────────────────────────────────
def _build_cv(doc):
    page_break(doc)
    front_heading(doc, "CURRICULUM VITAE")

    def _render_filled_cv(cv, *, qualif=None, is_first=False):
        if not is_first:
            page_break(doc)
        h2(doc, cv["full_name"])

        h3(doc, "PERSONAL INFORMATION")
        for k, v in [("Full Name", cv["full_name"]), ("Nationality", cv["nationality"]),
                     ("Place and Date of Birth", cv["birth"]), ("E-mail", cv["email"])]:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(2)
            r1 = p.add_run(f"{k}:  "); _set_run(r1, size=12, bold=True)
            r2 = p.add_run(v); _set_run(r2, size=12)

        h3(doc, "EDUCATION")
        add_table(doc, ["Degree", "Institution", "Graduation Year"],
                  [[deg, inst, yr] for deg, inst, yr in cv["education"]],
                  col_widths=[3.6, 8.4, 2.9])

        h3(doc, "PROFESSIONAL EXPERIENCE")
        if cv["experience"]:
            add_table(doc, ["Institution", "Role / Activities", "Year"],
                      [[inst, role, yr] for inst, role, yr in cv["experience"]],
                      col_widths=[4.2, 8.0, 2.7])
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "AREA OF EXPERTISE")
        for field in cv["expertise"]:
            bullet(doc, field, size=12)

        h3(doc, "FOREIGN LANGUAGES")
        add_table(doc, ["Language", "Proficiency Level"],
                  [[lang, lvl] for lang, lvl in cv["languages"]],
                  col_widths=[5.0, 9.9])

        h3(doc, "CERTIFICATES")
        if cv["certificates"]:
            add_table(doc, ["Certificate", "Area / Issuing Institution", "Year"],
                      cv["certificates"], col_widths=[4.5, 7.5, 2.9])
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "OTHER RELEVANT QUALIFICATIONS")
        if qualif:
            bullet(doc, qualif, size=12)
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "PUBLICATIONS")
        para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "PRESENTATIONS")
        para(doc, "—", size=12, indent=0.8, space_after=4)

    # ---- Tidiane (filled) ----
    _render_filled_cv(
        CV_TIDIANE,
        qualif="Hands-on experience deploying containerised AI services and "
               "orchestration workflows on remote servers.",
        is_first=True,
    )

    # ---- Sidi Mohamed Sall (filled) ----
    _render_filled_cv(CV_SIDI)

    # ---- Ahmed Essalem (filled) ----
    _render_filled_cv(CV_AHMED)

    # ---- Saad Ibrahim Houssein (filled) ----
    _render_filled_cv(CV_SAAD)


# ─── 13. Appendices ────────────────────────────────────────────────────
def _read_excerpt(path: Path, start_marker=None, n_lines=40):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"// (source file not available: {path.name})"
    lines = text.split("\n")
    if start_marker:
        for i, ln in enumerate(lines):
            if start_marker in ln:
                lines = lines[i:]
                break
    return "\n".join(lines[:n_lines]).rstrip()


def _build_appendices(doc):
    page_break(doc)
    h1(doc, "13.  Appendices")

    h2(doc, "13.1.  Appendix A: Source Code")
    para(doc, "Representative excerpts of the source code follow; the complete codebase is "
              f"available at {GITHUB_URL}.")

    h3(doc, "A.1  JWT authentication middleware (backend/middleware/auth.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "middleware" / "auth.js", n_lines=42))

    h3(doc, "A.2  Database pool and idempotent migrations (backend/db/index.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "db" / "index.js", n_lines=60))

    h3(doc, "A.3  Express entry point and security middleware (backend/server.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "server.js", n_lines=55))

    h2(doc, "13.2.  Appendix B: Sprint Backlog")
    para(doc, "Figure 13.1 shows the project timeline; the sprint goals and the increments "
              "delivered in each are listed in Table 4.2 in Section 4. Each sprint maintained a "
              "backlog of user stories with priority and acceptance criteria; items not finished "
              "in a sprint were re-ranked for the next one, and the advisor's review feedback was "
              "added to the backlog as new items.")
    add_figure(doc, DIAGRAMS / "sprints.png", "Figure 13.1: Sprint timeline of the project.", width_inches=6.4)
    add_table(doc,
              ["Sprint", "Selected user stories (abridged)", "Status"],
              [["1", "Set up repo & Docker Compose; create DB schema; implement register/login with JWT; minimal chat via n8n", "Done"],
               ["2", "Mistral AI Agent; conversation history (15 msg); 7 personas; Markdown/KaTeX/highlight.js/Mermaid; streaming-style reveal", "Done"],
               ["3", "Image generation & img-to-img; OCR + BLIP; Whisper transcription; RAG (chunk/embed/retrieve) & notebook mode; PDF report generation; workflow chains; tags & exports", "Done"],
               ["4", "Admin dashboard (stats, users, audit); 66-case integration test suite; deploy.py; security headers & rate limits; documentation", "Done"]],
              col_widths=[1.6, 10.6, 2.7])

    h2(doc, "13.3.  Appendix C: User Guide")
    para(doc, "Quick-start instructions for the deployed application:")
    bullet(doc, f"Public application — open {DEPLOY_URL}, register an account (or log in), and "
                "start a conversation from the central chat bar. Use the persona selector to change "
                "the assistant's tone, the attachment button to add images (analysed by OCR/BLIP) "
                "or a PDF (then choose notebook or RAG mode), and the microphone button to dictate "
                "a message. Ask for an image (\"generate an image of …\") or a report (\"make a PDF "
                "report of …\") and the result appears inline. Tag, search, and export sessions "
                "from the sidebar.")
    bullet(doc, f"Administrator — open {ADMIN_URL} and log in with an admin account. The dashboard "
                "shows KPIs and activity charts; the Users page lets you search, suspend, "
                "reactivate, reset the password of, delete, or create accounts; opening a user "
                "shows their conversation history grouped by session.")
    bullet(doc, "Deployment — from the repository, copy docker/.env.example to docker/.env and "
                "fill in the secrets, then run docker compose up -d --build in the docker/ folder; "
                "or run python deploy.py to deploy to the configured server. Run python test_all.py "
                "to execute the integration suite against the deployment.")
    bullet(doc, "Troubleshooting — if the public application is unreachable, check that the shared "
                "PostgreSQL container is running (docker ps); the AstroBot services restart "
                "automatically on a host reboot but the database must also be up for them to "
                "start serving.")


if __name__ == "__main__":
    build()
