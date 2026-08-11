#!/usr/bin/env python3
"""
AstroBot — Graduation Project Presentation Builder.

Generates a polished 15-minute, 4-presenter PowerPoint deck on top of the
OSTIM Technical University template stored in `Powerpoint template/`.

Run:
    python presentation/build_presentation.py

Output:
    presentation/AstroBot_Presentation.pptx
"""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

from lxml import etree

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ─── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = ROOT / "deliverables" / "references" / "Powerpoint template" / "Presentation template.pptx"
SCREENS = ROOT / "assets" / "screenshots"
ASSETS = ROOT / "deliverables" / "report" / "assets"
DEV_PHOTOS = ROOT / "assets" / "team"
ADVISOR_PHOTO = ROOT / "assets" / "advisor" / "Assist. Prof. Yücel TEKİN.jpg"
OUTPUT = Path(__file__).resolve().parent / "AstroBot_Presentation.pptx"

# ─── Brand palette ──────────────────────────────────────────────────────
NAVY = RGBColor(0x0F, 0x1A, 0x35)          # deep space
PURPLE = RGBColor(0x7B, 0x2C, 0xBF)        # primary accent
CYAN = RGBColor(0x06, 0xB6, 0xD4)          # secondary accent
GOLD = RGBColor(0xF9, 0xC9, 0x4D)          # highlight
LIGHT = RGBColor(0xF6, 0xF7, 0xFB)         # light card
INK = RGBColor(0x14, 0x1B, 0x2D)           # body text
INK_SOFT = RGBColor(0x40, 0x4A, 0x66)      # secondary text
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN_OK = RGBColor(0x16, 0xA3, 0x4A)


# ─── Layout helpers ─────────────────────────────────────────────────────
def find_layout(prs: Presentation, master_idx: int, name_contains: str):
    for layout in prs.slide_masters[master_idx].slide_layouts:
        if name_contains.lower() in layout.name.lower():
            return layout
    raise KeyError(f"layout '{name_contains}' not in master {master_idx}")


def get_placeholder(slide, idx: int):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def set_placeholder_text(slide, idx: int, text: str, *, size: int | None = None,
                         bold: bool | None = None, color: RGBColor | None = None,
                         align: PP_ALIGN | None = None):
    ph = get_placeholder(slide, idx)
    if ph is None:
        return None
    tf = ph.text_frame
    tf.clear()
    lines = text.split("\n")
    p = tf.paragraphs[0]
    if align is not None:
        p.alignment = align
    run = p.add_run()
    run.text = lines[0]
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    for line in lines[1:]:
        p2 = tf.add_paragraph()
        if align is not None:
            p2.alignment = align
        r2 = p2.add_run()
        r2.text = line
        if size is not None:
            r2.font.size = Pt(size)
        if bold is not None:
            r2.font.bold = bold
        if color is not None:
            r2.font.color.rgb = color
    return ph


# ─── Slide manipulation (XML) ───────────────────────────────────────────
def delete_slide(prs: Presentation, idx: int):
    """Remove the slide at position `idx` from the presentation."""
    sld_id_lst = prs.slides._sldIdLst
    sld_ids = list(sld_id_lst)
    rId = sld_ids[idx].get(qn("r:id"))
    prs.part.drop_rel(rId)
    sld_id_lst.remove(sld_ids[idx])


def move_slide(prs: Presentation, src_idx: int, dst_idx: int):
    sld_id_lst = prs.slides._sldIdLst
    sld_ids = list(sld_id_lst)
    sld = sld_ids[src_idx]
    sld_id_lst.remove(sld)
    new_ids = list(sld_id_lst)
    if dst_idx >= len(new_ids):
        sld_id_lst.append(sld)
    else:
        sld_id_lst.insert(list(sld_id_lst).index(new_ids[dst_idx]), sld)


# ─── Slide transitions (Morph + fallbacks) ──────────────────────────────
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P159_NS = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"


def _strip_existing_transition(sld_root):
    for tag in ("p:transition", "mc:AlternateContent"):
        prefix, local = tag.split(":")
        ns_map = {"p": P_NS, "mc": MC_NS}
        for el in sld_root.findall(f"{{{ns_map[prefix]}}}{local}"):
            sld_root.remove(el)


def add_morph_transition(slide, *, speed: str = "med", option: str = "byObject"):
    """Inject a Morph transition (PowerPoint 2016+) with a Fade fallback."""
    sld_root = slide._element
    _strip_existing_transition(sld_root)

    # Build the AlternateContent block
    xml = (
        f'<mc:AlternateContent xmlns:mc="{MC_NS}">'
        f'  <mc:Choice xmlns:p="{P_NS}" xmlns:p159="{P159_NS}" Requires="p159">'
        f'    <p:transition spd="{speed}">'
        f'      <p159:morph option="{option}"/>'
        f'    </p:transition>'
        f'  </mc:Choice>'
        f'  <mc:Fallback>'
        f'    <p:transition xmlns:p="{P_NS}" spd="{speed}">'
        f'      <p:fade/>'
        f'    </p:transition>'
        f'  </mc:Fallback>'
        f'</mc:AlternateContent>'
    )
    el = etree.fromstring(xml)
    sld_root.append(el)


def add_simple_transition(slide, kind: str = "push", *, speed: str = "med",
                          direction: str | None = None):
    """Inject a simple non-morph transition (push, cover, fade, zoom...)."""
    sld_root = slide._element
    _strip_existing_transition(sld_root)
    dir_attr = f' dir="{direction}"' if direction else ''
    xml = (
        f'<p:transition xmlns:p="{P_NS}" spd="{speed}">'
        f'  <p:{kind}{dir_attr}/>'
        f'</p:transition>'
    )
    el = etree.fromstring(xml)
    sld_root.append(el)


# ─── Drawing helpers ────────────────────────────────────────────────────
def add_textbox(slide, left, top, width, height, *, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    return tb


def style_run(run, *, size=14, bold=False, italic=False,
              color: RGBColor = INK, font="Calibri"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def add_paragraph(tf, text, *, size=14, bold=False, italic=False,
                  color: RGBColor = INK, font="Calibri",
                  align=PP_ALIGN.LEFT, space_after=4, level=0, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.level = level
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    style_run(run, size=size, bold=bold, italic=italic, color=color, font=font)
    return p


def add_card(slide, left, top, width, height, *,
             fill: RGBColor = LIGHT, line: RGBColor | None = None,
             corner=0.10, shadow=False):
    """Rounded-rectangle card used as a colored background block."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shp.adjustments[0] = corner
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    if not shadow:
        # remove default shadow
        sp = shp.shadow
        sp.inherit = False
    return shp


def add_picture_safe(slide, path: Path, left, top, width=None, height=None):
    if not path.exists():
        print(f"  WARN: missing picture {path}")
        return None
    if width and height:
        return slide.shapes.add_picture(str(path), left, top, width=width, height=height)
    if width:
        return slide.shapes.add_picture(str(path), left, top, width=width)
    if height:
        return slide.shapes.add_picture(str(path), left, top, height=height)
    return slide.shapes.add_picture(str(path), left, top)


def add_picture_in_card(slide, path: Path, left, top, width, height,
                        *, frame: RGBColor = NAVY, frame_pt=1.5):
    """Insert a picture sized to fit a rectangle, centered, with a thin frame."""
    if not path.exists():
        print(f"  WARN: missing picture {path}")
        return None
    pic = slide.shapes.add_picture(str(path), left, top, width=width, height=height)
    # Add frame outline on top of picture
    pic.line.color.rgb = frame
    pic.line.width = Pt(frame_pt)
    return pic


def add_chip(slide, text, left, top, width, *,
             fill: RGBColor = PURPLE, text_color: RGBColor = WHITE,
             size=11, bold=True, height=Inches(0.32)):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shp.adjustments[0] = 0.5
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    tf = shp.text_frame
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    style_run(run, size=size, bold=bold, color=text_color)
    return shp


def add_section_header(slide, title: str, accent: RGBColor = PURPLE, *,
                       subtitle: str | None = None):
    """Adds a title header at top-right of a content slide.

    The template's master 2 has the OSTIM logo pinned at
    (0.30",0.24") size (1.89",0.68"), so we start our header at
    X=2.55" — the same X the layout's title placeholder uses."""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(2.30), Inches(0.32),
                                 Inches(0.16), Inches(0.55))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()

    tb = add_textbox(slide, Inches(2.55), Inches(0.22),
                     Inches(9.45), Inches(0.85), anchor=MSO_ANCHOR.TOP)
    add_paragraph(tb.text_frame, title, size=24, bold=True, color=NAVY,
                  first=True, space_after=1)
    if subtitle:
        add_paragraph(tb.text_frame, subtitle, size=11, italic=True,
                      color=INK_SOFT)


def add_footer_bar(slide, presenter: str | None = None,
                   page_label: str | None = None):
    """Slim footer with project tag + presenter + slide tag."""
    # Thin bottom rule
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(0.45), Inches(7.10),
                                  Inches(12.45), Emu(9525))
    rule.fill.solid()
    rule.fill.fore_color.rgb = PURPLE
    rule.line.fill.background()

    tb_left = add_textbox(slide, Inches(0.45), Inches(7.18),
                          Inches(5), Inches(0.25))
    add_paragraph(tb_left.text_frame, "AstroBot · Graduation Project 2026",
                  size=9, color=INK_SOFT, first=True)

    if presenter:
        tb_right = add_textbox(slide, Inches(7.5), Inches(7.18),
                               Inches(5.4), Inches(0.25))
        add_paragraph(tb_right.text_frame, presenter,
                      size=9, color=INK_SOFT,
                      align=PP_ALIGN.RIGHT, first=True)


# ─── Project metadata ───────────────────────────────────────────────────
PROJECT_TITLE = "AstroBot"
PROJECT_TAGLINE = "An Intelligent Conversational AI Assistant\nwith Multimodal Capabilities, RAG and Workflow Integration"
COURSE = "MFBP 402 — Graduation Project II"
DEPARTMENT = "Computer Engineering · Faculty of Engineering"
UNIVERSITY = "OSTIM Technical University"
ADVISOR = "Assist. Prof. Dr. Yücel TEKİN"
DATE_RANGE = "May 18 – 21, 2026"
GITHUB = "github.com/tkonate788/astrobot"
LIVE_APP = "http://76.13.62.195:3000"
LIVE_ADMIN = "http://76.13.62.195:7040"

TEAM = [
    {"name": "Tidiane Konaté",         "role": "Architecture · Backend · Deployment", "photo": "TIDIANE KONATE.jpg",        "asset": "tidiane-konate.jpg"},
    {"name": "Sidi Mohamed Sall",      "role": "Vision · Product · UX",               "photo": "SIDI MOHAMED SALL.jpg",     "asset": "sidi-mohamed-sall.jpg"},
    {"name": "Ahmed Essalem",          "role": "AI Engineer · LLM & Multimodal",      "photo": "AHMED ESSALEM.jpg",         "asset": "ahmed-essalem.jpg"},
    {"name": "Saad Ibrahim Houssein",  "role": "QA · Frontend · Testing",             "photo": "SAAD IBRAHIM HOUSSEIN.jpg", "asset": "saad-ibrahim-houssein.jpg"},
]


def team_photo(idx: int) -> Path:
    """Prefer assets folder (better cropping); fall back to raw photos."""
    a = ASSETS / TEAM[idx]["asset"]
    if a.exists():
        return a
    return DEV_PHOTOS / TEAM[idx]["photo"]


# ════════════════════════════════════════════════════════════════════════
# SLIDE BUILDERS
# ════════════════════════════════════════════════════════════════════════

def fix_cover(slide):
    """Re-purpose the template cover (slide 1).

    The cover background is the OSTIM building on a magenta backdrop:
    the left half is solid magenta (perfect for big white text), the
    right half is busy (building + university logo). Bottom carries
    the dark base of the building.

    Strategy:
      • Strip the original placeholders (they were sized for short
        Turkish text and clip our title).
      • Place title + tagline + course line on the clean LEFT band.
      • Use NAVY cards for the team strip so it pops against magenta.
    """
    # Drop the original placeholders so we control everything
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    # Top chip
    add_chip(slide, "GRADUATION PROJECT · 2026",
             Inches(0.55), Inches(0.55), Inches(2.65),
             fill=PURPLE, size=10)

    # Mega title — left-aligned, takes the clean magenta band
    tb = add_textbox(slide, Inches(0.55), Inches(1.05),
                     Inches(8.0), Inches(1.55))
    add_paragraph(tb.text_frame, PROJECT_TITLE,
                  size=80, bold=True, color=WHITE,
                  first=True, space_after=2)

    # Tagline — narrower so it never bleeds into the building
    tb = add_textbox(slide, Inches(0.55), Inches(2.55),
                     Inches(6.50), Inches(1.40))
    tagline_lines = PROJECT_TAGLINE.split("\n")
    for i, line in enumerate(tagline_lines):
        add_paragraph(tb.text_frame, line,
                      size=17, color=LIGHT,
                      first=(i == 0), space_after=4)

    # Course + department + university (italic accent)
    tb = add_textbox(slide, Inches(0.55), Inches(4.10),
                     Inches(6.50), Inches(0.95))
    add_paragraph(tb.text_frame, COURSE,
                  size=14, bold=True, color=GOLD,
                  first=True, space_after=2)
    add_paragraph(tb.text_frame, DEPARTMENT,
                  size=12, color=LIGHT, italic=True, space_after=1)
    add_paragraph(tb.text_frame, UNIVERSITY,
                  size=12, color=LIGHT, italic=True)

    # Team strip — dark cards on the magenta bottom for legibility
    strip_top = Inches(5.30)
    strip_h = Inches(1.20)
    box_w = Inches(2.95)
    spacing = Inches(0.10)
    base_left = Inches(0.55)
    for i, member in enumerate(TEAM):
        left = Emu(int(base_left) + i * (int(box_w) + int(spacing)))
        add_card(slide, left, strip_top, box_w, strip_h, fill=NAVY)
        ph_size = Inches(1.0)
        photo = team_photo(i)
        if photo.exists():
            add_picture_safe(slide, photo,
                             Emu(int(left) + int(Inches(0.10))),
                             Emu(int(strip_top) + int(Inches(0.10))),
                             width=ph_size, height=ph_size)
        tb = add_textbox(slide,
                         Emu(int(left) + int(Inches(1.18))),
                         Emu(int(strip_top) + int(Inches(0.20))),
                         Emu(int(box_w) - int(Inches(1.28))),
                         Inches(0.85))
        add_paragraph(tb.text_frame, member["name"],
                      size=10.5, bold=True, color=WHITE, first=True, space_after=1)
        add_paragraph(tb.text_frame, member["role"],
                      size=8, color=GOLD)

    # Bottom info — date · advisor — centered below team strip
    tb = add_textbox(slide, Inches(0.55), Inches(6.85),
                     Inches(12.30), Inches(0.40))
    add_paragraph(tb.text_frame,
                  f"{DATE_RANGE}   ·   Advisor: {ADVISOR}",
                  size=11, color=LIGHT, italic=True,
                  align=PP_ALIGN.CENTER, first=True)


def fix_thanks(slide):
    """Re-purpose the template thank-you slide (originally slide 3).

    Same magenta+building backdrop as the cover — strip placeholders
    and rebuild with white/light text on a NAVY card for legibility.
    """
    # Drop original placeholders
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    # Big white title on the clean magenta band
    tb = add_textbox(slide, Inches(0.55), Inches(0.85),
                     Inches(11.5), Inches(1.30))
    add_paragraph(tb.text_frame, "Thank you for your attention!",
                  size=54, bold=True, color=WHITE,
                  first=True, space_after=2)

    # Q&A chip in gold
    add_chip(slide, "QUESTIONS WELCOME",
             Inches(0.55), Inches(2.30), Inches(2.40),
             fill=GOLD, text_color=NAVY, size=11)

    # Live URLs in a NAVY card so they read clearly over the building
    add_card(slide, Inches(0.55), Inches(2.95),
             Inches(7.80), Inches(2.60), fill=NAVY)
    tb = add_textbox(slide, Inches(0.85), Inches(3.10),
                     Inches(7.20), Inches(2.30))
    tf = tb.text_frame
    add_paragraph(tf, "Try AstroBot live",
                  size=20, bold=True, color=GOLD,
                  first=True, space_after=10)
    add_paragraph(tf, f"  Web app   ·   {LIVE_APP}",
                  size=14, color=WHITE, space_after=4, font="Consolas")
    add_paragraph(tf, f"  Admin     ·   {LIVE_ADMIN}",
                  size=14, color=WHITE, space_after=4, font="Consolas")
    add_paragraph(tf, f"  GitHub    ·   {GITHUB}",
                  size=14, color=WHITE, font="Consolas")

    # Team names + advisor at the bottom — light text on magenta
    tb = add_textbox(slide, Inches(0.55), Inches(5.85),
                     Inches(12.30), Inches(1.10))
    tf = tb.text_frame
    add_paragraph(tf,
                  "Tidiane Konaté   ·   Sidi Mohamed Sall   ·   Ahmed Essalem   ·   Saad Ibrahim Houssein",
                  size=13, bold=True, color=WHITE,
                  align=PP_ALIGN.CENTER, first=True, space_after=4)
    add_paragraph(tf, f"Advisor — {ADVISOR}",
                  size=11, italic=True, color=LIGHT,
                  align=PP_ALIGN.CENTER, space_after=2)
    add_paragraph(tf, f"{UNIVERSITY}   ·   {DATE_RANGE}",
                  size=11, italic=True, color=LIGHT,
                  align=PP_ALIGN.CENTER)


# ─── Section divider ─────────────────────────────────────────────────────
def build_section_divider(prs, number: str, title: str, presenter: str,
                          subtitle: str = ""):
    """Big visual section break — uses master 0 'Bölüm Ayracı' layout
    so the template's background image is included automatically."""
    layout = find_layout(prs, 0, "Bölüm Ayracı")
    slide = prs.slides.add_slide(layout)

    # Master layout has a full-bleed background image; lay our content
    # on top.
    # Number ribbon
    add_chip(slide, number,
             Inches(0.6), Inches(2.2), Inches(1.1),
             fill=PURPLE, size=24, bold=True, height=Inches(1.1))

    tb = add_textbox(slide, Inches(0.6), Inches(3.6),
                     Inches(11.5), Inches(2.4))
    add_paragraph(tb.text_frame, title,
                  size=54, bold=True, color=WHITE, first=True, space_after=8)
    add_paragraph(tb.text_frame, f"Presented by {presenter}",
                  size=22, color=GOLD, italic=True, space_after=4)
    if subtitle:
        add_paragraph(tb.text_frame, subtitle,
                      size=16, color=WHITE)

    return slide


# ─── Generic content slide builder ──────────────────────────────────────
def new_content_slide(prs):
    """Use the blank layout from master 2 and ignore its placeholders so we
    have full control over composition (no Turkish placeholder text leaks)."""
    layout = find_layout(prs, 2, "Boş Slayt")
    slide = prs.slides.add_slide(layout)
    # Hide the layout-bound title placeholder (we draw our own)
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx == 18:
            sp = ph._element
            sp.getparent().remove(sp)
    return slide


# ════════════════════════════════════════════════════════════════════════
# CONTENT — slide-by-slide
# ════════════════════════════════════════════════════════════════════════

def _populate_team_slide(slide):
    """Render the Team content into an already-allocated slide."""
    add_section_header(slide, "Meet the Team",
                       subtitle="Four engineers, one goal: make AI feel useful again.")
    add_footer_bar(slide, presenter="Introduction")

    # Four cards in a row
    top = Inches(1.55)
    h = Inches(4.7)
    w = Inches(2.85)
    gap = Inches(0.18)
    base_left = Inches(0.55)
    for i, member in enumerate(TEAM):
        left = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, left, top, w, h, fill=LIGHT)
        # Photo (square, centered horizontally)
        photo = team_photo(i)
        ph_w = Inches(2.10)
        ph_l = Emu(int(left) + (int(w) - int(ph_w)) // 2)
        add_picture_safe(slide, photo, ph_l, Emu(int(top) + int(Inches(0.30))),
                         width=ph_w, height=ph_w)
        # Name
        tb = add_textbox(slide, left, Emu(int(top) + int(Inches(2.65))),
                         w, Inches(0.45))
        add_paragraph(tb.text_frame, member["name"],
                      size=15, bold=True, color=NAVY, align=PP_ALIGN.CENTER, first=True)
        # Role
        tb = add_textbox(slide,
                         Emu(int(left) + int(Inches(0.10))),
                         Emu(int(top) + int(Inches(3.10))),
                         Emu(int(w) - int(Inches(0.20))),
                         Inches(1.2))
        add_paragraph(tb.text_frame, member["role"],
                      size=11, color=INK_SOFT, align=PP_ALIGN.CENTER, first=True)

    # Advisor block below team strip
    a_top = Inches(6.30)
    a_h = Inches(0.65)
    a_w = Inches(7.5)
    a_left = Inches(2.9)
    add_card(slide, a_left, a_top, a_w, a_h, fill=NAVY)
    if ADVISOR_PHOTO.exists():
        add_picture_safe(slide, ADVISOR_PHOTO,
                         Emu(int(a_left) + int(Inches(0.12))),
                         Emu(int(a_top) + int(Inches(0.07))),
                         width=Inches(0.50), height=Inches(0.50))
    tb = add_textbox(slide,
                     Emu(int(a_left) + int(Inches(0.80))),
                     a_top,
                     Emu(int(a_w) - int(Inches(0.85))), a_h,
                     anchor=MSO_ANCHOR.MIDDLE)
    add_paragraph(tb.text_frame, f"Advisor   ·   {ADVISOR}   —   {DEPARTMENT}",
                  size=12, bold=True, color=WHITE, first=True)


def repurpose_existing_slide_as_team(slide):
    """Strip the template's example slide and turn it into the Team slide.
    We do this rather than deleting + re-adding because python-pptx 1.0.x
    has a partname-allocation bug across slide deletes that leads to
    duplicate partname collisions in the saved package."""
    # Drop every placeholder so the slide becomes a clean canvas
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)
    _populate_team_slide(slide)


def build_agenda_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Agenda",
                       subtitle="Four parts. About fifteen minutes. One demo.")
    add_footer_bar(slide, presenter="Introduction")

    items = [
        ("01", "Introduction & Vision",
         "Why AstroBot — the problem, the goals, the users",
         "Sidi Mohamed Sall", PURPLE),
        ("02", "Architecture & Design",
         "System model, tech stack, data and security flow",
         "Tidiane Konaté", CYAN),
        ("03", "Implementation",
         "Chat, image gen, RAG, OCR, voice, productivity",
         "Ahmed Essalem", GOLD),
        ("04", "Admin · Testing · Deployment",
         "Dashboard, 66 tests, Docker stack, live MVP",
         "Saad Ibrahim Houssein", GREEN_OK),
    ]
    top = Inches(1.55)
    h = Inches(1.20)
    spacing = Inches(0.10)
    for i, (num, title, desc, who, color) in enumerate(items):
        y = Emu(int(top) + i * (int(h) + int(spacing)))
        # Numbered chip on the left
        add_chip(slide, num, Inches(0.55), y, Inches(0.95),
                 fill=color, size=20, height=h, text_color=WHITE if color != GOLD else NAVY)
        # Card with content
        add_card(slide, Inches(1.65), y, Inches(11.20), h, fill=LIGHT)
        tb = add_textbox(slide, Inches(1.85), y,
                         Inches(8.5), h, anchor=MSO_ANCHOR.MIDDLE)
        add_paragraph(tb.text_frame, title,
                      size=18, bold=True, color=NAVY, first=True, space_after=2)
        add_paragraph(tb.text_frame, desc, size=12, color=INK_SOFT)
        # Presenter pill on the right
        tb2 = add_textbox(slide, Inches(10.30), y,
                          Inches(2.45), h, anchor=MSO_ANCHOR.MIDDLE)
        add_paragraph(tb2.text_frame, "PRESENTER",
                      size=8, bold=True, color=PURPLE,
                      align=PP_ALIGN.RIGHT, first=True, space_after=1)
        add_paragraph(tb2.text_frame, who,
                      size=11, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)


# ─── Part 1: Sidi Mohamed Sall ─────────────────────────────────────────
PART1_PRESENTER = "Sidi Mohamed Sall · Part 1 of 4"


def build_problem_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "The Problem",
                       subtitle="The AI assistant landscape is rich — and broken.")
    add_footer_bar(slide, presenter=PART1_PRESENTER)

    pains = [
        ("Fragmented tools",
         "Chat, image gen, OCR, voice and document Q&A live in different apps. Users waste time switching contexts.",
         PURPLE),
        ("Paywalls everywhere",
         "Most useful features are gated behind subscriptions or per-call fees, which puts students and small teams off-side.",
         CYAN),
        ("Disposable conversations",
         "Sessions are flat lists. No tags, no folders, no notebook context, no exportable record of what was discussed.",
         GOLD),
        ("Black-box workflows",
         "Multi-step prompt pipelines are either rebuilt from scratch every time, or invisible inside closed agents.",
         GREEN_OK),
    ]
    top = Inches(1.55)
    h = Inches(1.30)
    w = Inches(6.10)
    gap_x = Inches(0.30)
    gap_y = Inches(0.20)
    for i, (title, body, color) in enumerate(pains):
        col = i % 2
        row = i // 2
        x = Emu(int(Inches(0.55)) + col * (int(w) + int(gap_x)))
        y = Emu(int(top) + row * (int(h) + int(gap_y)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        # Color bar on left
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.12), h)
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, Emu(int(x) + int(Inches(0.30))),
                         Emu(int(y) + int(Inches(0.12))),
                         Emu(int(w) - int(Inches(0.40))),
                         Emu(int(h) - int(Inches(0.20))))
        add_paragraph(tb.text_frame, title,
                      size=16, bold=True, color=NAVY, first=True, space_after=4)
        add_paragraph(tb.text_frame, body, size=11, color=INK_SOFT)


def build_objectives_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Project Objectives",
                       subtitle="Build one place where AI feels integrated, not glued together.")
    add_footer_bar(slide, presenter=PART1_PRESENTER)

    objs = [
        ("Unify modalities",
         "Text, image, audio, OCR, document Q&A and code highlighting in a single chat surface.",
         "01", PURPLE),
        ("Stay free for users",
         "Combine free-tier APIs (HuggingFace, Mistral, Groq) and self-hosted models behind one wrapper.",
         "02", CYAN),
        ("Make sessions persistent",
         "Folders, tags, notebooks, exports — give every conversation a memory and a paper trail.",
         "03", GOLD),
        ("Show our work",
         "Workflows are saved, replayable and visible — including the n8n graph that drives the agent.",
         "04", GREEN_OK),
        ("Ship a real MVP",
         "Live, dockerised, on a real server, with admin tooling and a 66-test suite — not a prototype.",
         "05", PURPLE),
        ("Ground on academic rigor",
         "Defend every choice with measurements, diagrams and reproducible deployment scripts.",
         "06", CYAN),
    ]
    top = Inches(1.55)
    h = Inches(1.55)
    w = Inches(4.05)
    gap_x = Inches(0.18)
    gap_y = Inches(0.18)
    for i, (title, body, num, color) in enumerate(objs):
        col = i % 3
        row = i // 3
        x = Emu(int(Inches(0.55)) + col * (int(w) + int(gap_x)))
        y = Emu(int(top) + row * (int(h) + int(gap_y)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        # Number badge top-left
        add_chip(slide, num, Emu(int(x) + int(Inches(0.20))),
                 Emu(int(y) + int(Inches(0.18))),
                 Inches(0.60), fill=color, size=11, bold=True,
                 height=Inches(0.36))
        tb = add_textbox(slide,
                         Emu(int(x) + int(Inches(0.92))),
                         Emu(int(y) + int(Inches(0.18))),
                         Emu(int(w) - int(Inches(1.05))),
                         Emu(int(h) - int(Inches(0.30))))
        add_paragraph(tb.text_frame, title,
                      size=14, bold=True, color=NAVY, first=True, space_after=4)
        add_paragraph(tb.text_frame, body, size=10.5, color=INK_SOFT)


def build_users_landing_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Users & First Impression",
                       subtitle="Who we built this for — and what they see.")
    add_footer_bar(slide, presenter=PART1_PRESENTER)

    # Left column — picture (landing page)
    pic = SCREENS / "1.png"
    add_picture_in_card(slide, pic, Inches(0.55), Inches(1.55),
                        Inches(7.40), Inches(4.85))

    # Caption under picture
    tb = add_textbox(slide, Inches(0.55), Inches(6.50),
                     Inches(7.40), Inches(0.4))
    add_paragraph(tb.text_frame,
                  "Public landing page — central chat bar, animated robot mascot.",
                  size=10, italic=True, color=INK_SOFT, align=PP_ALIGN.CENTER, first=True)

    # Right column — target users + scope
    rx = Inches(8.20)
    rw = Inches(4.65)
    tb = add_textbox(slide, rx, Inches(1.55), rw, Inches(5.6))
    tf = tb.text_frame
    add_paragraph(tf, "Target users", size=14, bold=True, color=PURPLE, first=True, space_after=4)
    for line in [
        "Students prepping reports & code",
        "Developers exploring multimodal AI",
        "Knowledge workers doing doc Q&A",
        "Anyone who wants one tab, not ten",
    ]:
        add_paragraph(tf, "•  " + line, size=12, color=INK, space_after=2)
    add_paragraph(tf, " ", size=6, space_after=2)
    add_paragraph(tf, "Scope of the MVP", size=14, bold=True, color=PURPLE, space_after=4)
    for line in [
        "Public + authenticated chat surface",
        "Admin dashboard with real metrics",
        "12+ AI-powered features (see Part 3)",
        "Production deployment on a real VM",
    ]:
        add_paragraph(tf, "•  " + line, size=12, color=INK, space_after=2)


# ─── Part 2: Tidiane Konaté ────────────────────────────────────────────
PART2_PRESENTER = "Tidiane Konaté · Part 2 of 4"

DIAGRAMS_DIR = ROOT / "deliverables" / "report" / "assets" / "diagrams"


def build_context_diagram_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Context Diagram",
                       subtitle="The system in its environment — who talks to AstroBot and what flows in and out.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    # Diagram on the left
    img_w = Inches(8.10)
    img_h = Inches(5.57)   # 1.455 aspect
    img_left = Inches(0.40)
    img_top = Inches(1.50)
    add_picture_in_card(slide, DIAGRAMS_DIR / "context.png",
                        img_left, img_top, img_w, img_h, frame=PURPLE, frame_pt=1.2)

    # Key-takeaways panel on the right
    panel_left = Inches(8.70)
    panel_top = Inches(1.50)
    panel_w = Inches(4.40)
    panel_h = Inches(5.57)
    add_card(slide, panel_left, panel_top, panel_w, panel_h, fill=LIGHT)

    tb = add_textbox(slide, Emu(int(panel_left) + int(Inches(0.20))),
                     Emu(int(panel_top) + int(Inches(0.20))),
                     Emu(int(panel_w) - int(Inches(0.40))),
                     Emu(int(panel_h) - int(Inches(0.40))))
    tf = tb.text_frame
    add_paragraph(tf, "What this shows",
                  size=14, bold=True, color=PURPLE, first=True, space_after=4)
    add_paragraph(tf,
                  "AstroBot sits in the middle. Around it are the people and "
                  "external services it talks to.",
                  size=11, color=INK, space_after=8)

    add_paragraph(tf, "Actors",
                  size=13, bold=True, color=NAVY, space_after=2)
    add_paragraph(tf, "•  End user — chats, uploads, listens to replies.",
                  size=11, color=INK, space_after=2)
    add_paragraph(tf, "•  Administrator — runs the dashboard, manages accounts and audits activity.",
                  size=11, color=INK, space_after=8)

    add_paragraph(tf, "External services",
                  size=13, bold=True, color=NAVY, space_after=2)
    add_paragraph(tf, "•  Mistral Cloud — the language model behind every reply.",
                  size=11, color=INK, space_after=2)
    add_paragraph(tf, "•  HuggingFace — image generation, captioning, embeddings.",
                  size=11, color=INK, space_after=2)
    add_paragraph(tf, "•  Groq Whisper — voice-to-text.",
                  size=11, color=INK, space_after=2)
    add_paragraph(tf, "•  SerpAPI — web search tool for the AI agent.",
                  size=11, color=INK, space_after=8)

    add_paragraph(tf, "Boundary",
                  size=13, bold=True, color=NAVY, space_after=2)
    add_paragraph(tf,
                  "Everything outside the central box is out of our control "
                  "and reached over HTTPS only.",
                  size=11, italic=True, color=INK_SOFT)


def build_usecase_diagram_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Use-Case Diagram",
                       subtitle="What end users and administrators can actually do with the system.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    # Diagram on the left
    img_w = Inches(7.40)
    img_h = Inches(5.55)   # 1.333 aspect → 7.40/1.333 = 5.55
    img_left = Inches(0.40)
    img_top = Inches(1.50)
    add_picture_in_card(slide, DIAGRAMS_DIR / "usecase.png",
                        img_left, img_top, img_w, img_h, frame=CYAN, frame_pt=1.2)

    # Right panel with the actor → use-case summary
    panel_left = Inches(8.00)
    panel_top = Inches(1.50)
    panel_w = Inches(5.10)
    panel_h = Inches(5.55)
    add_card(slide, panel_left, panel_top, panel_w, panel_h, fill=LIGHT)

    tb = add_textbox(slide, Emu(int(panel_left) + int(Inches(0.20))),
                     Emu(int(panel_top) + int(Inches(0.20))),
                     Emu(int(panel_w) - int(Inches(0.40))),
                     Emu(int(panel_h) - int(Inches(0.40))))
    tf = tb.text_frame

    add_paragraph(tf, "End user", size=14, bold=True,
                  color=PURPLE, first=True, space_after=2)
    add_paragraph(tf, "•  Register & log in (JWT)",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Chat in seven personas",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Generate or edit images",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Ask questions over a PDF (RAG or notebook)",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Speak a message (Whisper transcription)",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Read an image (OCR + BLIP captioning)",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Generate a PDF report on demand",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Save, tag, search and export sessions",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Compose multi-step workflow chains",
                  size=11, color=INK, space_after=10)

    add_paragraph(tf, "Administrator", size=14, bold=True,
                  color=CYAN, space_after=2)
    add_paragraph(tf, "•  Log in to the admin dashboard",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  View KPIs and activity charts",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Search, suspend, reactivate, delete or create users",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Reset a user's password",
                  size=11, color=INK, space_after=1)
    add_paragraph(tf, "•  Inspect any user's conversation history",
                  size=11, color=INK, space_after=10)

    add_paragraph(tf,
                  "Every use case here also goes through the JWT auth + role gate.",
                  size=10, italic=True, color=INK_SOFT)


def build_architecture_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "System Architecture",
                       subtitle="Three Docker services on a shared n8n private network.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    # Top row: client
    add_card(slide, Inches(5.20), Inches(1.55), Inches(3.0), Inches(0.65), fill=NAVY)
    tb = add_textbox(slide, Inches(5.20), Inches(1.55), Inches(3.0), Inches(0.65),
                     anchor=MSO_ANCHOR.MIDDLE)
    add_paragraph(tb.text_frame, "User Browser",
                  size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER, first=True)

    # Three services row
    services = [
        ("Main App", ":3000", "Public chat surface\nExpress · JWT · Helmet", PURPLE),
        ("Admin Dashboard", ":7040", "Stats · users · audit\nRole-gated by JWT", CYAN),
        ("n8n Orchestrator", ":5678", "Mistral agent · SerpAPI\nWhisper · Think tool", GOLD),
    ]
    top = Inches(2.55)
    h = Inches(1.65)
    w = Inches(3.85)
    gap = Inches(0.30)
    base_left = Inches(0.55)
    for i, (name, port, desc, color) in enumerate(services):
        x = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, x, top, w, h, fill=LIGHT)
        # Color top stripe
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, w, Inches(0.18))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, x, Emu(int(top) + int(Inches(0.28))),
                         w, Emu(int(h) - int(Inches(0.30))),
                         anchor=MSO_ANCHOR.TOP)
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r1 = p.add_run(); r1.text = name + "  "
        style_run(r1, size=18, bold=True, color=NAVY)
        r2 = p.add_run(); r2.text = port
        style_run(r2, size=14, bold=True, color=color)
        add_paragraph(tf, desc, size=11, color=INK_SOFT, align=PP_ALIGN.CENTER, space_after=2)

    # Storage row
    storage = [
        ("PostgreSQL (shared)", "users · convs · documents · embeddings · workflows", PURPLE),
        ("HuggingFace Router", "FLUX.1-schnell · BLIP · MiniLM · fal-ai", CYAN),
        ("External APIs", "Mistral Cloud · Groq Whisper · SerpAPI", GOLD),
    ]
    s_top = Inches(4.50)
    s_h = Inches(1.05)
    for i, (name, desc, color) in enumerate(storage):
        x = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, x, s_top, w, s_h, fill=NAVY)
        tb = add_textbox(slide, x, s_top, w, s_h, anchor=MSO_ANCHOR.MIDDLE)
        tf = tb.text_frame
        add_paragraph(tf, name, size=13, bold=True, color=color,
                      align=PP_ALIGN.CENTER, first=True, space_after=4)
        add_paragraph(tf, desc, size=10, color=WHITE, align=PP_ALIGN.CENTER)

    # Bottom note
    tb = add_textbox(slide, Inches(0.55), Inches(5.85),
                     Inches(12.30), Inches(0.95))
    add_paragraph(tb.text_frame,
                  "Why this shape:",
                  size=12, bold=True, color=PURPLE, first=True, space_after=2)
    add_paragraph(tb.text_frame,
                  "•  Reuses an existing PostgreSQL container — no extra DB to operate.",
                  size=11, color=INK, space_after=1)
    add_paragraph(tb.text_frame,
                  "•  All AI traffic exits through n8n, so prompts and tools can be tuned without redeploying.",
                  size=11, color=INK, space_after=1)
    add_paragraph(tb.text_frame,
                  "•  Admin lives in its own service so a public-facing exploit can never reach the dashboard process.",
                  size=11, color=INK, space_after=1)


def build_techstack_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Technology Stack",
                       subtitle="Boring, well-supported building blocks at every layer.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    cols = [
        ("Frontend", PURPLE, [
            "Vanilla HTML / CSS / JavaScript",
            "KaTeX  · highlight.js  · Mermaid",
            "Cropper.js  · Chart.js (admin)",
            "No framework — fast & maintainable",
        ]),
        ("Backend", CYAN, [
            "Node.js 18  ·  Express 4",
            "JWT  ·  bcrypt 12 rounds",
            "Helmet · express-rate-limit",
            "pg, pdfkit, tesseract.js, pdf-parse",
        ]),
        ("AI / LLM", GOLD, [
            "Mistral medium-latest (via n8n agent)",
            "HuggingFace FLUX.1-schnell · BLIP",
            "MiniLM-L6-v2 embeddings",
            "Groq Whisper-large-v3-turbo",
        ]),
        ("Infrastructure", GREEN_OK, [
            "Docker · Docker Compose",
            "Shared PostgreSQL container",
            "n8n network (existing)",
            "Python deploy.py (paramiko)",
        ]),
    ]
    top = Inches(1.55)
    h = Inches(4.85)
    w = Inches(3.05)
    gap = Inches(0.15)
    base_left = Inches(0.55)
    for i, (name, color, lines) in enumerate(cols):
        x = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, x, top, w, h, fill=LIGHT)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, w, Inches(0.55))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, x, top, w, Inches(0.55),
                         anchor=MSO_ANCHOR.MIDDLE)
        add_paragraph(tb.text_frame, name,
                      size=16, bold=True, color=WHITE,
                      align=PP_ALIGN.CENTER, first=True)
        tb = add_textbox(slide, Emu(int(x) + int(Inches(0.20))),
                         Emu(int(top) + int(Inches(0.75))),
                         Emu(int(w) - int(Inches(0.40))),
                         Emu(int(h) - int(Inches(0.85))))
        for line in lines:
            add_paragraph(tb.text_frame, "•  " + line,
                          size=12, color=INK,
                          first=(line == lines[0]), space_after=8)


def build_database_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Database Schema",
                       subtitle="Idempotent migrations on every boot — no manual DBA work.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    tables = [
        ("users",
         "id · email · password_hash\nis_admin · status · avatar · last_login",
         PURPLE),
        ("conversations",
         "id · user_id · message · response\nsession_id · session_tag · image_url\npdf_url · pdf_filename · attachment",
         CYAN),
        ("documents",
         "id · user_id · name · mime\nsize · text_content · created_at",
         GOLD),
        ("document_chunks",
         "document_id · chunk_index\nchunk_text · embedding (TEXT)",
         GREEN_OK),
        ("notebook_bindings",
         "user_id · session_id · document_id\nmode (notebook | rag)",
         PURPLE),
        ("workflows",
         "id · user_id · name\nsteps (JSON)",
         CYAN),
    ]
    top = Inches(1.55)
    h = Inches(2.40)
    w = Inches(4.05)
    gap = Inches(0.18)
    base_left = Inches(0.55)
    for i, (name, body, color) in enumerate(tables):
        col = i % 3
        row = i // 3
        x = Emu(int(base_left) + col * (int(w) + int(gap)))
        y = Emu(int(top) + row * (int(h) + int(gap)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.42))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, x, y, w, Inches(0.42),
                         anchor=MSO_ANCHOR.MIDDLE)
        add_paragraph(tb.text_frame, name,
                      size=14, bold=True, color=WHITE,
                      align=PP_ALIGN.CENTER, first=True, font="Consolas")
        tb = add_textbox(slide, Emu(int(x) + int(Inches(0.20))),
                         Emu(int(y) + int(Inches(0.55))),
                         Emu(int(w) - int(Inches(0.40))),
                         Emu(int(h) - int(Inches(0.65))))
        for j, line in enumerate(body.split("\n")):
            add_paragraph(tb.text_frame, line,
                          size=10.5, color=INK_SOFT, font="Consolas",
                          first=(j == 0), space_after=2)


def build_n8n_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "n8n LLM Orchestration",
                       subtitle="A visual workflow we can tune without redeploying the backend.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    # Left: workflow screenshot
    pic = SCREENS / "19n.png"
    add_picture_in_card(slide, pic, Inches(0.55), Inches(1.55),
                        Inches(8.20), Inches(5.30))

    # Right: node descriptions
    rx = Inches(9.00)
    rw = Inches(3.85)
    tb = add_textbox(slide, rx, Inches(1.55), rw, Inches(5.30))
    tf = tb.text_frame
    add_paragraph(tf, "Pipeline", size=14, bold=True, color=PURPLE,
                  first=True, space_after=6)
    pipeline = [
        ("Webhook", "POST receiver"),
        ("Switch", "audio vs text branch"),
        ("Whisper", "audio transcription"),
        ("Payload", "history + persona enrichment"),
        ("AI Agent", "Mistral medium · 20-iter cap"),
        ("SerpAPI", "live web search (max 2 calls)"),
        ("Think", "scratchpad reasoning"),
        ("Edit Fields", "extracts JSON `response`"),
        ("Respond", "back to backend"),
    ]
    for name, desc in pipeline:
        p = tf.add_paragraph()
        p.space_after = Pt(2)
        r1 = p.add_run(); r1.text = name + "  "
        style_run(r1, size=11, bold=True, color=NAVY)
        r2 = p.add_run(); r2.text = "—  " + desc
        style_run(r2, size=10, color=INK_SOFT)


def build_security_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Security & Resilience",
                       subtitle="Defence in depth — secrets never live in the repo.")
    add_footer_bar(slide, presenter=PART2_PRESENTER)

    pillars = [
        ("Authentication",
         "JWT (7-day expiry) signed with rotating secret\nbcrypt password hashing (12 rounds)\nAdmin gate via `is_admin` JWT claim",
         "01", PURPLE),
        ("Network surface",
         "Helmet HTTP security headers\nCORS allow-list per origin\nNo cache on static assets",
         "02", CYAN),
        ("Rate limits",
         "Auth  ·  20 / 15 min\nChat  ·  30 / min\nGlobal · 200 / 15 min · Admin · 500 / 15 min",
         "03", GOLD),
        ("Operational hygiene",
         "Secrets in .env files (gitignored)\nFile uploads capped 10 MB · 5 attachments\nIdempotent migrations + admin re-seed at boot",
         "04", GREEN_OK),
    ]
    top = Inches(1.55)
    h = Inches(2.55)
    w = Inches(6.10)
    gap_x = Inches(0.30)
    gap_y = Inches(0.20)
    for i, (title, body, num, color) in enumerate(pillars):
        col = i % 2
        row = i // 2
        x = Emu(int(Inches(0.55)) + col * (int(w) + int(gap_x)))
        y = Emu(int(top) + row * (int(h) + int(gap_y)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        add_chip(slide, num,
                 Emu(int(x) + int(Inches(0.25))),
                 Emu(int(y) + int(Inches(0.25))),
                 Inches(0.60), fill=color, size=12, height=Inches(0.40))
        tb = add_textbox(slide,
                         Emu(int(x) + int(Inches(1.00))),
                         Emu(int(y) + int(Inches(0.25))),
                         Emu(int(w) - int(Inches(1.20))),
                         Emu(int(h) - int(Inches(0.40))))
        add_paragraph(tb.text_frame, title,
                      size=16, bold=True, color=NAVY, first=True, space_after=4)
        for line in body.split("\n"):
            add_paragraph(tb.text_frame, "•  " + line,
                          size=11, color=INK_SOFT, space_after=2)


# ─── Part 3: Ahmed Essalem ─────────────────────────────────────────────
PART3_PRESENTER = "Ahmed Essalem · Part 3 of 4"


def _screenshot_slide(prs, title, subtitle, screen_name, bullets, *,
                      caption=None, presenter=PART3_PRESENTER):
    slide = new_content_slide(prs)
    add_section_header(slide, title, subtitle=subtitle)
    add_footer_bar(slide, presenter=presenter)

    pic = SCREENS / screen_name
    add_picture_in_card(slide, pic, Inches(0.55), Inches(1.55),
                        Inches(7.85), Inches(4.95))
    if caption:
        tb = add_textbox(slide, Inches(0.55), Inches(6.55),
                         Inches(7.85), Inches(0.40))
        add_paragraph(tb.text_frame, caption,
                      size=10, italic=True, color=INK_SOFT,
                      align=PP_ALIGN.CENTER, first=True)

    rx = Inches(8.65)
    rw = Inches(4.20)
    tb = add_textbox(slide, rx, Inches(1.55), rw, Inches(5.50))
    tf = tb.text_frame
    first = True
    for label, desc in bullets:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run(); r1.text = label + "\n"
        style_run(r1, size=14, bold=True, color=PURPLE)
        r2 = p.add_run(); r2.text = desc
        style_run(r2, size=11, color=INK_SOFT)
    return slide


def build_chat_experience_slide(prs):
    _screenshot_slide(
        prs,
        "Chat Experience",
        "Streaming-style replies, multilingual, persona-aware.",
        "6.png",
        [
            ("Mistral medium via n8n",
             "15-message context window per session, persona directives prepended."),
            ("Word-by-word reveal",
             "Animated streaming UX without server-side streaming complexity."),
            ("Markdown · Math · Code · Diagrams",
             "GitHub-flavored Markdown, KaTeX, highlight.js, Mermaid all live in the same bubble."),
            ("Multi-language",
             "Auto-detect FR / EN / ES / DE / AR / ZH / JA / KO / RU / EL."),
            ("7 personas",
             "Default · Formal · Casual · Teacher · Developer · Poet · Scientist."),
        ],
        caption="Authenticated chat — welcome screen with quick-start prompts.")


def build_richcontent_slide(prs):
    _screenshot_slide(
        prs,
        "Rich Content Rendering",
        "A bot bubble is a tiny IDE — it renders what the prompt deserves.",
        "12.png",
        [
            ("Markdown",
             "Lists, headings, emphasis, blockquotes, links — sanitised on output."),
            ("LaTeX math",
             "$E=mc^2$ inline,  $$\\int_0^\\infty$$  block, KaTeX renders client-side."),
            ("Code highlighting",
             "highlight.js detects 180+ languages; one-click copy buttons."),
            ("Mermaid diagrams",
             "Flow charts, sequence diagrams, ER models, Gantt — straight from text."),
        ],
        caption="Markdown rendering with structured lists, emphasis and code.")


def build_image_slide(prs):
    _screenshot_slide(
        prs,
        "AI Image Generation",
        "Prompt → image, inline, in the same chat thread.",
        "13.png",
        [
            ("FLUX.1-schnell",
             "HuggingFace router endpoint — 4-step diffusion model, free tier."),
            ("fal-ai fallback",
             "Automatic retry path when HF rate-limits or times out."),
            ("Image-to-image",
             "Style transfer (anime, oil painting, etc.) via FLUX dev img2img."),
            ("Inline rendering",
             "Image is stored as data URL on the conversation row — survives reloads."),
        ],
        caption="Image generation example — prompt-to-render in a single bubble.")


def build_pdf_slide(prs):
    _screenshot_slide(
        prs,
        "On-Demand PDF Reports",
        "Heuristic detection: when the bot promises a PDF, we ship one.",
        "14.png",
        [
            ("PDFKit",
             "Server-side composition with title, body, sections and styled emphasis."),
            ("Heuristic action triggers",
             "Backend re-parses the agent reply — if it acknowledges the report, we force `generate_pdf`."),
            ("Inline preview card",
             "Filename, size badge, one-click download from inside the bubble."),
            ("Persisted",
             "Stored as data URL in the conversation row for re-download anytime."),
        ],
        caption="A generated PDF surfaced as a download card inside the chat.")


def build_ocr_vision_slide(prs):
    _screenshot_slide(
        prs,
        "OCR & Visual Understanding",
        "Drop in any image — we'll read it AND describe it.",
        "11.png",
        [
            ("Tesseract.js",
             "On-server OCR · English + French · embedded as message context."),
            ("BLIP captioning",
             "HuggingFace BLIP visualizes the image when there's no text."),
            ("Combined into context",
             "Both signals are concatenated to the prompt before reaching Mistral."),
            ("Use cases",
             "Forms, screenshots, error messages, scanned documents, ID cards."),
        ],
        caption="OCR + reasoning — the AI explains a Green Card lottery confirmation.")


def build_rag_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Document Q&A — RAG & Notebook",
                       subtitle="Two retrieval modes, one chat surface.")
    add_footer_bar(slide, presenter=PART3_PRESENTER)

    # Pipeline as horizontal flow
    steps = [
        ("Upload PDF",  "pdf-parse",       PURPLE),
        ("Chunk",       "800 chars · 100 overlap",   CYAN),
        ("Embed",       "MiniLM-L6-v2",    GOLD),
        ("Retrieve",    "top-4 cosine",    GREEN_OK),
        ("Inject + Ask","Mistral via n8n", PURPLE),
    ]
    top = Inches(1.65)
    h = Inches(1.10)
    w = Inches(2.32)
    gap = Inches(0.12)
    base_left = Inches(0.55)
    for i, (name, sub, color) in enumerate(steps):
        x = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, x, top, w, h, fill=LIGHT)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, w, Inches(0.16))
        bar.fill.solid(); bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, x, Emu(int(top) + int(Inches(0.22))),
                         w, Emu(int(h) - int(Inches(0.25))))
        add_paragraph(tb.text_frame, name,
                      size=14, bold=True, color=NAVY,
                      align=PP_ALIGN.CENTER, first=True, space_after=2)
        add_paragraph(tb.text_frame, sub,
                      size=10, color=INK_SOFT, align=PP_ALIGN.CENTER)
        # Arrow except after last
        if i < len(steps) - 1:
            ax = Emu(int(x) + int(w))
            ay = Emu(int(top) + int(h) // 2 - int(Inches(0.10)))
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                           ax, ay, gap, Inches(0.20))
            arrow.fill.solid(); arrow.fill.fore_color.rgb = INK_SOFT
            arrow.line.fill.background()

    # Two modes side by side
    modes = [
        ("Notebook mode",
         "First 6,000 characters of the bound document are *always* in context. "
         "Best for short PDFs or when you want the AI to discuss the whole document.",
         PURPLE),
        ("RAG mode",
         "On every question we embed the prompt with MiniLM and pull the top-4 most "
         "similar chunks (cosine similarity) into context. Scales to long documents.",
         CYAN),
    ]
    m_top = Inches(3.20)
    m_h = Inches(2.30)
    m_w = Inches(6.10)
    for i, (name, body, color) in enumerate(modes):
        x = Emu(int(Inches(0.55)) + i * (int(m_w) + int(Inches(0.30))))
        add_card(slide, x, m_top, m_w, m_h, fill=NAVY)
        tb = add_textbox(slide, Emu(int(x) + int(Inches(0.30))),
                         Emu(int(m_top) + int(Inches(0.30))),
                         Emu(int(m_w) - int(Inches(0.60))),
                         Emu(int(m_h) - int(Inches(0.50))))
        add_paragraph(tb.text_frame, name,
                      size=16, bold=True, color=color, first=True, space_after=8)
        add_paragraph(tb.text_frame, body, size=12, color=WHITE)

    # Bottom note
    tb = add_textbox(slide, Inches(0.55), Inches(5.85),
                     Inches(12.30), Inches(1.0))
    add_paragraph(tb.text_frame,
                  "Why we kept both:",
                  size=12, bold=True, color=PURPLE, first=True, space_after=2)
    add_paragraph(tb.text_frame,
                  "•  Notebook is dependable for thesis-sized PDFs (<10 pages).",
                  size=11, color=INK, space_after=1)
    add_paragraph(tb.text_frame,
                  "•  RAG is the only thing that makes 200-page books answerable in real time.",
                  size=11, color=INK, space_after=1)


def build_productivity_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Productivity Tools",
                       subtitle="The pieces we missed in every other AI app.")
    add_footer_bar(slide, presenter=PART3_PRESENTER)

    feats = [
        ("Workflow chains",
         "Save multi-step prompt sequences and replay them on a single click.",
         "01", PURPLE),
        ("Folders & tags",
         "Color-coded session tags · search across full conversation history.",
         "02", CYAN),
        ("Exports",
         "Conversation as PDF · Markdown · JSON — three clicks each.",
         "03", GOLD),
        ("YouTube summarizer",
         "Paste a URL, get a transcript-grounded summary inside the chat.",
         "04", GREEN_OK),
        ("Audio transcription",
         "Browser recording → Groq Whisper-large-v3-turbo → typed reply.",
         "05", PURPLE),
        ("Profile + cropper",
         "Built-in image cropper (rotate · zoom · flip) for avatars.",
         "06", CYAN),
    ]
    top = Inches(1.55)
    h = Inches(1.55)
    w = Inches(4.05)
    gap_x = Inches(0.18)
    gap_y = Inches(0.18)
    for i, (title, body, num, color) in enumerate(feats):
        col = i % 3
        row = i // 3
        x = Emu(int(Inches(0.55)) + col * (int(w) + int(gap_x)))
        y = Emu(int(top) + row * (int(h) + int(gap_y)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        add_chip(slide, num, Emu(int(x) + int(Inches(0.20))),
                 Emu(int(y) + int(Inches(0.18))),
                 Inches(0.55), fill=color, size=11, bold=True,
                 height=Inches(0.36))
        tb = add_textbox(slide,
                         Emu(int(x) + int(Inches(0.92))),
                         Emu(int(y) + int(Inches(0.18))),
                         Emu(int(w) - int(Inches(1.05))),
                         Emu(int(h) - int(Inches(0.30))))
        add_paragraph(tb.text_frame, title,
                      size=14, bold=True, color=NAVY, first=True, space_after=4)
        add_paragraph(tb.text_frame, body, size=11, color=INK_SOFT)


# ─── Part 4: Saad Ibrahim Houssein ─────────────────────────────────────
PART4_PRESENTER = "Saad Ibrahim Houssein · Part 4 of 4"


def build_admin_dashboard_slide(prs):
    _screenshot_slide(
        prs,
        "Admin Dashboard",
        "A second Express service — fully isolated from the public app.",
        "16a.png",
        [
            ("Real-time KPIs",
             "Users · messages · sessions · tokens · images · PDFs · documents."),
            ("Charts",
             "Daily activity (30 days) and user-status doughnut, both Chart.js."),
            ("Recent signups & top users",
             "Quick triage panels visible above the fold."),
            ("Hard role gate",
             "Login refuses any account that is not `is_admin = TRUE`."),
        ],
        caption="Admin dashboard — KPIs, daily message chart, status doughnut.",
        presenter=PART4_PRESENTER)


def build_user_mgmt_slide(prs):
    _screenshot_slide(
        prs,
        "User Management",
        "Search, audit, suspend, reset, delete — without touching the database.",
        "17a.png",
        [
            ("Searchable table",
             "Status · role · sessions · messages · last login · joined date."),
            ("Lifecycle actions",
             "Suspend / activate · reset password · delete user (self-delete blocked)."),
            ("Account creation",
             "Admins create regular or admin accounts directly from the UI."),
            ("Soft 403 responses",
             "Non-admin tokens are rejected before any state is read."),
        ],
        caption="User management table with status, role and recent activity columns.",
        presenter=PART4_PRESENTER)


def build_user_detail_slide(prs):
    _screenshot_slide(
        prs,
        "Conversation Audit",
        "Every conversation, grouped by session, on demand.",
        "18a.png",
        [
            ("Profile metadata",
             "Email · joined · status · role · counts at a glance."),
            ("Sessions list",
             "Each session previewed with its first message and tag."),
            ("Drill-down",
             "Open any session to see the full message + response history."),
            ("Compliance-ready",
             "Built so we can answer a 'what did this user ask?' request in seconds."),
        ],
        caption="User detail — full conversation history grouped by session.",
        presenter=PART4_PRESENTER)


def build_testing_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Testing — 66 Integration Tests",
                       subtitle="`python test_all.py` — single command, full suite, real server.")
    add_footer_bar(slide, presenter=PART4_PRESENTER)

    cats = [
        ("Health",       "Main + admin /health endpoints reachable",     PURPLE),
        ("Static assets","HTML/CSS/JS served with no-cache headers",     CYAN),
        ("Auth",         "Login · wrong password · missing token · role check", GOLD),
        ("Admin CRUD",   "Stats · users list · create · update · suspend · reset · delete", GREEN_OK),
        ("Main app",     "Profile · avatar set + clear · password change", PURPLE),
        ("Chat flow",    "Round-trip via n8n → Mistral → response",      CYAN),
        ("Sessions",     "Tags · history · session detail · session delete", GOLD),
        ("Exports",      "PDF · Markdown · JSON exports validate",       GREEN_OK),
        ("Features",     "Documents · RAG bind/unbind · workflows CRUD", PURPLE),
        ("Validation",   "Bad inputs return clean 400/422 — never 500",  CYAN),
    ]
    top = Inches(1.55)
    h = Inches(0.85)
    w = Inches(6.10)
    gap_y = Inches(0.10)
    gap_x = Inches(0.30)
    for i, (cat, desc, color) in enumerate(cats):
        col = i % 2
        row = i // 2
        x = Emu(int(Inches(0.55)) + col * (int(w) + int(gap_x)))
        y = Emu(int(top) + row * (int(h) + int(gap_y)))
        add_card(slide, x, y, w, h, fill=LIGHT)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.10), h)
        bar.fill.solid(); bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = add_textbox(slide, Emu(int(x) + int(Inches(0.30))), y,
                         Emu(int(w) - int(Inches(0.40))), h,
                         anchor=MSO_ANCHOR.MIDDLE)
        tf = tb.text_frame
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = cat + "    "
        style_run(r1, size=13, bold=True, color=NAVY)
        r2 = p.add_run(); r2.text = desc
        style_run(r2, size=11, color=INK_SOFT)


def build_deployment_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Production Deployment",
                       subtitle="One command. Real VM. Real users.")
    add_footer_bar(slide, presenter=PART4_PRESENTER)

    # Left: deploy steps
    steps = [
        ("1.",  "tar -cz frontend backend admin docker"),
        ("2.",  "SFTP upload to /tmp on the VM"),
        ("3.",  "ssh: tar -xz into ~/astrobot"),
        ("4.",  "docker compose up -d --build"),
        ("5.",  "healthcheck verifies both services"),
    ]
    add_card(slide, Inches(0.55), Inches(1.55), Inches(6.10), Inches(3.20),
             fill=LIGHT)
    tb = add_textbox(slide, Inches(0.85), Inches(1.65),
                     Inches(5.50), Inches(0.40))
    add_paragraph(tb.text_frame, "deploy.py — five remote commands",
                  size=14, bold=True, color=PURPLE, first=True)
    tb = add_textbox(slide, Inches(0.85), Inches(2.10),
                     Inches(5.55), Inches(2.55))
    tf = tb.text_frame
    first = True
    for num, cmd in steps:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(6)
        r1 = p.add_run(); r1.text = num + "  "
        style_run(r1, size=12, bold=True, color=PURPLE)
        r2 = p.add_run(); r2.text = cmd
        style_run(r2, size=12, color=INK, font="Consolas")

    # Right: live URLs + container summary
    add_card(slide, Inches(6.85), Inches(1.55), Inches(6.00), Inches(3.20),
             fill=NAVY)
    tb = add_textbox(slide, Inches(7.10), Inches(1.65),
                     Inches(5.55), Inches(0.40))
    add_paragraph(tb.text_frame, "Live containers",
                  size=14, bold=True, color=GOLD, first=True)
    tb = add_textbox(slide, Inches(7.10), Inches(2.10),
                     Inches(5.55), Inches(2.55))
    tf = tb.text_frame
    rows = [
        ("astrobot:2.0.0",       ":3000",  "main app"),
        ("astrobot-admin:1.0.0", ":7040",  "admin dashboard"),
        ("postgre_container",    ":5432",  "shared (read/write own DB only)"),
        ("n8n",                  ":5678",  "external · do not modify"),
    ]
    first = True
    for name, port, role in rows:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(6)
        r1 = p.add_run(); r1.text = name
        style_run(r1, size=12, bold=True, color=WHITE, font="Consolas")
        r2 = p.add_run(); r2.text = "   " + port + "  "
        style_run(r2, size=11, color=CYAN, font="Consolas")
        r3 = p.add_run(); r3.text = role
        style_run(r3, size=11, color=LIGHT, italic=True)

    # Bottom: live URLs banner
    add_card(slide, Inches(0.55), Inches(5.00), Inches(12.30), Inches(1.55),
             fill=PURPLE)
    tb = add_textbox(slide, Inches(0.55), Inches(5.00),
                     Inches(12.30), Inches(0.50),
                     anchor=MSO_ANCHOR.MIDDLE)
    add_paragraph(tb.text_frame,
                  "Try it right now",
                  size=14, bold=True, color=GOLD,
                  align=PP_ALIGN.CENTER, first=True)
    tb = add_textbox(slide, Inches(0.55), Inches(5.55),
                     Inches(12.30), Inches(1.0))
    tf = tb.text_frame
    add_paragraph(tf, f"  Web app   ·   {LIVE_APP}",
                  size=14, color=WHITE, align=PP_ALIGN.CENTER,
                  first=True, space_after=2, font="Consolas")
    add_paragraph(tf, f"  Admin     ·   {LIVE_ADMIN}",
                  size=14, color=WHITE, align=PP_ALIGN.CENTER, space_after=2,
                  font="Consolas")
    add_paragraph(tf, f"  Source    ·   {GITHUB}",
                  size=14, color=WHITE, align=PP_ALIGN.CENTER, font="Consolas")


def build_demo_outcomes_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Lessons Learned & What's Next",
                       subtitle="What we'd build differently — and where we're heading.")
    add_footer_bar(slide, presenter=PART4_PRESENTER)

    learned = [
        ("Cache-Control: no-store on iOS", "Mobile Safari held onto stale CSS for hours; killed it at the express layer."),
        ("Heuristic action triggers", "LLMs occasionally agree to a PDF without flagging it — backend re-parses replies."),
        ("Idempotent migrations", "ALTER TABLE ... ADD COLUMN IF NOT EXISTS lets the app self-heal on every boot."),
        ("Single deploy script", "Beats `git pull` over SSH — no half-deployed state on partial failures."),
    ]
    nxt = [
        ("Mobile-first PWA",         "Service worker · push notifications · standalone app feel."),
        ("Voice mode",               "Two-way audio loop — Whisper in, Web Speech out."),
        ("More languages",           "Tesseract Arabic + Cyrillic; persona auto-tuning per language."),
        ("Self-hosted Whisper",      "Already in n8n graph — extend it to all audio paths."),
        ("Plug-in marketplace",      "Workflows shared and rated across users."),
    ]
    # Two columns
    add_card(slide, Inches(0.55), Inches(1.55), Inches(6.10), Inches(5.30),
             fill=LIGHT)
    tb = add_textbox(slide, Inches(0.80), Inches(1.65),
                     Inches(5.65), Inches(0.45))
    add_paragraph(tb.text_frame, "Lessons learned",
                  size=16, bold=True, color=PURPLE, first=True)
    tb = add_textbox(slide, Inches(0.80), Inches(2.15),
                     Inches(5.65), Inches(4.65))
    tf = tb.text_frame
    first = True
    for label, body in learned:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run(); r1.text = label + "\n"
        style_run(r1, size=12, bold=True, color=NAVY)
        r2 = p.add_run(); r2.text = body
        style_run(r2, size=11, color=INK_SOFT)

    add_card(slide, Inches(6.85), Inches(1.55), Inches(6.00), Inches(5.30),
             fill=NAVY)
    tb = add_textbox(slide, Inches(7.10), Inches(1.65),
                     Inches(5.55), Inches(0.45))
    add_paragraph(tb.text_frame, "What's next",
                  size=16, bold=True, color=GOLD, first=True)
    tb = add_textbox(slide, Inches(7.10), Inches(2.15),
                     Inches(5.55), Inches(4.65))
    tf = tb.text_frame
    first = True
    for label, body in nxt:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run(); r1.text = label + "\n"
        style_run(r1, size=12, bold=True, color=CYAN)
        r2 = p.add_run(); r2.text = body
        style_run(r2, size=11, color=LIGHT)


def build_takeaways_slide(prs):
    slide = new_content_slide(prs)
    add_section_header(slide, "Key Takeaways",
                       subtitle="What AstroBot proves we can deliver.")
    add_footer_bar(slide, presenter="Conclusion")

    items = [
        ("12+", "AI-powered features, all in one place — chat, image, OCR, RAG, voice, PDF, workflows."),
        ("66",  "Integration tests covering auth, chat, admin and features; runnable in one command."),
        ("3",   "Dockerised services on a single shared network — reproducible from a fresh VM."),
        ("4",   "Engineers, four roles, four months — no feature got dropped along the way."),
    ]
    top = Inches(1.55)
    h = Inches(2.25)
    w = Inches(3.05)
    gap = Inches(0.10)
    base_left = Inches(0.55)
    for i, (big, body) in enumerate(items):
        x = Emu(int(base_left) + i * (int(w) + int(gap)))
        add_card(slide, x, top, w, h, fill=NAVY)
        tb = add_textbox(slide, x, Emu(int(top) + int(Inches(0.25))),
                         w, Inches(1.10), anchor=MSO_ANCHOR.MIDDLE)
        add_paragraph(tb.text_frame, big,
                      size=64, bold=True, color=GOLD,
                      align=PP_ALIGN.CENTER, first=True)
        tb = add_textbox(slide,
                         Emu(int(x) + int(Inches(0.25))),
                         Emu(int(top) + int(Inches(1.40))),
                         Emu(int(w) - int(Inches(0.50))),
                         Inches(0.85))
        add_paragraph(tb.text_frame, body,
                      size=11, color=WHITE,
                      align=PP_ALIGN.CENTER, first=True)

    # Bottom one-liner
    add_card(slide, Inches(0.55), Inches(4.10), Inches(12.30), Inches(2.10),
             fill=LIGHT)
    tb = add_textbox(slide, Inches(0.55), Inches(4.10),
                     Inches(12.30), Inches(2.10),
                     anchor=MSO_ANCHOR.MIDDLE)
    tf = tb.text_frame
    add_paragraph(tf,
                  "AstroBot is not a demo — it is a working product.",
                  size=22, bold=True, color=NAVY,
                  align=PP_ALIGN.CENTER, first=True, space_after=10)
    add_paragraph(tf,
                  "Every feature shown today runs against the live VM at "
                  f"{LIVE_APP} — feel free to log in during Q&A.",
                  size=14, color=INK_SOFT, align=PP_ALIGN.CENTER, italic=True)


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

def main():
    print(f"[1/3] Opening template: {TEMPLATE.name}")
    prs = Presentation(str(TEMPLATE))
    if len(prs.slides) < 3:
        print("ERROR: template missing expected slides")
        sys.exit(1)

    print("[2/3] Reshaping cover, team and thanks slides ...")
    cover = prs.slides[0]
    example_slide = prs.slides[1]
    thanks = prs.slides[2]
    fix_cover(cover)
    fix_thanks(thanks)
    # Repurpose the template's example slide as the Team slide.
    # (We don't delete it: deleting + adding triggers a partname-collision
    # bug in python-pptx 1.0.x where two relationships end up pointing to
    # the same slide part.)
    repurpose_existing_slide_as_team(example_slide)
    print(f"      cover + team (reused) + thanks ready, building 27 more ...")

    print("[3/3] Building content slides ...")
    builders = [
        ("Agenda",                build_agenda_slide),
        # Part 1 — Sidi
        (None,                    lambda p: build_section_divider(
            p, "01", "Introduction & Vision",
            "Sidi Mohamed Sall",
            "Why AstroBot — the problem, the goals, the users.")),
        ("Problem",               build_problem_slide),
        ("Objectives",            build_objectives_slide),
        ("Users & landing",       build_users_landing_slide),
        # Part 2 — Tidiane
        (None,                    lambda p: build_section_divider(
            p, "02", "Architecture & Design",
            "Tidiane Konaté",
            "How the pieces fit together — services, data, security.")),
        ("Context diagram",       build_context_diagram_slide),
        ("Use-case diagram",      build_usecase_diagram_slide),
        ("Architecture",          build_architecture_slide),
        ("Tech stack",            build_techstack_slide),
        ("Database schema",       build_database_slide),
        ("n8n workflow",          build_n8n_slide),
        ("Security",              build_security_slide),
        # Part 3 — Ahmed
        (None,                    lambda p: build_section_divider(
            p, "03", "Implementation",
            "Ahmed Essalem",
            "The features — chat, multimedia, RAG, productivity.")),
        ("Chat experience",       build_chat_experience_slide),
        ("Rich content",          build_richcontent_slide),
        ("Image generation",      build_image_slide),
        ("PDF reports",           build_pdf_slide),
        ("OCR & vision",          build_ocr_vision_slide),
        ("RAG / Notebook",        build_rag_slide),
        ("Productivity",          build_productivity_slide),
        # Part 4 — Saad
        (None,                    lambda p: build_section_divider(
            p, "04", "Admin · Testing · Deployment",
            "Saad Ibrahim Houssein",
            "How we operate, audit and ship the product.")),
        ("Admin dashboard",       build_admin_dashboard_slide),
        ("User management",       build_user_mgmt_slide),
        ("User detail",           build_user_detail_slide),
        ("Testing",               build_testing_slide),
        ("Deployment",            build_deployment_slide),
        ("Lessons & roadmap",     build_demo_outcomes_slide),
        # Conclusion
        ("Takeaways",             build_takeaways_slide),
    ]
    for label, fn in builders:
        if label:
            print(f"      • {label}")
        else:
            print(f"      • (section divider)")
        fn(prs)

    # Reorder: state is [cover, team, thanks, agenda, sec1div, ...,
    # takeaways]. Move thanks (index 2) to the end.
    print(f"      moving thanks slide to the end ...")
    move_slide(prs, 2, len(prs.slides) - 1)

    # ── Apply transitions ─────────────────────────────────────────────
    # Cover gets a soft fade. Section dividers get a directional Push
    # (looks dramatic between parts). Everything else gets Morph,
    # which makes the recurring header bar / footer / cards glide
    # between slides — the deck feels like one continuous canvas.
    print("      adding slide transitions (Morph + Push + Fade) ...")
    n = len(prs.slides)
    for i, slide in enumerate(prs.slides):
        layout_name = slide.slide_layout.name.lower()
        if i == 0:
            add_simple_transition(slide, "fade", speed="med")
        elif i == n - 1:
            add_simple_transition(slide, "fade", speed="med")
        elif "bölüm ayracı" in layout_name or "ayracı" in layout_name:
            # Section divider — directional push for impact
            add_simple_transition(slide, "push", speed="med", direction="l")
        else:
            add_morph_transition(slide, speed="med", option="byObject")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"\nDone — wrote {len(prs.slides)} slides to:\n  {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
