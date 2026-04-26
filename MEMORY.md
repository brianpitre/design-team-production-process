# Design Memphis — Session Memory

Last updated: April 26, 2026

---

## Project Overview

This is the **The Life Church Design Memphis** team workspace, built on the WAT framework. The main deliverables are HTML reports generated from ClickUp data.

---

## Weekly Task Report (Built This Session)

### What it does
Pulls open tasks from ClickUp across **all spaces** (not just Creative Memphis) assigned to the design team, filters to overdue + due this week (Mon–Sun), and generates a clean HTML report grouped by team member.

### Live URL
**https://brianpitre.github.io/design-team-production-process/weekly_report.html**

GitHub repo: `https://github.com/brianpitre/design-team-production-process`
Branch: `main` — GitHub Pages serves from root.

### How to run
```bash
# Current week
python3 tools/fetch_weekly_tasks.py
python3 tools/generate_weekly_report.py

# Coming week (run on Friday or Sunday to get ahead)
python3 tools/fetch_weekly_tasks.py --next-week
python3 tools/generate_weekly_report.py

# Then push to update the live page
git add tools/fetch_weekly_tasks.py weekly_report.html
git commit -m "Update weekly report for [date range]"
git push
```

### Files
| File | Purpose |
|------|---------|
| `tools/fetch_weekly_tasks.py` | Fetches all workspace tasks with due dates in range → `.tmp/weekly_tasks.json` |
| `tools/generate_weekly_report.py` | Reads JSON → generates `weekly_report.html` |
| `weekly_report.html` | Output — the live report |
| `.tmp/weekly_tasks.json` | Intermediate cache (regenerate anytime) |

---

## Team Members

Matched by first name substring against ClickUp username:

| Name | First name used |
|------|----------------|
| Lizzie Miller | `lizzie` |
| Camilo Espinel | `camilo` |
| Daniel Gamboa | `daniel` |
| Caleb Chunn | `caleb` |
| Chris Steen | `chris` |
| Carlos Hernández | `carlos` |
| Olivia McCrimon | `olivia` |
| Bella | `bella` |

Defined in both scripts as `TEAM_FIRST_NAMES`.

---

## ClickUp API

- **API key**: stored in `.env` as `CLICKUP_API_KEY`
- **Workspace**: The Life Church (id=`8441198`)
- **Endpoint used**: `GET /team/{team_id}/task` with `due_date_gt`, `due_date_lt`, `subtasks=true`, `include_closed=false`
- **Date range**: 6 months ago → end of target week (Sunday 23:59:59)
- **Member lookup** (`GET /team/{team_id}/member`) returns 404 with personal API key — workaround: fetch all tasks and filter by name client-side.

### ClickUp MCP
The `mcp__plugin_productivity_clickup__*` tools appear in settings.local.json permissions from a previous session but were not available in this session. The Python REST API approach works reliably without it.

---

## Report Design

- **Dark header** (centered) with stats: Overdue count, Due This Week count, Total
- **Single section** per week — no separate Overdue/This Week panels
- **One card per team member** containing all their tasks
- Within each card: **Overdue** group label first (red dates), then **This Week** group label — only shown if the person has tasks in both categories
- Subtasks shown indented under parent task
- Meeting/check-in subtasks filtered out automatically (see `MEETING_PATTERNS` in generator)
- Each task name links directly to ClickUp (`https://app.clickup.com/t/{id}`)
- Status badges, breadcrumb context (Space › Folder › List), due date per task
- Font: Inter. Colors: dark bg `#1a1a1a`, overdue red `#c62828`, this-week blue `#0693e3`

---

## Known Quirks & Fixes

### Orphan subtasks
Subtasks whose parent task is **closed/approved** are normally invisible (parent doesn't appear in report). Fix is live: `generate_weekly_report.py` detects these and promotes them to top-level.

Example: "Assets for One Night" is a subtask of "May One Night - Option" (approved). It's now surfaced under Olivia's card.

### Branding
The report says **Design Memphis** (not Creative Memphis — was corrected this session).

### Task count in section header
Uses unique task IDs (not sum of per-member lists) so multi-assignee tasks don't inflate the count.

### Closed task detection
```python
def is_closed(task):
    raw = status.lower()
    return raw.startswith("complete") or raw.startswith("approved")
           or raw.startswith("closed") or raw in ("done", "complete")
```
Status emojis like "approved ✔️" are handled because `.startswith("approved")` matches.

---

## Other Reports in This Project

### 2026 Creative Events Report (older)
- **Tools**: `tools/fetch_clickup.py` + `tools/generate_html_report.py`
- **Output**: `event_report_2026.html` (currently deleted from working tree, still in git history)
- **Scope**: Creative Memphis space only, organized by event (Mother's Day, Axis Conference, etc.)
- **Run**: `python3 tools/fetch_clickup.py` then `python3 tools/generate_html_report.py`

---

## Permissions (`.claude/settings.local.json`)

Key allowed commands:
```
Bash(python3 tools/fetch_weekly_tasks.py)
Bash(python3 tools/generate_weekly_report.py)
Bash(python3 tools/fetch_clickup.py)
Bash(python3 tools/generate_html_report.py)
Bash(open /Users/brianpitre/Desktop/Claude/Design/weekly_report.html)
mcp__Claude_Preview__preview_start
```
Preview server: `npx serve -p 8765 .` — name `"report"` in `.claude/launch.json`.
