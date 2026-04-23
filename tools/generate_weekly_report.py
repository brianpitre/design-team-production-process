#!/usr/bin/env python3
"""
generate_weekly_report.py — WAT Tool
Reads .tmp/weekly_tasks.json and generates weekly_report.html.
Shows overdue and due-this-week tasks grouped by team member.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
TASKS_FILE = ROOT / ".tmp" / "weekly_tasks.json"
OUTPUT_FILE = ROOT / "weekly_report.html"

TEAM_FIRST_NAMES = ["lizzie", "camilo", "daniel", "caleb", "chris", "carlos", "olivia", "bella"]

# Subtask names matching these patterns are excluded (meeting overhead tasks)
MEETING_PATTERNS = [
    "weekly meeting", "team meeting", "monthly meeting", "staff meeting",
    "department meeting", "all hands", "all-hands",
    "check-in", "check in",
    "standup", "stand-up", "stand up",
    "1:1", "one on one", "one-on-one",
    "sync call", "daily sync", "weekly sync", "weekly check",
    "office hours",
]

STATUS_DISPLAY = {
    "complete":    ("Complete",    "#00a550", "#e6f9ef"),
    "completed":   ("Complete",    "#00a550", "#e6f9ef"),
    "approved":    ("Approved",    "#00a550", "#e6f9ef"),
    "closed":      ("Closed",      "#6b7280", "#f3f4f6"),
    "done":        ("Done",        "#00a550", "#e6f9ef"),
    "in progress": ("In Progress", "#0693e3", "#e8f4fd"),
    "in review":   ("In Review",   "#ff6900", "#fff3eb"),
    "review":      ("In Review",   "#ff6900", "#fff3eb"),
    "waiting":     ("Waiting",     "#9b51e0", "#f3ebfd"),
    "to do":       ("To Do",       "#6b7280", "#f3f4f6"),
    "not started": ("Not Started", "#6b7280", "#f3f4f6"),
}


def esc(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def fmt_date(ts_ms):
    if not ts_ms:
        return "—"
    return datetime.fromtimestamp(int(ts_ms) / 1000).strftime("%b %-d")


def status_info(task):
    raw = (task.get("status") or {}).get("status", "to do").lower().strip()
    for key, info in STATUS_DISPLAY.items():
        if key in raw:
            return info
    return ("To Do", "#6b7280", "#f3f4f6")


def is_closed(task):
    raw = (task.get("status") or {}).get("status", "").lower().strip()
    return (raw.startswith("complete") or raw.startswith("approved")
            or raw.startswith("closed") or raw in ("done", "complete"))


def is_meeting_subtask(task):
    name = task.get("name", "").lower().strip()
    return any(p in name for p in MEETING_PATTERNS)


def task_context(task):
    """Return breadcrumb: Space › Folder › List."""
    parts = []
    for key in ("space", "folder", "list"):
        name = (task.get(key) or {}).get("name", "")
        if name and name.lower() not in ("hidden", ""):
            parts.append(name)
    return " › ".join(parts)


def status_badge(task):
    label, color, bg = status_info(task)
    return f'<span class="badge" style="color:{color};background:{bg};">{esc(label)}</span>'


# ── HTML builders ─────────────────────────────────────────────────────────────

def task_row_html(task, subtasks, week_start_date, is_sub=False):
    due_ts = task.get("due_date")
    due_str = fmt_date(due_ts)
    task_url = f"https://app.clickup.com/t/{task['id']}"
    context = task_context(task)
    indent_class = " subtask" if is_sub else ""

    due_date = datetime.fromtimestamp(int(due_ts) / 1000).date() if due_ts else None
    is_overdue = due_date and due_date < week_start_date

    due_color = "#c62828" if is_overdue and not is_sub else ("#9ca3af" if is_sub else "#374151")

    sub_html = ""
    if subtasks and not is_sub:
        sub_html = "".join(
            task_row_html(s, [], week_start_date, is_sub=True)
            for s in subtasks
        )

    context_html = f'<span class="task-context">{esc(context)}</span>' if context else ""

    return f"""
    <div class="task-row{indent_class}">
      <div class="task-main">
        <div class="task-name">
          <a href="{task_url}" target="_blank" rel="noopener">{esc(task.get("name", "Untitled"))}</a>
        </div>
        <div class="task-meta">
          {context_html}
          {status_badge(task)}
        </div>
      </div>
      <div class="task-due" style="color:{due_color};">{due_str}</div>
    </div>
    {sub_html}"""


def card_group_label(label):
    return f'<div class="card-group-label">{label}</div>'


def member_card_html(member_name, overdue_tasks, this_week_tasks, subtask_map, week_start_date):
    initials = "".join(w[0].upper() for w in member_name.split()[:2])
    total = len(overdue_tasks) + len(this_week_tasks)
    has_both = overdue_tasks and this_week_tasks

    def task_rows(task_list):
        rows = ""
        for t in sorted(task_list, key=lambda x: int(x.get("due_date") or 0)):
            subs = [
                s for s in subtask_map.get(t["id"], [])
                if not is_closed(s) and not is_meeting_subtask(s)
            ]
            rows += task_row_html(t, subs, week_start_date)
        return rows

    rows = ""
    if overdue_tasks:
        if has_both:
            rows += card_group_label("Overdue")
        rows += task_rows(overdue_tasks)
    if this_week_tasks:
        if has_both:
            rows += card_group_label("This Week")
        rows += task_rows(this_week_tasks)

    return f"""
  <div class="member-card">
    <div class="member-header">
      <div class="avatar">{initials}</div>
      <div class="member-name">{esc(member_name)}</div>
      <div class="member-count">{total}</div>
    </div>
    <div class="task-list">
      {rows}
    </div>
  </div>"""


def combined_section_html(combined_by_member, overdue_by_member, this_week_by_member,
                           subtask_map, week_start_date, week_label):
    if not combined_by_member:
        return '<div class="empty-state">No tasks due this week or overdue.</div>'

    unique_ids = {t["id"] for tasks in combined_by_member.values() for t in tasks}
    total = len(unique_ids)

    cards = "".join(
        member_card_html(
            name,
            overdue_by_member.get(name, []),
            this_week_by_member.get(name, []),
            subtask_map,
            week_start_date,
        )
        for name in combined_by_member
    )

    return f"""
  <section class="report-section">
    <div class="section-header">
      <div class="section-icon">📋</div>
      <div>
        <h2 class="section-title">{week_label}</h2>
        <div class="section-meta">{total} task{"s" if total != 1 else ""} &middot; {len(combined_by_member)} team member{"s" if len(combined_by_member) != 1 else ""}</div>
      </div>
    </div>
    <div class="member-grid">
      {cards}
    </div>
  </section>"""


def build_html(overdue_by_member, this_week_by_member, week_start, week_end,
               subtask_map, overdue_count, this_week_count, generated_iso):

    week_label = f"{week_start.strftime('%B %-d')} – {week_end.strftime('%B %-d, %Y')}"
    gen_label = (datetime.fromisoformat(generated_iso).strftime("%B %-d, %Y at %-I:%M %p")
                 if generated_iso else "")

    # Merge per-member, preserving alphabetical order
    all_names = sorted(set(list(overdue_by_member) + list(this_week_by_member)))
    combined_by_member = {
        name: overdue_by_member.get(name, []) + this_week_by_member.get(name, [])
        for name in all_names
    }

    section = combined_section_html(
        combined_by_member, overdue_by_member, this_week_by_member,
        subtask_map, week_start, week_label
    )

    total = overdue_count + this_week_count

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Weekly Tasks — The Life Church Design</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --text:       #1a1a1a;
      --text-light: #6b7280;
      --border:     #e5e7eb;
      --surface:    #f9fafb;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: #eef0f3;
      color: var(--text);
      line-height: 1.5;
    }}

    /* ── HEADER ────────────────────────────────────────────── */
    .site-header {{
      background: #1a1a1a;
      padding: 48px 48px 44px;
      text-align: center;
    }}
    .header-eyebrow {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.35);
      margin-bottom: 10px;
    }}
    .header-title {{
      font-size: clamp(28px, 4vw, 44px);
      font-weight: 800;
      letter-spacing: -0.025em;
      color: #fff;
      line-height: 1.1;
      margin-bottom: 8px;
    }}
    .header-week {{
      font-size: 15px;
      color: rgba(255,255,255,0.45);
      margin-bottom: 28px;
    }}
    .header-stats {{
      display: flex;
      justify-content: center;
      gap: 36px;
      flex-wrap: wrap;
    }}
    .stat-num {{
      font-size: 30px;
      font-weight: 800;
      line-height: 1;
    }}
    .stat-label {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.35);
      margin-top: 4px;
    }}

    /* ── MAIN ──────────────────────────────────────────────── */
    .main {{
      max-width: 1140px;
      margin: 0 auto;
      padding: 44px 24px 60px;
    }}

    /* ── SECTIONS ──────────────────────────────────────────── */
    .report-section {{ margin-bottom: 52px; }}

    .section-header {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }}
    .section-icon {{
      width: 42px;
      height: 42px;
      border-radius: 11px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 19px;
      flex-shrink: 0;
    }}
    .section-title {{
      font-size: 21px;
      font-weight: 800;
      letter-spacing: -0.015em;
    }}
    .section-meta {{
      font-size: 12px;
      color: var(--text-light);
      margin-top: 3px;
    }}

    /* ── MEMBER GRID ───────────────────────────────────────── */
    .member-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 16px;
    }}

    /* ── MEMBER CARD ───────────────────────────────────────── */
    .member-card {{
      background: #fff;
      border-radius: 12px;
      border: 1px solid var(--border);
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .member-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 13px 16px;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }}
    .avatar {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #1a1a1a;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      letter-spacing: 0.04em;
    }}
    .member-name {{
      font-size: 14px;
      font-weight: 700;
      flex: 1;
    }}
    .member-count {{
      font-size: 11px;
      font-weight: 700;
      color: var(--text-light);
      background: #e5e7eb;
      padding: 2px 9px;
      border-radius: 9999px;
    }}

    /* ── TASK ROWS ─────────────────────────────────────────── */
    .task-list {{ padding: 4px 0; }}

    .task-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 16px;
      border-bottom: 1px solid #f3f4f6;
    }}
    .task-row:last-child {{ border-bottom: none; }}

    .task-row.subtask {{
      padding-left: 34px;
      background: #fafafa;
    }}

    .task-main {{ flex: 1; min-width: 0; }}

    .task-name a {{
      font-size: 13px;
      font-weight: 500;
      color: var(--text);
      text-decoration: none;
      line-height: 1.4;
      display: block;
    }}
    .task-name a:hover {{ color: #0693e3; text-decoration: underline; }}

    .task-row.subtask .task-name a {{
      font-size: 12px;
      color: var(--text-light);
      font-weight: 400;
    }}

    .task-meta {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 4px;
      flex-wrap: wrap;
    }}
    .task-context {{
      font-size: 11px;
      color: #9ca3af;
    }}
    .badge {{
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 9999px;
      white-space: nowrap;
    }}
    .task-due {{
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
      flex-shrink: 0;
      padding-top: 1px;
    }}

    /* ── CARD GROUP LABEL ──────────────────────────────────── */
    .card-group-label {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text-light);
      padding: 6px 16px 4px;
      background: var(--surface);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }}
    .card-group-label:first-child {{
      border-top: none;
    }}

    /* ── EMPTY STATE ───────────────────────────────────────── */
    .empty-state {{
      background: #fff;
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 28px 24px;
      font-size: 14px;
      color: var(--text-light);
      font-style: italic;
    }}

    /* ── FOOTER ────────────────────────────────────────────── */
    .site-footer {{
      background: #1a1a1a;
      color: rgba(255,255,255,0.3);
      padding: 24px 48px;
      font-size: 12px;
      text-align: center;
      line-height: 2;
    }}

    @media (max-width: 640px) {{
      .site-header {{ padding: 32px 20px; }}
      .main {{ padding: 28px 16px 48px; }}
      .member-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <header class="site-header">
    <div class="header-eyebrow">The Life Church · Creative Memphis</div>
    <h1 class="header-title">Weekly Task Report</h1>
    <div class="header-week">Week of {week_label}</div>
    <div class="header-stats">
      <div class="stat">
        <div class="stat-num" style="color:#ff7b7b;">{overdue_count}</div>
        <div class="stat-label">Overdue</div>
      </div>
      <div class="stat">
        <div class="stat-num" style="color:#60b4ff;">{this_week_count}</div>
        <div class="stat-label">Due This Week</div>
      </div>
      <div class="stat">
        <div class="stat-num" style="color:#fff;">{total}</div>
        <div class="stat-label">Total</div>
      </div>
    </div>
  </header>

  <main class="main">
    {section}
  </main>

  <footer class="site-footer">
    <p>The Life Church Creative Memphis &middot; Weekly Task Report</p>
    <p>Generated {gen_label} &middot; Read-only &mdash; no ClickUp data was modified.</p>
  </footer>

</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not TASKS_FILE.exists():
        print(f"ERROR: {TASKS_FILE} not found. Run tools/fetch_weekly_tasks.py first.")
        sys.exit(1)

    with open(TASKS_FILE) as f:
        data = json.load(f)

    tasks = data["tasks"]
    week_start = datetime.fromisoformat(data["week_start"]).date()
    week_end   = datetime.fromisoformat(data["week_end"]).date()
    generated  = data.get("generated", "")

    # Build subtask index: parent_id → [subtask, ...]
    subtask_map = {}
    for t in tasks:
        parent = t.get("parent")
        if parent:
            subtask_map.setdefault(str(parent), []).append(t)

    def is_team_task(task):
        for a in (task.get("assignees") or []):
            n = (a.get("username") or a.get("email") or "").lower()
            if any(first in n for first in TEAM_FIRST_NAMES):
                return True
        return False

    # Build task ID index for parent lookups
    task_by_id = {t["id"]: t for t in tasks}

    # Top-level, open, assigned to a team member
    top_level = [
        t for t in tasks
        if not t.get("parent") and not is_closed(t) and is_team_task(t)
    ]
    top_level_ids = {t["id"] for t in top_level}

    # Promote orphan subtasks: team-assigned, open, in-range, whose parent is
    # closed or not in the report (so they'd otherwise be invisible)
    for t in tasks:
        parent_id = t.get("parent")
        if not parent_id:
            continue
        if not is_team_task(t) or is_closed(t) or is_meeting_subtask(t):
            continue
        if not t.get("due_date"):
            continue
        if str(parent_id) in top_level_ids:
            continue  # already visible as a subtask under its parent
        parent = task_by_id.get(str(parent_id), {})
        if is_closed(parent):
            top_level.append(t)  # surface it as standalone

    # Categorize by due date
    overdue_tasks   = []
    this_week_tasks = []

    for t in top_level:
        due_ts = t.get("due_date")
        if not due_ts:
            continue
        due_date = datetime.fromtimestamp(int(due_ts) / 1000).date()
        if due_date < week_start:
            overdue_tasks.append(t)
        elif week_start <= due_date <= week_end:
            this_week_tasks.append(t)

    # Group by assignee (task appears under each assigned team member)
    def group_by_member(task_list):
        groups = {}
        for t in task_list:
            for a in (t.get("assignees") or []):
                username = (a.get("username") or a.get("email") or "").strip()
                if username and any(first in username.lower() for first in TEAM_FIRST_NAMES):
                    groups.setdefault(username, []).append(t)
        return dict(sorted(groups.items()))

    overdue_by_member   = group_by_member(overdue_tasks)
    this_week_by_member = group_by_member(this_week_tasks)

    html = build_html(
        overdue_by_member, this_week_by_member,
        week_start, week_end,
        subtask_map,
        len(overdue_tasks), len(this_week_tasks),
        generated,
    )

    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    print(f"✓ Report written → {OUTPUT_FILE}")
    print(f"  Overdue:    {len(overdue_tasks)} tasks across {len(overdue_by_member)} members")
    print(f"  This week:  {len(this_week_tasks)} tasks across {len(this_week_by_member)} members")


if __name__ == "__main__":
    main()
