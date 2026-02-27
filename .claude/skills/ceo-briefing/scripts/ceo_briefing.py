"""
CEO Briefing — Weekly summary report of all AI Employee activities.

Generates comprehensive briefing from vault data: tasks, social media, errors, recommendations.

Usage:
    uv run python .claude/skills/ceo-briefing/scripts/ceo_briefing.py --vault ./AI_Employee_Vault
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def collect_log_entries(logs_dir: Path, days: int = 7) -> list[dict]:
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


def count_files(directory: Path, pattern: str = "*.md") -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def generate_briefing(vault_path: str, days: int = 7) -> str:
    vault = Path(vault_path)
    logs_dir = vault / "Logs"
    done_dir = vault / "Done"
    needs_action_dir = vault / "Needs_Action"
    pending_dir = vault / "Pending_Approval"
    rejected_dir = vault / "Rejected"
    accounting_dir = vault / "Accounting"

    entries = collect_log_entries(logs_dir, days) if logs_dir.exists() else []

    # Task metrics
    tasks_done = count_files(done_dir)
    tasks_pending_action = count_files(needs_action_dir)
    tasks_pending_approval = count_files(pending_dir)
    tasks_rejected = count_files(rejected_dir)

    # Social media counts from logs
    social = defaultdict(int)
    email_count = 0
    whatsapp_count = 0
    linkedin_notif_count = 0
    errors = []
    key_actions = []

    for entry in entries:
        action = entry.get("action_type", "")
        result = entry.get("result", entry.get("status", ""))
        ts = entry.get("timestamp", "")[:10]
        fname = entry.get("file", "")

        if "post" in action and result in ("posted", "success"):
            platform = action.replace("_post", "")
            social[platform] += 1
            key_actions.append(f"Published {platform} post: {fname}")
        elif action == "email_sent":
            email_count += 1
        elif action == "whatsapp_detected":
            whatsapp_count += 1
        elif action == "linkedin_notification":
            linkedin_notif_count += 1
        elif action == "error" or result == "failed":
            errors.append(f"{ts}: {entry.get('details', fname)} — {result}")

    total_posts = sum(social.values())
    total_tasks = tasks_done + tasks_pending_action + tasks_pending_approval + tasks_rejected

    today = datetime.now()
    week_start = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    week_end = today.strftime("%Y-%m-%d")

    lines = [
        f"# CEO Briefing — {week_start} to {week_end}",
        "",
        "## Executive Summary",
        f"AI Employee processed {total_tasks} tasks this period with {tasks_done} completed. "
        f"{total_posts} social media posts published across platforms.",
        "",
        "## Task Metrics",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Tasks Completed | {tasks_done} |",
        f"| Pending Action | {tasks_pending_action} |",
        f"| Pending Approval | {tasks_pending_approval} |",
        f"| Rejected | {tasks_rejected} |",
        "",
        "## Communication Summary",
        f"- **Emails processed**: {email_count}",
        f"- **WhatsApp alerts**: {whatsapp_count}",
        f"- **LinkedIn notifications**: {linkedin_notif_count}",
        "",
        "## Social Media",
        f"- **Posts published**: {total_posts}",
    ]

    for platform, count in social.items():
        lines.append(f"  - {platform.capitalize()}: {count}")

    if total_tasks > 0:
        approval_rate = round((tasks_done / total_tasks) * 100)
        lines.append(f"- **Completion rate**: {approval_rate}%")

    # Financial summary
    lines.append("")
    lines.append("## Financial Summary")
    if accounting_dir.exists() and list(accounting_dir.glob("*.md")):
        lines.append("- See accounting reports in `/Accounting/`")
    else:
        lines.append("- No financial data available (Odoo not connected)")

    # Key actions
    lines.append("")
    lines.append("## Key Actions Taken")
    if key_actions:
        for i, action in enumerate(key_actions[:10], 1):
            lines.append(f"{i}. {action}")
    else:
        lines.append("- No notable actions logged this period")

    # Errors
    lines.append("")
    lines.append("## Errors & Issues")
    if errors:
        for err in errors[:5]:
            lines.append(f"- {err}")
    else:
        lines.append("- No errors reported ✅")

    # Recommendations
    lines.append("")
    lines.append("## Recommendations")
    if tasks_pending_action > 3:
        lines.append(f"- {tasks_pending_action} tasks awaiting action — review Needs_Action folder")
    if tasks_pending_approval > 2:
        lines.append(f"- {tasks_pending_approval} items awaiting approval — check Pending_Approval")
    if len(errors) > 3:
        lines.append(f"- {len(errors)} errors detected — run weekly audit for details")
    if total_posts == 0:
        lines.append("- No social media posts this period — consider content creation")
    lines.append("- Continue monitoring system health via weekly audits")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="CEO Briefing Generator")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--days", type=int, default=7, help="Days to cover")
    args = parser.parse_args()

    vault = Path(args.vault)
    briefings_dir = vault / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)

    report = generate_briefing(args.vault, args.days)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = briefings_dir / f"CEO_Briefing_{today}.md"
    output_file.write_text(report, encoding="utf-8")
    print(f"CEO Briefing saved to: {output_file}")
    print(report.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
