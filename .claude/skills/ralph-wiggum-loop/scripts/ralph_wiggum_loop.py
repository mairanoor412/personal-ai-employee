"""
Ralph Wiggum Loop — Autonomous task processing loop for AI Employee.

Continuously processes tasks from /Needs_Action/ until empty or all need human input.
Named after the persistent (if confused) Simpsons character.

Safety guards:
- Max 50 tasks per run
- 5 second pause between tasks
- Stops after 3 consecutive errors
- Never auto-approves — always routes to human

Usage:
    uv run python .claude/skills/ralph-wiggum-loop/scripts/ralph_wiggum_loop.py --vault ./AI_Employee_Vault
"""

import json
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("RalphWiggumLoop")

# Actions that can be done without human approval
AUTO_ACTIONS = {
    "summary", "report", "briefing", "audit", "dashboard",
    "log", "analyze", "read", "scan", "check",
}

# Actions that ALWAYS need human approval
APPROVAL_ACTIONS = {
    "post", "send", "email", "reply", "invoice", "payment",
    "delete", "contact", "publish", "tweet",
}

MAX_TASKS = 50
PAUSE_SECONDS = 5
MAX_CONSECUTIVE_ERRORS = 3


def detect_task_type(filepath: Path) -> dict:
    """Analyze a task file to determine type and priority."""
    content = filepath.read_text(encoding="utf-8").lower()
    name = filepath.name.lower()

    # Determine priority
    priority = "medium"
    if "critical" in content or "urgent" in content or "error" in name:
        priority = "critical"
    elif "whatsapp" in name or "email" in name:
        priority = "high"
    elif "linkedin" in name or "file" in name:
        priority = "medium"
    else:
        priority = "low"

    # Determine if auto-executable
    needs_approval = False
    for keyword in APPROVAL_ACTIONS:
        if keyword in name or keyword in content:
            needs_approval = True
            break

    auto_executable = False
    if not needs_approval:
        for keyword in AUTO_ACTIONS:
            if keyword in name or keyword in content:
                auto_executable = True
                break

    return {
        "priority": priority,
        "needs_approval": needs_approval,
        "auto_executable": auto_executable,
        "filename": filepath.name,
    }


def sort_by_priority(tasks: list[tuple[Path, dict]]) -> list[tuple[Path, dict]]:
    """Sort tasks by priority: critical > high > medium > low."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(tasks, key=lambda x: priority_order.get(x[1]["priority"], 99))


def process_auto_task(filepath: Path, vault: Path) -> bool:
    """Process a task that doesn't need approval (read, summarize, report)."""
    done_dir = vault / "Done"
    try:
        # For auto tasks, we just move them to Done with a processed note
        content = filepath.read_text(encoding="utf-8")
        processed_content = content + f"\n\n---\n_Auto-processed by Ralph Wiggum Loop at {datetime.now().isoformat()}_\n"
        dest = done_dir / filepath.name
        dest.write_text(processed_content, encoding="utf-8")
        filepath.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to process {filepath.name}: {e}")
        return False


def route_to_approval(filepath: Path, vault: Path) -> bool:
    """Move task to Pending_Approval for human review."""
    pending_dir = vault / "Pending_Approval"
    try:
        dest = pending_dir / filepath.name
        shutil.move(str(filepath), str(dest))
        logger.info(f"Routed to approval: {filepath.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to route {filepath.name}: {e}")
        return False


def log_action(logs_dir: Path, filename: str, action: str, result: str):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "ralph_wiggum_loop",
        "actor": "ralph_wiggum_loop",
        "file": filename,
        "action": action,
        "result": result,
    }
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def run_loop(vault_path: str):
    vault = Path(vault_path)
    needs_action = vault / "Needs_Action"
    logs_dir = vault / "Logs"

    if not needs_action.exists():
        logger.info("Needs_Action folder not found")
        return

    # Collect and analyze tasks
    task_files = list(needs_action.glob("*.md"))
    if not task_files:
        logger.info("No tasks in Needs_Action — nothing to do!")
        return

    logger.info(f"Found {len(task_files)} task(s) in Needs_Action")

    analyzed = []
    for f in task_files[:MAX_TASKS]:
        try:
            info = detect_task_type(f)
            analyzed.append((f, info))
        except Exception as e:
            logger.error(f"Failed to analyze {f.name}: {e}")

    # Sort by priority
    analyzed = sort_by_priority(analyzed)

    processed = 0
    skipped = 0
    routed = 0
    errors = 0
    consecutive_errors = 0

    for filepath, info in analyzed:
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.error(f"Stopping: {MAX_CONSECUTIVE_ERRORS} consecutive errors")
            break

        logger.info(f"[{info['priority'].upper()}] Processing: {filepath.name}")

        if info["needs_approval"]:
            # Route to human approval
            success = route_to_approval(filepath, vault)
            if success:
                routed += 1
                log_action(logs_dir, filepath.name, "routed_to_approval", "success")
                consecutive_errors = 0
            else:
                errors += 1
                consecutive_errors += 1
                log_action(logs_dir, filepath.name, "route_failed", "failed")

        elif info["auto_executable"]:
            # Auto-process
            success = process_auto_task(filepath, vault)
            if success:
                processed += 1
                log_action(logs_dir, filepath.name, "auto_processed", "success")
                logger.info(f"  Auto-processed → Done")
                consecutive_errors = 0
            else:
                errors += 1
                consecutive_errors += 1
                log_action(logs_dir, filepath.name, "auto_process_failed", "failed")

        else:
            # Unknown task type — route to approval to be safe
            success = route_to_approval(filepath, vault)
            if success:
                routed += 1
                log_action(logs_dir, filepath.name, "routed_unknown", "success")
                logger.info(f"  Unknown type → routed to approval")
                consecutive_errors = 0
            else:
                skipped += 1
                consecutive_errors += 1

        time.sleep(PAUSE_SECONDS)

    # Summary
    logger.info("=" * 40)
    logger.info("Ralph Wiggum Loop Complete!")
    logger.info(f"  Processed: {processed}")
    logger.info(f"  Routed to approval: {routed}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Errors: {errors}")
    logger.info("=" * 40)


def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop — Autonomous Task Processor")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    args = parser.parse_args()

    run_loop(args.vault)


if __name__ == "__main__":
    main()
