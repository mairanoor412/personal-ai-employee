"""
Social Media Summary — Cross-platform analytics report generator.

Reads logs and Done folder to generate social media summary report.

Usage:
    uv run python .claude/skills/social-summary/scripts/social_summary.py --vault ./AI_Employee_Vault
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


PLATFORMS = {
    "linkedin": "LinkedIn",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "Twitter",
}


def collect_log_entries(logs_dir: Path, days: int = 7) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    for log_file in sorted(logs_dir.glob("*.json")):
        try:
            date_str = log_file.stem  # YYYY-MM-DD
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
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


def count_done_posts(done_dir: Path) -> dict[str, int]:
    counts = defaultdict(int)
    for platform_key in PLATFORMS:
        pattern = f"{platform_key.upper()}_POST_*.md"
        counts[platform_key] = len(list(done_dir.glob(pattern)))
    return dict(counts)


def generate_summary(vault_path: str, days: int = 7) -> str:
    vault = Path(vault_path)
    logs_dir = vault / "Logs"
    done_dir = vault / "Done"
    rejected_dir = vault / "Rejected"

    entries = collect_log_entries(logs_dir, days) if logs_dir.exists() else []
    done_counts = count_done_posts(done_dir) if done_dir.exists() else {}

    # Count from logs
    posted = defaultdict(int)
    failed = defaultdict(int)
    recent_activity = []

    for entry in entries:
        action = entry.get("action_type", "")
        result = entry.get("result", "")
        ts = entry.get("timestamp", "")

        for key in PLATFORMS:
            if key in action:
                if result == "posted" or entry.get("status") == "success":
                    posted[key] += 1
                elif result == "failed" or entry.get("status") == "failed":
                    failed[key] += 1

                preview = entry.get("file", entry.get("details", {}).get("file", ""))
                status_icon = "✅" if result in ("posted", "success") else "❌"
                if ts and preview:
                    recent_activity.append(f"- {ts[:10]} {PLATFORMS[key]}: {preview} {status_icon}")
                break

    # Count rejected posts
    rejected_counts = defaultdict(int)
    if rejected_dir and rejected_dir.exists():
        for key in PLATFORMS:
            rejected_counts[key] = len(list(rejected_dir.glob(f"{key.upper()}_POST_*.md")))

    today = datetime.now().strftime("%Y-%m-%d")
    total_posted = sum(posted.values())
    total_failed = sum(failed.values())
    total_rejected = sum(rejected_counts.values())

    lines = [
        f"# Social Media Summary — Week of {today}",
        "",
        "## Posts Published",
        "| Platform | Done | Posted (logs) | Failed | Rejected |",
        "|----------|------|---------------|--------|----------|",
    ]
    for key, name in PLATFORMS.items():
        lines.append(
            f"| {name} | {done_counts.get(key, 0)} | {posted[key]} | {failed[key]} | {rejected_counts[key]} |"
        )
    lines.append(
        f"| **Total** | **{sum(done_counts.values())}** | **{total_posted}** | **{total_failed}** | **{total_rejected}** |"
    )

    lines.append("")
    lines.append("## Recent Activity")
    if recent_activity:
        lines.extend(recent_activity[-15:])  # last 15
    else:
        lines.append("- No recent social media activity in logs")

    lines.append("")
    lines.append("## Recommendations")
    for key, name in PLATFORMS.items():
        if done_counts.get(key, 0) == 0 and posted[key] == 0:
            lines.append(f"- Consider posting on {name} — no posts found this period")
    if total_failed > 0:
        lines.append(f"- {total_failed} post(s) failed — check error logs for details")
    if total_posted > 0:
        lines.append(f"- Keep it up! {total_posted} successful post(s) this period")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Social Media Summary Generator")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    args = parser.parse_args()

    vault = Path(args.vault)
    briefings_dir = vault / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)

    report = generate_summary(args.vault, args.days)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = briefings_dir / f"Social_Summary_{today}.md"
    output_file.write_text(report, encoding="utf-8")
    print(f"Social summary saved to: {output_file}")
    print(report.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
