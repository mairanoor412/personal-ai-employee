"""
Scheduler Setup - Creates Windows Task Scheduler tasks for AI Employee

Usage:
    uv run python .claude/skills/scheduler/scripts/setup_scheduler.py          # Setup all tasks
    uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --list   # List tasks
    uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --remove # Remove all tasks
"""

import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("Scheduler")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def create_task(task_name: str, command: str, schedule: str, time: str = None, interval: str = None):
    """Create a Windows Scheduled Task."""
    cmd = [
        "schtasks", "/create",
        "/tn", f"AIEmployee\\{task_name}",
        "/tr", command,
        "/sc", schedule,
        "/f",
    ]
    if time:
        cmd.extend(["/st", time])
    if interval and schedule == "MINUTE":
        cmd.extend(["/mo", interval])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Task '{task_name}' created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create task '{task_name}': {e.stderr}")
        return False


def setup_all_tasks():
    """Setup all AI Employee scheduled tasks."""
    uv_cmd = f"cmd /c \"cd /d {PROJECT_ROOT} && uv run python"

    tasks = [
        {
            "name": "FileWatcher",
            "command": f'{uv_cmd} .claude/skills/file-watcher/scripts/file_watcher.py --watch ./DropFolder --vault ./AI_Employee_Vault"',
            "schedule": "ONLOGON",
        },
        {
            "name": "DailyBriefing",
            "command": f'cmd /c "cd /d {PROJECT_ROOT} && claude --print \\"Generate daily briefing and update Dashboard.md\\""',
            "schedule": "DAILY",
            "time": "08:00",
        },
        {
            "name": "WeeklyAudit",
            "command": f'cmd /c "cd /d {PROJECT_ROOT} && claude --print \\"Run weekly business audit and create CEO briefing\\""',
            "schedule": "WEEKLY",
            "time": "20:00",
        },
    ]

    success_count = 0
    for task in tasks:
        if create_task(
            task_name=task["name"],
            command=task["command"],
            schedule=task["schedule"],
            time=task.get("time"),
            interval=task.get("interval"),
        ):
            success_count += 1

    logger.info(f"Created {success_count}/{len(tasks)} scheduled tasks")


def list_tasks():
    """List all AI Employee scheduled tasks."""
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "TABLE", "/tn", "AIEmployee\\"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("No AI Employee tasks found")


def remove_all_tasks():
    """Remove all AI Employee scheduled tasks."""
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "AIEmployee", "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        logger.info("All AI Employee tasks removed")
    else:
        logger.warning("Could not remove tasks (may not exist)")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_all_tasks()
        elif sys.argv[1] == "--list":
            list_tasks()
        else:
            print("Usage: setup_scheduler.py [--list | --remove]")
    else:
        setup_all_tasks()


if __name__ == "__main__":
    main()
