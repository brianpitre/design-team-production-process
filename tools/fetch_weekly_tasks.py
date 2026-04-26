#!/usr/bin/env python3
"""
fetch_weekly_tasks.py — WAT Tool
Fetches tasks across all ClickUp spaces assigned to the design team
that are overdue or due through end of the current week (Sunday).
Saves to .tmp/weekly_tasks.json.

Read-only: GET requests only.
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Team members — matched by first name substring against ClickUp username
TEAM_FIRST_NAMES = ["lizzie", "camilo", "daniel", "caleb", "chris", "carlos", "olivia", "bella"]

# ── Load API key ──────────────────────────────────────────────────────────────
def load_env(path):
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

env = load_env(ROOT / ".env")
API_KEY = env.get("CLICKUP_API_KEY", "")
if not API_KEY:
    print("ERROR: CLICKUP_API_KEY not found in .env")
    sys.exit(1)

BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def get(path, params=None):
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {path}: {e.read().decode()[:300]}")
        return {}
    except Exception as e:
        print(f"  Error {path}: {e}")
        return {}


def get_team_tasks(team_id, due_lt_ms, due_gt_ms, page=0):
    """Fetch tasks filtered by date range across the entire workspace."""
    parts = [
        f"due_date_gt={due_gt_ms}",
        f"due_date_lt={due_lt_ms}",
        "subtasks=true",
        "include_closed=false",
        f"page={page}",
    ]
    url = f"{BASE}/team/{team_id}/task?" + "&".join(parts)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
        return {}
    except Exception as e:
        print(f"  Error fetching tasks page {page}: {e}")
        return {}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--next-week", action="store_true",
                        help="Fetch for next week instead of the current week")
    args = parser.parse_args()

    out_dir = ROOT / ".tmp"
    out_dir.mkdir(exist_ok=True)

    print("Connecting to ClickUp...")
    teams = get("/team").get("teams", [])
    if not teams:
        print("ERROR: No workspace found. Check your API key.")
        sys.exit(1)

    team = teams[0]
    team_id = team["id"]
    print(f"Workspace: {team['name']} (id={team_id})")

    # ── Calculate date range ──────────────────────────────────────────────────
    today = datetime.now().date()
    week_offset = timedelta(weeks=1) if args.next_week else timedelta(0)
    monday = today - timedelta(days=today.weekday()) + week_offset
    sunday = monday + timedelta(days=6)

    end_of_week = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59)
    six_months_ago = datetime.now() - timedelta(days=180)

    end_ms   = int(end_of_week.timestamp() * 1000)
    start_ms = int(six_months_ago.timestamp() * 1000)

    print(f"\nFetching tasks due {monday} through {sunday}...")
    print(f"(Overdue cutoff: {six_months_ago.date()})\n")

    # ── Paginate tasks ────────────────────────────────────────────────────────
    all_tasks = []
    page = 0
    while True:
        data = get_team_tasks(team_id, end_ms, start_ms, page)
        batch = data.get("tasks", [])
        if not batch:
            break
        all_tasks.extend(batch)
        print(f"  Page {page}: {len(batch)} tasks  (running total: {len(all_tasks)})")
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.3)

    # ── Save output ───────────────────────────────────────────────────────────
    output = {
        "generated": datetime.now().isoformat(),
        "week_start": monday.isoformat(),
        "week_end":   sunday.isoformat(),
        "tasks": all_tasks,
    }

    out_path = out_dir / "weekly_tasks.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ {len(all_tasks)} tasks saved → {out_path}")


if __name__ == "__main__":
    main()
