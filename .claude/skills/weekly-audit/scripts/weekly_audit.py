"""
Weekly Audit — System health check for AI Employee.

Checks stale tasks, errors, watcher status, vault integrity.

Usage:
    uv run python .claude/skills/weekly-audit/scripts/weekly_audit.py --vault ./AI_Employee_Vault
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta


REQUIRED_FOLDERS = [
    "Needs_Action", "Plans", "Pending_Approval", "Approved",
    "Done", "Rejected", "Logs", "Briefings", "Templates", "Accounting",
]

WATCHERS = ["file_watcher", "linkedin_watcher", "whatsapp_watcher", "gmail_watcher"]


def get_file_age_hours(filepath: Path) -> float:
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    return (datetime.now() - mtime).total_seconds() / 3600


def collect_recent_logs(logs_dir: Path, days: int = 7) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    for log_file in sorted(logs_dir.glob("*.json")):
        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
            if file_date < cutoff:
                continue
        except ValueError:
            continue
        try:
            data = json.loads(log_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                entries.extend(data)
        except (json.JSONDecodeError, OSError):
            continue
    return entries


def generate_audit(vault_path: str) -> str:
    vault = Path(vault_path)
    issues = []
    warnings = []

    # 1. Stale tasks (older than 48h)
    stale_tasks = []
    needs_action = vault / "Needs_Action"
    if needs_action.exists():
        for f in needs_action.glob("*.md"):
            age_h = get_file_age_hours(f)
            if age_h > 48:
                days_old = round(age_h / 24, 1)
                stale_tasks.append(f"- {f.name} — {days_old} days old")
                issues.append(f"Stale task: {f.name}")

    # 2. Pending approvals (older than 24h)
    stale_approvals = []
    pending = vault / "Pending_Approval"
    if pending.exists():
        for f in pending.glob("*.md"):
            age_h = get_file_age_hours(f)
            if age_h > 24:
                days_old = round(age_h / 24, 1)
                stale_approvals.append(f"- {f.name} — waiting {days_old} days")
                warnings.append(f"Pending approval: {f.name}")

    # 3. Error logs
    logs_dir = vault / "Logs"
    entries = collect_recent_logs(logs_dir) if logs_dir.exists() else []
    error_entries = [
        e for e in entries
        if e.get("result") == "failed" or e.get("status") == "failed" or e.get("action_type") == "error"
    ]

    # 4. Watcher health
    watcher_status = {}
    for watcher in WATCHERS:
        last_seen = None
        for entry in reversed(entries):
            actor = entry.get("actor", "")
            if watcher in actor or watcher.replace("_", "") in actor:
                last_seen = entry.get("timestamp", "")[:16]
                break
        if last_seen:
            watcher_status[watcher] = ("OK", last_seen)
        else:
            watcher_status[watcher] = ("NO DATA", "—")

    # 5. Vault integrity
    missing_folders = []
    for folder in REQUIRED_FOLDERS:
        if not (vault / folder).exists():
            missing_folders.append(folder)
            issues.append(f"Missing folder: {folder}")

    dashboard_ok = (vault / "Dashboard.md").exists()
    handbook_ok = (vault / "Company_Handbook.md").exists()

    # Determine health
    if len(issues) >= 3 or len(error_entries) >= 5:
        health = "CRITICAL ❌"
    elif len(issues) >= 1 or len(warnings) >= 2 or len(error_entries) >= 2:
        health = "WARNING ⚠️"
    else:
        health = "GOOD ✅"

    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Weekly Audit — {today}",
        "",
        f"## System Health: {health}",
        "",
        "## Stale Tasks (older than 48h)",
    ]
    if stale_tasks:
        lines.extend(stale_tasks)
    else:
        lines.append("- None ✅")

    lines.append("")
    lines.append("## Pending Approvals (older than 24h)")
    if stale_approvals:
        lines.extend(stale_approvals)
    else:
        lines.append("- None ✅")

    lines.append("")
    lines.append("## Errors This Week")
    if error_entries:
        for err in error_entries[:10]:
            ts = err.get("timestamp", "")[:10]
            desc = err.get("file", err.get("details", "unknown"))
            lines.append(f"- {ts}: {desc} — {err.get('result', 'failed')}")
    else:
        lines.append("- No errors ✅")

    lines.append("")
    lines.append("## Watcher Status")
    lines.append("| Watcher | Last Run | Status |")
    lines.append("|---------|----------|--------|")
    for watcher in WATCHERS:
        name = watcher.replace("_", " ").title()
        status, last_run = watcher_status.get(watcher, ("UNKNOWN", "—"))
        lines.append(f"| {name} | {last_run} | {status} |")

    lines.append("")
    lines.append("## Vault Integrity")
    if missing_folders:
        lines.append(f"- Missing folders: {', '.join(missing_folders)}")
    else:
        lines.append(f"- All {len(REQUIRED_FOLDERS)} folders: OK ✅")
    lines.append(f"- Dashboard.md: {'OK ✅' if dashboard_ok else 'MISSING ❌'}")
    lines.append(f"- Company_Handbook.md: {'OK ✅' if handbook_ok else 'MISSING ❌'}")

    lines.append("")
    lines.append("## Recommendations")
    if stale_tasks:
        lines.append(f"- Review {len(stale_tasks)} stale task(s) in Needs_Action")
    if stale_approvals:
        lines.append(f"- Approve or reject {len(stale_approvals)} pending item(s)")
    if error_entries:
        lines.append(f"- Investigate {len(error_entries)} error(s) in logs")
    if missing_folders:
        lines.append(f"- Create missing folders: {', '.join(missing_folders)}")
    if not stale_tasks and not stale_approvals and not error_entries:
        lines.append("- System is healthy — no action needed")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Weekly Audit for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    args = parser.parse_args()

    vault = Path(args.vault)
    briefings_dir = vault / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)

    report = generate_audit(args.vault)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = briefings_dir / f"Weekly_Audit_{today}.md"
    output_file.write_text(report, encoding="utf-8")
    print(f"Weekly audit saved to: {output_file}")
    print(report.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
