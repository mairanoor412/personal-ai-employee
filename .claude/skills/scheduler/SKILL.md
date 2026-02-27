---
name: scheduler
description: This skill should be used when the user asks to "schedule a task", "setup cron job", "create scheduled task", "automate recurring tasks", or mentions scheduling, cron, Task Scheduler, or timed automation.
version: 1.0.0
---

# Scheduler Skill

Sets up scheduled/recurring tasks using Windows Task Scheduler (or cron on Linux/Mac) to automate AI Employee operations.

## What This Skill Does

Creates scheduled tasks that trigger watchers, processing loops, and briefing generation at specified times. Handles both one-time and recurring schedules.

## Scheduled Tasks for AI Employee

| Task | Schedule | Command |
|------|----------|---------|
| Gmail Watcher | Every 2 min (continuous) | `uv run python .claude/skills/gmail-watcher/scripts/gmail_watcher.py` |
| File Watcher | Continuous (daemon) | `uv run python .claude/skills/file-watcher/scripts/file_watcher.py` |
| Process Inbox | Every 15 min | Claude reads `/Needs_Action/` |
| Dashboard Update | Every 30 min | Claude updates `Dashboard.md` |
| Daily Briefing | 8:00 AM daily | Claude generates daily summary |
| Weekly Audit | Sunday 8:00 PM | Claude runs business audit |

## Windows Task Scheduler Setup

Located at `scripts/setup_scheduler.py`:

```python
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UV_PATH = "uv"


def create_task(task_name: str, command: str, schedule: str, time: str = None, interval: str = None):
    """Create a Windows Scheduled Task."""
    cmd = [
        "schtasks", "/create",
        "/tn", f"AIEmployee\\{task_name}",
        "/tr", command,
        "/sc", schedule,
        "/f"  # force overwrite if exists
    ]
    if time:
        cmd.extend(["/st", time])
    if interval and schedule == "MINUTE":
        cmd.extend(["/mo", interval])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Task '{task_name}' created: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create task '{task_name}': {e.stderr}")
        return False


def setup_all_tasks():
    """Setup all AI Employee scheduled tasks."""
    tasks = [
        {
            "name": "FileWatcher",
            "command": f'cmd /c "cd /d {PROJECT_ROOT} && {UV_PATH} run python .claude/skills/file-watcher/scripts/file_watcher.py --watch ./DropFolder --vault ./AI_Employee_Vault"',
            "schedule": "ONLOGON",
        },
        {
            "name": "ProcessInbox",
            "command": f'cmd /c "cd /d {PROJECT_ROOT} && claude --print \\"Process all files in AI_Employee_Vault/Needs_Action/\\""',
            "schedule": "MINUTE",
            "interval": "15",
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

    for task in tasks:
        create_task(
            task_name=task["name"],
            command=task["command"],
            schedule=task["schedule"],
            time=task.get("time"),
            interval=task.get("interval"),
        )

    logger.info("All scheduled tasks created successfully")


def list_tasks():
    """List all AI Employee scheduled tasks."""
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "TABLE", "/tn", "AIEmployee\\"],
        capture_output=True, text=True
    )
    print(result.stdout if result.returncode == 0 else "No tasks found")


def remove_all_tasks():
    """Remove all AI Employee scheduled tasks."""
    subprocess.run(
        ["schtasks", "/delete", "/tn", "AIEmployee", "/f"],
        capture_output=True, text=True
    )
    logger.info("All AI Employee tasks removed")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_all_tasks()
    elif len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_tasks()
    else:
        setup_all_tasks()
```

## Usage

```bash
# Setup all scheduled tasks
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py

# List current tasks
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --list

# Remove all tasks
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --remove
```

## Important Rules

- Scheduled tasks run under YOUR Windows user account
- Tasks persist across reboots (ONLOGON tasks start at login)
- Check Task Scheduler app to verify tasks are running
- Continuous watchers should use ONLOGON schedule (start with login)
- Processing tasks use MINUTE intervals
- Briefings/audits use DAILY/WEEKLY schedules
- Log all scheduler operations to `/Logs/`

## When to Use

- Initial setup of AI Employee automation
- Adding new recurring tasks
- Modifying schedule timings
- Debugging why tasks aren't running
