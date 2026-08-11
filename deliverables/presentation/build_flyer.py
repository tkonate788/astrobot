#!/usr/bin/env python3
"""
AstroBot — A5 two-sided distribution flyer generator.

Produces a 148×210 mm print-quality two-page flyer (A5 portrait at 300 DPI)
inspired by the "VDS Try-on Before You Buy" promo flyer but with a fully
edge-to-edge dark design (no white margins).

Front (recto): big tagline, description, one large QR code → live demo.
Back  (verso): grid of feature cards (chat, image gen, PDFs, voice, OCR,
               workflows, sessions, admin), stats, team, demo URL.

Outputs:
    presentation/AstroBot_Flyer.png            — recto (1748×2480, 300 DPI)
    presentation/AstroBot_Flyer_Verso.png      — verso (same size)
    presentation/AstroBot_Flyer.pdf            — 2-page A5 PDF (print-ready)

Run:    python presentation/build_flyer.py
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "deliverables" / "report" / "assets"
LOGO_PATH = ASSETS / "astrobot_logo.png"
OSTIM_LOGO = ASSETS / "ostim_logo_official.png"
OUT_DIR = Path(__file__).resolve().parent
OUTPUT_RECTO = OUT_DIR / "AstroBot_Flyer.png"
OUTPUT_VERSO = OUT_DIR / "AstroBot_Flyer_Verso.png"
OUTPUT_PDF   = OUT_DIR / "AstroBot_Flyer.pdf"

DPI = 300
W = int(148 / 25.4 * DPI)        # 1748 (A5 width @ 300 DPI)
H = int(210 / 25.4 * DPI)        # 2480 (A5 height)

# ── Colors  (aligned with the AstroBot website palette) ──────────
# Site CSS variables this matches:
#   --bg-primary    #070d1a  → NAVY
#   --bg-secondary  #0d1b35  → NAVY_INK
#   --accent-blue   #1a73e8  → BLUE       (primary brand accent)
#   --accent-cyan   #00d4ff  → CYAN       (secondary accent)
#   --accent-orange #f4a623  → GOLD
#   --accent-green  #00e676  → GREEN
WHITE       = (255, 255, 255)
NAVY        = (7, 13, 26)        # #070d1a — main dark
NAVY_DEEP   = (3, 7, 17)         # slightly darker for bottom of gradient
NAVY_INK    = (13, 27, 53)       # #0d1b35 — mid-tone navy
BLUE        = (26, 115, 232)     # #1a73e8 — PRIMARY accent (was BLUE)
BLUE_GLOW   = (75, 155, 255)     # brighter variant for headings / accents
CYAN        = (0, 212, 255)      # #00d4ff — secondary accent
CYAN_GLOW   = (110, 235, 255)    # brighter cyan
GOLD        = (244, 166, 35)     # #f4a623 — warm accent
GOLD_GLOW   = (255, 200, 80)
GREEN       = (0, 230, 118)      # #00e676
PINK        = (236, 100, 170)    # used to add variety in feature cards
INK         = (24, 32, 52)
INK_SOFT    = (200, 220, 245)
INK_MUTED   = (140, 165, 205)

FDIR = Path("C:/Windows/Fonts")
def F(name, size):
    try: return ImageFont.truetype(str(FDIR / name), size)
    except OSError: return ImageFont.load_default()
def FB(s):  return F("segoeuib.ttf", s)
def FBL(s): return F("seguibl.ttf", s)
def FS(s):  return F("seguisb.ttf", s)
def FR(s):  return F("segoeui.ttf", s)
def FL(s):  return F("segoeuil.ttf", s)


# ── Drawing helpers ──────────────────────────────────────────────
def _text_w(d, text, font):
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _vertical_gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def _radial_glow(size, center, color, radius, alpha=170):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    for rmul, amul in [(1.0, 0.0), (0.78, 0.25), (0.55, 0.55),
                       (0.32, 0.85), (0.15, 1.0)]:
        r = int(radius * rmul)
        a = int(alpha * amul)
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  fill=(color[0], color[1], color[2], a))
    return layer.filter(ImageFilter.GaussianBlur(100))


def _wave_particles(size, seed=42):
    """Faint flowing curves + dots — the 'cosmic dust' effect."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    W2, H2 = size
    rng = random.Random(seed)
    # 5 flowing curves
    for ci in range(5):
        amp = rng.uniform(80, 180)
        freq = rng.uniform(0.0012, 0.0025)
        offset = rng.uniform(0, math.tau)
        yc = rng.uniform(H2 * 0.10, H2 * 0.90)
        color = rng.choice([BLUE_GLOW, CYAN_GLOW, BLUE_GLOW])
        pts = []
        for x in range(0, W2, 8):
            y = yc + math.sin(x * freq + offset) * amp \
                + math.cos(x * freq * 0.4 + offset * 1.7) * amp * 0.5
            pts.append((x, y))
        for i in range(len(pts) - 1):
            t = i / max(1, len(pts) - 1)
            edge = math.sin(t * math.pi)
            a = int(55 * edge)
            if a < 5: continue
            d.line([pts[i], pts[i + 1]],
                   fill=(color[0], color[1], color[2], a), width=2)
    # Stars
    for _ in range(280):
        x = rng.randint(0, W2)
        y = rng.randint(0, H2)
        r = rng.choice([1, 1, 1, 2, 2, 2, 3, 3, 4])
        a = rng.randint(60, 220)
        c = rng.choice([WHITE, WHITE, BLUE_GLOW, CYAN_GLOW, PINK])
        d.ellipse((x, y, x + r, y + r), fill=(c[0], c[1], c[2], a))
    return layer.filter(ImageFilter.GaussianBlur(0.6))


def make_cosmic_background(W2=W, H2=H, seed=42):
    """Full-bleed cosmic dark background reused by both pages."""
    bg = _vertical_gradient(W2, H2, NAVY, NAVY_DEEP).convert("RGBA")
    # Big purple glow upper-left
    bg = Image.alpha_composite(
        bg, _radial_glow((W2, H2),
                         (int(W2 * 0.18), int(H2 * 0.22)),
                         BLUE, int(W2 * 0.95), alpha=180))
    # Cyan glow lower-right
    bg = Image.alpha_composite(
        bg, _radial_glow((W2, H2),
                         (int(W2 * 0.88), int(H2 * 0.85)),
                         CYAN, int(W2 * 0.55), alpha=130))
    # Magenta accent middle
    bg = Image.alpha_composite(
        bg, _radial_glow((W2, H2),
                         (int(W2 * 0.55), int(H2 * 0.55)),
                         BLUE_GLOW, int(W2 * 0.30), alpha=70))
    # Particles
    bg = Image.alpha_composite(bg, _wave_particles((W2, H2), seed=seed))
    return bg


def light_logo(path: Path, height_px: int, tint=WHITE) -> Image.Image | None:
    """Return a single-color silhouette of the logo, sized to height_px.
    Useful on dark backgrounds where the original colored logo is invisible."""
    if not path.exists():
        return None
    src = Image.open(path).convert("RGBA")
    alpha = src.split()[-1]
    color_layer = Image.new("RGBA", src.size, (tint[0], tint[1], tint[2], 255))
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out.paste(color_layer, (0, 0), alpha)
    # resize
    new_w = int(src.size[0] * height_px / src.size[1])
    return out.resize((new_w, height_px), Image.LANCZOS)


def make_qr(data: str, size_px: int, *, fg=(20, 28, 60), bg=WHITE):
    qr = qrcode.QRCode(version=None,
                       error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg).convert("RGB")
    return img.resize((size_px, size_px), Image.LANCZOS)


def _fit_text(d, text, font_fn, max_w, start_size, min_size=20):
    s = start_size
    while s > min_size:
        f = font_fn(s)
        if _text_w(d, text, f) <= max_w:
            return f
        s -= 2
    return font_fn(min_size)


def wrap_text(d, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if _text_w(d, test, font) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


# ── RECTO (front) ────────────────────────────────────────────────
def draw_recto(canvas: Image.Image):
    d = ImageDraw.Draw(canvas)

    # ── Logo at top ──
    logo = light_logo(LOGO_PATH, 240, tint=WHITE)
    if logo:
        canvas.alpha_composite(logo, ((W - logo.size[0]) // 2, 80))
    # Subtitle
    sub_f = FS(34)
    sub = "Intelligent  Conversational  AI  Assistant"
    tw = _text_w(d, sub, sub_f)
    d.text(((W - tw) // 2, 350), sub, font=sub_f, fill=INK_SOFT)
    # Accent line
    line_w = tw + 80
    d.rectangle(((W - line_w) // 2, 410,
                 (W - line_w) // 2 + line_w, 414),
                fill=BLUE_GLOW)

    # ── Mini label ──
    label_f = FS(28)
    label = "OSTIM  ·  Graduation Project 2026"
    tw = _text_w(d, label, label_f)
    d.text(((W - tw) // 2, 460), label, font=label_f, fill=CYAN_GLOW)

    # ── Big 3-line tagline ──
    tagline_lines = [("ONE CHAT.",  WHITE),
                     ("TWELVE",      BLUE_GLOW),
                     ("AI POWERS.",  WHITE)]
    y = 600
    max_w = W - 200
    widest = max(tagline_lines, key=lambda x: len(x[0]))[0]
    tag_f = _fit_text(d, widest, FBL, max_w, 240, 100)
    line_h = int(tag_f.size * 1.05)
    for ln, color in tagline_lines:
        tw = _text_w(d, ln, tag_f)
        d.text(((W - tw) // 2 + 5, y + 6), ln, font=tag_f, fill=(0, 0, 0, 220))
        d.text(((W - tw) // 2, y), ln, font=tag_f, fill=color)
        y += line_h
    y += 40

    # ── Description ──
    desc = ("Chat with seven personas. Generate images. Read PDFs. "
            "Transcribe voice. Read images with OCR. Automate workflows. "
            "Twelve AI features in one place — and it's free to try.")
    desc_f = FR(32)
    lines = wrap_text(d, desc, desc_f, W - 240)
    for ln in lines:
        tw = _text_w(d, ln, desc_f)
        d.text(((W - tw) // 2, y), ln, font=desc_f, fill=INK_SOFT)
        y += 44
    y += 60

    # ── One large QR code, centered, with glow halo ──
    qr_size = 520
    qr_x = (W - qr_size) // 2
    qr_y = y
    # Halo behind QR
    halo = Image.new("RGBA", (qr_size + 220, qr_size + 220), (0, 0, 0, 0))
    halo_d = ImageDraw.Draw(halo)
    halo_d.ellipse((0, 0, qr_size + 220, qr_size + 220),
                   fill=(BLUE_GLOW[0], BLUE_GLOW[1], BLUE_GLOW[2], 120))
    halo = halo.filter(ImageFilter.GaussianBlur(60))
    canvas.alpha_composite(halo, (qr_x - 110, qr_y - 110))
    # White rounded frame
    frame = Image.new("RGBA", (qr_size + 60, qr_size + 60), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        (0, 0, qr_size + 60, qr_size + 60), radius=32, fill=WHITE)
    canvas.alpha_composite(frame, (qr_x - 30, qr_y - 30))
    qr_img = make_qr("http://76.13.62.195:3000", qr_size,
                     fg=(20, 28, 60), bg=WHITE)
    canvas.paste(qr_img, (qr_x, qr_y))
    # Caption under QR
    cap_f = FBL(40)
    cap = "SCAN  TO  TRY  ASTROBOT"
    tw = _text_w(d, cap, cap_f)
    d.text(((W - tw) // 2 + 3, qr_y + qr_size + 70 + 3),
           cap, font=cap_f, fill=(0, 0, 0, 200))
    d.text(((W - tw) // 2, qr_y + qr_size + 70),
           cap, font=cap_f, fill=WHITE)
    # URL plain text below caption (so people without a QR scanner can type)
    url_f = FS(30)
    url = "http://76.13.62.195:3000"
    tw = _text_w(d, url, url_f)
    d.text(((W - tw) // 2, qr_y + qr_size + 132),
           url, font=url_f, fill=CYAN_GLOW)

    # ── OSTIM logo + university text footer ──
    # Subtle top divider
    div_w = 220
    d.rectangle(((W - div_w) // 2, H - 220,
                 (W - div_w) // 2 + div_w, H - 218),
                fill=(255, 255, 255, 60))

    # OSTIM logo (drop into a small white rounded card so the burgundy/gray
    # logo stays readable on the dark navy background).
    if OSTIM_LOGO.exists():
        ostim_src = Image.open(OSTIM_LOGO).convert("RGBA")
        lh = 96
        lw = int(ostim_src.size[0] * lh / ostim_src.size[1])
        ostim_img = ostim_src.resize((lw, lh), Image.LANCZOS)
        # White card
        pad_x, pad_y = 22, 14
        card_w = lw + 2 * pad_x
        card_h = lh + 2 * pad_y
        card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle(
            (0, 0, card_w, card_h), radius=16, fill=WHITE)
        card.alpha_composite(ostim_img, (pad_x, pad_y))
    else:
        card = None
        card_w = card_h = 0

    # Right-hand text (two lines)
    uni_f  = FBL(34)
    sub_f  = FS(24)
    uni    = "OSTIM Technical University"
    sub    = "Computer Engineering  ·  Graduation Project 2026"
    text_w = max(_text_w(d, uni, uni_f), _text_w(d, sub, sub_f))

    gap = 30
    total_w = (card_w + gap if card else 0) + text_w
    x_start = (W - total_w) // 2
    y_block = H - 195

    if card:
        canvas.alpha_composite(card, (x_start, y_block))
    text_x = x_start + (card_w + gap if card else 0)
    text_y_uni = y_block + (card_h - 72) // 2 if card else y_block + 10
    d.text((text_x, text_y_uni), uni, font=uni_f, fill=WHITE)
    d.text((text_x, text_y_uni + 44), sub, font=sub_f, fill=INK_MUTED)

    # Advisor line below
    adv_f = FS(24)
    adv = "Advisor : Assist. Prof. Dr. Yücel TEKİN"
    tw = _text_w(d, adv, adv_f)
    d.text(((W - tw) // 2, H - 70), adv, font=adv_f, fill=BLUE_GLOW)


# ── VERSO (back) — feature grid ──────────────────────────────────
# Each card: title, one-line subtitle, icon-drawer fn, accent color
FEATURES = []  # populated below after icon-drawers are defined


def icon_chat(d, x, y, s, color):
    """Speech bubble"""
    r = int(s * 0.18)
    d.rounded_rectangle((x, y, x + s, y + int(s * 0.78)),
                        radius=r, outline=color, width=int(s * 0.06))
    # tail
    tx = x + int(s * 0.22)
    ty = y + int(s * 0.78)
    d.polygon([(tx, ty), (tx + int(s * 0.20), ty),
               (tx, ty + int(s * 0.20))], fill=color)
    # dots
    cy = y + int(s * 0.40)
    for i, dx in enumerate([0.28, 0.50, 0.72]):
        cx = x + int(s * dx)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=color)


def icon_image(d, x, y, s, color):
    """Image / picture frame with star"""
    w_ = int(s * 0.06)
    d.rounded_rectangle((x, y, x + s, y + int(s * 0.78)),
                        radius=12, outline=color, width=w_)
    # sun in corner
    cx, cy = x + int(s * 0.30), y + int(s * 0.28)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=color)
    # mountain
    d.polygon([(x + int(s * 0.15), y + int(s * 0.72)),
               (x + int(s * 0.45), y + int(s * 0.36)),
               (x + int(s * 0.65), y + int(s * 0.60)),
               (x + int(s * 0.78), y + int(s * 0.46)),
               (x + int(s * 0.92), y + int(s * 0.72))], fill=color)


def icon_pdf(d, x, y, s, color):
    """Document with fold corner + lines"""
    w_ = int(s * 0.06)
    fold = int(s * 0.20)
    pts = [(x + int(s * 0.10), y),
           (x + s - fold, y),
           (x + s, y + fold),
           (x + s, y + int(s * 0.85)),
           (x + int(s * 0.10), y + int(s * 0.85))]
    d.polygon(pts, outline=color, width=w_)
    # fold
    d.polygon([(x + s - fold, y),
               (x + s, y + fold),
               (x + s - fold, y + fold)], outline=color, width=w_)
    # text lines
    for i, ly in enumerate([0.40, 0.55, 0.70]):
        d.rectangle((x + int(s * 0.22), y + int(s * ly) - 4,
                     x + int(s * (0.78 - i * 0.10)), y + int(s * ly) + 4),
                    fill=color)


def icon_mic(d, x, y, s, color):
    """Microphone"""
    w_ = int(s * 0.06)
    mw = int(s * 0.32)
    mh = int(s * 0.45)
    mx = x + (s - mw) // 2
    my = y + int(s * 0.10)
    d.rounded_rectangle((mx, my, mx + mw, my + mh),
                        radius=mw // 2, fill=color)
    # stand
    arc_x1 = x + int(s * 0.20)
    arc_y1 = my + int(mh * 0.5)
    arc_x2 = x + s - int(s * 0.20)
    arc_y2 = arc_y1 + int(s * 0.30)
    d.arc((arc_x1, arc_y1, arc_x2, arc_y2),
          start=0, end=180, fill=color, width=w_)
    foot_x = (arc_x1 + arc_x2) // 2
    d.line((foot_x, arc_y2 - (arc_y2 - arc_y1) // 2,
            foot_x, y + int(s * 0.80)), fill=color, width=w_)
    d.line((foot_x - int(s * 0.10), y + int(s * 0.80),
            foot_x + int(s * 0.10), y + int(s * 0.80)),
           fill=color, width=w_)


def icon_eye(d, x, y, s, color):
    """Eye (vision / OCR)"""
    w_ = int(s * 0.06)
    cx, cy = x + s // 2, y + int(s * 0.42)
    rw, rh = int(s * 0.42), int(s * 0.26)
    d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh),
              outline=color, width=w_)
    d.ellipse((cx - int(s * 0.13), cy - int(s * 0.13),
               cx + int(s * 0.13), cy + int(s * 0.13)), fill=color)


def icon_workflow(d, x, y, s, color):
    """Linked nodes"""
    w_ = int(s * 0.06)
    r = int(s * 0.10)
    # 3 nodes
    pts = [(x + r + 8,             y + int(s * 0.20)),
           (x + s - r - 8,         y + int(s * 0.20)),
           (x + s // 2,            y + int(s * 0.70))]
    # links
    d.line((pts[0][0] + r, pts[0][1], pts[1][0] - r, pts[1][1]),
           fill=color, width=w_)
    d.line((pts[0][0], pts[0][1] + r, pts[2][0] - r, pts[2][1]),
           fill=color, width=w_)
    d.line((pts[1][0], pts[1][1] + r, pts[2][0] + r, pts[2][1]),
           fill=color, width=w_)
    for px, py in pts:
        d.ellipse((px - r, py - r, px + r, py + r), fill=color)


def icon_tag(d, x, y, s, color):
    """Tag / label"""
    w_ = int(s * 0.06)
    pts = [(x + int(s * 0.08), y + int(s * 0.20)),
           (x + int(s * 0.55), y + int(s * 0.20)),
           (x + int(s * 0.92), y + int(s * 0.50)),
           (x + int(s * 0.55), y + int(s * 0.80)),
           (x + int(s * 0.08), y + int(s * 0.80))]
    d.polygon(pts, outline=color, width=w_)
    # hole
    hx, hy = x + int(s * 0.22), y + int(s * 0.50)
    d.ellipse((hx - 8, hy - 8, hx + 8, hy + 8), fill=color)


def icon_dashboard(d, x, y, s, color):
    """Dashboard / chart bars"""
    w_ = int(s * 0.06)
    d.rounded_rectangle((x, y, x + s, y + int(s * 0.80)),
                        radius=12, outline=color, width=w_)
    # bars
    base = y + int(s * 0.68)
    for i, h in enumerate([0.20, 0.40, 0.28, 0.50]):
        bx = x + int(s * (0.18 + i * 0.18))
        bh = int(s * h)
        d.rectangle((bx, base - bh, bx + int(s * 0.10), base),
                    fill=color)


FEATURES = [
    ("Smart Chat",        "7 personas, Markdown, math, code rendered live", icon_chat,      BLUE_GLOW),
    ("AI Image Gen",      "FLUX-1 + image-to-image editing",                icon_image,     CYAN_GLOW),
    ("Talk to your PDFs", "RAG retrieval & full-notebook mode",             icon_pdf,       GOLD),
    ("Voice Input",       "Whisper transcribes you in seconds",             icon_mic,       PINK),
    ("Vision & OCR",      "Read and describe any image",                    icon_eye,       GREEN),
    ("Workflows",         "Multi-step prompt chains, saved & reusable",     icon_workflow,  BLUE_GLOW),
    ("Sessions & Tags",   "Search, tag, export PDF / Markdown / JSON",      icon_tag,       CYAN_GLOW),
    ("Admin Dashboard",   "Real-time KPIs, user audit, role-gated",         icon_dashboard, GOLD),
]


def draw_feature_card(canvas, x, y, w, h, *, title, subtitle, draw_icon, color):
    d = ImageDraw.Draw(canvas)
    # Card background — subtle translucent fill
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, w, h), radius=28,
                         fill=(255, 255, 255, 16),
                         outline=(255, 255, 255, 60), width=2)
    canvas.alpha_composite(card, (x, y))
    # Icon container (rounded square left)
    icon_box = 130
    ix = x + 36
    iy = y + (h - icon_box) // 2
    # Colored translucent square behind icon
    iconbg = Image.new("RGBA", (icon_box, icon_box), (0, 0, 0, 0))
    ImageDraw.Draw(iconbg).rounded_rectangle(
        (0, 0, icon_box, icon_box), radius=22,
        fill=(color[0], color[1], color[2], 40),
        outline=(color[0], color[1], color[2], 200), width=3)
    canvas.alpha_composite(iconbg, (ix, iy))
    # Icon (drawn directly on canvas)
    draw_icon(d, ix + 18, iy + 16, icon_box - 36, color)
    # Title
    tf = FBL(46)
    d.text((ix + icon_box + 40, y + 36), title, font=tf, fill=WHITE)
    # Subtitle (may wrap)
    sf = FR(26)
    sub_x = ix + icon_box + 40
    sub_w = w - (sub_x - x) - 32
    lines = wrap_text(d, subtitle, sf, sub_w)
    sy = y + 36 + 60
    for ln in lines[:2]:
        d.text((sub_x, sy), ln, font=sf, fill=INK_SOFT)
        sy += 38


def draw_verso(canvas: Image.Image):
    d = ImageDraw.Draw(canvas)
    # Logo + small header
    logo = light_logo(LOGO_PATH, 130, tint=WHITE)
    if logo:
        canvas.alpha_composite(logo, ((W - logo.size[0]) // 2, 80))
    # Header text
    head_f = FBL(72)
    head = "INSIDE ASTROBOT"
    tw = _text_w(d, head, head_f)
    d.text(((W - tw) // 2 + 3, 263), head, font=head_f, fill=(0, 0, 0, 200))
    d.text(((W - tw) // 2, 260), head, font=head_f, fill=WHITE)
    # Accent line
    line_w = 220
    d.rectangle(((W - line_w) // 2, 365,
                 (W - line_w) // 2 + line_w, 369), fill=BLUE_GLOW)
    # Subtitle
    sub_f = FL(34)
    sub = "Twelve AI features in one chat."
    tw = _text_w(d, sub, sub_f)
    d.text(((W - tw) // 2, 395), sub, font=sub_f, fill=INK_SOFT)

    # Feature grid: 2 cols × 4 rows
    pad = 70
    gap = 30
    top = 490
    n_cols = 2
    n_rows = 4
    card_w = (W - 2 * pad - (n_cols - 1) * gap) // n_cols
    card_h = 280
    for i, (title, sub, icon, color) in enumerate(FEATURES[:8]):
        row, col = divmod(i, n_cols)
        cx = pad + col * (card_w + gap)
        cy = top + row * (card_h + gap)
        draw_feature_card(canvas, cx, cy, card_w, card_h,
                          title=title, subtitle=sub,
                          draw_icon=icon, color=color)

    # Bottom: stats line + URL + team
    grid_bottom = top + n_rows * card_h + (n_rows - 1) * gap + 60
    # Three big stats
    stats = [("12",  "AI FEATURES",        BLUE_GLOW),
             ("66",  "INTEGRATION TESTS",  CYAN_GLOW),
             ("LIVE", "RIGHT NOW",         GOLD)]
    col_w = W // 3
    stat_y = grid_bottom
    for i, (num, lbl, color) in enumerate(stats):
        cx = col_w * i + col_w // 2
        nf = FBL(110)
        # auto-shrink if too wide
        while _text_w(d, num, nf) > col_w - 60 and nf.size > 60:
            nf = FBL(nf.size - 6)
        tw = _text_w(d, num, nf)
        d.text((cx - tw // 2 + 3, stat_y + 5), num, font=nf, fill=(0, 0, 0, 180))
        d.text((cx - tw // 2, stat_y), num, font=nf, fill=color)
        lf = FS(24)
        tw = _text_w(d, lbl, lf)
        d.text((cx - tw // 2, stat_y + 130), lbl, font=lf, fill=INK_SOFT)

    # URL big
    url_f = FBL(64)
    url = "76.13.62.195:3000"
    tw = _text_w(d, url, url_f)
    url_y = stat_y + 220
    d.text(((W - tw) // 2 + 3, url_y + 4), url, font=url_f, fill=(0, 0, 0, 200))
    d.text(((W - tw) // 2, url_y), url, font=url_f, fill=WHITE)
    # caption
    cap_f = FS(26)
    cap = "Open it in any browser. Free to try."
    tw = _text_w(d, cap, cap_f)
    d.text(((W - tw) // 2, url_y + 92), cap, font=cap_f, fill=INK_MUTED)

    # Team line
    team_f = FBL(28)
    names = "Tidiane Konaté    ·    Sidi Mohamed Sall    ·    Ahmed Essalem    ·    Saad Ibrahim Houssein"
    # auto-fit
    names_f = team_f
    while _text_w(d, names, names_f) > W - 120 and names_f.size > 18:
        names_f = FBL(names_f.size - 2)
    tw = _text_w(d, names, names_f)
    d.text(((W - tw) // 2, H - 165), names, font=names_f, fill=WHITE)
    sub_f = FL(22)
    sub = "OSTIM Technical University  ·  Computer Engineering  ·  Graduation Project 2026"
    tw = _text_w(d, sub, sub_f)
    d.text(((W - tw) // 2, H - 115), sub, font=sub_f, fill=INK_MUTED)
    # advisor
    adv_f = FS(22)
    adv = "Advisor : Assist. Prof. Dr. Yücel TEKİN"
    tw = _text_w(d, adv, adv_f)
    d.text(((W - tw) // 2, H - 75), adv, font=adv_f, fill=BLUE_GLOW)


def build():
    print(f"[1/4] Canvas {W}×{H}px (A5 @ 300 DPI) ...")

    print("[2/4] Recto (front) — full-bleed cosmic background ...")
    recto = make_cosmic_background(seed=42).copy()
    draw_recto(recto)

    print("[3/4] Verso (back) — feature grid ...")
    verso = make_cosmic_background(seed=17).copy()
    draw_verso(verso)

    print("[4/4] Exporting PNG + 2-page PDF ...")
    recto.convert("RGB").save(OUTPUT_RECTO, "PNG", optimize=True,
                              dpi=(DPI, DPI))
    verso.convert("RGB").save(OUTPUT_VERSO, "PNG", optimize=True,
                              dpi=(DPI, DPI))
    # 2-page PDF
    recto_rgb = recto.convert("RGB")
    verso_rgb = verso.convert("RGB")
    recto_rgb.save(OUTPUT_PDF, "PDF", resolution=DPI,
                   save_all=True, append_images=[verso_rgb])

    sz_r = OUTPUT_RECTO.stat().st_size // 1024
    sz_v = OUTPUT_VERSO.stat().st_size // 1024
    sz_p = OUTPUT_PDF.stat().st_size // 1024
    print(f"\n[OK] Flyer ready:")
    print(f"     Recto PNG: {OUTPUT_RECTO.name}  ({sz_r} KB)")
    print(f"     Verso PNG: {OUTPUT_VERSO.name}  ({sz_v} KB)")
    print(f"     PDF (2 pages): {OUTPUT_PDF.name}  ({sz_p} KB)")
    print(f"     Print size : 148 × 210 mm (A5 portrait)")


if __name__ == "__main__":
    build()
