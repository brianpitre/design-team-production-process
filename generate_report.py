#!/usr/bin/env python3
"""
Creative Space Task Summary Report — The Life Church
Design philosophy: Sacred Clarity
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black
import os
import math

# ─── Paths ────────────────────────────────────────────────────────────────────
FONTS_DIR = (
    "/Users/brianpitre/Library/Application Support/Claude/"
    "local-agent-mode-sessions/skills-plugin/"
    "8e885952-0c08-4e00-8e2e-348a16970533/"
    "68eef5e2-9471-464b-bd32-3acbb61b3737/skills/canvas-design/canvas-fonts"
)
OUTPUT = "/Users/brianpitre/Desktop/Claude/Design/Creative_Space_Report_Apr_Jul_2026.pdf"

# ─── Register Fonts ───────────────────────────────────────────────────────────
def reg(name, file):
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS_DIR, file)))

reg("Outfit-Regular",       "Outfit-Regular.ttf")
reg("Outfit-Bold",          "Outfit-Bold.ttf")
reg("Instrument-Regular",   "InstrumentSans-Regular.ttf")
reg("Instrument-Bold",      "InstrumentSans-Bold.ttf")
reg("Instrument-Italic",    "InstrumentSans-Italic.ttf")
reg("InstrumentSerif-Italic","InstrumentSerif-Italic.ttf")
reg("Italiana",             "Italiana-Regular.ttf")
reg("Lora-Regular",         "Lora-Regular.ttf")
reg("Lora-Bold",            "Lora-Bold.ttf")
reg("Lora-Italic",          "Lora-Italic.ttf")

# ─── Palette ──────────────────────────────────────────────────────────────────
INK        = HexColor("#2C1F2A")   # deep plum
PAPER      = HexColor("#FAF6F3")   # warm ivory
OFFWHITE   = HexColor("#FAF6F3")   # warm ivory
LIGHT_GRAY = HexColor("#E8D5DC")   # pale rose
MID_GRAY   = HexColor("#B08898")   # muted rose (was mid-gray)
DIM_GRAY   = HexColor("#7A6B72")   # warm dim tone
GOLD       = HexColor("#D4A5B5")   # dusty rose (replaces gold)
PETAL      = HexColor("#EDD5DE")   # soft blush pink
RULE       = HexColor("#E8D5DC")   # pale rose rule

W, H = letter   # 612 x 792

# ─── Helpers ──────────────────────────────────────────────────────────────────
def rule(c, x, y, w, color=RULE, thickness=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    c.line(x, y, x + w, y)

def filled_rect(c, x, y, w, h, color):
    c.setFillColor(color)
    c.rect(x, y, w, h, stroke=0, fill=1)

def text(c, x, y, s, font, size, color=INK, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "center":
        c.drawCentredString(x, y, s)
    elif align == "right":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)

def wrapped_text(c, x, y, s, font, size, max_width, line_height, color=INK):
    """Draw wrapped text, return final y position."""
    c.setFont(font, size)
    c.setFillColor(color)
    words = s.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= line_height
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_height
    return y

# ─── Page 1: Cover ────────────────────────────────────────────────────────────
def page_cover(c):
    # Warm ivory background
    filled_rect(c, 0, 0, W, H, PAPER)

    # Left blush side panel — elegant vertical stripe
    filled_rect(c, 0, 0, 0.18*inch, H, PETAL)

    # Delicate hairline fan — decorative pattern in upper half
    fan_cx = W / 2
    fan_cy = H - 2.8*inch
    n_lines = 28
    for i in range(n_lines):
        t = i / (n_lines - 1)
        angle = math.radians(-35 + t * 70)   # -35° to +35°
        length = (1.6 + t * 0.6) * inch
        x2 = fan_cx + math.sin(angle) * length
        y2 = fan_cy - math.cos(angle) * length
        alpha = 0.18 + 0.22 * (1 - abs(t - 0.5) * 2)
        # Blend PETAL → BLUSH → PETAL
        if t < 0.5:
            col = HexColor("#D4A5B5")
        else:
            col = HexColor("#EDD5DE")
        c.setStrokeColor(col)
        c.setLineWidth(0.35)
        c.line(fan_cx, fan_cy, x2, y2)

    # Top thin rose rule
    rule(c, 0.55*inch, H - 0.6*inch, W - 0.73*inch, color=GOLD, thickness=0.6)

    # Church name
    text(c, W/2, H - 1.0*inch, "The Life Church",
         "Lora-Italic", 10, color=GOLD, align="center")

    # Main display title — Italiana for tall elegant letterforms
    text(c, W/2, H - 2.35*inch, "Creative",
         "Italiana", 88, color=INK, align="center")
    text(c, W/2, H - 3.2*inch, "Space",
         "Italiana", 88, color=INK, align="center")

    # Thin central divider
    rule(c, 1.1*inch, H - 3.6*inch, W - 2.2*inch, color=GOLD, thickness=0.5)

    # Report descriptor
    text(c, W/2, H - 4.0*inch, "Task Summary Report",
         "Lora-Regular", 11, color=MID_GRAY, align="center")

    # Date range
    text(c, W/2, H - 4.55*inch, "April  —  July 2026",
         "Lora-Italic", 20, color=INK, align="center")

    # Delicate horizontal hairlines — lower section
    base_y = 2.8*inch
    spacing = 0.095*inch
    thicknesses = [0.6, 0.35, 0.25, 0.35, 0.6, 0.25, 0.35]
    colors_h = [GOLD, PETAL, GOLD, PETAL, GOLD, PETAL, GOLD]
    margins   = [0.55, 0.8, 1.1, 0.8, 0.55, 1.1, 0.8]
    for i, (th, ch, mg) in enumerate(zip(thicknesses, colors_h, margins)):
        ry = base_y - i * spacing
        rule(c, mg*inch, ry, W - 2*mg*inch, color=ch, thickness=th)

    # Bottom metadata
    text(c, W/2, 0.52*inch,
         "Memphis  ·  Creative (Memphis) Space  ·  Generated April 2026",
         "Outfit-Regular", 7, color=MID_GRAY, align="center")

    # Bottom rule
    rule(c, 0.55*inch, 0.42*inch, W - 0.73*inch, color=GOLD, thickness=0.6)

# ─── Page 2: Team + Quarter Overview ─────────────────────────────────────────
def page_overview(c):
    filled_rect(c, 0, 0, W, H, PAPER)

    # Left blush side panel
    filled_rect(c, 0, 0, 0.18*inch, H, PETAL)

    # Header band — deep plum
    filled_rect(c, 0, H - 1.05*inch, W, 1.05*inch, INK)
    text(c, 0.45*inch, H - 0.42*inch, "The Life Church",
         "Lora-Italic", 8, color=GOLD)
    text(c, W - 0.55*inch, H - 0.42*inch, "Creative Space  ·  Q2 2026",
         "Instrument-Regular", 7.5, color=MID_GRAY, align="right")
    rule(c, 0.45*inch, H - 0.6*inch, W - 0.9*inch, color=HexColor("#4A3545"), thickness=0.3)
    text(c, 0.45*inch, H - 0.88*inch, "Overview",
         "Italiana", 28, color=PAPER)

    # ── Active Team Members ────────────────────────────────────────────────────
    y = H - 1.45*inch
    text(c, 0.45*inch, y, "Active Team Members",
         "Lora-Bold", 8, color=GOLD)
    y -= 0.16*inch
    rule(c, 0.45*inch, y, W - 0.9*inch, color=LIGHT_GRAY, thickness=0.5)
    y -= 0.24*inch

    members = [
        "Olivia McCrimon", "Lizzie Miller", "Camilo Espinel",
        "Chris Steen", "Carlos Hernández", "Daniel Gamboa",
        "Caleb Chunn", "Zach VanBlaricom", "Anna Siebeling",
        "Caleb Trinidad", "Johnny Hill", "Emma Pier",
        "Jane Lawson", "Jonathon Willcox",
    ]

    col_w = (W - 0.9*inch) / 3
    for i, m in enumerate(members):
        col = i % 3
        row = i // 3
        mx = 0.45*inch + col * col_w
        my = y - row * 0.22*inch
        c.setFillColor(GOLD)
        c.circle(mx + 0.07*inch, my + 0.045*inch, 0.028*inch, stroke=0, fill=1)
        text(c, mx + 0.17*inch, my, m, "Instrument-Regular", 9, color=DIM_GRAY)

    y -= (((len(members) - 1) // 3) + 1) * 0.22*inch + 0.32*inch

    # ── Quarter at a Glance ────────────────────────────────────────────────────
    text(c, 0.45*inch, y, "Quarter at a Glance",
         "Lora-Bold", 8, color=GOLD)
    y -= 0.16*inch
    rule(c, 0.45*inch, y, W - 0.9*inch, color=LIGHT_GRAY, thickness=0.5)
    y -= 0.06*inch

    months = [
        ("April",
         "Axis Conference graphics kickoff · 30th Anniversary deliverables · "
         "Video opener refresh · Zoe Conference final approvals · "
         "Outsourcing: YouTube Header · Print & Capture kick off"),
        ("May",
         "Axis Conference full production phase (openers, loops, backgrounds) · "
         "Zoe Conference promo launch & website · 2026 Series assets continue · "
         "Life Leadership Capture events · Content Refresh: Easter/Summer"),
        ("June",
         "Axis Conference final deliveries & event · Merch shoot (June 4) · "
         "Father's Day assets · Series design work continues · "
         "Zoe website fully live · Next Gen Building banner installed"),
        ("July",
         "2026 Series wrap-up (Legacy, Pocket Change) · Next Gen Building promo · "
         "Zoe Conference in-church promo · Sound of Christmas early prep · "
         "Content Refresh: Back to School"),
    ]

    col_w2 = (W - 0.9*inch) / 4
    for i, (month, desc) in enumerate(months):
        mx = 0.45*inch + i * col_w2
        my = y

        # Month label — soft PETAL band with plum text
        filled_rect(c, mx, my - 0.27*inch, col_w2 - 0.08*inch, 0.27*inch, PETAL)
        text(c, mx + (col_w2 - 0.08*inch)/2, my - 0.19*inch, month,
             "Lora-Bold", 11, color=INK, align="center")

        dy = my - 0.37*inch
        words = desc.split(" · ")
        for bullet in words:
            c.setFillColor(GOLD)
            c.circle(mx + 0.07*inch, dy + 0.055*inch, 0.02*inch, stroke=0, fill=1)
            dy = wrapped_text(c, mx + 0.17*inch, dy, bullet,
                              "Instrument-Regular", 7.6,
                              col_w2 - 0.3*inch, 0.13*inch,
                              color=DIM_GRAY)
            dy -= 0.04*inch

    # Footer
    rule(c, 0.45*inch, 0.45*inch, W - 0.9*inch, color=LIGHT_GRAY)
    text(c, 0.45*inch, 0.28*inch, "Creative Space  ·  Task Summary Report  ·  April–July 2026",
         "Instrument-Regular", 7, color=MID_GRAY)
    text(c, W - 0.55*inch, 0.28*inch, "2",
         "Lora-Regular", 8, color=MID_GRAY, align="right")

# ─── Page 3 & 4: Project Summaries ───────────────────────────────────────────
PROJECTS = [
    {
        "name": "Axis Conference 2026",
        "dates": "April 20 – June 25",
        "tasks": "~50 tasks",
        "status": "NOT STARTED",
        "urgent": True,
        "assignees": "Camilo Espinel · Lizzie Miller · Zach VanBlaricom · Anna Siebeling · Caleb Trinidad · Johnny Hill",
        "summary": (
            "The largest active project in this window, spanning the full quarter with "
            "deliverables across graphics, motion, merch, and print."
        ),
        "phases": [
            ("APRIL — Design Phase",
             "10+ graphic look concepts including Thank You (Vol/YP), Game Changer, You Rock, "
             "Tribal War, Serve Day, Wristbands. First graphic review meeting with Anna & Zach."),
            ("MAY — Production Phase",
             "All video openers (Mon–Thu) in production. Worship background loops for 4 nights, "
             "lobby loops, countdowns (2 & 10 min), walkin loops. Merch garments ordered. "
             "Serve shirts designed and ordered."),
            ("JUNE — Final Delivery",
             "All openers due for final review. Merch shoot June 4. Print installs ordered and "
             "handed off. Recap video and message cover images due late June. Conference runs mid-June."),
        ],
    },
    {
        "name": "Zoe Conference",
        "dates": "April 21 – July 26",
        "tasks": "11 tasks",
        "status": "NOT STARTED",
        "urgent": False,
        "assignees": "Lizzie Miller · Jane Lawson",
        "summary": "Ramps up through May with a soft launch targeting Mother's Day weekend, culminating in full in-church promo by late July.",
        "phases": [
            ("APRIL",
             "Final graphic approved. Zoe Promo Plan reviewed with Erin & Ps. Leslie. Save the Date Email sent."),
            ("MAY",
             "Brushfire assets, promo assets for weekends, website design completed, custom book "
             "jacket for The Story Bible, soft launch on Mother's Day (tentative)."),
            ("JULY",
             "Promo booths design finalized. Promo launches in-church. Website copy live."),
        ],
    },
    {
        "name": "2026 Series",
        "dates": "April 23 – July 23",
        "tasks": "7 tasks",
        "status": "NOT STARTED",
        "urgent": False,
        "assignees": "Lizzie Miller · Camilo Espinel",
        "summary": "Ongoing series artwork and design work running in parallel to all major event projects throughout the quarter.",
        "phases": [
            ("APRIL", "Design work begins for Under New Management and Legacy series."),
            ("MAY", "Series assets delivered for Under New Management and Under the Sun."),
            ("JULY", "Legacy Series assets, Pocket Change Series assets, and Pocket Change design work all due."),
        ],
    },
    {
        "name": "Next Gen Building Project",
        "dates": "April 22 – July 13",
        "tasks": "6 tasks",
        "status": "NOT STARTED",
        "urgent": True,
        "assignees": "Lizzie Miller · Emma Pier",
        "summary": "Design and production support for the Next Gen Building campaign, from banner redesign through groundbreaking promo.",
        "phases": [
            ("APRIL", "Redesign of the Next Gen Building banner (urgent)."),
            ("MAY", "Source hammers. Order banner to arrive on time. LED loop of module stories begins."),
            ("JULY", "Hammers arrive by deadline. Promo video for Do It for Them & Groundbreaking (plays in July) completed."),
        ],
    },
    {
        "name": "The Sound of Christmas 2026",
        "dates": "May 21 – July 31",
        "tasks": "3 tasks",
        "status": "NOT STARTED",
        "urgent": False,
        "assignees": "Lizzie Miller · Jane Lawson",
        "summary": "Early pre-production beginning this quarter. Song selection and look development precede full production later in the year.",
        "phases": [
            ("MAY", "Song selection for SOC 2026 finalized."),
            ("JULY", "Refresh look for SOC 2026 completed. Seating logistics set up."),
        ],
    },
    {
        "name": "30th Anniversary Vision Season",
        "dates": "April 21–22",
        "tasks": "2 tasks",
        "status": "NOT STARTED",
        "urgent": False,
        "assignees": "Lizzie Miller",
        "summary": "Two focused deliverables early in the period establishing the visual identity for the 30th anniversary.",
        "phases": [
            ("APRIL", "30-year logo mark (forward style) and a 30-year timeline graphic for August installation — both due."),
        ],
    },
    {
        "name": "Video Production",
        "dates": "April 20–23",
        "tasks": "3 tasks",
        "status": "NOT STARTED",
        "urgent": False,
        "assignees": "Olivia McCrimon · Daniel Gamboa · Caleb Chunn",
        "summary": "Short-term deliverables at the opening of the quarter focused on weekend service production.",
        "phases": [
            ("APRIL", "Service opener refresh — motion graphics and editing phases. Axis recurring video."),
        ],
    },
    {
        "name": "Supporting Projects",
        "dates": "April 20 – June 21",
        "tasks": "8 tasks across 5 lists",
        "status": "MIXED",
        "urgent": False,
        "assignees": "Olivia McCrimon · Lizzie Miller · Camilo Espinel · Chris Steen · Carlos Hernández",
        "summary": "A collection of smaller ongoing projects running in parallel.",
        "phases": [
            ("DIGITAL",
             "Axis event & lead week assets. May calendar social post (Olivia McCrimon)."),
            ("PRINT",
             "Discovery Lessons 1 & 2. HSL GreenRoom Vision Wall (currently in review)."),
            ("CAPTURE",
             "Life Leadership Team Ruck (April 27) and Life Leadership Capture #10 — May (May 13)."),
            ("MERCH",
             "Press Cafe Aprons due June 4 (Olivia McCrimon)."),
            ("OUTSOURCING",
             "Refresh YouTube Header — due April 21 (Olivia McCrimon & Jonathon Willcox). "
             "Content Refresh: Easter/Summer (May) and Back to School (July)."),
        ],
    },
]

def page_projects(c, projects_slice, page_num):
    filled_rect(c, 0, 0, W, H, PAPER)

    # Left blush side panel
    filled_rect(c, 0, 0, 0.18*inch, H, PETAL)

    # Header band — deep plum
    filled_rect(c, 0, H - 0.6*inch, W, 0.6*inch, INK)
    text(c, 0.45*inch, H - 0.36*inch, "The Life Church",
         "Lora-Italic", 8, color=GOLD)
    text(c, W - 0.55*inch, H - 0.36*inch, "Creative Space  ·  Q2 2026",
         "Instrument-Regular", 7.5, color=MID_GRAY, align="right")

    y = H - 0.82*inch

    for proj in projects_slice:
        # Project header — plum band with blush accent
        filled_rect(c, 0.45*inch, y - 0.3*inch, W - 0.9*inch, 0.3*inch, INK)

        # Urgent indicator — blush left bar
        if proj.get("urgent"):
            filled_rect(c, 0.45*inch, y - 0.3*inch, 0.045*inch, 0.3*inch, GOLD)

        text(c, 0.57*inch, y - 0.21*inch, proj["name"],
             "Italiana", 15, color=PAPER)
        text(c, W - 0.6*inch, y - 0.205*inch,
             proj["dates"] + "  ·  " + proj["tasks"],
             "Instrument-Regular", 7.2, color=MID_GRAY, align="right")

        y -= 0.37*inch

        # Assignees row
        text(c, 0.45*inch, y, "Assigned to",
             "Lora-Bold", 6.5, color=GOLD)
        text(c, 1.25*inch, y, proj["assignees"],
             "InstrumentSerif-Italic", 7.5, color=DIM_GRAY)
        y -= 0.17*inch

        # Summary
        y_after = wrapped_text(c, 0.45*inch, y, proj["summary"],
                               "Instrument-Regular", 8.5,
                               W - 0.9*inch, 0.145*inch, color=DIM_GRAY)
        y = y_after - 0.09*inch

        # Phases
        for phase_title, phase_desc in proj["phases"]:
            filled_rect(c, 0.45*inch, y, 0.038*inch, 0.125*inch, GOLD)
            text(c, 0.57*inch, y, phase_title,
                 "Lora-Bold", 7, color=INK)
            y -= 0.155*inch
            y_after = wrapped_text(c, 0.57*inch, y, phase_desc,
                                   "Instrument-Regular", 7.8,
                                   W - 1.2*inch, 0.135*inch, color=DIM_GRAY)
            y = y_after - 0.045*inch

        rule(c, 0.45*inch, y, W - 0.9*inch, color=LIGHT_GRAY, thickness=0.4)
        y -= 0.22*inch

        if y < 0.85*inch:
            break

    # Footer
    rule(c, 0.45*inch, 0.45*inch, W - 0.9*inch, color=LIGHT_GRAY)
    text(c, 0.45*inch, 0.28*inch, "Creative Space  ·  Task Summary Report  ·  April–July 2026",
         "Instrument-Regular", 7, color=MID_GRAY)
    text(c, W - 0.55*inch, 0.28*inch, str(page_num),
         "Lora-Regular", 8, color=MID_GRAY, align="right")

# ─── Build PDF ────────────────────────────────────────────────────────────────
def build():
    c = canvas.Canvas(OUTPUT, pagesize=letter)
    c.setTitle("Creative Space Task Summary Report — Apr–Jul 2026")
    c.setAuthor("The Life Church")

    # Cover
    page_cover(c)
    c.showPage()

    # Overview
    page_overview(c)
    c.showPage()

    # Projects — split across pages
    # Page 3: first 3 projects
    page_projects(c, PROJECTS[:3], 3)
    c.showPage()

    # Page 4: next 3 projects
    page_projects(c, PROJECTS[3:6], 4)
    c.showPage()

    # Page 5: remaining projects
    page_projects(c, PROJECTS[6:], 5)
    c.showPage()

    c.save()
    print(f"✓ PDF saved to: {OUTPUT}")

if __name__ == "__main__":
    build()
