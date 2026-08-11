#!/usr/bin/env python3
"""
AstroBot — 80–90 s French promo video generator.

Visual: cinematic 1920×1080 with subtle Ken-Burns zoom on every screenshot,
fade-and-slide-in title/kicker animations, animated radial glows and a
final CTA with QR + URL.

Audio: edge-tts neural French narration (DeniseNeural — natural female voice)
mixed over the user-supplied background track at presentation/promo_music.mp3
(ducked to about 18 % under the voice).

Output: presentation/AstroBot_Promo_FR.mp4

Run:    python presentation/build_promo_video_fr.py
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import edge_tts

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)
from moviepy.audio.fx import MultiplyVolume, AudioFadeIn, AudioFadeOut
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, FadeIn, FadeOut, Resize


# ── Paths & constants ────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS = ROOT / "assets" / "screenshots"
ASSETS = ROOT / "deliverables" / "report" / "assets"
LOGO_PATH = ASSETS / "astrobot_logo.png"
TEAM_PHOTO = ROOT / "assets" / "team" / "Photo de groupe.jpg"
MUSIC_PATH = Path(__file__).resolve().parent / "promo_music.mp3"
OUTPUT = Path(__file__).resolve().parent / "AstroBot_Promo_FR.mp4"

W, H = 1920, 1080
FPS = 30

NAVY = (15, 26, 53)
NAVY_DEEP = (8, 14, 32)
PURPLE = (124, 58, 191)
PURPLE_GLOW = (155, 95, 220)
CYAN = (8, 145, 178)
CYAN_GLOW = (60, 190, 220)
GOLD = (217, 119, 6)
GREEN = (22, 163, 74)
PINK = (236, 72, 153)
WHITE = (255, 255, 255)
INK_SOFT = (180, 192, 220)
INK_MUTED = (130, 145, 175)

FDIR = Path("C:/Windows/Fonts")
def F(name, size):
    try: return ImageFont.truetype(str(FDIR / name), size)
    except OSError: return ImageFont.load_default()
def FB(s):  return F("segoeuib.ttf", s)   # bold
def FBL(s): return F("seguibl.ttf", s)    # black
def FS(s):  return F("seguisb.ttf", s)    # semibold
def FR(s):  return F("segoeui.ttf", s)    # regular
def FL(s):  return F("segoeuil.ttf", s)   # light


# ── Background composition helpers ───────────────────────────────
def _gradient(top, bottom):
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / (H - 1)
        for c in range(3):
            arr[y, :, c] = int(top[c] * (1 - t) + bottom[c] * t)
    return Image.fromarray(arr)


def _glow(center, color, radius, alpha=110):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    for r, a_mult in [(1.0, 0.0), (0.7, 0.30), (0.45, 0.60), (0.25, 1.0)]:
        r0 = int(radius * r)
        a = int(alpha * a_mult)
        d.ellipse((cx - r0, cy - r0, cx + r0, cy + r0),
                  fill=(color[0], color[1], color[2], a))
    return layer.filter(ImageFilter.GaussianBlur(70))


def make_bg(*, accent=PURPLE, side="center"):
    if side == "right":
        gx = int(W * 0.7); ax = (int(W * 0.25), int(H * 0.85))
    elif side == "left":
        gx = int(W * 0.3); ax = (int(W * 0.75), int(H * 0.85))
    else:
        gx = W // 2; ax = (int(W * 0.85), int(H * 0.85))
    bg = _gradient(NAVY, NAVY_DEEP).convert("RGBA")
    bg = Image.alpha_composite(bg, _glow((gx, int(H * 0.35)), accent, 850, 130))
    bg = Image.alpha_composite(bg, _glow(ax, CYAN_GLOW, 600, 80))
    # subtle dotted grid (very faint) — adds a tech feel
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for gy in range(0, H, 64):
        for gx2 in range(0, W, 64):
            gd.ellipse((gx2, gy, gx2 + 1, gy + 1), fill=(255, 255, 255, 22))
    bg = Image.alpha_composite(bg, grid)
    return bg


def _draw_text(d, xy, text, font, fill, *, shadow=True, shadow_offset=(3, 3),
               shadow_color=(0, 0, 0, 150)):
    x, y = xy
    if shadow:
        d.text((x + shadow_offset[0], y + shadow_offset[1]), text,
               font=font, fill=shadow_color[:3] + (shadow_color[3] // 2,))
    d.text((x, y), text, font=font, fill=fill)


def _text_centered(d, text, font, color, y, *, shadow=True):
    bb = d.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    _draw_text(d, ((W - tw) // 2, y), text, font, color, shadow=shadow)
    return bb[3] - bb[1]


def _fit_screenshot(path: Path, box_w, box_h, *, radius=22,
                    border_color=None, border_w=3):
    src = Image.open(path).convert("RGB")
    iw, ih = src.size
    s = min(box_w / iw, box_h / ih)
    nw, nh = int(iw * s), int(ih * s)
    src = src.resize((nw, nh), Image.LANCZOS)
    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, nw, nh), radius=radius, fill=255)
    out = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    if border_color:
        bd = ImageDraw.Draw(out)
        bd.rounded_rectangle((0, 0, nw - 1, nh - 1), radius=radius,
                             outline=border_color, width=border_w)
    return out


def _drop_shadow(rgba: Image.Image, blur=28, offset=(0, 16),
                 color=(0, 0, 0, 170)):
    pad = blur + max(abs(offset[0]), abs(offset[1])) + 8
    w, h = rgba.size
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle(
        (pad + offset[0], pad + offset[1],
         pad + w + offset[0], pad + h + offset[1]),
        fill=color)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.alpha_composite(rgba, (pad, pad))
    return canvas, pad


# ── Scene background renderers (returns RGB PIL.Image) ───────────
def bg_logo(t_in_scene=None):
    bg = make_bg(accent=PURPLE, side="center")
    d = ImageDraw.Draw(bg)
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            lw = 340
            lh = int(logo.size[1] * lw / logo.size[0])
            bg.alpha_composite(logo, ((W - lw) // 2, H // 2 - lh - 60))
        except Exception:
            pass
    _text_centered(d, "AstroBot", FBL(200), WHITE, H // 2 + 60)
    _text_centered(d, "Un assistant conversationnel intelligent",
                   FL(42), INK_SOFT, H // 2 + 320)
    return bg.convert("RGB")


def bg_tagline():
    bg = make_bg(accent=PURPLE, side="left")
    d = ImageDraw.Draw(bg)
    _text_centered(d, "Une IA qui fait",       FBL(130), WHITE, 320)
    _text_centered(d, "réellement la différence.", FBL(120), PURPLE_GLOW, 470)
    _text_centered(d,
                   "Douze fonctionnalités d'IA  ·  Multimodale  ·  Prête pour la production",
                   FL(34), INK_SOFT, 720)
    return bg.convert("RGB")


def bg_feature(*, kicker, accent, side):
    """Background WITHOUT title or screenshot (those are animated overlays)."""
    bg = make_bg(accent=accent, side=("right" if side == "right" else "left"))
    d = ImageDraw.Draw(bg)
    text_x = 110 if side == "right" else 1000
    # kicker
    d.rectangle((text_x, 250, text_x + 80, 258), fill=accent)
    d.text((text_x + 100, 226), kicker, font=FBL(36), fill=accent)
    return bg.convert("RGB")


def bg_voice():
    bg = make_bg(accent=CYAN, side="center")
    d = ImageDraw.Draw(bg)
    _text_centered(d, "Parlez.",         FBL(170), WHITE, 280)
    _text_centered(d, "On vous écoute.", FBL(150), CYAN_GLOW, 460)
    _text_centered(d, "Transcription vocale propulsée par Groq Whisper",
                   FL(38), INK_SOFT, 700)
    # static waveform decoration
    cx = W // 2; cy = 870
    bar_w = 8; gap = 14
    heights = [30, 60, 110, 80, 140, 95, 50, 120, 70, 100,
               60, 130, 90, 45, 110, 75, 140, 80, 110, 55]
    n = len(heights)
    total_w = n * (bar_w + gap) - gap
    sx = cx - total_w // 2
    for i, hh in enumerate(heights):
        x = sx + i * (bar_w + gap)
        d.rounded_rectangle((x, cy - hh // 2, x + bar_w, cy + hh // 2),
                            radius=4, fill=CYAN_GLOW)
    return bg.convert("RGB")


def bg_stats():
    bg = make_bg(accent=GOLD, side="center")
    d = ImageDraw.Draw(bg)
    _text_centered(d, "PRÊT POUR LA PRODUCTION", FBL(44), GOLD, 230)
    stats = [
        ("12",       "fonctionnalités\nd'IA",   PURPLE_GLOW),
        ("66",       "tests\nd'intégration",    (110, 200, 130)),
        ("EN LIGNE", "en ce moment",            CYAN_GLOW),
    ]
    col_w = W // 3
    s_f = FS(38)
    max_num_w = col_w - 60          # leave breathing room inside the column
    for i, (num, lbl, color) in enumerate(stats):
        cx = col_w * i + col_w // 2
        # autoscale numeric size so it fits the column
        size = 230
        while size > 70:
            n_f = FBL(size)
            bb = d.textbbox((0, 0), num, font=n_f)
            if bb[2] - bb[0] <= max_num_w:
                break
            size -= 8
        bb = d.textbbox((0, 0), num, font=n_f)
        nw, nh = bb[2] - bb[0], bb[3] - bb[1]
        # vertical-align: number baseline anchored around y≈500
        ny = 500 - nh // 2
        d.text((cx - nw // 2 + 4, ny + 4), num, font=n_f, fill=(0, 0, 0, 110))
        d.text((cx - nw // 2, ny), num, font=n_f, fill=color)
        for j, line in enumerate(lbl.split("\n")):
            bb2 = d.textbbox((0, 0), line, font=s_f)
            tw = bb2[2] - bb2[0]
            d.text((cx - tw // 2, 700 + j * 50), line, font=s_f,
                   fill=INK_SOFT)
    return bg.convert("RGB")


def bg_cta():
    bg = make_bg(accent=PURPLE, side="center")
    d = ImageDraw.Draw(bg)
    _text_centered(d, "ESSAYEZ ASTROBOT MAINTENANT", FBL(46), PURPLE_GLOW, 130)
    _text_centered(d, "76.13.62.195:3000",  FBL(140), WHITE, 230)
    _text_centered(d, "Ouvrez-le dans un navigateur. Sans installation. C'est gratuit.",
                   FL(36), INK_SOFT, 430)
    _text_centered(d, "github.com/tkonate788/astrobot",
                   FS(36), CYAN_GLOW, 540)
    _text_centered(
        d,
        "Tidiane Konaté  ·  Sidi Mohamed Sall  ·  Ahmed Essalem  ·  Saad Ibrahim Houssein",
        FL(30), INK_SOFT, 940)
    _text_centered(
        d, "Université Technique d'OSTIM  ·  Projet de Fin d'Études 2026",
        FL(28), INK_MUTED, 990)
    try:
        import qrcode
        qr = qrcode.QRCode(version=4,
                           error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=8, border=2)
        qr.add_data("http://76.13.62.195:3000")
        qr.make(fit=True)
        qi = qr.make_image(fill_color="white",
                           back_color=NAVY_DEEP).convert("RGBA")
        qw = 240
        qi = qi.resize((qw, qw), Image.LANCZOS)
        bg.alpha_composite(qi, ((W - qw) // 2, 640))
    except Exception:
        pass
    return bg.convert("RGB")


# ── Title / bullets overlay (for animated reveal) ────────────────
def render_title_overlay(*, title, bullets, accent, side):
    """A transparent layer that contains the big title + bullets. Animated separately.

    French titles are typically longer than English, so the title font is
    auto-shrunk to fit the available column width."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    text_x = 110 if side == "right" else 1000
    avail_w = (W - text_x - 60) if side == "right" else (W - text_x - 60)
    # Pick the largest title font size for which every line fits the column
    size = 110
    while size > 60:
        tf = FBL(size)
        widths = [d.textbbox((0, 0), ln, font=tf)[2] for ln in title.split("\n")]
        if max(widths) <= avail_w:
            break
        size -= 6
    line_h = int(size * 1.12)
    y = 320
    for ln in title.split("\n"):
        _draw_text(d, (text_x, y), ln, tf, WHITE, shadow=True,
                   shadow_offset=(5, 5), shadow_color=(0, 0, 0, 200))
        y += line_h
    y = max(y + 30, 620)
    bf = FS(38)
    for b in bullets:
        d.ellipse((text_x, y + 16, text_x + 16, y + 32), fill=accent)
        d.text((text_x + 38, y), b, font=bf, fill=INK_SOFT)
        y += 64
    return img


# ── ImageClip helper from PIL ────────────────────────────────────
def pil_clip(im: Image.Image, duration: float) -> ImageClip:
    return ImageClip(np.array(im.convert("RGB"))).with_duration(duration).with_fps(FPS)


def pil_clip_rgba(im: Image.Image, duration: float) -> ImageClip:
    return (ImageClip(np.array(im.convert("RGBA")), is_mask=False, transparent=True)
            .with_duration(duration)
            .with_fps(FPS))


# ── Scene builders (return CompositeVideoClip of the right duration) ──
def scene_logo(duration: float):
    bg = pil_clip(bg_logo(), duration)
    return CompositeVideoClip([bg], size=(W, H)).with_duration(duration)


def scene_tagline(duration: float):
    bg = pil_clip(bg_tagline(), duration)
    return CompositeVideoClip([bg], size=(W, H)).with_duration(duration)


def scene_feature(*, duration, title, kicker, bullets, screenshot, accent,
                  side):
    """Background + Ken-Burns screenshot + fade-and-slide title overlay."""
    # 1) Background (kicker baked in)
    bg = pil_clip(bg_feature(kicker=kicker, accent=accent, side=side),
                  duration)

    layers = [bg]

    # 2) Screenshot with Ken-Burns zoom
    if screenshot.exists():
        if side == "right":
            box_x, box_w, box_h = 960, 880, 720
        else:
            box_x, box_w, box_h = 60, 820, 720
        box_y = 200
        shot = _fit_screenshot(screenshot, box_w, box_h, radius=22,
                               border_color=accent, border_w=3)
        shadowed, pad = _drop_shadow(shot, blur=32, offset=(0, 18),
                                     color=(0, 0, 0, 180))
        sw, sh = shadowed.size
        cx = box_x + (box_w - shot.size[0]) // 2 - pad
        cy = box_y + (box_h - shot.size[1]) // 2 - pad
        shot_clip = pil_clip_rgba(shadowed, duration).with_position(
            (cx, cy))
        # subtle Ken-Burns: scale from 1.00 to 1.06 over scene
        z0, z1 = 1.0, 1.06
        shot_clip = shot_clip.with_effects(
            [Resize(lambda t: z0 + (z1 - z0) * (t / duration))])
        # fade-in/out
        shot_clip = shot_clip.with_effects(
            [CrossFadeIn(0.5), CrossFadeOut(0.4)])
        layers.append(shot_clip)

    # 3) Title + bullets overlay with fade-in slide-up
    overlay = render_title_overlay(title=title, bullets=bullets, accent=accent,
                                   side=side)
    # slide up: position starts +35px below final and rises in 0.5s
    overlay_clip = pil_clip_rgba(overlay, duration).with_position(
        lambda t: (0, int(35 * max(0.0, 1.0 - t / 0.55))))
    overlay_clip = overlay_clip.with_effects(
        [CrossFadeIn(0.55), CrossFadeOut(0.35)])
    layers.append(overlay_clip)

    return CompositeVideoClip(layers, size=(W, H)).with_duration(duration)


def scene_voice(duration: float):
    bg = pil_clip(bg_voice(), duration)
    return CompositeVideoClip([bg], size=(W, H)).with_duration(duration)


def scene_stats(duration: float):
    bg = pil_clip(bg_stats(), duration)
    return CompositeVideoClip([bg], size=(W, H)).with_duration(duration)


def scene_cta(duration: float):
    bg = pil_clip(bg_cta(), duration)
    return CompositeVideoClip([bg], size=(W, H)).with_duration(duration)


def bg_team_static():
    """Background + left-side text (everything except the animated photo)."""
    bg = make_bg(accent=PURPLE, side="left")
    d = ImageDraw.Draw(bg)
    text_x = 90
    # kicker
    d.rectangle((text_x, 200, text_x + 80, 208), fill=PURPLE_GLOW)
    d.text((text_x + 100, 176), "L'ÉQUIPE", font=FBL(36), fill=PURPLE_GLOW)
    # Big "thank you"
    y = 280
    for ln in ["Merci,",
               "de la part",
               "de nous quatre."]:
        _draw_text(d, (text_x, y), ln, FBL(110), WHITE,
                   shadow=True, shadow_offset=(5, 5),
                   shadow_color=(0, 0, 0, 200))
        y += 130
    # Names
    y += 30
    names = [
        ("Tidiane Konaté",        "Architecture · Backend · Déploiement"),
        ("Sidi Mohamed Sall",     "Vision · Produit · UX"),
        ("Ahmed Essalem",         "IA · LLM · Multimodal"),
        ("Saad Ibrahim Houssein", "QA · Frontend · Tests"),
    ]
    for nm, role in names:
        d.ellipse((text_x, y + 14, text_x + 14, y + 28), fill=PURPLE_GLOW)
        d.text((text_x + 32, y), nm, font=FB(34), fill=WHITE)
        d.text((text_x + 32, y + 42), role, font=FL(24), fill=INK_MUTED)
        y += 84
    return bg.convert("RGB")


def _fit_team_photo(path: Path, box_w, box_h, *, radius=26,
                    border_color=PURPLE_GLOW, border_w=4):
    return _fit_screenshot(path, box_w, box_h, radius=radius,
                           border_color=border_color, border_w=border_w)


def scene_team(duration: float):
    """Final closing scene with the group photo on the right + Ken-Burns zoom."""
    bg = pil_clip(bg_team_static(), duration)
    layers = [bg]
    if TEAM_PHOTO.exists():
        # The photo is 1200x1600 portrait; show it in a 660 wide, 880 tall box on the right
        box_x, box_y = 1180, 100
        box_w, box_h = 680, 880
        photo = _fit_team_photo(TEAM_PHOTO, box_w, box_h, radius=26,
                                border_color=PURPLE_GLOW, border_w=4)
        shadowed, pad = _drop_shadow(photo, blur=38, offset=(0, 22),
                                     color=(0, 0, 0, 200))
        cx = box_x + (box_w - photo.size[0]) // 2 - pad
        cy = box_y + (box_h - photo.size[1]) // 2 - pad
        photo_clip = pil_clip_rgba(shadowed, duration).with_position(
            (cx, cy))
        z0, z1 = 1.0, 1.07
        photo_clip = photo_clip.with_effects(
            [Resize(lambda t: z0 + (z1 - z0) * (t / max(duration, 0.01)))])
        photo_clip = photo_clip.with_effects(
            [CrossFadeIn(0.7), CrossFadeOut(0.5)])
        layers.append(photo_clip)
    return CompositeVideoClip(layers, size=(W, H)).with_duration(duration)


# ── Narration script & TTS ───────────────────────────────────────
# Per-scene narration with custom prosody.
# `rate`  — positive % speeds up, negative % slows down
# `pitch` — Hz offset (positive = brighter/more energetic, negative = deeper)
NARRATION = [
    ("logo",
     "AstroBot.",
     {"rate": "-8%",  "pitch": "+0Hz"}),
    ("tagline",
     "Un assistant conversationnel intelligent, "
     "développé par quatre ingénieurs à l'Université Technique d'OSTIM.",
     {"rate": "+8%",  "pitch": "+3Hz"}),
    ("chat",
     "Tout commence par une conversation. Sept personnages. "
     "Le Markdown, les mathématiques et le code, "
     "rendus en direct dans une seule bulle.",
     {"rate": "+10%", "pitch": "+4Hz"}),
    ("image",
     "Générez des images époustouflantes en un clin d'œil avec FLUX. "
     "Ou éditez une photo en une seule phrase.",
     {"rate": "+10%", "pitch": "+4Hz"}),
    ("rag",
     "Déposez n'importe quel P D F. Posez-lui vos questions. "
     "AstroBot lit le document en mode recherche augmentée, "
     "ou en mode notebook pour les fichiers plus courts.",
     {"rate": "+6%",  "pitch": "+3Hz"}),
    ("voice",
     "Parlez. On vous écoute. "
     "Whisper transcrit votre voix en quelques secondes.",
     {"rate": "+8%",  "pitch": "+4Hz"}),
    ("ocr",
     "Déposez une image. AstroBot la lit grâce à l'O C R, "
     "la décrit avec une IA de vision, "
     "et utilise ces deux signaux dans sa réponse.",
     {"rate": "+8%",  "pitch": "+3Hz"}),
    ("admin",
     "En coulisses, un tableau de bord administrateur épuré "
     "suit chaque utilisateur, chaque session, et chaque action.",
     {"rate": "+6%",  "pitch": "+3Hz"}),
    ("stats",
     "Douze fonctionnalités d'I A. "
     "Soixante-six tests d'intégration, tous au vert. "
     "En ligne, en ce moment même.",
     {"rate": "+10%", "pitch": "+5Hz"}),
    ("cta",
     "Essayez AstroBot dès aujourd'hui. "
     "Ouvrez soixante-seize point treize, point soixante-deux, "
     "point cent-quatre-vingt-quinze, "
     "deux-points trois mille, "
     "dans n'importe quel navigateur. C'est gratuit, et ça fonctionne.",
     {"rate": "+3%",  "pitch": "+2Hz"}),
    ("team",
     "De la part de nous quatre — Tidiane, Sidi, Ahmed et Saad — "
     "merci d'avoir regardé.",
     {"rate": "-2%",  "pitch": "+1Hz"}),
]


async def _generate_tts(out_dir: Path,
                        voice: str = "fr-FR-VivienneMultilingualNeural"):
    """One MP3 per narration line — each with its own rate / pitch for rhythm."""
    out_files = []
    for key, text, opts in NARRATION:
        mp3 = out_dir / f"{key}.mp3"
        comm = edge_tts.Communicate(
            text,
            voice=voice,
            rate=opts.get("rate", "+5%"),
            pitch=opts.get("pitch", "+0Hz"),
        )
        await comm.save(str(mp3))
        out_files.append((key, mp3))
        print(f"      • TTS {key:>8}  rate={opts['rate']:>5}  pitch={opts['pitch']:>5}  "
              f"({mp3.stat().st_size // 1024} KB)")
    return out_files


# ── Main pipeline ────────────────────────────────────────────────
def main():
    tmp = Path(tempfile.mkdtemp(prefix="astrobot_promo_"))

    # 1) Generate narration with edge-tts (async)
    print("[1/4] Generating neural TTS narration "
          "(Microsoft VivienneMultilingualNeural — fr-FR, per-scene prosody) ...")
    tts_dir = tmp / "tts"
    tts_dir.mkdir()
    tts_files = asyncio.run(_generate_tts(tts_dir))

    # 2) Measure each TTS duration and pick scene lengths
    print("[2/4] Measuring narration durations ...")
    BUFFER_PRE = 0.30      # silence before narration starts within scene
    BUFFER_POST = 1.05     # silence after narration ends within scene
    XFADE = 0.45           # crossfade between scenes (seconds)
    durations = {}
    audio_clips = {}
    for key, mp3 in tts_files:
        ac = AudioFileClip(str(mp3))
        ad = ac.duration
        durations[key] = ad
        audio_clips[key] = ac
        print(f"      • {key:>8}: {ad:.2f}s")

    # Scene durations (per key)
    scene_dur = {k: durations[k] + BUFFER_PRE + BUFFER_POST
                 for k in durations}

    # 3) Build per-scene visual clips
    print("[3/4] Building animated scenes ...")
    builders = {
        "logo":    lambda d: scene_logo(d),
        "tagline": lambda d: scene_tagline(d),
        "chat":    lambda d: scene_feature(duration=d,
            title="Conversation\nIntelligente",
            kicker="01 · CONVERSATION",
            bullets=["7 personnages sélectionnables",
                     "Markdown · KaTeX · coloration de code",
                     "Affichage en flux continu"],
            screenshot=SCREENSHOTS / "6.png",
            accent=PURPLE_GLOW, side="right"),
        "image":   lambda d: scene_feature(duration=d,
            title="Génération\nd'Images par IA",
            kicker="02 · MULTIMODAL",
            bullets=["FLUX-1 via HuggingFace",
                     "Édition image-vers-image",
                     "Bascule automatique vers fal-ai"],
            screenshot=SCREENSHOTS / "13.png",
            accent=CYAN_GLOW, side="left"),
        "rag":     lambda d: scene_feature(duration=d,
            title="Parlez à\nvos PDF",
            kicker="03 · RECHERCHE",
            bullets=["RAG avec embeddings MiniLM",
                     "Mode notebook pour les docs courts",
                     "Citations par fragment"],
            screenshot=SCREENSHOTS / "8.png",
            accent=GOLD, side="right"),
        "voice":   lambda d: scene_voice(d),
        "ocr":     lambda d: scene_feature(duration=d,
            title="Lit Toutes\nles Images",
            kicker="04 · VISION",
            bullets=["OCR en FR et EN (Tesseract)",
                     "Légendage d'images avec BLIP",
                     "Injecté automatiquement dans le prompt"],
            screenshot=SCREENSHOTS / "11.png",
            accent=(110, 200, 130), side="left"),
        "admin":   lambda d: scene_feature(duration=d,
            title="Tableau d'\nAdministration",
            kicker="05 · ADMINISTRATION",
            bullets=["KPI et graphiques en temps réel",
                     "Recherche · suspension · suppression",
                     "Audit complet des conversations"],
            screenshot=SCREENSHOTS / "16a.png",
            accent=PURPLE_GLOW, side="right"),
        "stats":   lambda d: scene_stats(d),
        "cta":     lambda d: scene_cta(d),
        "team":    lambda d: scene_team(d),
    }

    scene_clips = []
    for key, *_ in NARRATION:
        d = scene_dur[key]
        clip = builders[key](d)
        # add fade in/out for the whole scene
        clip = clip.with_effects([FadeIn(0.35), FadeOut(0.35)])
        scene_clips.append(clip)
        print(f"      • {key:>8}: scene = {d:.2f}s")

    # Concatenate with crossfade overlap
    # Compose method allows overlapping/crossfade
    for i, c in enumerate(scene_clips):
        if i > 0:
            scene_clips[i] = c.with_effects([CrossFadeIn(XFADE)])
    # When using crossfadein, the concatenation must allow overlap:
    video = concatenate_videoclips(scene_clips, method="compose",
                                   padding=-XFADE)

    total_v = video.duration
    print(f"      total video duration: {total_v:.2f}s")

    # 4) Build audio: narration timed + music ducked
    print("[4/4] Mixing audio (narration + ducked background music) ...")
    audio_segments = []
    cursor = 0.0
    for key, *_ in NARRATION:
        # Narration plays slightly after scene start (BUFFER_PRE)
        ac = audio_clips[key].with_start(cursor + BUFFER_PRE)
        audio_segments.append(ac)
        # advance cursor by scene duration MINUS overlap with next scene
        # (every scene after the first overlaps by XFADE)
        cursor += scene_dur[key] - (XFADE if key != "team" else 0)

    # Music
    music = AudioFileClip(str(MUSIC_PATH))
    # take from start, trim to video length, fade in/out
    music = music.with_duration(total_v).with_effects([
        MultiplyVolume(0.16),    # ducked under the voice
        AudioFadeIn(1.2),
        AudioFadeOut(2.5),
    ])
    # Composite audio
    final_audio = CompositeAudioClip([music, *audio_segments])
    final = video.with_audio(final_audio)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(OUTPUT),
        codec="libx264", audio_codec="aac",
        fps=FPS, bitrate="8000k",
        preset="medium", threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        temp_audiofile=str(tmp / "_aud.m4a"),
        remove_temp=True,
        logger=None,
    )

    print(f"\n[OK] Video written: {OUTPUT}")
    print(f"     Duration: {total_v:.2f}s   ({len(scene_clips)} scenes)")

    # cleanup
    try:
        for k, ac in audio_clips.items():
            ac.close()
        music.close()
        video.close()
        final.close()
    except Exception:
        pass
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
