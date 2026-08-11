#!/usr/bin/env python3
"""
AstroBot — Générateur du Rapport de Projet de Fin d'Études (version française).

Construit le rapport de projet de fin d'études (.docx) en suivant le modèle
"Capstone Project Report" de l'OSTIM Technical University demandé par
l'encadrant (couverture → APPROBATION → REMERCIEMENTS → RÉSUMÉ (TR/FR) →
TABLE DES MATIÈRES / LISTE DES TABLEAUX / FIGURES / SYMBOLES → sections
numérotées 1. Introduction … 12. Conclusion → RÉFÉRENCES → CURRICULUM
VITAE → 13. Annexes).

Les diagrammes UML (contexte, cas d'utilisation, architecture, classes/ER,
séquence, états) sont dessinés avec Pillow dans `report/assets/diagrams/`
au premier lancement.

Exécution :
    python report/build_report_fr.py

Sortie :
    report/AstroBot_Rapport_Graduation_FR.docx
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
OUTPUT = REPORT_DIR / "AstroBot_Rapport_Graduation_FR.docx"

# ── Métadonnées du projet ──────────────────────────────────────────
PROJECT_TITLE = ("ASTROBOT — UN ASSISTANT CONVERSATIONNEL INTELLIGENT À "
                 "CAPACITÉS MULTIMODALES, GÉNÉRATION AUGMENTÉE PAR LA "
                 "RECHERCHE (RAG) ET INTÉGRATION DE WORKFLOWS WEB")
SHORT_TITLE = "AstroBot"
GITHUB_URL = "https://github.com/tkonate788/astrobot"
DEPLOY_URL = "http://76.13.62.195:3000"
ADMIN_URL = "http://76.13.62.195:7040"
UNIVERSITY = "OSTIM TECHNICAL UNIVERSITY"
FACULTY = "FACULTÉ D'INGÉNIERIE"
DEPARTMENT = "Département de Génie Informatique"
COURSE = "MFBP 402 — Projet de Fin d'Études II"
DATE_LINE = "Mai 2026"
ADVISOR = "Assist. Prof. Dr. Yücel TEKİN"
ADVISOR_PLAIN = "Yücel TEKİN"

STUDENTS = [
    ("220201838", "TIDIANE KONATE"),
    ("210208992", "SIDI MOHAMED SALL"),
    ("220201992", "AHMED ESSALEM"),
    ("210201983", "SAAD IBRAHIM HOUSSEIN"),
]

# Détails du CV de Tidiane (fournis). Autres membres → pages CV remplies.
CV_TIDIANE = {
    "full_name": "Tidiane KONATÉ",
    "nationality": "Malienne (Mali)",
    "birth": "—",
    "email": "Tkonate788@gmail.com  ·  220201838@ostimteknik.edu.tr",
    "education": [
        ("Lycée", "Lycée Privé d'Excellence (LPE), Mali — Baccalauréat scientifique", "2021"),
        ("Formation linguistique en turc", "Yozgat Bozok University (YOBU), Turquie", "2022"),
        ("Licence", "OSTIM Technical University, Ankara — Génie informatique", "2026 (prévue)"),
    ],
    "experience": [
        ("INEDIIA — Lille, France (Télétravail)", "Stagiaire IA Générative appliquée / LLMOps — "
         "conception et déploiement de workflows d'automatisation alimentés par l'IA avec n8n, "
         "intégration d'APIs de LLM dans les processus métier, déploiement de services "
         "conteneurisés avec Docker, pipelines GenAI de bout en bout.", "2025 – présent"),
    ],
    "expertise": [
        "IA générative appliquée et APIs de LLM",
        "Automatisation et orchestration de workflows IA (n8n)",
        "DevOps / LLMOps — Docker, webhooks, intégration d'API",
        "Développement logiciel — C, C++, Python, C#",
        "Systèmes d'exploitation et réseaux",
    ],
    "languages": [
        ("Français", "Maternelle"),
        ("Anglais", "Avancé (B2)"),
        ("Turc", "Intermédiaire (B1)"),
        ("Bambara", "Courant"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_SIDI = {
    "full_name": "Sidi Mohamed SALL",
    "nationality": "Malienne (Mali)",
    "birth": "Bamako, Mali",
    "email": "Sidimohamedsall5@gmail.com  ·  210208992@ostimteknik.edu.tr",
    "education": [
        ("Lycée", "Lycée Complexe Scolaire Kanouté Aïssé, Bamako, Mali", "2020"),
        ("Compétence en langue anglaise", "OSTIM Technical University, Ankara", "2021"),
        ("Licence", "OSTIM Technical University, Ankara — Génie logiciel",
         "2026 (prévue)"),
    ],
    "experience": [],
    "expertise": [
        "Vision produit, expérience utilisateur et conception d'interface",
        "Développement front-end en HTML, CSS et JavaScript",
        "Génie logiciel — analyse, conception et documentation",
        "Collaboration en équipe et travail agile",
    ],
    "languages": [
        ("Français", "Maternelle"),
        ("Anglais", "Avancé (B2)"),
        ("Turc", "Intermédiaire (B1)"),
        ("Bambara", "Courant"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_AHMED = {
    "full_name": "Ahmed ESSALEM",
    "nationality": "Mauritanienne (Mauritanie)",
    "birth": "Mauritanie",
    "email": "220201992@ostimteknik.edu.tr",
    "education": [
        ("Licence", "OSTIM Technical University, Ankara — Génie informatique",
         "2026 (prévue)"),
    ],
    "experience": [
        ("OSTIM Technical University", "C# : programmation orientée objet (POO) "
         "avancée, développement d'applications multi-modules, scripts, automatisation, "
         "intégration d'APIs et développement back-end.", "2026"),
        ("Datacamp", "Python : programmation orientée objet (POO) avancée, "
         "développement d'applications multi-modules, scripts, automatisation, "
         "intégration d'APIs et développement back-end.", "2024"),
        ("Smart SA Company", "Gestion de bases de données — bases SQL, modélisation "
         "de données, opérations CRUD et intégration en applications.", "2025"),
        ("Smart SA Company", "Technologies web — développement front-end et back-end, "
         "applications web responsives et systèmes basés sur des APIs.", "2024"),
    ],
    "expertise": [
        "Génie informatique : architecture des systèmes, cycle de vie du développement "
        "logiciel (SDLC), résolution de problèmes, débogage et optimisation d'applications.",
        "Programmation Python : POO avancée, applications multi-modules, scripts, "
        "automatisation, intégration d'APIs et développement back-end.",
        "Programmation C# : POO avancée, applications multi-modules et développement "
        "back-end.",
        "Génie logiciel : conception d'applications, bonnes pratiques de code propre, "
        "gestion de versions avec Git/GitHub, tests et documentation.",
        "Gestion de bases de données : bases SQL, modélisation et intégration.",
        "Technologies web : applications web responsives et systèmes basés sur des APIs.",
        "Collaboration en équipe et résolution de problèmes : travail d'équipe agile, "
        "communication technique et raisonnement analytique.",
    ],
    "languages": [
        ("Arabe", "Courant"),
        ("Français", "Courant"),
        ("Turc", "Avancé (C1)"),
        ("Anglais", "Avancé (C1)"),
    ],
    "certificates": [],
    "publications": [],
    "presentations": [],
}


CV_SAAD = {
    "full_name": "Saad Ibrahim HOUSSEIN",
    "nationality": "Djiboutienne (Djibouti)",
    "birth": "Djibouti",
    "email": "saadgodin2@gmail.com  ·  210201983@ostimteknik.edu.tr",
    "education": [
        ("Licence", "OSTIM Technical University, Ankara — Génie logiciel",
         "2026 (prévue)"),
    ],
    "experience": [
        ("Datacomp", "Développement Flutter — applications mobiles et web "
         "multi-plateformes avec Dart, UI/UX responsive, gestion d'état, intégration "
         "Firebase et connexion à des APIs REST.", "2024"),
        ("Datacomp", "Gestion de bases de données — bases SQL, modélisation de "
         "données, opérations CRUD et intégration en applications.", "2025"),
        ("Datacomp", "Technologies web — développement front-end et back-end, "
         "applications web responsives et systèmes basés sur des APIs.", "2024"),
    ],
    "expertise": [
        "Génie informatique : architecture des systèmes, cycle de vie du développement "
        "logiciel (SDLC), résolution de problèmes, débogage et optimisation d'applications.",
        "Programmation Python : POO avancée, applications multi-modules, scripts, "
        "automatisation, intégration d'APIs et développement back-end.",
        "Développement Flutter : applications mobiles et web multi-plateformes avec "
        "Dart, UI/UX responsive, gestion d'état, Firebase et APIs REST.",
        "Génie logiciel : conception d'applications, bonnes pratiques de code propre, "
        "gestion de versions avec Git/GitHub, tests et documentation.",
        "Gestion de bases de données : bases SQL, modélisation et intégration.",
        "Technologies web : applications web responsives et systèmes basés sur des APIs.",
        "Collaboration en équipe et résolution de problèmes : travail d'équipe agile, "
        "communication technique et raisonnement analytique.",
    ],
    "languages": [
        ("Somali", "Courant"),
        ("Arabe", "Courant"),
        ("Français", "Courant"),
        ("Turc", "Avancé (C1)"),
        ("Anglais", "Pré-avancé (B2)"),
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
        r = p.add_run(f"[figure manquante : {os.path.basename(image_path)}]")
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
# starting at 1). Page numbers kept as-is from the English version — they
# will be re-verified when the PDF is re-rendered.
TOC_ENTRIES = [
    ("TABLE DES MATIÈRES", "iv", False, 0.0),
    ("LISTE DES TABLEAUX", "vi", False, 0.0),
    ("LISTE DES FIGURES", "vii", False, 0.0),
    ("LISTE DES SYMBOLES ET ABRÉVIATIONS", "viii", False, 0.0),
    ("1.  Introduction", "1", True, 0.0),
    ("1.1.  Énoncé du problème", "1", False, 0.8),
    ("1.2.  Objectifs du projet", "1", False, 0.8),
    ("1.3.  Portée du projet", "2", False, 0.8),
    ("1.4.  Organisation du rapport", "2", False, 0.8),
    ("2.  Concepts généraux", "3", True, 0.0),
    ("2.1.  Définition du domaine", "3", False, 0.8),
    ("2.2.  Technologies utilisées", "3", False, 0.8),
    ("2.3.  Concepts fondamentaux", "4", False, 0.8),
    ("3.  Travaux connexes", "5", True, 0.0),
    ("3.1.  Systèmes existants", "5", False, 0.8),
    ("3.2.  Études académiques", "5", False, 0.8),
    ("3.3.  Analyse comparative", "5", False, 0.8),
    ("4.  Modèle de processus logiciel", "7", True, 0.0),
    ("4.1.  Modèle de développement choisi", "7", False, 0.8),
    ("4.2.  Définition des rôles Scrum", "7", False, 0.8),
    ("4.3.  Processus Scrum", "8", False, 0.8),
    ("4.4.  Mise en œuvre de Scrum dans le projet", "8", False, 0.8),
    ("5.  Analyse des besoins", "10", True, 0.0),
    ("5.1.  Parties prenantes", "10", False, 0.8),
    ("5.2.  Besoins utilisateurs", "10", False, 0.8),
    ("5.2.1.  Besoins fonctionnels", "10", False, 1.4),
    ("5.2.2.  Besoins non fonctionnels", "11", False, 1.4),
    ("5.3.  Spécifications du système", "11", False, 0.8),
    ("6.  Modélisation du système", "13", True, 0.0),
    ("6.1.  Diagramme de contexte", "13", False, 0.8),
    ("6.2.  Diagramme de cas d'utilisation", "13", False, 0.8),
    ("6.3.  Descriptions des cas d'utilisation", "14", False, 0.8),
    ("6.4.  Diagrammes de séquence", "15", False, 0.8),
    ("7.  Architecture et conception du système", "17", True, 0.0),
    ("7.1.  Architecture du système", "17", False, 0.8),
    ("7.2.  Modèles structurels", "18", False, 0.8),
    ("7.2.1.  Diagramme de classes / entité-association", "19", False, 1.4),
    ("7.2.2.  Héritage (généralisation)", "19", False, 1.4),
    ("7.2.3.  Agrégation / composition", "20", False, 1.4),
    ("7.3.  Modèles comportementaux", "20", False, 0.8),
    ("7.3.1.  Modèle événementiel", "20", False, 1.4),
    ("7.3.2.  Diagramme d'états", "20", False, 1.4),
    ("8.  Implémentation du système", "22", True, 0.0),
    ("8.1.  Environnement de développement", "22", False, 0.8),
    ("8.2.  Composants du système", "22", False, 0.8),
    ("8.3.  Structure du code", "23", False, 0.8),
    ("9.  Développement du MVP", "25", True, 0.0),
    ("9.1.  Définition du MVP", "25", False, 0.8),
    ("9.2.  Fonctionnalités implémentées", "25", False, 0.8),
    ("9.3.  Interfaces du système", "26", False, 0.8),
    ("9.4.  Démonstration du système", "30", False, 0.8),
    ("10.  Tests et évaluation", "33", True, 0.0),
    ("10.1.  Stratégie de tests", "33", False, 0.8),
    ("10.2.  Scénarios de tests", "33", False, 0.8),
    ("10.3.  Résultats des tests", "33", False, 0.8),
    ("11.  Résultats et discussion", "35", True, 0.0),
    ("12.  Conclusion et travaux futurs", "36", True, 0.0),
    ("12.1.  Conclusion", "36", False, 0.8),
    ("12.2.  Travaux futurs", "36", False, 0.8),
    ("RÉFÉRENCES", "37", True, 0.0),
    ("CURRICULUM VITAE", "38", True, 0.0),
    ("13.  Annexes", "46", True, 0.0),
    ("13.1.  Annexe A : Code source", "46", False, 0.8),
    ("13.2.  Annexe B : Backlog des sprints", "48", False, 0.8),
    ("13.3.  Annexe C : Guide utilisateur", "49", False, 0.8),
]

# (num, caption, page)
FIGURES = [
    ("Figure 6.1", "Diagramme de contexte de la plateforme AstroBot", "13"),
    ("Figure 6.2", "Diagramme de cas d'utilisation (utilisateur final et administrateur)", "14"),
    ("Figure 6.3", "Diagramme de séquence d'un aller-retour de message de chat", "16"),
    ("Figure 7.1", "Architecture du système (couches client / application / orchestration / données)", "18"),
    ("Figure 7.2", "Modèle entité-association du schéma PostgreSQL", "19"),
    ("Figure 7.3", "Diagramme d'états d'un message de conversation", "21"),
    ("Figure 8.1", "Workflow n8n qui achemine chaque message via Mistral", "23"),
    ("Figure 9.1", "Page d'accueil publique avec la barre de chat centrale", "26"),
    ("Figure 9.2", "Section fonctionnalités de l'application publique", "27"),
    ("Figure 9.3", "Page « À propos » présentant l'équipe de quatre développeurs", "27"),
    ("Figure 9.4", "Interface de chat authentifiée (écran d'accueil)", "28"),
    ("Figure 9.5", "Sélecteur de personas — sept personas d'assistant disponibles", "28"),
    ("Figure 9.6", "Paramètres de profil avec un recadreur d'image dans le navigateur", "28"),
    ("Figure 9.7", "Tableau de bord admin — KPI et graphiques d'activité", "29"),
    ("Figure 9.8", "Tableau de gestion des utilisateurs (admin)", "29"),
    ("Figure 9.9", "Paramètres en libre-service de l'admin (profil et mot de passe)", "30"),
    ("Figure 9.10", "Réponse riche en Markdown rendue dans une bulle de l'assistant", "30"),
    ("Figure 9.11", "Exemple de génération d'image par IA", "31"),
    ("Figure 9.12", "Rapport PDF à la demande affiché comme carte de téléchargement", "31"),
    ("Figure 9.13", "Analyse OCR d'une image attachée", "31"),
    ("Figure 9.14", "Questions-réponses sur document — téléversement et liaison d'un PDF (notebook / RAG)", "32"),
    ("Figure 9.15", "Composition d'une chaîne de workflow réutilisable", "32"),
    ("Figure 13.1", "Chronologie des sprints du projet", "49"),
]

TABLES = [
    ("Tableau 4.1", "Rôles Scrum et membres de l'équipe les ayant assumés", "7"),
    ("Tableau 4.2", "Plan des sprints et incréments livrés", "8"),
    ("Tableau 5.1", "Besoins fonctionnels", "10"),
    ("Tableau 5.2", "Besoins non fonctionnels", "11"),
    ("Tableau 5.3", "Endpoints REST sélectionnés et leurs responsabilités", "11"),
    ("Tableau 7.1", "Principales tables de la base de données et leur rôle", "18"),
    ("Tableau 8.1", "Services tiers utilisés par AstroBot", "22"),
    ("Tableau 10.1", "Suite de tests d'intégration — résultats par catégorie", "33"),
]

SYMBOLS = [
    ("IA", "Intelligence Artificielle"),
    ("API", "Application Programming Interface (interface de programmation)"),
    ("BLIP", "Bootstrapping Language-Image Pre-training (modèle de légendage d'images)"),
    ("CRUD", "Create, Read, Update, Delete (créer, lire, mettre à jour, supprimer)"),
    ("CSS", "Cascading Style Sheets (feuilles de style en cascade)"),
    ("BD", "Base de Données"),
    ("ETA", "Estimated Time of Arrival (utilisé de manière générique)"),
    ("BF", "Besoin Fonctionnel"),
    ("HTML", "HyperText Markup Language"),
    ("HTTP", "HyperText Transfer Protocol"),
    ("JSON", "JavaScript Object Notation"),
    ("JWT", "JSON Web Token (jeton web JSON)"),
    ("KaTeX", "Bibliothèque web de composition mathématique LaTeX"),
    ("LLM", "Large Language Model (grand modèle de langage)"),
    ("MVP", "Minimum Viable Product (produit minimum viable)"),
    ("BNF", "Besoin Non Fonctionnel"),
    ("OCR", "Optical Character Recognition (reconnaissance optique de caractères)"),
    ("ORM", "Object-Relational Mapping (mapping objet-relationnel)"),
    ("RAG", "Retrieval-Augmented Generation (génération augmentée par la recherche)"),
    ("REST", "Representational State Transfer"),
    ("SQL", "Structured Query Language"),
    ("STT", "Speech-to-Text (parole vers texte)"),
    ("TTS", "Text-to-Speech (texte vers parole)"),
    ("UI / UX", "User Interface / User Experience (interface / expérience utilisateur)"),
    ("UML", "Unified Modeling Language"),
    ("VM", "Virtual Machine (machine virtuelle)"),
    ("VPS", "Virtual Private Server (serveur privé virtuel)"),
]


# ════════════════════════════════════════════════════════════════════════
# DOCUMENT
# ════════════════════════════════════════════════════════════════════════

def build():
    print("[1/3] Génération des diagrammes ...")
    generate_all_diagrams()

    print("[2/3] Construction du document ...")
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = TNR
    style.font.size = Pt(12)

    # ─────────────────────────────────────────────────────────────────
    # SECTION A — couverture + APPROBATION  (sans numéros de page)
    # ─────────────────────────────────────────────────────────────────
    sec_a = doc.sections[0]
    _apply_a4(sec_a)
    _no_footer(sec_a)

    # COUVERTURE (limitée à une seule page)
    para(doc, "", space_after=10, line_spacing=1.0)
    para(doc, UNIVERSITY, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, FACULTY, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, "RAPPORT DE PROJET DE FIN D'ÉTUDES", size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=22, line_spacing=1.1)
    if (ASSETS / "ostim_logo_official.png").exists():
        pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.add_run().add_picture(str(ASSETS / "ostim_logo_official.png"), width=Inches(1.9))
        pp.paragraph_format.space_after = Pt(22)
    para(doc, PROJECT_TITLE, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         line_spacing=1.25, space_after=26)
    para(doc, "Équipe du projet", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3, line_spacing=1.0)
    for sid, sname in STUDENTS:
        para(doc, f"{sname}    ({sid})", size=12, align=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=1, line_spacing=1.1)
    para(doc, "", space_after=12, line_spacing=1.0)
    para(doc, "Encadrant du projet", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.0)
    para(doc, ADVISOR, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, line_spacing=1.1)
    para(doc, "Projet de licence", size=12, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.0)
    para(doc, DEPARTMENT, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, line_spacing=1.1)
    para(doc, COURSE, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, line_spacing=1.1)
    para(doc, DATE_LINE, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0, line_spacing=1.0)

    # APPROBATION
    page_break(doc)
    front_heading(doc, "APPROBATION")
    para(doc, f"Ce projet de fin d'études de licence, intitulé « {SHORT_TITLE} — Un assistant "
              f"conversationnel intelligent à capacités multimodales, génération augmentée par la "
              f"recherche (RAG) et intégration de workflows web », préparé par "
              f"{', '.join(s[1].title() for s in STUDENTS[:-1])} et {STUDENTS[-1][1].title()} "
              f"sous la supervision de {ADVISOR}, a été examiné par le jury et "
              f"accepté comme projet de fin d'études de licence en termes de portée et de qualité.",
         space_after=36)
    for role, name in [("Encadrant", ADVISOR),
                       ("Membre du jury", "Nom Prénom du membre du jury"),
                       ("Membre du jury", "Nom Prénom du membre du jury"),
                       ("Chef de département", "Nom Prénom du chef de département")]:
        para(doc, name, size=12, bold=True, space_after=2, line_spacing=1.2)
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(22)
        r1 = p.add_run(f"{role}   "); _set_run(r1, size=12)
        r2 = p.add_run(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ."); _set_run(r2, size=12)

    # ─────────────────────────────────────────────────────────────────
    # SECTION B — pages liminaires (chiffres romains, commence à i)
    # ─────────────────────────────────────────────────────────────────
    sec_b = doc.add_section(WD_SECTION.NEW_PAGE)
    _apply_a4(sec_b)
    _set_pgnum_format(sec_b, "lowerRoman", start=1)
    _footer_pageno(sec_b)

    # REMERCIEMENTS
    front_heading(doc, "REMERCIEMENTS")
    para(doc, f"Les auteurs remercient chaleureusement leur encadrant de projet, "
              f"{ADVISOR}, dont les retours lors des revues ont façonné aussi bien la portée que la "
              f"qualité de ce travail. Nous remercions le Département de Génie Informatique de "
              f"l'OSTIM Technical University pour les ressources mises à disposition tout au long du "
              f"projet, ainsi que nos camarades qui ont participé à des séances informelles de tests "
              f"d'utilisabilité et nous ont aidés à affiner l'interface et le comportement de "
              f"l'assistant. Enfin, nous remercions les mainteneurs des outils open source et des "
              f"services à offre gratuite sur lesquels AstroBot est construit.")

    # ÖZET (version en langue locale — turc, conservée)
    page_break(doc)
    front_heading(doc, "ÖZET (RÉSUMÉ EN TURC)")
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

    # RÉSUMÉ (français)
    page_break(doc)
    front_heading(doc, "RÉSUMÉ")
    para(doc, "Ce rapport présente la conception et l'implémentation d'AstroBot, un assistant "
              "conversationnel intelligent fondé sur l'intelligence artificielle et doté de "
              "capacités multimodales. Le projet répond à la fragmentation des outils d'IA "
              "actuels : le chat, la génération d'images, la recherche dans des documents, l'OCR "
              "et la transcription audio résident généralement dans des applications distinctes, "
              "et les utilisateurs doivent jongler avec plusieurs abonnements payants pour "
              "accéder aux modèles de pointe. Le système proposé se compose d'une interface "
              "publique de chat, d'un tableau de bord d'administration et d'un orchestrateur de "
              "workflows basé sur n8n qui achemine chaque message utilisateur via un grand "
              "modèle de langage Mistral. Le produit minimum viable (MVP) couvre les "
              "fonctionnalités principales : chat textuel avec mémoire conversationnelle et "
              "personas, génération d'images et retouche image-à-image, OCR et légendage "
              "visuel, transcription audio, questions-réponses augmentées par la recherche (RAG) "
              "sur des documents PDF téléversés, génération de rapports PDF à la demande, ainsi "
              "que des chaînes de workflows réutilisables, le tout aux côtés d'un service "
              "d'administration distinct pour les statistiques et la gestion des utilisateurs. "
              "Le développement a suivi un processus itératif de type Scrum sur quatre sprints, "
              "les besoins ayant été recueillis auprès des utilisateurs finaux et des "
              "administrateurs. La solution est conteneurisée avec Docker, déployée sur un "
              "serveur virtuel en production, et validée par une suite de 66 cas de tests "
              "d'intégration. L'évaluation montre que le système satisfait ses critères "
              "d'acceptation et atteint l'objectif de réunir plusieurs modalités d'IA derrière "
              "une seule application web gratuite.",
         space_after=10)
    para(doc, "Mots-clés : IA conversationnelle, grand modèle de langage, génération augmentée "
              "par la recherche, multimodalité, orchestration de workflows, MVP", size=12, italic=True)

    # TABLE DES MATIÈRES
    page_break(doc)
    front_heading(doc, "TABLE DES MATIÈRES")
    pg = doc.add_paragraph()
    pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True)
    pg.paragraph_format.space_after = Pt(4)
    for label, page, bold, indent in TOC_ENTRIES:
        _leader_line(doc, label, page, bold=bold, indent=indent)

    # LISTE DES TABLEAUX
    page_break(doc)
    front_heading(doc, "LISTE DES TABLEAUX")
    pg = doc.add_paragraph(); pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True); pg.paragraph_format.space_after = Pt(4)
    for num, label, page in TABLES:
        _leader_line(doc, f"{num} :  {label}", page)

    # LISTE DES FIGURES
    page_break(doc)
    front_heading(doc, "LISTE DES FIGURES")
    pg = doc.add_paragraph(); pg.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pg.add_run("Page"); _set_run(r, size=11, bold=True); pg.paragraph_format.space_after = Pt(4)
    for num, label, page in FIGURES:
        _leader_line(doc, f"{num} :  {label}", page)

    # LISTE DES SYMBOLES ET ABRÉVIATIONS
    page_break(doc)
    front_heading(doc, "LISTE DES SYMBOLES ET ABRÉVIATIONS")
    for abbr, full in SYMBOLS:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        r1 = p.add_run(f"{abbr}  :  "); _set_run(r1, size=11, bold=True)
        r2 = p.add_run(full); _set_run(r2, size=11)

    # ─────────────────────────────────────────────────────────────────
    # SECTION C — corps + CV + annexes  (arabe, commence à 1)
    # ─────────────────────────────────────────────────────────────────
    sec_c = doc.add_section(WD_SECTION.NEW_PAGE)
    _apply_a4(sec_c)
    _set_pgnum_format(sec_c, "decimal", start=1)
    _footer_pageno(sec_c)

    _build_body(doc)
    _build_cv(doc)
    _build_appendices(doc)

    print("[3/3] Enregistrement ...")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    sz = OUTPUT.stat().st_size / 1024
    print(f"\n[OK] Rapport généré : {OUTPUT}")
    print(f"  Taille : {sz:.1f} Ko")


# ─── 1. Introduction … 12. Conclusion + RÉFÉRENCES ─────────────────────
def _build_body(doc):
    # ── 1. INTRODUCTION ───────────────────────────────────────────────
    h1(doc, "1.  Introduction")

    h2(doc, "1.1.  Énoncé du problème")
    para(doc, "Les assistants d'intelligence artificielle modernes sont puissants mais "
              "fragmentés. Un utilisateur qui souhaite discuter avec un modèle, générer une "
              "image, transcrire un enregistrement audio, lancer une reconnaissance optique de "
              "caractères sur une capture d'écran et poser des questions sur un fichier PDF doit "
              "généralement utiliser quatre ou cinq applications différentes, chacune avec son "
              "propre compte, sa propre interface et — de plus en plus — son propre abonnement "
              "payant. Les modèles de pointe se trouvent derrière des barrières payantes qui "
              "désavantagent les étudiants et les petites équipes, tandis que l'auto-hébergement "
              "de modèles open source reste complexe car chaque modèle a sa propre histoire "
              "d'intégration. Les conversations sont également traitées comme jetables : la "
              "plupart des outils n'offrent que de simples listes de messages, sans dossiers, "
              "sans étiquettes, sans moyen d'épingler un document comme contexte durable, et "
              "sans trace exportable de ce qui a été dit. Les pipelines réutilisables de prompts "
              "à plusieurs étapes sont soit reconstruits à chaque fois, soit cachés dans des "
              "agents fermés. Il n'existe pas de lieu unique et abordable qui réunit l'IA "
              "conversationnelle, l'entrée multimodale, la compréhension de documents et les "
              "workflows réutilisables.")

    h2(doc, "1.2.  Objectifs du projet")
    para(doc, "L'objectif de ce projet est de concevoir, implémenter et déployer un produit "
              "minimum viable (MVP) qui unifie ces capacités derrière une seule application web "
              "gratuite. Les objectifs spécifiques sont :")
    bullet(doc, "Offrir une surface de chat conversationnel adossée à un grand modèle de "
                "langage, avec une mémoire par session, plusieurs personas et un rendu enrichi "
                "du Markdown, des mathématiques, du code et des diagrammes.")
    bullet(doc, "Prendre en charge l'entrée et la sortie multimodales — génération d'images et "
                "retouche image-à-image, OCR et légendage visuel, et transcription audio.")
    bullet(doc, "Offrir la compréhension de documents via la génération augmentée par la "
                "recherche (RAG) sur des PDF téléversés, ainsi qu'un mode notebook qui épingle "
                "un document comme contexte durable.")
    bullet(doc, "Rendre les conversations persistantes et exportables, avec des dossiers/étiquettes, "
                "une recherche et la génération de rapports PDF.")
    bullet(doc, "Fournir un tableau de bord d'administration pour les statistiques, la gestion "
                "des utilisateurs et l'audit des conversations, isolé de l'application publique.")
    bullet(doc, "Maintenir le système gratuit à exploiter en combinant des APIs à offre gratuite "
                "(Mistral, HuggingFace, Groq) et un moteur de workflows auto-hébergeable, et le "
                "livrer comme un déploiement Docker reproductible.")

    h2(doc, "1.3.  Portée du projet")
    para(doc, "Le projet couvre le pipeline complet de génie logiciel pour le MVP : analyse des "
              "besoins, modélisation du système, architecture et conception, implémentation, "
              "tests et déploiement sur un serveur en production. Sont inclus l'application "
              "publique de chat, le tableau de bord d'administration, le workflow d'orchestration "
              "n8n et les douze-et-plus fonctionnalités basées sur l'IA décrites dans ce "
              "rapport. Sont hors portée — et reportés aux travaux futurs — les applications "
              "mobiles natives, un modèle interne ajusté finement, la facturation et l'application "
              "de quotas, et les tests de charge à grande échelle. Le système vise un "
              "environnement de déploiement unique plutôt qu'une offre SaaS multi-tenants.")

    h2(doc, "1.4.  Organisation du rapport")
    para(doc, "La section 2 introduit le domaine et les technologies habilitantes. La section 3 "
              "passe en revue les systèmes existants et les travaux académiques et positionne "
              "AstroBot parmi eux. La section 4 décrit le modèle de processus logiciel. La "
              "section 5 présente l'analyse des besoins, et la section 6 les modèles du système "
              "(diagrammes de contexte, de cas d'utilisation et de séquence). La section 7 "
              "détaille l'architecture ainsi que la conception structurelle et comportementale. "
              "La section 8 couvre l'implémentation ; la section 9 le MVP, ses fonctionnalités, "
              "ses interfaces et une démonstration. La section 10 présente les tests et "
              "l'évaluation, la section 11 discute les résultats, et la section 12 conclut avec "
              "les travaux futurs. Les curriculum vitae des membres de l'équipe et les annexes "
              "(extraits de code source, backlog des sprints et guide utilisateur) suivent les "
              "références.")

    # ── 2. CONCEPTS GÉNÉRAUX ──────────────────────────────────────────
    page_break(doc)
    h1(doc, "2.  Concepts généraux")

    h2(doc, "2.1.  Définition du domaine")
    para(doc, "AstroBot appartient au domaine des applications d'IA conversationnelle : des "
              "systèmes logiciels qui exposent un grand modèle de langage via une interface de "
              "chat et orchestrent des outils complémentaires — modèles d'images, modèles de "
              "parole, recherche et récupération — pour répondre aux demandes des utilisateurs. "
              "Ce domaine combine la conception d'interactions en langage naturel, le génie des "
              "applications web et les préoccupations opérationnelles liées à l'appel fiable et "
              "économique d'APIs de modèles externes. À l'intérieur de ce domaine, le projet se "
              "situe à l'intersection d'un outil de productivité pour utilisateur final et d'une "
              "petite plateforme opérationnelle disposant de son propre volet d'administration.")

    h2(doc, "2.2.  Technologies utilisées")
    para(doc, "La pile technique est délibérément construite à partir de briques bien soutenues "
              "et majoritairement gratuites :")
    bullet(doc, "Front-end — HTML, CSS et JavaScript natifs (sans framework), avec KaTeX pour "
                "les mathématiques, highlight.js pour le code, Mermaid pour les diagrammes, "
                "Cropper.js pour le recadrage d'avatar, et Chart.js dans le tableau de bord "
                "d'administration.")
    bullet(doc, "Back-end — Node.js 18 avec Express 4, JSON Web Tokens pour l'authentification, "
                "bcrypt pour le hachage des mots de passe, Helmet pour les en-têtes de sécurité "
                "HTTP, et express-rate-limit. Le traitement des documents et des PDF utilise "
                "pdf-parse et PDFKit ; l'OCR utilise Tesseract.js.")
    bullet(doc, "IA et modèles — Mistral medium-latest comme modèle de chat (atteint via l'AI "
                "Agent de n8n), HuggingFace Inference pour FLUX.1-schnell (génération d'images), "
                "BLIP (légendage d'images) et MiniLM-L6-v2 (embeddings de phrases), Groq "
                "Whisper-large-v3 pour la transcription, et SerpAPI pour la recherche web en "
                "direct au sein de l'agent.")
    bullet(doc, "Orchestration et infrastructure — n8n comme moteur visuel de workflows, "
                "PostgreSQL (avec l'image pgvector, utilisée comme simple base relationnelle) "
                "pour la persistance, et Docker avec Docker Compose pour l'empaquetage et le "
                "déploiement. Un script Python (deploy.py) effectue le déploiement par SSH/SFTP "
                "sur le serveur.")

    h2(doc, "2.3.  Concepts fondamentaux")
    para(doc, "Plusieurs concepts reviennent tout au long du rapport. Un grand modèle de langage "
              "(LLM) est un réseau de neurones entraîné à prédire du texte ; étant donné une "
              "conversation, il en produit la suite, et avec un prompt système et des outils, il "
              "peut agir comme un agent. La génération augmentée par la recherche (RAG) "
              "améliore l'ancrage en récupérant les fragments les plus pertinents d'un document "
              "— ici classés par similarité cosinus sur des embeddings MiniLM — et en les "
              "insérant dans le prompt avant que le modèle ne réponde. L'orchestration de "
              "workflows consiste à décrire un pipeline à plusieurs étapes (recevoir une "
              "requête, la router selon son type, l'enrichir, appeler le modèle, post-traiter, "
              "répondre) comme un graphe modifiable sans redéployer le code applicatif ; "
              "AstroBot utilise n8n pour cela. Les JSON Web Tokens portent une identité signée "
              "et à durée de vie limitée, de sorte que l'API sans état peut autoriser les "
              "requêtes, et une revendication is_admin verrouille le service d'administration. "
              "La conteneurisation empaquette chaque service avec ses dépendances afin que le "
              "système soit reproductible à partir d'une machine virtuelle vierge.")

    # ── 3. TRAVAUX CONNEXES ──────────────────────────────────────────
    page_break(doc)
    h1(doc, "3.  Travaux connexes")

    h2(doc, "3.1.  Systèmes existants")
    para(doc, "Les assistants généralistes tels que ChatGPT, Claude et Gemini offrent une "
              "excellente qualité conversationnelle et, dans leurs offres payantes, certaines "
              "fonctionnalités multimodales. Cependant, les capacités avancées — grandes "
              "fenêtres de contexte, génération d'images, analyse de documents — sont "
              "généralement réservées aux abonnements, et les tâches plus spécialisées (OCR, "
              "transcription, recherche vectorielle sur des documents privés, pipelines "
              "reproductibles à plusieurs étapes) sont réparties entre des produits distincts "
              "tels que des services OCR dédiés, des APIs de parole-vers-texte et des outils "
              "RAG de type notebook. Des alternatives auto-hébergeables (modèles ouverts servis "
              "localement) existent mais demandent un effort opérationnel important et offrent "
              "rarement une interface multifonctionnelle aboutie clé en main.")

    h2(doc, "3.2.  Études académiques")
    para(doc, "Les travaux sur la génération augmentée par la recherche ont montré que ancrer "
              "les sorties du modèle dans des passages récupérés réduit les hallucinations et "
              "améliore l'exactitude factuelle pour la question-réponse en domaine ouvert, et "
              "que les récupérateurs denses fondés sur des embeddings de type transformeur avec "
              "similarité cosinus surpassent généralement les références lexicales creuses dans "
              "ce cadre. Les travaux sur les agents fondés sur des LLM démontrent que donner à "
              "un modèle un petit ensemble d'outils (recherche, brouillon de raisonnement, "
              "contrat de sortie structurée) lui permet de décomposer les tâches de manière "
              "fiable tout en gardant le système environnant simple. Du côté du génie logiciel, "
              "des études sur la livraison agile rapportent que le développement itératif piloté "
              "par les retours utilisateurs convient bien aux projets dont les besoins évoluent "
              "à mesure que les utilisateurs essaient les premières versions — ce qui est "
              "précisément la situation d'un assistant riche en fonctionnalités.")

    h2(doc, "3.3.  Analyse comparative")
    para(doc, "Comparé aux alternatives ci-dessus, AstroBot met en avant trois éléments "
              "distinctifs. Premièrement, l'étendue derrière une seule surface : chat, "
              "génération et retouche d'images, OCR et légendage, transcription, RAG sur "
              "documents, mode notebook, génération de rapports PDF, chaînes de workflows et "
              "volet d'administration sont tous accessibles depuis une même application avec un "
              "seul compte. Deuxièmement, l'accessibilité financière : en combinant des APIs de "
              "modèles à offre gratuite avec une couche d'orchestration auto-hébergeable, le "
              "système est gratuit à exploiter pour l'équipe et ses utilisateurs. Troisièmement, "
              "la transparence et la reproductibilité : la logique d'orchestration est un graphe "
              "n8n visible qui peut être ajusté sans redéployer le code, le modèle de données "
              "et le déploiement sont documentés, et toute la pile démarre avec une seule "
              "commande docker compose. AstroBot ne cherche pas à battre les modèles de pointe "
              "sur la qualité brute ; il intègre bien des modèles accessibles.")

    # ── 4. MODÈLE DE PROCESSUS LOGICIEL ──────────────────────────────
    page_break(doc)
    h1(doc, "4.  Modèle de processus logiciel")

    h2(doc, "4.1.  Modèle de développement choisi")
    para(doc, "Un modèle agile itératif de type Scrum a été retenu. L'ensemble des "
              "fonctionnalités souhaitables pour un assistant IA est vaste et évolue rapidement "
              "à mesure que l'équipe et les testeurs informels utilisent les premières versions, "
              "si bien qu'un processus en cascade piloté par un plan aurait été mal adapté. Le "
              "projet a été organisé en quatre sprints courts, chacun produisant un incrément "
              "fonctionnel et testable du produit, avec les éléments les plus précieux et les "
              "plus fondateurs planifiés en premier.")

    h2(doc, "4.2.  Définition des rôles Scrum")
    para(doc, "Le projet étant mené par une équipe étudiante de quatre personnes, les rôles "
              "Scrum standards ont été projetés sur l'équipe comme le montre le Tableau 4.1. Le "
              "rôle de Product Owner (priorisation du backlog, validation des incréments selon "
              "les critères d'acceptation) a été tenu principalement par le chef de projet en "
              "concertation avec l'encadrant, qui a joué le rôle de partie prenante externe. Le "
              "rôle de Scrum Master (animation des cérémonies, levée des blocages) a tourné de "
              "manière informelle mais est resté ancré sur le chef de projet. Les quatre membres "
              "formaient l'équipe de développement, chacun étant responsable d'un ou plusieurs "
              "domaines fonctionnels.")
    add_table(doc,
              ["Rôle Scrum", "Tenu par", "Principales responsabilités"],
              [["Product Owner / partie prenante", "Tidiane Konaté (avec l'encadrant)",
                "Priorité du backlog, acceptation des incréments, décisions de portée"],
               ["Scrum Master", "Tidiane Konaté", "Cérémonies de sprint, levée des blocages, coordination"],
               ["Équipe de développement — Architecture / Back-end / Déploiement", "Tidiane Konaté",
                "Architecture système, API REST, workflow n8n, Docker, déploiement"],
               ["Équipe de développement — Vision / Produit / UX", "Sidi Mohamed Sall",
                "Cadrage produit, conception de l'interface publique, séances d'utilisabilité"],
               ["Équipe de développement — IA / LLM / Multimodal", "Ahmed Essalem",
                "Intégration de modèles, fonctionnalités image/OCR/audio, pipeline RAG"],
               ["Équipe de développement — Tests / Front-end / QA", "Saad Ibrahim Houssein",
                "Finition du front-end, tableau de bord admin, suite de tests d'intégration"]],
              col_widths=[5.0, 4.5, 6.0],
              caption="Tableau 4.1 : Rôles Scrum et membres de l'équipe les ayant assumés.")

    h2(doc, "4.3.  Processus Scrum")
    para(doc, "Chaque sprint a suivi les cérémonies habituelles, adaptées à la taille de "
              "l'équipe : une réunion de planification de sprint pour sélectionner les éléments "
              "du backlog et définir les critères d'acceptation, de courtes synchronisations "
              "quotidiennes pour faire émerger l'avancement et les blocages, une revue de sprint "
              "au cours de laquelle l'incrément était démontré, et une brève rétrospective pour "
              "ajuster la manière de travailler. Le backlog produit était maintenu comme une "
              "liste de récits utilisateurs avec une priorité et des critères d'acceptation ; "
              "les éléments non terminés dans un sprint étaient repriorisés pour le suivant. Les "
              "retours de revue de l'encadrant alimentaient directement le backlog.")

    h2(doc, "4.4.  Mise en œuvre de Scrum dans le projet")
    para(doc, "Le projet a été livré en quatre sprints sur environ douze semaines, comme "
              "résumé dans le Tableau 4.2 et la Figure 13.1 (Annexe B). Le sprint 1 a posé les "
              "fondations — dépôt, Docker Compose, schéma de base de données, authentification "
              "JWT et un chemin de chat minimal via n8n. Le sprint 2 a construit le cœur "
              "conversationnel — l'AI Agent Mistral, l'historique de conversation, les personas, "
              "le rendu enrichi du contenu et la révélation de style streaming dans l'interface "
              "de chat. Le sprint 3 a ajouté les fonctionnalités multimodales et de récupération "
              "— génération d'images et retouche image-à-image, OCR et légendage BLIP, "
              "transcription Whisper, RAG et mode notebook, et rapports PDF à la demande. Le "
              "sprint 4 a livré le tableau de bord d'administration, la suite de 66 tests "
              "d'intégration, le script de déploiement, le durcissement de sécurité et la "
              "documentation.")
    add_table(doc,
              ["Sprint", "Semaines", "Objectif", "Incrément livré"],
              [["1 — Fondations", "≈ 1–3", "Mettre en place le squelette",
                "Dépôt, Docker Compose, schéma PostgreSQL, authentification JWT, chat de base via n8n"],
               ["2 — Cœur conversationnel", "≈ 3–5", "Rendre le chat de qualité",
                "AI Agent Mistral, historique de conversation, 7 personas, Markdown/KaTeX/highlight.js/Mermaid, révélation de style streaming"],
               ["3 — Multimodal et RAG", "≈ 5–8", "Ajouter les fonctionnalités IA",
                "Génération d'images et img-à-img, OCR, légendes BLIP, transcription Whisper, RAG et mode notebook, génération de rapports PDF, chaînes de workflows, étiquettes/exports"],
               ["4 — Admin, tests et déploiement", "≈ 8–11", "Exploiter et durcir",
                "Tableau de bord admin (stats, utilisateurs, audit), suite de 66 tests d'intégration, deploy.py, durcissement de sécurité, documentation"]],
              col_widths=[3.4, 1.8, 3.6, 6.7],
              caption="Tableau 4.2 : Plan des sprints et incréments livrés.")

    # ── 5. ANALYSE DES BESOINS ───────────────────────────────────────
    page_break(doc)
    h1(doc, "5.  Analyse des besoins")

    h2(doc, "5.1.  Parties prenantes")
    para(doc, "Les parties prenantes principales sont les utilisateurs finaux de l'application "
              "publique — étudiants préparant des rapports et du code, développeurs explorant "
              "l'IA multimodale, et travailleurs du savoir ayant besoin de questions-réponses "
              "sur leurs propres documents — ainsi que l'administrateur, qui exploite le "
              "déploiement, gère les comptes et audite l'usage. Les parties prenantes "
              "secondaires incluent l'encadrant du projet, qui a joué le rôle de relecteur "
              "externe et a façonné la portée, et l'équipe de développement elle-même, qui "
              "s'est appuyée sur une construction reproductible et une boucle de déploiement "
              "rapide.")

    h2(doc, "5.2.  Besoins utilisateurs")
    para(doc, "Les besoins ont été recueillis à partir de l'usage que l'équipe faisait elle-même "
              "d'outils comparables, de courtes séances informelles de tests d'utilisabilité "
              "avec d'autres étudiants, et des revues de l'encadrant, puis traduits en éléments "
              "de backlog priorisés assortis de critères d'acceptation et validés lors des "
              "revues de sprint. Ils sont résumés ci-dessous sous forme de besoins fonctionnels "
              "et non fonctionnels.")

    h3(doc, "5.2.1.  Besoins fonctionnels")
    para(doc, "Les besoins fonctionnels sont résumés dans le Tableau 5.1.")
    add_table(doc,
              ["ID", "Besoin fonctionnel"],
              [["BF-1", "Un visiteur peut s'inscrire ; les utilisateurs authentifiés peuvent se connecter et se déconnecter."],
               ["BF-2", "Un utilisateur peut envoyer un message texte et recevoir une réponse du modèle, les quinze derniers messages de la session étant conservés comme contexte."],
               ["BF-3", "Un utilisateur peut choisir un persona qui ajuste le ton de l'assistant."],
               ["BF-4", "Un utilisateur peut demander une image à partir d'un prompt textuel et la recevoir directement dans la conversation."],
               ["BF-5", "Un utilisateur peut téléverser une image et demander à l'assistant de la retoucher (image-à-image)."],
               ["BF-6", "Un utilisateur peut joindre une image et obtenir l'extraction de son texte (OCR) et/ou sa description (légendage), le résultat servant de contexte."],
               ["BF-7", "Un utilisateur peut téléverser un PDF et poser des questions auxquelles on répond à partir de son contenu (RAG), ou l'épingler comme contexte notebook durable."],
               ["BF-8", "Un utilisateur peut enregistrer de l'audio et le faire transcrire en texte."],
               ["BF-9", "Un utilisateur peut obtenir un rapport PDF généré à partir d'une réponse rédigée."],
               ["BF-10", "Un utilisateur peut organiser ses sessions avec des étiquettes colorées, rechercher dans l'historique de conversation, et exporter une session au format PDF, Markdown ou JSON."],
               ["BF-11", "Un utilisateur peut définir et rejouer des chaînes de workflows réutilisables à plusieurs étapes."],
               ["BF-12", "Un utilisateur peut gérer son profil et son avatar (avec un recadreur dans le navigateur)."],
               ["BF-13", "Un administrateur peut se connecter à un tableau de bord distinct et consulter des statistiques en temps réel ainsi que des graphiques d'activité."],
               ["BF-14", "Un administrateur peut rechercher, suspendre, réactiver, réinitialiser le mot de passe, supprimer et créer des comptes utilisateurs."],
               ["BF-15", "Un administrateur peut parcourir l'historique de conversation de n'importe quel utilisateur regroupé par session."]],
              col_widths=[1.6, 13.3],
              caption="Tableau 5.1 : Besoins fonctionnels.", font_size=10)

    h3(doc, "5.2.2.  Besoins non fonctionnels")
    add_table(doc,
              ["ID", "Catégorie", "Besoin"],
              [["BNF-1", "Performance", "Les requêtes de chat et de CRUD principales doivent être traitées dans un budget de latence interactif sous charge normale ; les appels longs de modèle sont bornés par la limite d'itérations de l'agent n8n."],
               ["BNF-2", "Sécurité", "Les mots de passe doivent être stockés hachés avec bcrypt (12 tours de sel) ; les sessions doivent utiliser des JWT signés expirant après 7 jours ; le service d'administration doit rejeter tout jeton sans revendication is_admin."],
               ["BNF-3", "Sécurité", "Les réponses HTTP doivent porter les en-têtes de sécurité Helmet ; un rate limiting doit s'appliquer (auth 20/15 min, chat 30/min, admin 500/15 min) ; les téléversements sont plafonnés à 10 Mo et 5 pièces jointes par message."],
               ["BNF-4", "Fiabilité", "L'application doit s'auto-réparer au redémarrage via des migrations de base idempotentes et une réinitialisation de l'administrateur ; les conteneurs doivent utiliser des politiques de redémarrage pour qu'un redémarrage de l'hôte rétablisse le système."],
               ["BNF-5", "Maintenabilité", "La logique d'orchestration doit résider dans un workflow n8n visible, modifiable sans redéployer le code ; le code doit être modulaire par domaine fonctionnel."],
               ["BNF-6", "Portabilité", "L'ensemble du système doit démarrer avec une seule commande docker compose et doit être déployable sur un serveur virtuel vierge à l'aide d'un script."],
               ["BNF-7", "Coût", "Le système ne doit reposer que sur des APIs externes à offre gratuite et des composants auto-hébergeables."]],
              col_widths=[1.6, 2.6, 11.3],
              caption="Tableau 5.2 : Besoins non fonctionnels.")

    h2(doc, "5.3.  Spécifications du système")
    para(doc, "Le back-end expose une API REST : les endpoints d'authentification et de profil "
              "sous /api/auth, les endpoints de chat et d'historique sous /api/chat, et les "
              "endpoints de documents, RAG, transcription, retouche d'image, YouTube et "
              "workflows sous /api/features ; le service d'administration expose un ensemble "
              "/api parallèle. Quelques endpoints sélectionnés sont listés dans le Tableau 5.3. "
              "Chaque message de chat est transmis au webhook n8n, qui renvoie un objet JSON "
              "contenant le texte de la réponse et une action optionnelle (generate_image ou "
              "generate_pdf). Les entités de données persistantes sont users, conversations "
              "(avec des champs optionnels image, PDF et pièce jointe), documents, "
              "document_chunks (avec embeddings stockés en texte), notebook_bindings et "
              "workflows ; elles sont détaillées dans la section 7.")
    add_table(doc,
              ["Méthode et chemin", "Service", "Responsabilité"],
              [["POST /api/auth/register · /login", "Principal", "Création de compte et connexion ; émet un JWT de 7 jours."],
               ["PUT /api/auth/profile · /password · /avatar", "Principal", "Mise à jour des champs du profil, changement du mot de passe, mise/retrait de l'avatar."],
               ["POST /api/chat/message", "Principal", "Chat principal : OCR/BLIP sur les images, enrichissement par l'historique et le persona, aller-retour n8n, génération d'image/PDF, persistance."],
               ["GET /api/chat/history · /sessions · /session/:id", "Principal", "Historique de conversation, sessions distinctes, et messages d'une session unique."],
               ["PUT /api/chat/sessions/:id/tag · GET /tags", "Principal", "Système de dossiers/étiquettes sur les sessions."],
               ["GET /api/chat/export/:id?format=pdf|md|json", "Principal", "Exporter une session dans le format choisi."],
               ["POST /api/features/documents · PUT /notebook", "Principal", "Téléverser un PDF (découpage + embeddings), le lier à une session en mode notebook ou RAG."],
               ["POST /api/features/transcribe · /image-edit · /youtube-transcript", "Principal", "Transcription audio (Whisper), retouche image-à-image, résumé YouTube."],
               ["GET/POST/PUT/DELETE /api/features/workflows", "Principal", "CRUD pour les chaînes de workflows définies par l'utilisateur."],
               ["GET /api/stats", "Admin", "Métriques du tableau de bord : totaux d'utilisateurs/messages/sessions/tokens/images/PDF/docs, activité quotidienne, utilisateurs les plus actifs."],
               ["GET/POST/PUT/DELETE /api/users[/:id]", "Admin", "Lister, créer, modifier (statut/rôle), réinitialiser le mot de passe, supprimer des utilisateurs ; conversations par utilisateur."]],
              col_widths=[6.0, 1.6, 7.3],
              caption="Tableau 5.3 : Endpoints REST sélectionnés et leurs responsabilités.", font_size=10)

    # ── 6. MODÉLISATION DU SYSTÈME ───────────────────────────────────
    page_break(doc)
    h1(doc, "6.  Modélisation du système")

    h2(doc, "6.1.  Diagramme de contexte")
    para(doc, "La Figure 6.1 montre le modèle de contexte. La plateforme AstroBot (l'application "
              "web publique, le service d'administration et l'orchestrateur n8n) est le système "
              "étudié. Deux acteurs humains interagissent avec elle : l'utilisateur final, qui "
              "envoie des messages de chat, téléverse des fichiers et consomme les réponses et "
              "médias générés, et l'administrateur, qui gère les comptes et consulte les "
              "statistiques. La plateforme s'intègre à plusieurs systèmes externes : Mistral "
              "Cloud pour l'inférence LLM, le routeur HuggingFace Inference pour la génération "
              "d'images, le légendage et les embeddings, Groq Whisper pour la transcription, "
              "SerpAPI pour la recherche web en direct, et une base PostgreSQL partagée pour la "
              "persistance.")
    add_figure(doc, DIAGRAMS / "context.png", "Figure 6.1 : Diagramme de contexte de la plateforme AstroBot.", width_inches=6.2)

    h2(doc, "6.2.  Diagramme de cas d'utilisation")
    para(doc, "La Figure 6.2 résume les cas d'utilisation. L'utilisateur final peut s'inscrire "
              "et se connecter, envoyer des messages de chat, générer et retoucher des images, "
              "analyser des images via OCR et légendage, poser des questions sur un PDF via "
              "RAG, transcrire de l'audio, générer des rapports PDF, lancer des chaînes de "
              "workflows sauvegardées, exporter des conversations et gérer son profil et son "
              "avatar. L'administrateur peut en outre consulter le tableau de bord de "
              "statistiques, gérer les comptes utilisateurs (recherche, suspension, "
              "réinitialisation, suppression, création) et auditer l'historique des "
              "conversations.")
    add_figure(doc, DIAGRAMS / "usecase.png", "Figure 6.2 : Diagramme de cas d'utilisation (utilisateur final et administrateur).", width_inches=6.2)

    h2(doc, "6.3.  Descriptions des cas d'utilisation")
    para(doc, "Deux cas d'utilisation représentatifs sont décrits ci-dessous.")
    para(doc, "Envoyer un message de chat — Acteur : utilisateur final authentifié. Préconditions : "
              "l'utilisateur dispose d'un JWT valide et se trouve sur la page de chat. Flux "
              "principal : l'utilisateur saisit un message, joint éventuellement des images et "
              "l'envoie ; le back-end exécute l'OCR et le légendage sur les images, charge les "
              "quinze derniers messages de la session, ajoute la directive du persona actif et "
              "tout contexte notebook/RAG, puis transmet la requête enrichie au webhook n8n ; "
              "l'AI Agent n8n appelle Mistral (avec recherche SerpAPI et un brouillon de "
              "raisonnement optionnels) et renvoie une réponse JSON ; le back-end déclenche la "
              "génération d'image ou de PDF si la réponse le demande, persiste la ligne de "
              "conversation et renvoie la réponse et les éventuels médias. Postconditions : "
              "l'historique de la conversation contient le nouvel échange. Flux alternatifs : "
              "si la sortie du modèle ne peut pas être interprétée selon le contrat attendu, "
              "le back-end traite la sortie entière comme texte de réponse ; les erreurs de "
              "rate limit et de validation renvoient des réponses 4xx claires.")
    para(doc, "Poser des questions sur un PDF (RAG) — Acteur : utilisateur final authentifié. "
              "Préconditions : l'utilisateur a téléversé un PDF et l'a lié à la session en mode "
              "RAG. Flux principal : à chaque question, le back-end calcule l'embedding de la "
              "question avec MiniLM, récupère les quatre fragments les plus similaires du "
              "document par similarité cosinus, les insère dans le prompt et continue comme dans "
              "le cas d'utilisation de chat. Postconditions : la réponse est ancrée dans les "
              "fragments récupérés. Flux alternatif : en mode notebook, les six mille premiers "
              "caractères du document servent de contexte à la place des fragments récupérés.")

    h2(doc, "6.4.  Diagrammes de séquence")
    para(doc, "La Figure 6.3 retrace l'aller-retour d'un message de chat. Le navigateur poste le "
              "message (avec d'éventuelles pièces jointes et le JWT) à l'application "
              "principale, qui charge l'historique de la session depuis PostgreSQL, poste un "
              "prompt enrichi au webhook n8n, où l'AI Agent appelle Mistral (et, le cas échéant, "
              "HuggingFace pour les images ou embeddings) ; n8n renvoie une réponse JSON "
              "structurée, l'application principale génère une image ou un PDF si demandé, "
              "insère la ligne de conversation et renvoie la réponse, les médias et les "
              "métadonnées au navigateur.")
    add_figure(doc, DIAGRAMS / "sequence.png", "Figure 6.3 : Diagramme de séquence d'un aller-retour de message de chat.", width_inches=6.4)

    # ── 7. ARCHITECTURE ET CONCEPTION DU SYSTÈME ─────────────────────
    page_break(doc)
    h1(doc, "7.  Architecture et conception du système")

    h2(doc, "7.1.  Architecture du système")
    para(doc, "AstroBot suit une architecture client-serveur en couches, montrée dans la Figure "
              "7.1, déployée sous forme de trois services Docker sur un même réseau privé. La "
              "couche client est le navigateur, qui sert l'interface publique de chat et celle "
              "du tableau de bord d'administration à partir de fichiers statiques. La couche "
              "application contient deux services Express indépendants : l'application "
              "principale sur le port 3000 (chat public, authentifié par JWT, avec Helmet et "
              "rate limiting) et le service d'administration sur le port 7040 (verrouillé par "
              "une revendication is_admin, complètement séparé du processus public). La couche "
              "d'orchestration est une instance n8n sur le port 5678 qui héberge le workflow de "
              "l'AI Agent et atteint Mistral, SerpAPI, un brouillon Think et un transcripteur "
              "Whisper auto-hébergé. La couche de données et de services externes se compose "
              "d'un conteneur PostgreSQL partagé (utilisé comme simple base relationnelle), du "
              "routeur HuggingFace Inference (FLUX, BLIP, MiniLM, avec un repli fal-ai) et des "
              "services externes Mistral, Groq et SerpAPI. Cette forme a été choisie pour que "
              "le conteneur PostgreSQL existant puisse être réutilisé sans exploiter une "
              "seconde base, que tout le trafic IA sorte par n8n afin de pouvoir ajuster les "
              "prompts et les outils sans redéploiement, et qu'une éventuelle exploitation "
              "publique ne puisse jamais atteindre le processus d'administration.")
    add_figure(doc, DIAGRAMS / "architecture.png", "Figure 7.1 : Architecture du système (couches client / application / orchestration / données).", width_inches=6.4)

    h2(doc, "7.2.  Modèles structurels")
    para(doc, "La conception statique est centrée sur le modèle de données persistant plutôt que "
              "sur une hiérarchie de classes profonde : le back-end est organisé par modules "
              "fonctionnels (auth, chat, features) avec des responsabilités de contrôleur, de "
              "service et d'accès aux données, et l'état durable réside dans un petit ensemble "
              "de tables relationnelles décrites ci-dessous et dans la Figure 7.2.")
    add_table(doc,
              ["Table", "Rôle"],
              [["users", "Comptes : nom, e-mail, mot de passe haché, is_admin, statut, avatar, last_login."],
               ["conversations", "Une ligne par message/réponse, avec session_id, session_tag, et les champs optionnels image_url, pdf_url, pdf_filename et un blob JSON attachment."],
               ["documents", "Fichiers téléversés pour notebook/RAG : nom, type MIME, taille, texte extrait text_content."],
               ["document_chunks", "Fragments par document pour le RAG : chunk_index, chunk_text et un embedding stocké en texte."],
               ["notebook_bindings", "Quel document est actif pour quelle session, et le mode (notebook | rag)."],
               ["workflows", "Chaînes de prompts à plusieurs étapes définies par l'utilisateur, stockées comme tableau JSON steps."]],
              col_widths=[3.6, 11.3],
              caption="Tableau 7.1 : Principales tables de la base de données et leur rôle.")
    add_figure(doc, DIAGRAMS / "er.png", "Figure 7.2 : Modèle entité-association du schéma PostgreSQL.", width_inches=6.4)

    h3(doc, "7.2.1.  Diagramme de classes / entité-association")
    para(doc, "Comme le back-end est en JavaScript avec un accès SQL direct plutôt qu'un modèle "
              "de domaine orienté objet, la conception structurelle s'exprime au mieux par le "
              "diagramme entité-association de la Figure 7.2. Un utilisateur possède plusieurs "
              "conversations, plusieurs documents, plusieurs liaisons notebook et plusieurs "
              "workflows (un-à-plusieurs dans chaque cas) ; un document possède plusieurs "
              "fragments (un-à-plusieurs) ; et une liaison notebook relie la session d'un "
              "utilisateur à un document. Les clés étrangères cascadent à la suppression, de "
              "sorte que supprimer un utilisateur ou un document supprime ses lignes "
              "dépendantes.")

    h3(doc, "7.2.2.  Héritage (généralisation)")
    para(doc, "Le système utilise très peu d'héritage par conception. Conceptuellement, le type "
              "utilisateur est spécialisé en utilisateur ordinaire et administrateur, mais "
              "cette spécialisation est représentée par un booléen is_admin sur la table users "
              "unique plutôt que par une sous-classe, ce qui maintient le schéma et la logique "
              "d'autorisation simples — le service d'administration exige simplement que "
              "is_admin soit vrai dans le JWT.")

    h3(doc, "7.2.3.  Agrégation / composition")
    para(doc, "L'agrégation et la composition apparaissent à deux endroits. Une session de "
              "conversation agrège ses lignes individuelles de messages (elles partagent un "
              "session_id mais chaque ligne reste indépendamment signifiante), et un document "
              "compose ses fragments : ceux-ci n'ont pas de sens hors de leur document parent "
              "et sont supprimés avec lui (composition, imposée par une clé étrangère ON DELETE "
              "CASCADE). Les liaisons notebook sont des objets d'association qui relient une "
              "session et un document avec un attribut de mode.")

    h2(doc, "7.3.  Modèles comportementaux")
    para(doc, "La conception dynamique est événementielle à la frontière d'orchestration et "
              "fondée sur des états pour un message individuel.")

    h3(doc, "7.3.1.  Modèle événementiel")
    para(doc, "Chaque message de chat est un événement posté au webhook n8n. À l'intérieur du "
              "workflow, un nœud Switch route l'événement par type (audio ou texte) ; la "
              "branche audio poste le fichier à un transcripteur Whisper et rejoint la branche "
              "texte ; un nœud de code enrichit la charge utile avec le nom de l'utilisateur et "
              "l'historique de conversation ; le nœud AI Agent la consomme et peut lui-même "
              "émettre des événements d'appel d'outil vers SerpAPI (plafonné à deux recherches) "
              "et vers un brouillon Think avant de produire sa réponse JSON, qu'un nœud final "
              "extrait et renvoie. Côté client, la réponse de l'assistant est révélée mot par "
              "mot, une animation pilotée par un timer plutôt que par un streaming côté "
              "serveur.")

    h3(doc, "7.3.2.  Diagramme d'états")
    para(doc, "La Figure 7.3 modélise le cycle de vie d'un message de conversation unique. "
              "Depuis l'état Idle, l'envoi d'un message fait passer la session en Processing ; "
              "si le modèle a besoin d'un outil ou d'une génération de média, la session entre "
              "dans Awaiting tool / media et revient à Processing dès l'arrivée du résultat ; "
              "lorsque la réponse est prête, la session passe à Replied ; l'envoi du message "
              "suivant la ramène à Processing, et la fermeture de la session est la transition "
              "terminale.")
    add_figure(doc, DIAGRAMS / "state.png", "Figure 7.3 : Diagramme d'états d'un message de conversation.", width_inches=6.2)

    # ── 8. IMPLÉMENTATION DU SYSTÈME ─────────────────────────────────
    page_break(doc)
    h1(doc, "8.  Implémentation du système")

    h2(doc, "8.1.  Environnement de développement")
    para(doc, "Le développement a utilisé Git pour la gestion de versions avec un miroir public "
              f"sur GitHub ({GITHUB_URL}), Visual Studio Code comme éditeur, Node.js 18 pour le "
              "back-end, et Docker Desktop / Docker Compose pour exécuter les services en local "
              "exactement comme en production. Le workflow n8n a été développé dans l'éditeur "
              "n8n et exporté en JSON conservé dans le dépôt. Le déploiement vers le serveur est "
              "effectué par un script Python (deploy.py) qui empaquette le projet, le téléverse "
              "par SFTP et exécute docker compose up -d --build à distance ; une suite Python de "
              "66 cas d'intégration (test_all.py) est exécutée contre le déploiement en "
              "production.")

    h2(doc, "8.2.  Composants du système")
    para(doc, "Le MVP comprend quatre composants. L'application principale (front-end + "
              "back-end) sert l'interface publique de chat et l'API REST sur le port 3000. Le "
              "service d'administration sert l'interface du tableau de bord et une API "
              "parallèle sur le port 7040. L'instance n8n sur le port 5678 héberge le workflow "
              "d'orchestration. Le conteneur PostgreSQL partagé assure la persistance. En "
              "complément, le système dépend de plusieurs services tiers, résumés dans le "
              "Tableau 8.1. La Figure 8.1 montre le workflow n8n par lequel chaque message "
              "transite.")
    add_table(doc,
              ["Service", "Usage", "Comment il est appelé"],
              [["Mistral Cloud (mistral-medium-latest)", "LLM conversationnel et raisonnement de l'agent", "À l'intérieur du nœud AI Agent de n8n"],
               ["Routeur HuggingFace Inference", "Génération d'images (FLUX.1-schnell), légendage d'images (BLIP), embeddings de phrases (MiniLM-L6-v2)", "En HTTPS depuis le back-end / n8n"],
               ["fal-ai", "Génération d'images de repli et retouche image-à-image", "En HTTPS depuis le back-end"],
               ["Groq (Whisper-large-v3-turbo)", "Transcription audio", "En HTTPS depuis le back-end / la branche audio de n8n"],
               ["SerpAPI", "Recherche web en direct disponible pour l'agent (plafonnée à deux appels par message)", "À l'intérieur de l'AI Agent n8n comme outil"],
               ["PostgreSQL (conteneur partagé)", "Stockage persistant pour toutes les entités", "En TCP sur le réseau Docker privé"]],
              col_widths=[4.6, 7.0, 3.3],
              caption="Tableau 8.1 : Services tiers utilisés par AstroBot.", font_size=10)
    add_figure(doc, SCREENSHOTS / "19n.png", "Figure 8.1 : Workflow n8n qui achemine chaque message via Mistral, avec recherche web et outils de raisonnement optionnels.", width_inches=6.4)

    h2(doc, "8.3.  Structure du code")
    para(doc, "Le dépôt est organisé par composant et, au sein du back-end, par domaine "
              "fonctionnel :")
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
    para(doc, "Au sein du back-end, chaque module de routes sépare la gestion des requêtes des "
              "opérations effectuées, et le module de base de données détient l'ensemble du SQL "
              "et des migrations de schéma, afin que le schéma puisse évoluer en toute sécurité "
              "à chaque redéploiement. Des extraits de code représentatifs sont donnés en "
              "Annexe A.")

    # ── 9. DÉVELOPPEMENT DU MVP ──────────────────────────────────────
    page_break(doc)
    h1(doc, "9.  Développement du MVP")

    h2(doc, "9.1.  Définition du MVP")
    para(doc, "Le MVP est défini comme le plus petit système déployable apportant une valeur "
              "réelle aux utilisateurs finaux et à un administrateur : un assistant de chat "
              "fonctionnel avec mémoire de conversation, les fonctionnalités multimodales et de "
              "récupération listées ci-dessous, des conversations persistantes et exportables, "
              "et un tableau de bord d'administration séparé — l'ensemble fonctionnant sur un "
              "serveur réel et couvert par une suite de tests automatisés. Tout ce qui dépasse "
              "ce périmètre (applications mobiles natives, facturation, modèle ajusté finement) "
              "est explicitement repoussé aux travaux futurs.")

    h2(doc, "9.2.  Fonctionnalités implémentées")
    para(doc, "Le MVP implémente les capacités suivantes :")
    bullet(doc, "Chat conversationnel — Mistral medium-latest via l'AI Agent n8n, avec une "
                "fenêtre de contexte de quinze messages par session et sept personas "
                "sélectionnables.")
    bullet(doc, "Rendu de contenu enrichi — Markdown, mathématiques KaTeX, coloration "
                "syntaxique du code par highlight.js et diagrammes Mermaid dans la bulle de "
                "l'assistant, avec une révélation mot par mot.")
    bullet(doc, "Génération d'images — FLUX.1-schnell via le routeur HuggingFace avec un repli "
                "fal-ai, plus la retouche image-à-image (transfert de style) via FLUX dev.")
    bullet(doc, "OCR et compréhension visuelle — OCR Tesseract.js (anglais et français) et "
                "légendage BLIP, les deux signaux étant ajoutés au prompt avant que le modèle "
                "ne réponde.")
    bullet(doc, "Questions-réponses sur document — génération augmentée par la recherche sur "
                "des PDF téléversés (découpage, embeddings MiniLM, récupération top-4 par "
                "cosinus) et un mode notebook qui épingle le document comme contexte durable.")
    bullet(doc, "Transcription audio — enregistrement dans le navigateur transcrit par Groq "
                "Whisper-large-v3.")
    bullet(doc, "Génération de rapports PDF — réponses rédigées transformées en PDF "
                "téléchargeable (PDFKit), avec une heuristique qui force la génération lorsque "
                "le modèle reconnaît un rapport.")
    bullet(doc, "Outils de productivité — étiquettes de session colorées et recherche, "
                "exportation de conversations (PDF / Markdown / JSON), résumeur YouTube, "
                "chaînes de workflows réutilisables, et éditeur de profil/avatar avec un "
                "recadreur dans le navigateur.")
    bullet(doc, "Administration — un tableau de bord séparé avec des KPI et graphiques en "
                "temps réel, la gestion des utilisateurs (recherche, suspension, "
                "réactivation, réinitialisation du mot de passe, suppression, création) et "
                "l'audit des conversations par utilisateur, regroupées par session.")

    h2(doc, "9.3.  Interfaces du système")
    para(doc, "L'application publique s'ouvre sur une page d'accueil (Figure 9.1) avec une "
              "barre de chat centrale et une mascotte sympathique, une section fonctionnalités "
              "(Figure 9.2) et une page « À propos » présentant l'équipe (Figure 9.3). Après "
              "connexion, l'utilisateur atteint l'interface de chat (Figure 9.4) avec la barre "
              "latérale de sessions et les commandes de pièces jointes ; un sélecteur de "
              "personas (Figure 9.5) ajuste le ton de l'assistant, et un panneau de profil "
              "avec un recadreur d'image dans le navigateur (Figure 9.6) gère le compte. "
              "L'administrateur utilise un tableau de bord séparé avec des tuiles KPI et des "
              "graphiques d'activité (Figure 9.7), un tableau de gestion des utilisateurs "
              "(Figure 9.8) et un panneau de paramètres en libre-service (Figure 9.9).")
    add_figure(doc, SCREENSHOTS / "1.png", "Figure 9.1 : Page d'accueil publique avec la barre de chat centrale.")
    add_figure(doc, SCREENSHOTS / "2.png", "Figure 9.2 : Section fonctionnalités de l'application publique.")
    add_figure(doc, SCREENSHOTS / "3.png", "Figure 9.3 : Page « À propos » présentant l'équipe de quatre développeurs.")
    add_figure(doc, SCREENSHOTS / "6.png", "Figure 9.4 : Interface de chat authentifiée (écran d'accueil).")
    add_figure(doc, SCREENSHOTS / "7.png", "Figure 9.5 : Sélecteur de personas — sept personas d'assistant disponibles.", width_inches=4.5)
    add_figure(doc, SCREENSHOTS / "14.png", "Figure 9.6 : Paramètres de profil avec un recadreur d'image dans le navigateur.", width_inches=3.6)
    add_figure(doc, SCREENSHOTS / "16a.png", "Figure 9.7 : Tableau de bord admin — KPI et graphiques d'activité.")
    add_figure(doc, SCREENSHOTS / "17a.png", "Figure 9.8 : Tableau de gestion des utilisateurs (admin).")
    add_figure(doc, SCREENSHOTS / "18a.png", "Figure 9.9 : Paramètres en libre-service de l'admin (profil et mot de passe).")

    h2(doc, "9.4.  Démonstration du système")
    para(doc, "Les fonctionnalités ont été démontrées contre le déploiement en production avec "
              "des scénarios représentatifs : une réponse riche en Markdown rendue dans la "
              "bulle de chat (Figure 9.10) ; la génération d'une image à partir d'un prompt "
              "(Figure 9.11) ; la transformation d'une réponse rédigée en rapport PDF "
              "téléchargeable (Figure 9.12) ; l'attachement d'une capture d'écran pour que "
              "l'assistant en lise le texte par OCR et l'explique (Figure 9.13) ; le "
              "téléversement d'un PDF et sa liaison comme contexte notebook/RAG (Figure 9.14) ; "
              "et la composition d'une chaîne de workflow réutilisable (Figure 9.15). La "
              "transcription audio a été démontrée en enregistrant un court extrait et en "
              "recevant la transcription en ligne.")
    add_figure(doc, SCREENSHOTS / "15.png", "Figure 9.10 : Réponse riche en Markdown rendue dans une bulle de l'assistant.")
    add_figure(doc, SCREENSHOTS / "13.png", "Figure 9.11 : Exemple de génération d'image par IA.")
    add_figure(doc, SCREENSHOTS / "12.png", "Figure 9.12 : Rapport PDF à la demande affiché comme carte de téléchargement.")
    add_figure(doc, SCREENSHOTS / "11.png", "Figure 9.13 : Analyse OCR d'une image attachée.")
    add_figure(doc, SCREENSHOTS / "8.png", "Figure 9.14 : Questions-réponses sur document — téléversement et liaison d'un PDF (notebook / RAG).", width_inches=4.6)
    add_figure(doc, SCREENSHOTS / "10.png", "Figure 9.15 : Composition d'une chaîne de workflow réutilisable.", width_inches=4.6)

    # ── 10. TESTS ET ÉVALUATION ──────────────────────────────────────
    page_break(doc)
    h1(doc, "10.  Tests et évaluation")

    h2(doc, "10.1.  Stratégie de tests")
    para(doc, "La stratégie de tests combine des tests d'intégration du système en cours "
              "d'exécution avec des contrôles d'acceptation basés sur des scénarios. "
              "L'instrument principal est test_all.py, une suite Python de 66 cas qui s'exécute "
              "contre le déploiement en production (application principale sur le port 3000 et "
              "service d'administration sur le port 7040), sollicitant de vraies requêtes "
              "HTTP, la base de données et l'aller-retour n8n plutôt que des mocks. En outre, "
              "chaque élément de backlog a été vérifié contre ses critères d'acceptation à la "
              "revue de sprint correspondante, et des séances informelles de tests "
              "d'utilisabilité ont fait émerger des améliorations de l'interface.")

    h2(doc, "10.2.  Scénarios de tests")
    para(doc, "Les scénarios représentatifs couverts par la suite incluent : la santé des deux "
              "services ; les fichiers statiques servis avec les bons en-têtes no-cache ; les "
              "flux d'authentification (identifiants corrects et incorrects, jeton manquant, "
              "vérification de rôle) ; l'ensemble de la surface CRUD d'administration "
              "(statistiques, liste, création, mise à jour, suspension/activation, "
              "réinitialisation du mot de passe, suppression) ; les opérations de profil et "
              "d'avatar de l'application principale et le changement de mot de passe ; "
              "l'aller-retour de chat via n8n et Mistral ; les étiquettes de session, "
              "l'historique, le détail de session et la suppression ; les trois formats "
              "d'export (PDF, Markdown, JSON) ; les endpoints document, bind/unbind RAG et "
              "CRUD workflows ; et la validation des entrées (requêtes mal formées renvoyant "
              "des réponses 4xx propres plutôt que 5xx).")

    h2(doc, "10.3.  Résultats des tests")
    para(doc, "Les 66 cas passent contre le déploiement en production. Le Tableau 10.1 résume "
              "les résultats par catégorie. Les quelques problèmes découverts durant le "
              "développement ont été corrigés avant ce rapport — notamment les fichiers "
              "statiques périmés sur iOS Safari (résolu avec des en-têtes de cache no-store) et "
              "le modèle reconnaissant occasionnellement un rapport PDF sans signaler l'action "
              "(traité en réanalysant la réponse et en forçant la génération). La limite "
              "principale de l'évaluation est l'échelle : les tests étaient fonctionnels et à "
              "petite échelle plutôt qu'un test de charge, ce qui est laissé aux travaux "
              "futurs.")
    add_table(doc,
              ["Catégorie", "Résultat"],
              [["Santé des services (principal + admin)", "réussi"],
               ["Fichiers statiques et en-têtes no-cache", "réussi"],
               ["Authentification et contrôles de rôle", "réussi"],
               ["CRUD admin (stats, utilisateurs, cycle de vie)", "réussi"],
               ["Profil / avatar / mot de passe de l'app principale", "réussi"],
               ["Aller-retour de chat (n8n → Mistral)", "réussi"],
               ["Sessions, étiquettes, historique, suppression", "réussi"],
               ["Exports (PDF / Markdown / JSON)", "réussi"],
               ["Documents, bind/unbind RAG, workflows", "réussi"],
               ["Validation des entrées (4xx propre)", "réussi"],
               ["Total", "66 / 66 réussis"]],
              col_widths=[8.5, 6.4],
              caption="Tableau 10.1 : Suite de tests d'intégration — résultats par catégorie.")

    # ── 11. RÉSULTATS ET DISCUSSION ──────────────────────────────────
    page_break(doc)
    h1(doc, "11.  Résultats et discussion")
    para(doc, "Le projet a produit un produit minimum viable déployé et fonctionnel qui "
              "atteint ses objectifs : une seule application web qui réunit l'IA "
              "conversationnelle avec la génération et la retouche d'images, l'OCR et le "
              "légendage, la transcription audio, les questions-réponses augmentées par la "
              "recherche, le contexte notebook, la génération de rapports PDF et les chaînes de "
              "workflows réutilisables, plus un tableau de bord d'administration séparé — le "
              "tout construit à partir d'APIs à offre gratuite et de composants "
              "auto-hébergeables, empaqueté avec Docker, déployé sur un serveur en production "
              "et couvert par une suite de 66 tests d'intégration qui passe intégralement. Le "
              "processus de type Scrum a bien fonctionné pour ce type de projet : planifier les "
              "fondations et le cœur conversationnel en premier a fait en sorte que chaque "
              "sprint ultérieur s'appuie sur une base stable, et les retours de l'encadrant ont "
              "alimenté directement le backlog. Acheminer tout le trafic IA via un workflow n8n "
              "visible s'est révélé précieux en pratique — les prompts, les limites d'outils et "
              "la branche audio ont été ajustés à plusieurs reprises sans redéployer le code "
              "applicatif. Les limites principales sont le compromis étendue contre "
              "profondeur (le système intègre des modèles accessibles plutôt que de concurrencer "
              "des modèles de pointe), la dépendance à la disponibilité et aux limites de débit "
              "des services externes gratuits, et la petite échelle de l'évaluation.")

    # ── 12. CONCLUSION ET TRAVAUX FUTURS ─────────────────────────────
    page_break(doc)
    h1(doc, "12.  Conclusion et travaux futurs")
    h2(doc, "12.1.  Conclusion")
    para(doc, "AstroBot illustre un pipeline complet de génie logiciel — recueil des besoins, "
              "modélisation, architecture et conception, implémentation, tests et déploiement "
              "— appliqué à un problème pratique : la fragmentation des outils d'IA du "
              "quotidien. Le MVP résultant est en ligne, reproductible et utile, et il "
              "établit une architecture de base claire (une application publique, un service "
              "d'administration séparé, et une couche d'orchestration n8n sur une base de "
              "données partagée) sur laquelle d'autres capacités peuvent être ajoutées de "
              "manière incrémentale.")
    h2(doc, "12.2.  Travaux futurs")
    para(doc, "Les travaux futurs prévus comprennent une application web progressive (PWA) "
              "axée sur le mobile avec support hors-ligne et notifications push ; un mode "
              "vocal bidirectionnel (transcription continue en entrée, parole en sortie) ; une "
              "couverture OCR de plus de langues et un réglage des personas par langue ; le "
              "passage de tous les chemins audio à un service Whisper entièrement "
              "auto-hébergé ; une place de marché où les utilisateurs partagent et notent des "
              "chaînes de workflows ; des quotas et de la facturation optionnels par "
              "utilisateur pour un déploiement multi-tenants ; et une évaluation de "
              "performance et de fiabilité à plus grande échelle.")

    # ── RÉFÉRENCES ───────────────────────────────────────────────────
    page_break(doc)
    front_heading(doc, "RÉFÉRENCES")
    refs = [
        "P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, 2020.",
        "V. Karpukhin et al., “Dense Passage Retrieval for Open-Domain Question Answering,” Proc. EMNLP, 2020.",
        "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” Proc. EMNLP-IJCNLP, 2019.",
        "S. Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” Proc. ICLR, 2023.",
        "K. Schwaber and J. Sutherland, “The Scrum Guide,” 2020. [En ligne]. Disponible : https://scrumguides.org",
        "Mistral AI, “Mistral models documentation.” [En ligne]. Disponible : https://docs.mistral.ai",
        "HuggingFace, “Inference API documentation.” [En ligne]. Disponible : https://huggingface.co/docs/api-inference",
        "n8n GmbH, “n8n documentation.” [En ligne]. Disponible : https://docs.n8n.io",
        "PostgreSQL Global Development Group, “PostgreSQL 16 documentation.” [En ligne]. Disponible : https://www.postgresql.org/docs/",
        "Docker Inc., “Docker documentation.” [En ligne]. Disponible : https://docs.docker.com",
        "OpenJS Foundation, “Express 4.x API reference.” [En ligne]. Disponible : https://expressjs.com",
        f"Dépôt source d'AstroBot. [En ligne]. Disponible : {GITHUB_URL}",
    ]
    for i, r in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.9)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(f"[{i}]  {r}")
        _set_run(run, size=11)


# ─── Pages CURRICULUM VITAE ────────────────────────────────────────────
def _build_cv(doc):
    page_break(doc)
    front_heading(doc, "CURRICULUM VITAE")

    def _render_filled_cv(cv, *, qualif=None, is_first=False):
        if not is_first:
            page_break(doc)
        h2(doc, cv["full_name"])

        h3(doc, "INFORMATIONS PERSONNELLES")
        for k, v in [("Nom complet", cv["full_name"]), ("Nationalité", cv["nationality"]),
                     ("Lieu et date de naissance", cv["birth"]), ("E-mail", cv["email"])]:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(2)
            r1 = p.add_run(f"{k} :  "); _set_run(r1, size=12, bold=True)
            r2 = p.add_run(v); _set_run(r2, size=12)

        h3(doc, "FORMATION")
        add_table(doc, ["Diplôme", "Établissement", "Année d'obtention"],
                  [[deg, inst, yr] for deg, inst, yr in cv["education"]],
                  col_widths=[3.6, 8.4, 2.9])

        h3(doc, "EXPÉRIENCE PROFESSIONNELLE")
        if cv["experience"]:
            add_table(doc, ["Institution", "Rôle / activités", "Année"],
                      [[inst, role, yr] for inst, role, yr in cv["experience"]],
                      col_widths=[4.2, 8.0, 2.7])
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "DOMAINES DE COMPÉTENCE")
        for field in cv["expertise"]:
            bullet(doc, field, size=12)

        h3(doc, "LANGUES ÉTRANGÈRES")
        add_table(doc, ["Langue", "Niveau de maîtrise"],
                  [[lang, lvl] for lang, lvl in cv["languages"]],
                  col_widths=[5.0, 9.9])

        h3(doc, "CERTIFICATS")
        if cv["certificates"]:
            add_table(doc, ["Certificat", "Domaine / organisme émetteur", "Année"],
                      cv["certificates"], col_widths=[4.5, 7.5, 2.9])
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "AUTRES QUALIFICATIONS PERTINENTES")
        if qualif:
            bullet(doc, qualif, size=12)
        else:
            para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "PUBLICATIONS")
        para(doc, "—", size=12, indent=0.8, space_after=4)

        h3(doc, "PRÉSENTATIONS")
        para(doc, "—", size=12, indent=0.8, space_after=4)

    # ---- Tidiane (rempli) ----
    _render_filled_cv(
        CV_TIDIANE,
        qualif="Expérience pratique du déploiement de services d'IA conteneurisés et de "
               "workflows d'orchestration sur des serveurs distants.",
        is_first=True,
    )

    # ---- Sidi Mohamed Sall (rempli) ----
    _render_filled_cv(CV_SIDI)

    # ---- Ahmed Essalem (rempli) ----
    _render_filled_cv(CV_AHMED)

    # ---- Saad Ibrahim Houssein (rempli) ----
    _render_filled_cv(CV_SAAD)


# ─── 13. Annexes ───────────────────────────────────────────────────────
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
    h1(doc, "13.  Annexes")

    h2(doc, "13.1.  Annexe A : Code source")
    para(doc, "Des extraits représentatifs du code source suivent ; le code complet est "
              f"disponible à l'adresse {GITHUB_URL}.")

    h3(doc, "A.1  Middleware d'authentification JWT (backend/middleware/auth.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "middleware" / "auth.js", n_lines=42))

    h3(doc, "A.2  Pool de base de données et migrations idempotentes (backend/db/index.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "db" / "index.js", n_lines=60))

    h3(doc, "A.3  Point d'entrée Express et middleware de sécurité (backend/server.js)")
    add_code_block(doc, _read_excerpt(BACKEND / "server.js", n_lines=55))

    h2(doc, "13.2.  Annexe B : Backlog des sprints")
    para(doc, "La Figure 13.1 montre la chronologie du projet ; les objectifs des sprints et "
              "les incréments livrés sont listés dans le Tableau 4.2 de la section 4. Chaque "
              "sprint maintenait un backlog de récits utilisateurs avec une priorité et des "
              "critères d'acceptation ; les éléments non terminés dans un sprint étaient "
              "repriorisés pour le suivant, et les retours de revue de l'encadrant étaient "
              "ajoutés au backlog comme nouveaux éléments.")
    add_figure(doc, DIAGRAMS / "sprints.png", "Figure 13.1 : Chronologie des sprints du projet.", width_inches=6.4)
    add_table(doc,
              ["Sprint", "Récits utilisateurs sélectionnés (résumé)", "Statut"],
              [["1", "Mettre en place le dépôt et Docker Compose ; créer le schéma de la BD ; implémenter l'inscription/connexion avec JWT ; chat minimal via n8n", "Terminé"],
               ["2", "AI Agent Mistral ; historique de conversation (15 messages) ; 7 personas ; Markdown/KaTeX/highlight.js/Mermaid ; révélation de style streaming", "Terminé"],
               ["3", "Génération d'images et img-à-img ; OCR + BLIP ; transcription Whisper ; RAG (découpage/embedding/récupération) et mode notebook ; génération de rapports PDF ; chaînes de workflows ; étiquettes et exports", "Terminé"],
               ["4", "Tableau de bord admin (stats, utilisateurs, audit) ; suite de 66 tests d'intégration ; deploy.py ; en-têtes de sécurité et rate limits ; documentation", "Terminé"]],
              col_widths=[1.6, 10.6, 2.7])

    h2(doc, "13.3.  Annexe C : Guide utilisateur")
    para(doc, "Instructions de démarrage rapide pour l'application déployée :")
    bullet(doc, f"Application publique — ouvrez {DEPLOY_URL}, inscrivez-vous (ou connectez-vous) "
                "et démarrez une conversation depuis la barre de chat centrale. Utilisez le "
                "sélecteur de personas pour changer le ton de l'assistant, le bouton de pièce "
                "jointe pour ajouter des images (analysées par OCR/BLIP) ou un PDF (puis "
                "choisissez le mode notebook ou RAG), et le bouton micro pour dicter un "
                "message. Demandez une image (« génère une image de … ») ou un rapport "
                "(« fais-moi un rapport PDF de … ») et le résultat apparaît en ligne. "
                "Étiquetez, recherchez et exportez les sessions depuis la barre latérale.")
    bullet(doc, f"Administrateur — ouvrez {ADMIN_URL} et connectez-vous avec un compte "
                "administrateur. Le tableau de bord affiche les KPI et graphiques d'activité ; "
                "la page Utilisateurs permet de rechercher, suspendre, réactiver, "
                "réinitialiser le mot de passe, supprimer ou créer des comptes ; ouvrir un "
                "utilisateur affiche son historique de conversation regroupé par session.")
    bullet(doc, "Déploiement — depuis le dépôt, copiez docker/.env.example vers docker/.env "
                "et renseignez les secrets, puis exécutez docker compose up -d --build dans le "
                "dossier docker/ ; ou exécutez python deploy.py pour déployer sur le serveur "
                "configuré. Exécutez python test_all.py pour lancer la suite d'intégration "
                "contre le déploiement.")
    bullet(doc, "Dépannage — si l'application publique est injoignable, vérifiez que le "
                "conteneur PostgreSQL partagé est en cours d'exécution (docker ps) ; les "
                "services AstroBot redémarrent automatiquement au redémarrage de l'hôte, mais "
                "la base de données doit elle aussi être en marche pour qu'ils puissent "
                "commencer à servir.")


if __name__ == "__main__":
    build()
