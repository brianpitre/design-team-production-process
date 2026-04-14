#!/usr/bin/env python3
"""
generate_html_report.py — WAT Tool
Reads .tmp/clickup_tasks.json and generates event_report_2026.html —
a one-panel-per-event SUMMARY report in thelifechurch.com design language.

Read-only with respect to ClickUp — only writes local HTML file.
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
TASKS_FILE = ROOT / ".tmp" / "clickup_tasks.json"
OUTPUT_FILE = ROOT / "event_report_2026.html"

# ── Events (from RTF) ─────────────────────────────────────────────────────────
EVENTS = [
    {
        "key": "series",
        "name": "2026 Series",
        "dates": "Multiple dates (see ClickUp)",
        "rehearsal": None,
        "deadline": datetime(2026, 12, 31),
        "color": "#0693e3",
        "icon": "📺",
    },
    {
        "key": "mothers_day",
        "name": "Mother's Day",
        "dates": "May 10, 2026",
        "rehearsal": None,
        "deadline": datetime(2026, 5, 10),
        "color": "#e91e8c",
        "icon": "🌸",
    },
    {
        "key": "fathers_day",
        "name": "Father's Day",
        "dates": "June 21, 2026",
        "rehearsal": None,
        "deadline": datetime(2026, 6, 21),
        "color": "#1565c0",
        "icon": "👔",
    },
    {
        "key": "axis",
        "name": "Axis Conference",
        "dates": "June 22–25, 2026",
        "rehearsal": "Content needed by June 11",
        "deadline": datetime(2026, 6, 11),
        "color": "#ff6900",
        "icon": "🎯",
    },
    {
        "key": "quarterly",
        "name": "Quarterly Refreshes",
        "dates": "Aug 9, 2026 · Screens assets due July 30",
        "rehearsal": None,
        "deadline": datetime(2026, 7, 30),
        "color": "#00d084",
        "icon": "🔄",
    },
    {
        "key": "zoe",
        "name": "Zoe Conference",
        "dates": "Sept 25–26, 2026",
        "rehearsal": "Content needed by Sept 17",
        "deadline": datetime(2026, 9, 17),
        "color": "#9b51e0",
        "icon": "✨",
    },
    {
        "key": "anniversary",
        "name": "30th Anniversary Vision Season",
        "dates": "Oct 11 – Nov 15, 2026",
        "rehearsal": None,
        "deadline": datetime(2026, 10, 11),
        "color": "#d4a017",
        "icon": "🎂",
    },
    {
        "key": "christmas",
        "name": "The Sound of Christmas",
        "dates": "Dec 18–19, 2026",
        "rehearsal": "Content needed by Dec 10",
        "deadline": datetime(2026, 12, 10),
        "color": "#c62828",
        "icon": "🎄",
    },
]

# ── List name → event key ─────────────────────────────────────────────────────
LIST_MAP = {
    "2026 series":                    "series",
    "next gen building project":      "series",
    "revival nights":                 "series",
    "makeroom":                       "series",
    "vision partner spring event":    "series",
    "easter":                         "series",
    "mother's day":                   "mothers_day",
    "father's day":                   "fathers_day",
    "axis conference 2026":           "axis",
    "quarterly refreshes":            "quarterly",
    "zoe conference":                 "zoe",
    "30th anniversary vision season": "anniversary",
    "the sound of christmas":         "christmas",
    "christmas at the life church":   "christmas",
}

def match_task_to_event(task):
    space = (task.get("_space_name") or "").lower()
    if "creative" not in space:
        return None
    folder = (task.get("_folder_name") or "").lower()
    if "2026" not in folder or "planned" not in folder:
        return None
    lst = (task.get("_list_name") or "").lower()
    for list_key, event_key in LIST_MAP.items():
        if list_key in lst:
            return event_key
    return None

def is_closed(task):
    s = (task.get("status") or {}).get("status", "").lower().strip()
    return (s.startswith("completed") or s.startswith("approved")
            or s.startswith("closed") or s in ("done", "complete"))

def format_ts(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts) / 1000)
    except Exception:
        return None

def fmt_date(dt):
    if not dt:
        return None
    return dt.strftime("%b %-d, %Y")

# ── Categorize tasks ──────────────────────────────────────────────────────────
CATEGORIES = [
    ("Graphic Design",    ["graphic", "design", "logo", "banner", "art", "artwork",
                           "slide", "background", "visual", "branding", "look", "concept",
                           "poster", "flyer", "social", "asset", "print"]),
    ("Motion Graphics",   ["motion", "opener", "loop", "animation", "led loop"]),
    ("Video Production",  ["video", "edit", "recap", "film", "footage", "reel", "promo video"]),
    ("Capture / Photo",   ["capture", "photo", "shoot", "cinemat", "photograph"]),
    ("Script / Copy",     ["script", "copy", "write", "caption", "lyric", "email",
                           "announcement", "content", "story", "message"]),
    ("Merch / Print",     ["merch", "shirt", "wristband", "garment", "apparel",
                           "order", "print", "install", "banner install", "signage"]),
    ("Project Mgmt",      ["manage", "project", "coordinate", "milestone", "review",
                           "approval", "handoff", "delivery", "plan"]),
    ("Worship / Songs",   ["song", "worship", "setlist", "music", "rehearsal"]),
    ("Website / Digital", ["website", "web", "brushfire", "digital", "social media",
                           "youtube", "online"]),
]

def categorize_task(name):
    n = name.lower()
    for cat_name, keywords in CATEGORIES:
        if any(kw in n for kw in keywords):
            return cat_name
    return "Other"

# ── Collect assignees from tasks ──────────────────────────────────────────────
def collect_assignees(tasks):
    """Return sorted list of unique assignee names from ClickUp data."""
    names = set()
    for t in tasks:
        for a in (t.get("assignees") or []):
            name = (a.get("username") or a.get("email") or "").strip()
            if name and "@" not in name:
                names.add(name.title())
    return sorted(names)

# ── Propose assignees based on categories present ─────────────────────────────
ROLE_MAP = {
    "Graphic Design":    ["Lizzie Miller", "Camilo Espinel"],
    "Motion Graphics":   ["Daniel Gamboa", "Chris Steen"],
    "Video Production":  ["Caleb Chunn", "Chris Steen"],
    "Capture / Photo":   ["Carlos Hernandez", "Chris Steen"],
    "Script / Copy":     ["Parker VanBlaricom", "Ben Forehand"],
    "Merch / Print":     ["Olivia McCrimmon"],
    "Project Mgmt":      ["Olivia McCrimmon"],
    "Worship / Songs":   ["Johnny Hill"],
    "Website / Digital": ["Lizzie Miller", "Parker VanBlaricom"],
}

def propose_team(categories_present):
    proposed = set()
    for cat in categories_present:
        for name in ROLE_MAP.get(cat, []):
            proposed.add(name)
    return sorted(proposed)

# ── Upcoming tasks (nearest due dates) ───────────────────────────────────────
def upcoming_tasks(open_tasks, n=5):
    """Return up to n open tasks with the nearest actual due dates."""
    dated = [(t, format_ts(t.get("due_date")))
             for t in open_tasks if t.get("due_date") and not t.get("parent")]
    dated.sort(key=lambda x: x[1])
    return dated[:n]

# ── Status breakdown ─────────────────────────────────────────────────────────
def status_breakdown(top_level_tasks):
    counts = Counter()
    for t in top_level_tasks:
        s = (t.get("status") or {}).get("status", "to do").lower()
        if s.startswith("completed") or s.startswith("approved") or s.startswith("closed"):
            counts["complete"] += 1
        elif "in progress" in s:
            counts["in progress"] += 1
        elif "review" in s or "waiting" in s or "update" in s:
            counts["in review"] += 1
        else:
            counts["not started"] += 1
    return counts

# ── HTML helpers ──────────────────────────────────────────────────────────────
def _esc(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

def status_pill(label, count, color, bg):
    if count == 0:
        return ""
    return (f'<span class="status-pill" style="color:{color};background:{bg};">'
            f'{count} {label}</span>')

# ── Event panel HTML ──────────────────────────────────────────────────────────
def event_panel_html(event, tasks, idx):
    bg = "#ffffff" if idx % 2 == 0 else "#f5f5f7"

    top_level = [t for t in tasks if not t.get("parent")]
    open_tasks = [t for t in top_level if not is_closed(t)]
    closed_tasks = [t for t in top_level if is_closed(t)]

    total = len(top_level)
    open_count = len(open_tasks)
    closed_count = len(closed_tasks)

    # Status breakdown
    breakdown = status_breakdown(top_level)

    # Category breakdown
    cat_counts = Counter(categorize_task(t.get("name", "")) for t in open_tasks)
    categories = [cat for cat, _ in sorted(cat_counts.items(),
                                            key=lambda x: -x[1]) if cat != "Other"]

    # Actual assignees from ClickUp
    actual_assignees = collect_assignees(tasks)

    # Proposed assignees (for unassigned tasks based on categories present)
    proposed = propose_team(categories)
    # Only suggest people not already in ClickUp data
    extra_proposed = [p for p in proposed if p not in actual_assignees]

    # Upcoming tasks (nearest due dates, top-level only)
    upcoming = upcoming_tasks(open_tasks)

    # Days until event
    now = datetime.now()
    days_left = (event["deadline"] - now).days
    if days_left < 0:
        days_str = "Past"
        days_color = "#6b7280"
    elif days_left <= 30:
        days_str = f"{days_left}d away"
        days_color = "#c62828"
    elif days_left <= 90:
        days_str = f"{days_left}d away"
        days_color = "#ff6900"
    else:
        days_str = f"{days_left}d away"
        days_color = "#00d084"

    # Rehearsal note
    rehearsal_html = ""
    if event["rehearsal"]:
        rehearsal_html = f'<div class="panel-rehearsal">{_esc(event["rehearsal"])}</div>'

    # Status pills
    pills = "".join([
        status_pill("not started", breakdown["not started"], "#6b7280", "#f3f4f6"),
        status_pill("in progress", breakdown["in progress"], "#0693e3", "#e8f4fd"),
        status_pill("in review",   breakdown["in review"],   "#ff6900", "#fff3eb"),
        status_pill("complete",    breakdown["complete"],    "#00d084", "#e6faf3"),
    ])

    # Category tags
    cat_tags = "".join(
        f'<span class="cat-tag">{_esc(cat)} <em>({cat_counts[cat]})</em></span>'
        for cat in categories[:6]
    )
    if not cat_tags:
        cat_tags = '<span class="cat-tag no-tasks">No open tasks in ClickUp</span>'

    # Upcoming tasks list
    if upcoming:
        upcoming_items = "".join(
            f'<li><span class="task-due">{fmt_date(dt)}</span> {_esc(t["name"][:65])}'
            + ("…" if len(t.get("name","")) > 65 else "")
            + '</li>'
            for t, dt in upcoming
        )
        upcoming_html = f'<ul class="upcoming-list">{upcoming_items}</ul>'
    elif open_count == 0 and closed_count > 0:
        upcoming_html = '<p class="no-upcoming">All tasks are complete.</p>'
    else:
        upcoming_html = '<p class="no-upcoming">No due dates set in ClickUp yet.</p>'

    # Assignees
    assignee_items = ""
    for name in actual_assignees:
        assignee_items += (f'<span class="assignee-chip actual">'
                           f'<span class="chip-dot"></span>{_esc(name)}</span>')
    for name in extra_proposed:
        assignee_items += (f'<span class="assignee-chip proposed" '
                           f'title="Proposed based on task types">'
                           f'<span class="chip-dot"></span>{_esc(name)} '
                           f'<em>proposed</em></span>')
    if not assignee_items:
        assignee_items = '<span class="no-assignees">No assignees set in ClickUp</span>'

    return f"""
  <section class="event-panel" style="background:{bg};" id="{event['key']}">
    <div class="panel-inner">

      <!-- Left: event identity -->
      <div class="panel-left">
        <div class="panel-icon" style="background:{event['color']}22;color:{event['color']};">{event['icon']}</div>
        <div class="panel-eyebrow">EVENT</div>
        <h2 class="panel-title" style="color:{event['color']};">{_esc(event['name'])}</h2>
        <div class="panel-date">{_esc(event['dates'])}</div>
        {rehearsal_html}
        <div class="panel-countdown" style="color:{days_color};">{days_str}</div>
        <div class="panel-task-counts">
          <span class="count-open">{open_count} open</span>
          <span class="count-sep">·</span>
          <span class="count-closed">{closed_count} done</span>
          <span class="count-sep">·</span>
          <span class="count-total">{total} total</span>
        </div>
        <div class="panel-status-pills">{pills}</div>
      </div>

      <!-- Right: details -->
      <div class="panel-right">

        <!-- Task categories -->
        <div class="panel-section">
          <div class="panel-section-label">Work Types</div>
          <div class="cat-tags">{cat_tags}</div>
        </div>

        <!-- Upcoming due dates -->
        <div class="panel-section">
          <div class="panel-section-label">Nearest Due Dates</div>
          {upcoming_html}
        </div>

        <!-- Team -->
        <div class="panel-section">
          <div class="panel-section-label">
            Team
            <span class="legend-inline">
              <span class="dot-actual"></span> in ClickUp
              <span class="dot-proposed"></span> proposed
            </span>
          </div>
          <div class="assignee-chips">{assignee_items}</div>
        </div>

      </div>
    </div>
  </section>"""

def nav_pill(event):
    return (f'<a href="#{event["key"]}" class="nav-pill" '
            f'style="--pill-color:{event["color"]};">{_esc(event["name"])}</a>')

# ── Full HTML ─────────────────────────────────────────────────────────────────
def build_html(tasks_by_event, total_matched):
    generated = datetime.now().strftime("%B %-d, %Y at %-I:%M %p")
    nav_pills = "".join(nav_pill(e) for e in EVENTS)
    panels = "".join(
        event_panel_html(event, tasks_by_event.get(event["key"], []), idx)
        for idx, event in enumerate(EVENTS)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>2026 Creative Events Report — The Life Church</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --color-text: #32373c;
      --color-text-light: #6b7280;
      --color-nav: #32373c;
      --radius: 12px;
      --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.05);
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', Arial, sans-serif; background: #fff;
            color: var(--color-text); line-height: 1.6; }}

    /* NAV */
    .site-nav {{
      position: sticky; top: 0; z-index: 100;
      background: var(--color-nav); padding: 0 40px; height: 58px;
      display: flex; align-items: center; justify-content: space-between;
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .nav-brand {{ display: flex; align-items: center; gap: 10px;
                  color: #fff; font-weight: 700; font-size: 15px;
                  letter-spacing: -0.01em; text-decoration: none; }}
    .brand-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #0693e3; }}
    .nav-sub {{ color: rgba(255,255,255,0.5); font-size: 13px; }}

    /* HERO */
    .hero {{ background: #1a1a1a; color: #fff;
             padding: 72px 40px 64px; text-align: center; }}
    .hero-eyebrow {{
      display: inline-block; background: rgba(255,255,255,0.10);
      border-radius: 9999px; font-size: 11px; font-weight: 700;
      letter-spacing: 0.12em; text-transform: uppercase;
      padding: 5px 16px; margin-bottom: 18px; color: rgba(255,255,255,0.65);
    }}
    .hero h1 {{
      font-size: clamp(30px, 4.5vw, 50px); font-weight: 800;
      letter-spacing: -0.025em; line-height: 1.1; margin-bottom: 14px;
    }}
    .hero h1 span {{ color: #0693e3; }}
    .hero-sub {{ font-size: 15px; color: rgba(255,255,255,0.5); margin-bottom: 32px; }}
    .hero-stats {{
      display: flex; justify-content: center; gap: 40px;
      flex-wrap: wrap; margin-bottom: 32px;
    }}
    .hero-stat-number {{ font-size: 30px; font-weight: 800; color: #fff; }}
    .hero-stat-label {{
      font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
      text-transform: uppercase; color: rgba(255,255,255,0.4);
    }}
    .hero-pills {{ display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }}
    .nav-pill {{
      display: inline-block; padding: 6px 16px; border-radius: 9999px;
      font-size: 12px; font-weight: 600;
      background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.7);
      text-decoration: none; border: 1px solid rgba(255,255,255,0.12);
      transition: background 0.15s, color 0.15s;
    }}
    .nav-pill:hover {{ background: var(--pill-color, #0693e3);
                       color: #fff; border-color: transparent; }}

    /* LEGEND BAR */
    .legend-bar {{
      background: #f5f5f7; border-bottom: 1px solid #e5e7eb;
      padding: 10px 48px; display: flex; align-items: center;
      gap: 20px; flex-wrap: wrap; font-size: 12px; color: var(--color-text-light);
    }}
    .legend-chip {{
      display: inline-block; padding: 2px 10px; border-radius: 9999px;
      font-size: 11px; font-weight: 600;
    }}

    /* EVENT PANELS */
    .event-panel {{ padding: 52px 0; }}
    .panel-inner {{
      max-width: 1200px; margin: 0 auto; padding: 0 48px;
      display: grid; grid-template-columns: 220px 1fr; gap: 48px;
      align-items: start;
    }}

    /* LEFT COLUMN */
    .panel-icon {{
      width: 52px; height: 52px; border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 24px; margin-bottom: 12px;
    }}
    .panel-eyebrow {{
      font-size: 10px; font-weight: 700; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--color-text-light);
      margin-bottom: 4px;
    }}
    .panel-title {{
      font-size: 20px; font-weight: 800; letter-spacing: -0.02em;
      line-height: 1.2; margin-bottom: 8px;
    }}
    .panel-date {{ font-size: 13px; font-weight: 600; color: var(--color-text); margin-bottom: 4px; }}
    .panel-rehearsal {{
      font-size: 12px; color: #92400e; background: #fef3c7;
      padding: 3px 10px; border-radius: 6px; margin-bottom: 8px;
      display: inline-block;
    }}
    .panel-countdown {{
      font-size: 12px; font-weight: 700; margin-bottom: 10px;
    }}
    .panel-task-counts {{
      font-size: 12px; color: var(--color-text-light);
      display: flex; gap: 5px; align-items: center; margin-bottom: 10px;
    }}
    .count-open {{ font-weight: 700; color: var(--color-text); }}
    .count-closed {{ color: #00d084; font-weight: 600; }}
    .count-sep {{ opacity: 0.4; }}
    .panel-status-pills {{ display: flex; flex-direction: column; gap: 4px; }}
    .status-pill {{
      display: inline-block; padding: 3px 10px; border-radius: 9999px;
      font-size: 11px; font-weight: 600; width: fit-content;
    }}

    /* RIGHT COLUMN */
    .panel-right {{ display: flex; flex-direction: column; gap: 24px; }}
    .panel-section {{ }}
    .panel-section-label {{
      font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--color-text-light);
      margin-bottom: 8px; display: flex; align-items: center; gap: 10px;
    }}

    /* Category tags */
    .cat-tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .cat-tag {{
      padding: 5px 12px; border-radius: 8px;
      font-size: 12px; font-weight: 600;
      background: #f5f5f7; color: var(--color-text);
    }}
    .cat-tag em {{ font-style: normal; color: var(--color-text-light); font-weight: 400; }}
    .cat-tag.no-tasks {{ color: var(--color-text-light); background: #f9fafb; }}

    /* Upcoming list */
    .upcoming-list {{
      list-style: none; display: flex; flex-direction: column; gap: 6px;
    }}
    .upcoming-list li {{
      font-size: 13px; display: flex; align-items: baseline; gap: 10px;
      padding: 6px 10px; background: #fff; border-radius: 8px;
      border: 1px solid #e5e7eb;
    }}
    .task-due {{
      font-size: 11px; font-weight: 700; color: #0693e3;
      white-space: nowrap; flex-shrink: 0;
    }}
    .no-upcoming {{ font-size: 13px; color: var(--color-text-light); font-style: italic; }}

    /* Assignee chips */
    .assignee-chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .assignee-chip {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 9999px;
      font-size: 12px; font-weight: 600;
    }}
    .assignee-chip.actual {{
      background: #e8f4fd; color: #0693e3;
    }}
    .assignee-chip.proposed {{
      background: #fef3c7; color: #92400e;
    }}
    .assignee-chip.proposed em {{
      font-style: normal; font-weight: 400; opacity: 0.7; font-size: 10px;
    }}
    .chip-dot {{
      width: 6px; height: 6px; border-radius: 50%; background: currentColor;
    }}
    .no-assignees {{ font-size: 13px; color: var(--color-text-light); font-style: italic; }}
    .legend-inline {{
      font-size: 10px; font-weight: 500; color: var(--color-text-light);
      display: flex; align-items: center; gap: 5px; letter-spacing: 0;
      text-transform: none;
    }}
    .dot-actual, .dot-proposed {{
      width: 6px; height: 6px; border-radius: 50%; display: inline-block;
    }}
    .dot-actual {{ background: #0693e3; margin-left: 4px; }}
    .dot-proposed {{ background: #d97706; }}

    /* Divider */
    .panel-divider {{
      height: 1px; background: #e5e7eb; max-width: 1200px;
      margin: 0 auto; margin-left: 48px; margin-right: 48px;
    }}

    /* FOOTER */
    .site-footer {{
      background: var(--color-nav); color: rgba(255,255,255,0.45);
      padding: 28px 48px; text-align: center;
      font-size: 12px; line-height: 2;
    }}
    .site-footer strong {{ color: rgba(255,255,255,0.8); }}

    @media (max-width: 700px) {{
      .panel-inner {{ grid-template-columns: 1fr; gap: 24px; padding: 0 24px; }}
      .legend-bar {{ padding: 10px 24px; }}
    }}
  </style>
</head>
<body>

  <nav class="site-nav">
    <a class="nav-brand" href="#">
      <span class="brand-dot"></span>The Life Church
    </a>
    <span class="nav-sub">Creative Memphis — 2026 Events Report</span>
  </nav>

  <header class="hero">
    <div class="hero-eyebrow">The Life Church Creative Memphis</div>
    <h1>2026 Creative <span>Events</span> Report</h1>
    <p class="hero-sub">Event summaries · Team assignments · Upcoming due dates</p>
    <div class="hero-stats">
      <div class="hero-stat">
        <div class="hero-stat-number">{len(EVENTS)}</div>
        <div class="hero-stat-label">Events</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-number">{total_matched}</div>
        <div class="hero-stat-label">Total Tasks</div>
      </div>
      <div class="hero-stat">
        <div class="hero-stat-number">12</div>
        <div class="hero-stat-label">Team Members</div>
      </div>
    </div>
    <div class="hero-pills">{nav_pills}</div>
  </header>

  <div class="legend-bar">
    <strong>Team legend:</strong>
    <span>
      <span class="legend-chip" style="background:#e8f4fd;color:#0693e3;">● Name</span>
      Assigned in ClickUp
    </span>
    <span>
      <span class="legend-chip" style="background:#fef3c7;color:#92400e;">● Name proposed</span>
      Suggested based on task type — not set in ClickUp
    </span>
  </div>

  {panels}

  <footer class="site-footer">
    <p><strong>The Life Church Creative Memphis — 2026 Events Report</strong></p>
    <p>Generated {generated}</p>
    <p>Read-only — no ClickUp data was created, modified, or deleted.</p>
  </footer>

</body>
</html>"""

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not TASKS_FILE.exists():
        print(f"ERROR: {TASKS_FILE} not found. Run tools/fetch_clickup.py first.")
        sys.exit(1)

    print(f"Loading tasks from {TASKS_FILE}...")
    with open(TASKS_FILE) as f:
        all_tasks = json.load(f)
    print(f"  {len(all_tasks)} total tasks loaded.")

    tasks_by_event = {e["key"]: [] for e in EVENTS}
    for task in all_tasks:
        key = match_task_to_event(task)
        if key:
            tasks_by_event[key].append(task)

    print("\nEvent summary:")
    total = 0
    for event in EVENTS:
        tasks = tasks_by_event[event["key"]]
        top = [t for t in tasks if not t.get("parent")]
        open_t = [t for t in top if not is_closed(t)]
        print(f"  {event['name']}: {len(top)} top-level ({len(open_t)} open)")
        total += len(top)

    html = build_html(tasks_by_event, total)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"\n✓ Report written → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
