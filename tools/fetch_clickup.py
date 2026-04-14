#!/usr/bin/env python3
"""
fetch_clickup.py — WAT Tool
Fetches all tasks from the "Creative (Memphis)" ClickUp space and
saves them to .tmp/clickup_tasks.json.

Read-only: makes only GET requests. No data is created or modified.
"""

import json
import os
import sys
import time
from pathlib import Path

# ── Load API key from .env ────────────────────────────────────────────────────
def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

ROOT = Path(__file__).parent.parent
env = load_env(ROOT / ".env")
API_KEY = env.get("CLICKUP_API_KEY", "")

if not API_KEY:
    print("ERROR: CLICKUP_API_KEY not found in .env")
    print("Create .env in the project root with: CLICKUP_API_KEY=your_token_here")
    sys.exit(1)

# ── HTTP helper (stdlib only) ─────────────────────────────────────────────────
import urllib.request
import urllib.error

BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}

def get(path: str, params: dict = None) -> dict:
    url = BASE + path
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code} on GET {path}: {body[:200]}")
        return {}
    except Exception as e:
        print(f"  Error on GET {path}: {e}")
        return {}

# ── Fetch tasks from a list (paginated) ──────────────────────────────────────
def fetch_tasks_for_list(list_id: str, list_name: str) -> list:
    tasks = []
    page = 0
    while True:
        data = get(f"/list/{list_id}/task", {
            "subtasks": "true",
            "include_closed": "true",
            "page": str(page),
        })
        batch = data.get("tasks", [])
        if not batch:
            break
        tasks.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.3)   # gentle rate limit
    print(f"    [{list_name}] {len(tasks)} tasks")
    return tasks

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    out_dir = ROOT / ".tmp"
    out_dir.mkdir(exist_ok=True)

    print("Fetching ClickUp workspace...")
    teams = get("/team").get("teams", [])
    if not teams:
        print("ERROR: No teams found — check your API key.")
        sys.exit(1)

    all_tasks = []
    space_found = False

    for team in teams:
        team_id = team["id"]
        team_name = team["name"]
        print(f"\nWorkspace: {team_name} (id={team_id})")

        spaces = get(f"/team/{team_id}/space", {"archived": "false"}).get("spaces", [])
        for space in spaces:
            space_name = space["name"]
            space_id = space["id"]
            print(f"  Space: {space_name}")

            # Look for "Creative (Memphis)" — case-insensitive partial match
            if "creative" not in space_name.lower() and "memphis" not in space_name.lower():
                continue

            space_found = True
            print(f"  ✓ Matched Creative Memphis space: {space_name}")

            # ── Top-level lists (not in a folder) ─────────────────────────────
            folderless = get(f"/space/{space_id}/list", {"archived": "false"}).get("lists", [])
            for lst in folderless:
                tasks = fetch_tasks_for_list(lst["id"], lst["name"])
                for t in tasks:
                    t["_list_name"] = lst["name"]
                    t["_folder_name"] = None
                    t["_space_name"] = space_name
                all_tasks.extend(tasks)

            # ── Folders ───────────────────────────────────────────────────────
            folders = get(f"/space/{space_id}/folder", {"archived": "false"}).get("folders", [])
            for folder in folders:
                folder_name = folder["name"]
                print(f"    Folder: {folder_name}")
                folder_lists = get(f"/folder/{folder['id']}/list", {"archived": "false"}).get("lists", [])
                for lst in folder_lists:
                    tasks = fetch_tasks_for_list(lst["id"], lst["name"])
                    for t in tasks:
                        t["_list_name"] = lst["name"]
                        t["_folder_name"] = folder_name
                        t["_space_name"] = space_name
                    all_tasks.extend(tasks)
                time.sleep(0.2)

    if not space_found:
        # Fallback: fetch from all spaces if none matched
        print("\nWARNING: Could not find a space named 'Creative (Memphis)'.")
        print("Available spaces were listed above. Update the name filter in this script if needed.")

    # ── Write output ──────────────────────────────────────────────────────────
    out_path = out_dir / "clickup_tasks.json"
    with open(out_path, "w") as f:
        json.dump(all_tasks, f, indent=2)

    print(f"\n✓ Saved {len(all_tasks)} tasks → {out_path}")

if __name__ == "__main__":
    main()
