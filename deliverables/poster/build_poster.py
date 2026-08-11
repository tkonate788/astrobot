#!/usr/bin/env python3
"""
AstroBot — Graduation Project Poster generator (70 x 100 cm).

Rebuilds the conference-style poster from scratch with a clean two-column
grid, large readable type, and the layout the team asked for:
  • card 05 "Try AstroBot in Action" is a half-width card (not full-row)
  • card 08 "Try It Live" carries a BIG QR code, sitting next to card 05
  • the advisor block sits low, near the bottom
Everything is vector-drawn at 200 DPI so it stays crisp at print size.

Run:
    python presentation/build_poster.py

Outputs (overwrites — keep the *.bak made earlier as a fallback):
    report/AstroBot_Poster.png
    report/AstroBot_Poster.pdf
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "deliverables" / "report" / "assets"
SCREENS = ROOT / "assets" / "screenshots"
ADVISOR_PHOTO = ROOT / "assets" / "advisor" / "Assist. Prof. Yücel TEKİN.jpg"
OUT_PNG = Path(__file__).resolve().parent / "AstroBot_Poster.png"
OUT_PDF = Path(__file__).resolve().parent / "AstroBot_Poster.pdf"

# ─── Canvas: 70 x 100 cm @ 200 DPI ─────────────────────────────────────
DPI = 200
CM = DPI / 2.54
W = round(70 * CM)        # 5512
H = round(100 * CM)       # 7874
PT = DPI / 72.0           # px per point

# ─── Palette ───────────────────────────────────────────────────────────
BG_TOP = (243, 247, 253)
BG_BOT = (228, 237, 250)
WHITE = (255, 255, 255)
NAVY = (15, 26, 53)
INK = (28, 36, 56)
INK_SOFT = (94, 105, 128)
CARD_BG = (255, 255, 255)
CARD_BORDER = (224, 230, 240)
LINE = (214, 221, 232)

ORANGE = (245, 158, 11)     # 01 Problem
GREEN = (22, 163, 74)       # 02 Objectives
DEEPBLUE = (30, 58, 138)    # 03 Architecture
PURPLE = (123, 44, 191)     # 04 Key Features
CYAN = (6, 182, 212)        # 05 Try AstroBot
LIGHTBLUE = (56, 189, 248)  # 08 Try It Live
TEAMBLUE = (37, 99, 235)    # 06 Team
MAROON = (139, 21, 56)      # 07 Advisor

# Per-developer accent (used for the photo ring)
TEAM_ACCENTS = [(37, 99, 235), (245, 158, 11), (22, 163, 74), (123, 44, 191)]

# ─── Fonts (Segoe UI family — close match to the original) ─────────────
FDIR = Path("C:/Windows/Fonts")


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FDIR / name), size)


def F_black(s):   return _font("segoeuib.ttf", s)   # bold
def F_semi(s):    return _font("seguisb.ttf", s)    # semibold
def F_reg(s):     return _font("segoeui.ttf", s)    # regular
def F_light(s):   return _font("segoeuisl.ttf", s)  # semilight
def F_italic(s):  return _font("segoeuii.ttf", s)   # italic
def F_mono(s):    return _font("consola.ttf", s)    # monospace


# ════════════════════════════════════════════════════════════════════════
# DRAWING HELPERS
# ════════════════════════════════════════════════════════════════════════

def vertical_gradient(size, top_rgb, bot_rgb):
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), tuple(round(top_rgb[i] + (bot_rgb[i] - top_rgb[i]) * t) for i in range(3)))
    return base.resize((w, h))


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def card(img: Image.Image, x, y, w, h, *, radius=46, fill=CARD_BG,
         border=CARD_BORDER, border_w=3, shadow=True):
    """Draw a soft-shadowed rounded card. Returns the inner content box."""
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((x + 10, y + 18, x + w + 10, y + h + 18),
                             radius=radius, fill=(20, 30, 55, 38))
        sh = sh.filter(ImageFilter.GaussianBlur(28))
        img.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(img)
    rounded_rect(d, (x, y, x + w, y + h), radius, fill=fill,
                 outline=border, width=border_w)
    return (x, y, w, h)


def circle_badge(img, cx, cy, r, text, color, *, fsize=None, fg=WHITE):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    if fsize is None:
        fsize = int(r * 1.05)
    f = F_black(fsize)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - tw / 2 - bb[0], cy - th / 2 - bb[1]), text, font=f, fill=fg)


def card_header(img, x, y, num, title, color, *, badge_r=66, title_size=86):
    """Numbered circle badge + uppercase title. Returns y below the header."""
    cy = y + badge_r
    circle_badge(img, x + badge_r, cy, badge_r, num, color, fsize=int(badge_r * 1.05))
    d = ImageDraw.Draw(img)
    f = F_black(title_size)
    tx = x + badge_r * 2 + 48
    # vertically centre the title text against the badge
    bb = d.textbbox((0, 0), title, font=f)
    th = bb[3] - bb[1]
    d.text((tx, cy - th / 2 - bb[1]), title, font=f, fill=NAVY)
    return y + badge_r * 2 + 28


def text_block(img, x, y, max_w, text, font, fill, *, line_spacing=1.32,
               align="left", max_lines=None):
    """Word-wrap `text` to fit `max_w` and draw it. Returns y after the block."""
    d = ImageDraw.Draw(img)
    # measure space width by char
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + "…"
    asc, desc = font.getmetrics()
    line_h = (asc + desc) * line_spacing
    for i, ln in enumerate(lines):
        if align == "center":
            tw = d.textlength(ln, font=font)
            d.text((x + (max_w - tw) / 2, y + i * line_h), ln, font=font, fill=fill)
        else:
            d.text((x, y + i * line_h), ln, font=font, fill=fill)
    return y + len(lines) * line_h


def _wrap_lines(d, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def fill_text_block(img, x, y, max_w, max_h, text, font_fn, fill, *,
                    line_spacing=1.45, min_size=28, max_size=120):
    """Pick the largest font size such that the word-wrapped `text` fits inside
    (max_w, max_h), then draw it. Used so a card's body text fills the card."""
    d = ImageDraw.Draw(img)
    best = min_size
    lo, hi = min_size, max_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = font_fn(mid)
        lines = _wrap_lines(d, text, f, max_w)
        asc, desc = f.getmetrics()
        h = len(lines) * (asc + desc) * line_spacing
        if h <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    f = font_fn(best)
    lines = _wrap_lines(d, text, f, max_w)
    asc, desc = f.getmetrics()
    lh = (asc + desc) * line_spacing
    # vertically centre the block within the available height
    total_h = len(lines) * lh
    oy = y + max(0, (max_h - total_h) / 2)
    for i, ln in enumerate(lines):
        d.text((x, oy + i * lh), ln, font=f, fill=fill)
    return best


def circ_photo(path: Path, diameter: int, *, ring_color=None, ring_w=14,
               bias_top=0.0) -> Image.Image:
    """Return a circular thumbnail (RGBA) of the photo, optionally ringed."""
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    side = min(sw, sh)
    left = (sw - side) // 2
    top = max(0, int((sh - side) / 2 - side * bias_top))
    src = src.crop((left, top, left + side, top + side)).resize(
        (diameter, diameter), Image.LANCZOS)
    ss = 4
    mask = Image.new("L", (diameter * ss, diameter * ss), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter * ss - 1, diameter * ss - 1), fill=255)
    mask = mask.resize((diameter, diameter), Image.LANCZOS)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    if ring_color:
        d = ImageDraw.Draw(out)
        for k in range(ring_w):
            d.ellipse((k, k, diameter - 1 - k, diameter - 1 - k),
                      outline=ring_color + (255,), width=1)
    return out


def paste_rgba(base: Image.Image, overlay: Image.Image, x, y):
    base.paste(overlay, (int(x), int(y)), overlay)


def fit_image_in_box(path: Path, box_w, box_h, *, radius=22,
                     border_color=(210, 218, 230), border_w=3) -> Image.Image:
    """Letterbox an image to fit (box_w, box_h), rounded corners + thin border."""
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    scale = min(box_w / sw, box_h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    src = src.resize((nw, nh), Image.LANCZOS)
    canvas_img = Image.new("RGBA", (box_w, box_h), (255, 255, 255, 0))
    ox, oy = (box_w - nw) // 2, (box_h - nh) // 2
    canvas_img.paste(src, (ox, oy))
    # rounded mask over the whole box
    ss = 4
    m = Image.new("L", (box_w * ss, box_h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, box_w * ss - 1, box_h * ss - 1),
                                        radius=radius * ss, fill=255)
    m = m.resize((box_w, box_h), Image.LANCZOS)
    out = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    out.paste(canvas_img, (0, 0), m)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, box_w - 1, box_h - 1), radius=radius,
                        outline=border_color + (255,), width=border_w)
    return out


def make_qr(data: str, px: int, *, fg=(15, 26, 53)) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color="white").convert("RGB")
    return img.resize((px, px), Image.NEAREST)


# ════════════════════════════════════════════════════════════════════════
# CONTENT
# ════════════════════════════════════════════════════════════════════════

UNIVERSITY = "OSTIM TECHNICAL UNIVERSITY"
DEPT = "Faculty of Engineering  ·  Department of Computer Engineering"
COURSE = "MFBP 402  ·  Graduation Project II  ·  2026"
ADVISOR_NAME = "Assist. Prof. Dr. Yücel TEKİN"
GITHUB = "github.com/tkonate788/astrobot"
LIVE_URL = "http://76.13.62.195:3000"
STACK = "Node.js · Express · PostgreSQL · n8n · Mistral · Hugging Face · Docker"

PROBLEM_TEXT = (
    "Modern AI assistants are scattered across separate tools — one product for "
    "chat, another for image generation, another for document search, another "
    "for OCR and audio. Users juggle several paid subscriptions to reach "
    "state-of-the-art models, while self-hosting stays complex. AstroBot fills "
    "that gap: one free-to-use web application that unifies conversational AI, "
    "multimodal input, document Q&A and reusable workflows behind a clean chat "
    "interface — plus an admin dashboard for operations."
)

OBJECTIVES = [
    "A unified, containerised conversational AI assistant",
    "Mistral LLM routed through an n8n visual workflow",
    "Image generation (FLUX.1) + image-to-image editing",
    "Document Q&A via RAG with MiniLM embeddings",
    "OCR (Tesseract) + audio transcription (Whisper)",
    "On-demand PDF report generation from chat",
    "Admin dashboard with live stats & user management",
]

KEY_FEATURES = [
    ("Conversational chat", "Mistral medium via n8n"),
    ("Image generation", "FLUX.1-schnell + fal-ai"),
    ("PDF reports", "PDFKit, styled output"),
    ("Document Q&A — RAG", "MiniLM-L6-v2 embeddings"),
    ("OCR + captioning", "Tesseract.js + BLIP"),
    ("Audio transcription", "Groq Whisper-large-v3"),
    ("Admin dashboard", "Stats · users · audit"),
    ("Notebook mode", "Pin a PDF as context"),
]

TEAM = [
    ("Tidiane Konaté", "Architecture · Backend · Deployment", "tidiane-konate.jpg"),
    ("Sidi Mohamed Sall", "Vision · Product · UX", "sidi-mohamed-sall.jpg"),
    ("Ahmed Essalem", "AI · LLM · Multimodal", "ahmed-essalem.jpg"),
    ("Saad Ibrahim Houssein", "QA · Frontend · Testing", "saad-ibrahim-houssein.jpg"),
]


# ─── Diagram for card 03 (Architecture) ─────────────────────────────────
def draw_architecture_diagram(img, x, y, w, h):
    """A compact context diagram: USER -> {Public App, Admin} -> {DB, n8n, HF}."""
    d = ImageDraw.Draw(img)

    def box(bx, by, bw, bh, title, sub, color, *, title_fs=58, sub_fs=38, fill=WHITE):
        rounded_rect(d, (bx, by, bx + bw, by + bh), 20, fill=fill,
                     outline=color, width=6)
        # shrink title to fit the box width
        f1 = F_black(title_fs)
        while d.textlength(title, font=f1) > bw - 24 and f1.size > 28:
            f1 = F_black(f1.size - 2)
        bb = d.textbbox((0, 0), title, font=f1)
        d.text((bx + (bw - (bb[2] - bb[0])) / 2, by + bh * 0.16), title, font=f1, fill=NAVY)
        if sub:
            f2 = F_reg(sub_fs)
            while d.textlength(sub, font=f2) > bw - 24 and f2.size > 22:
                f2 = F_reg(f2.size - 2)
            bb2 = d.textbbox((0, 0), sub, font=f2)
            d.text((bx + (bw - (bb2[2] - bb2[0])) / 2, by + bh * 0.56), sub, font=f2, fill=INK_SOFT)
        return (bx, by, bw, bh)

    def connect(x1, y1, x2, y2, color=INK_SOFT):
        d.line((x1, y1, x2, y2), fill=color, width=6)

    # Row 1: USER (centred)
    uw, uh = int(w * 0.46), int(h * 0.18)
    ux = x + (w - uw) // 2
    uy = y
    box(ux, uy, uw, uh, "USER", "Browser · Mobile", DEEPBLUE, fill=(240, 245, 252))

    # Row 2: Public App | Admin
    gap = int(w * 0.06)
    rw = (w - gap) // 2
    rh = int(h * 0.22)
    ry = uy + uh + int(h * 0.13)
    pax, pbx = x, x + rw + gap
    box(pax, ry, rw, rh, "Public App", "Express · :3000", GREEN)
    box(pbx, ry, rw, rh, "Admin", "Express · :7040", ORANGE)
    # connectors USER -> apps
    connect(ux + uw // 2, uy + uh, ux + uw // 2, ry - int(h * 0.065))
    connect(pax + rw // 2, ry - int(h * 0.065), pbx + rw // 2, ry - int(h * 0.065))
    connect(pax + rw // 2, ry - int(h * 0.065), pax + rw // 2, ry)
    connect(pbx + rw // 2, ry - int(h * 0.065), pbx + rw // 2, ry)

    # Row 3: PostgreSQL | n8n | Hugging Face
    cw = (w - 2 * gap) // 3
    ch = int(h * 0.22)
    cy3 = ry + rh + int(h * 0.13)
    cx0, cx1, cx2 = x, x + cw + gap, x + 2 * (cw + gap)
    box(cx0, cy3, cw, ch, "PostgreSQL", "shared DB", PURPLE, title_fs=50)
    box(cx1, cy3, cw, ch, "n8n", "Mistral LLM", (155, 78, 220), title_fs=54)
    box(cx2, cy3, cw, ch, "Hugging Face", "FLUX · BLIP", CYAN, title_fs=50)
    # connectors apps -> services (a simple bus line)
    bus_y = cy3 - int(h * 0.065)
    connect(pax + rw // 2, ry + rh, pax + rw // 2, bus_y)
    connect(pbx + rw // 2, ry + rh, pbx + rw // 2, bus_y)
    connect(cx0 + cw // 2, bus_y, cx2 + cw // 2, bus_y)
    for cxn in (cx0, cx1, cx2):
        connect(cxn + cw // 2, bus_y, cxn + cw // 2, cy3)


# ════════════════════════════════════════════════════════════════════════
# CARDS
# ════════════════════════════════════════════════════════════════════════

def card_problem(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "01", "PROBLEM DEFINITION", ORANGE)
    # auto-size the body so it fills the rest of the card
    avail_h = (y + h - pad) - (cy + 24)
    fill_text_block(img, x + pad, cy + 24, w - 2 * pad, avail_h,
                    PROBLEM_TEXT, F_reg, INK, line_spacing=1.5,
                    min_size=44, max_size=84)


def card_objectives(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "02", "PROJECT OBJECTIVES", GREEN)
    d = ImageDraw.Draw(img)
    # size the rows so the 7 bullets fill the card
    avail_h = (y + h - pad) - (cy + 24)
    row_h = avail_h / len(OBJECTIVES)
    fsize = max(40, min(70, int(row_h / 1.55)))
    f = F_semi(fsize)
    asc = f.getmetrics()[0]
    yy = cy + 24 + (row_h - (f.getmetrics()[0] + f.getmetrics()[1])) / 2
    for obj in OBJECTIVES:
        r = int(fsize * 0.62)
        cxx = x + pad + r
        cyy = yy + asc * 0.58
        d.ellipse((cxx - r, cyy - r, cxx + r, cyy + r), fill=GREEN)
        d.line([(cxx - r * 0.42, cyy + r * 0.02),
                (cxx - r * 0.08, cyy + r * 0.40),
                (cxx + r * 0.48, cyy - r * 0.36)],
               fill=WHITE, width=max(8, int(r * 0.35)), joint="curve")
        d.text((cxx + r + 34, yy), obj, font=f, fill=INK)
        yy += row_h


def card_architecture(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "03", "ARCHITECTURE", DEEPBLUE)
    d = ImageDraw.Draw(img)
    sub = "Three Docker services on a private network, sharing one PostgreSQL"
    d.text((x + pad, cy + 12), sub, font=F_reg(40), fill=INK_SOFT)
    diag_y = cy + 96
    draw_architecture_diagram(img, x + pad, diag_y, w - 2 * pad, (y + h - pad) - diag_y - 10)


def card_features(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "04", "KEY FEATURES", PURPLE)
    d = ImageDraw.Draw(img)
    col_w = (w - 2 * pad - 60) // 2
    rows = (len(KEY_FEATURES) + 1) // 2
    fy = cy + 28
    block_h = ((y + h - pad) - fy) / rows
    ft = F_black(54)
    fs = F_reg(38)
    title_lh = ft.getmetrics()[0] + ft.getmetrics()[1]
    for i, (title, sub) in enumerate(KEY_FEATURES):
        col = i % 2
        row = i // 2
        bx = x + pad + col * (col_w + 60)
        by = fy + row * block_h + (block_h - (title_lh + 50)) / 2
        # bullet square
        d.rounded_rectangle((bx, by + 10, bx + 30, by + 40), radius=7, fill=PURPLE)
        d.text((bx + 52, by), title, font=ft, fill=NAVY)
        d.text((bx + 52, by + title_lh + 4), sub, font=fs, fill=INK_SOFT)


def card_try_action(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "05", "TRY ASTROBOT IN ACTION", CYAN)
    d = ImageDraw.Draw(img)
    d.text((x + pad, cy + 12),
           "The public landing page — ask the bot anything from the central chat bar",
           font=F_reg(38), fill=INK_SOFT)
    img_y = cy + 96
    strip_h = 90
    box_w = w - 2 * pad
    box_h = (y + h - pad) - img_y - strip_h - 28
    shot = fit_image_in_box(SCREENS / "1.png", box_w, box_h, radius=22,
                            border_color=(60, 70, 95), border_w=4)
    paste_rgba(img, shot, x + pad, img_y)
    # feature pills strip
    sy = img_y + box_h + 32
    pills = ["Central chat bar", "Animated mascot", "10 languages", "Dark / light"]
    fx = x + pad
    fp = F_semi(38)
    ph_h = 70
    for p in pills:
        tw = d.textlength(p, font=fp)
        pw = tw + 60
        d.rounded_rectangle((fx, sy, fx + pw, sy + ph_h), radius=ph_h // 2,
                            fill=(235, 246, 250), outline=(190, 222, 232), width=3)
        d.text((fx + 30, sy + (ph_h - (fp.getmetrics()[0] + fp.getmetrics()[1])) / 2),
               p, font=fp, fill=(11, 110, 130))
        fx += pw + 28


def card_qr(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "08", "TRY IT LIVE", LIGHTBLUE)
    d = ImageDraw.Draw(img)
    d.text((x + pad, cy + 12), "Scan the QR code to launch AstroBot in your browser",
           font=F_reg(38), fill=INK_SOFT)
    cap_h = 200      # space reserved for the two caption lines
    qy = cy + 110
    avail_h = (y + h - pad) - qy - cap_h
    qr_px = int(min(w - 2 * pad - 40, avail_h))
    qr_px = max(qr_px, 700)
    qr = make_qr(LIVE_URL, qr_px, fg=NAVY)
    qx = x + (w - qr_px) // 2
    d.rounded_rectangle((qx - 34, qy - 34, qx + qr_px + 34, qy + qr_px + 34),
                        radius=26, fill=WHITE, outline=LINE, width=3)
    img.paste(qr, (qx, qy))
    cap_y = qy + qr_px + 56
    f = F_black(64)
    bb = d.textbbox((0, 0), "Scan to launch AstroBot", font=f)
    d.text((x + (w - (bb[2] - bb[0])) / 2, cap_y), "Scan to launch AstroBot", font=f, fill=NAVY)
    f2 = F_mono(48)
    bb2 = d.textbbox((0, 0), LIVE_URL, font=f2)
    d.text((x + (w - (bb2[2] - bb2[0])) / 2, cap_y + 88), LIVE_URL, font=f2, fill=CYAN)


def card_team(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "06", "PROJECT TEAM", TEAMBLUE)
    d = ImageDraw.Draw(img)
    d.text((x + pad, cy + 12), "Four developers — Computer Engineering, Faculty of Engineering",
           font=F_reg(40), fill=INK_SOFT)
    grid_y = cy + 100
    n = len(TEAM)
    gap = 56
    cw = (w - 2 * pad - (n - 1) * gap) // n
    ch = (y + h - pad) - grid_y - 10
    photo_d = min(cw - 56, int(ch * 0.58))
    for i, (name, role, photo) in enumerate(TEAM):
        bx = x + pad + i * (cw + gap)
        d.rounded_rectangle((bx, grid_y, bx + cw, grid_y + ch), radius=30,
                            fill=(248, 250, 253), outline=(228, 234, 242), width=3)
        d.rounded_rectangle((bx, grid_y, bx + cw, grid_y + 18), radius=9,
                            fill=TEAM_ACCENTS[i])
        ph = circ_photo(ASSETS / photo, photo_d, ring_color=TEAM_ACCENTS[i],
                        ring_w=14, bias_top=0.06)
        paste_rgba(img, ph, bx + (cw - photo_d) // 2, grid_y + 52)
        # name
        ny = grid_y + 52 + photo_d + 30
        f = F_black(52)
        while d.textlength(name, font=f) > cw - 24 and f.size > 32:
            f = F_black(f.size - 2)
        bb = d.textbbox((0, 0), name, font=f)
        d.text((bx + (cw - (bb[2] - bb[0])) / 2, ny), name, font=f, fill=NAVY)
        # role (wrap to <= 2 lines)
        ry = ny + (f.getmetrics()[0] + f.getmetrics()[1]) + 14
        fr = F_reg(34)
        if d.textlength(role, font=fr) <= cw - 24:
            bb2 = d.textbbox((0, 0), role, font=fr)
            d.text((bx + (cw - (bb2[2] - bb2[0])) / 2, ry), role, font=fr, fill=INK_SOFT)
        else:
            words = role.split(" · ")
            mid = len(words) // 2 + 1
            l1 = " · ".join(words[:mid]); l2 = " · ".join(words[mid:])
            rlh = fr.getmetrics()[0] + fr.getmetrics()[1]
            for k, ln in enumerate((l1, l2)):
                bb2 = d.textbbox((0, 0), ln, font=fr)
                d.text((bx + (cw - (bb2[2] - bb2[0])) / 2, ry + k * (rlh + 2)), ln, font=fr, fill=INK_SOFT)


def card_advisor(img, x, y, w, h):
    card(img, x, y, w, h)
    pad = 80
    cy = card_header(img, x + pad, y + pad, "07", "ADVISOR", MAROON)
    d = ImageDraw.Draw(img)
    avail_h = (y + h - pad) - cy
    pd = int(min(avail_h - 20, h * 0.50))
    px = x + pad + 20
    py = cy + (avail_h - pd) // 2 + 6
    ph = circ_photo(ADVISOR_PHOTO, pd, ring_color=MAROON, ring_w=16, bias_top=0.04)
    paste_rgba(img, ph, px, py)
    # name + title, vertically centred on the photo
    tx = px + pd + 80
    name_f = F_black(84)
    while d.textlength(ADVISOR_NAME, font=name_f) > (x + w - pad - int(w * 0.30) - 60) - tx and name_f.size > 48:
        name_f = F_black(name_f.size - 2)
    sub_f = F_reg(48)
    nlh = name_f.getmetrics()[0] + name_f.getmetrics()[1]
    slh = sub_f.getmetrics()[0] + sub_f.getmetrics()[1]
    total_h = nlh + 24 + slh
    ty = py + (pd - total_h) // 2
    d.text((tx, ty), ADVISOR_NAME, font=name_f, fill=NAVY)
    d.text((tx, ty + nlh + 18), "Project Supervisor", font=sub_f, fill=MAROON)

    # far right: repo + stack info
    rx = x + w - pad - int(w * 0.30)
    rw = int(w * 0.30) - 10
    d.line((rx - 60, cy + 16, rx - 60, y + h - pad - 8), fill=LINE, width=3)
    info_t = F_black(44)
    info_m = F_mono(38)
    info_r = F_reg(34)
    iy = py + 4
    d.text((rx, iy), "Source code", font=info_t, fill=NAVY)
    d.text((rx, iy + 64), GITHUB, font=info_m, fill=TEAMBLUE)
    d.text((rx, iy + 150), "Built with", font=info_t, fill=NAVY)
    text_block(img, rx, iy + 214, rw, STACK, info_r, INK_SOFT, line_spacing=1.4)


# ════════════════════════════════════════════════════════════════════════
# HEADER + TITLE
# ════════════════════════════════════════════════════════════════════════

def draw_header(img, margin):
    d = ImageDraw.Draw(img)
    hx, hy = margin, 130
    hw, hh = W - 2 * margin, 470
    card(img, hx, hy, hw, hh, radius=46, shadow=True)
    # OSTIM logo (left)
    logo = Image.open(ASSETS / "ostim_logo_official.png").convert("RGBA")
    lw = 760
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    ly = hy + (hh - lh) // 2
    paste_rgba(img, logo, hx + 70, ly)
    # University text
    tx = hx + 70 + lw + 70
    d.text((tx, hy + 95), UNIVERSITY, font=F_black(74), fill=NAVY)
    d.text((tx, hy + 195), DEPT, font=F_reg(40), fill=INK_SOFT)
    d.text((tx, hy + 265), COURSE, font=F_semi(40), fill=DEEPBLUE)
    # GRADUATION PROJECT badge (right)
    bw, bh = 620, 230
    bx = hx + hw - bw - 70
    by = hy + (hh - bh) // 2
    # gradient-ish: just a navy block with a lighter top strip
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=24, fill=DEEPBLUE)
    d.rounded_rectangle((bx, by, bx + bw, by + 64), radius=24, fill=(56, 102, 178))
    d.rectangle((bx, by + 36, bx + bw, by + 64), fill=(56, 102, 178))
    f1 = F_reg(34)
    t1 = "MAY 2026  ·  ANKARA"
    bb1 = d.textbbox((0, 0), t1, font=f1)
    d.text((bx + (bw - (bb1[2] - bb1[0])) / 2, by + 14), t1, font=f1, fill=(225, 235, 248))
    f2 = F_black(64)
    for k, ln in enumerate(("GRADUATION", "PROJECT")):
        bb2 = d.textbbox((0, 0), ln, font=f2)
        d.text((bx + (bw - (bb2[2] - bb2[0])) / 2, by + 80 + k * 70), ln, font=f2, fill=WHITE)


def draw_title(img, margin, top):
    """AstroBot logo + taglines. Returns y below."""
    d = ImageDraw.Draw(img)
    logo = Image.open(ASSETS / "astrobot_logo.png").convert("RGBA")
    target_h = 880
    lw = int(logo.width * target_h / logo.height)
    logo = logo.resize((lw, target_h), Image.LANCZOS)
    lx = (W - lw) // 2
    paste_rgba(img, logo, lx, top)
    y = top + target_h + 20
    t1 = "An Intelligent Conversational AI Assistant"
    f1 = F_black(96)
    bb1 = d.textbbox((0, 0), t1, font=f1)
    d.text(((W - (bb1[2] - bb1[0])) / 2, y), t1, font=f1, fill=NAVY)
    y += (bb1[3] - bb1[1]) + 56
    t2 = "Multimodal  ·  Retrieval-Augmented Generation  ·  Workflow Integration"
    f2 = F_reg(52)
    bb2 = d.textbbox((0, 0), t2, font=f2)
    d.text(((W - (bb2[2] - bb2[0])) / 2, y), t2, font=f2, fill=DEEPBLUE)
    y += (bb2[3] - bb2[1]) + 30
    # little divider
    d.line((W / 2 - 200, y, W / 2 - 40, y), fill=DEEPBLUE, width=6)
    d.line((W / 2 + 40, y, W / 2 + 200, y), fill=DEEPBLUE, width=6)
    d.ellipse((W / 2 - 16, y - 14, W / 2 + 16, y + 14), fill=CYAN)
    return y + 30


def draw_footer(img, margin):
    d = ImageDraw.Draw(img)
    fy = H - 110
    d.line((margin, fy, W - margin, fy), fill=LINE, width=3)
    d.text((margin, fy + 26), f"GitHub  ·  {GITHUB}", font=F_semi(34), fill=DEEPBLUE)
    t = STACK
    f = F_reg(32)
    bb = d.textbbox((0, 0), t, font=f)
    d.text((W - margin - (bb[2] - bb[0]), fy + 28), t, font=f, fill=INK_SOFT)


def draw_decor_planets(img):
    """A few faint planets in the title area, like the original."""
    d = ImageDraw.Draw(img, "RGBA")
    def planet(cx, cy, r, color, ring=True):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (235,))
        # little crater highlight
        d.ellipse((cx - r * 0.4, cy - r * 0.55, cx - r * 0.4 + r * 0.4,
                   cy - r * 0.55 + r * 0.4), fill=(255, 255, 255, 150))
        if ring:
            for k in range(8):
                d.ellipse((cx - r * 1.7, cy - r * 0.34 - k, cx + r * 1.7, cy + r * 0.34 + k),
                          outline=(120, 150, 200, 90), width=1)
    planet(margin + 230, 1500, 110, (96, 165, 220))
    planet(W - margin - 200, 1480, 70, (40, 70, 130), ring=True)


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

def main():
    print(f"Canvas {W}x{H} px  (70x100 cm @ {DPI} DPI)")
    img = vertical_gradient((W, H), BG_TOP, BG_BOT).convert("RGB")

    margin = 130
    globals()["margin"] = margin  # used by draw_decor_planets

    # Header
    draw_header(img, margin)

    # Decorative planets (behind the title) — draw before the title logo? after is fine
    draw_decor_planets(img)

    # Title
    title_bottom = draw_title(img, margin, top=640)

    # ── Content grid ────────────────────────────────────────────────
    content_top = title_bottom + 70
    content_bottom = H - 150
    gutter = 110
    col_w = (W - 2 * margin - gutter) // 2
    xL = margin
    xR = margin + col_w + gutter

    avail = content_bottom - content_top
    # Row heights (tuned to fill the page). 4 row gaps of 90 px.
    gap = 90
    # Rows: A (problem/obj), B (arch/feat), C (try/qr), D (team), E (advisor)
    hA = int(avail * 0.190)
    hB = int(avail * 0.205)
    hC = int(avail * 0.225)
    hE = int(avail * 0.135)
    hD = avail - hA - hB - hC - hE - 4 * gap

    yA = content_top
    yB = yA + hA + gap
    yC = yB + hB + gap
    yD = yC + hC + gap
    yE = yD + hD + gap

    # Row A
    card_problem(img, xL, yA, col_w, hA)
    card_objectives(img, xR, yA, col_w, hA)
    # Row B
    card_architecture(img, xL, yB, col_w, hB)
    card_features(img, xR, yB, col_w, hB)
    # Row C
    card_try_action(img, xL, yC, col_w, hC)
    card_qr(img, xR, yC, col_w, hC)
    # Row D — full width
    card_team(img, xL, yD, W - 2 * margin, hD)
    # Row E — full width advisor
    card_advisor(img, xL, yE, W - 2 * margin, hE)

    draw_footer(img, margin)

    print(f"Saving {OUT_PNG.name} ...")
    img.save(OUT_PNG, optimize=True)
    print(f"  PNG: {OUT_PNG.stat().st_size/1024/1024:.1f} MB")

    print(f"Saving {OUT_PDF.name} (70x100 cm) ...")
    c = pdfcanvas.Canvas(str(OUT_PDF), pagesize=(70 / 2.54 * 72, 100 / 2.54 * 72))
    c.drawImage(ImageReader(img), 0, 0, width=70 / 2.54 * 72, height=100 / 2.54 * 72,
                preserveAspectRatio=False)
    c.showPage()
    c.save()
    print(f"  PDF: {OUT_PDF.stat().st_size/1024/1024:.1f} MB")
    print("Done.")


if __name__ == "__main__":
    main()
