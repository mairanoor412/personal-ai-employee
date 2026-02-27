"""
Audit Logger — Centralized JSON audit logging for all AI Employee actions.

Provides a single interface for logging all actions, decisions, and state changes.

Usage:
    Import and use in other scripts:
        from audit_logger import AuditLogger
        logger = AuditLogger("./AI_Employee_Vault")
        logger.log("linkedin_post", "linkedin_poster", "success", {"file": "post.md"})

    Or run standalone to query logs:
        uv run python .claude/skills/audit-logger/scripts/audit_logger.py --vault ./AI_Employee_Vault --query today
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta


class AuditLogger:
    def __init__(self, vault_path: str = "./AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.logs_dir = self.vault / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action_type: str,
        actor: str,
        status: str = "success",
        details: dict = None,
        duration_ms: int = None,
        approval: dict = None,
    ):
        """Log an action to today's log file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "status": status,
        }
        if details:
            entry["details"] = details
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if approval:
            entry["approval"] = approval

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                entries = []

        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return entry

    def log_post(self, platform: str, filename: str, result: str, duration_ms: int = None):
        """Shortcut for social media post logging."""
        return self.log(
            action_type=f"{platform}_post",
            actor=f"{platform}_poster",
            status=result,
            details={"file": filename, "platform": platform},
            duration_ms=duration_ms,
        )

    def log_watcher(self, watcher_name: str, items_found: int, details: dict = None):
        """Shortcut for watcher activity logging."""
        return self.log(
            action_type=f"{watcher_name}_detected",
            actor=watcher_name,
            status="success",
            details={"items_found": items_found, **(details or {})},
        )

    def log_approval(self, filename: str, approved_by: str, action: str = "approval_granted"):
        """Log an approval decision."""
        return self.log(
            action_type=action,
            actor=approved_by,
            status="success",
            details={"file": filename},
            approval={
                "required": True,
                "approved_by": approved_by,
                "approved_at": datetime.now().isoformat(),
            },
        )

    def log_error(self, source: str, error: str, severity: str = "medium"):
        """Log an error."""
        return self.log(
            action_type="error",
            actor=source,
            status="failed",
            details={"error": error, "severity": severity},
        )

    def query(self, days: int = 1, action_type: str = None, actor: str = None, status: str = None) -> list[dict]:
        """Query log entries with filters."""
        cutoff = datetime.now() - timedelta(days=days)
        results = []

        for log_file in sorted(self.logs_dir.glob("*.json")):
            try:
                file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
                if file_date < cutoff:
                    continue
            except ValueError:
                continue
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
                if not isinstance(entries, list):
                    continue
            except (json.JSONDecodeError, OSError):
                continue

            for entry in entries:
                if action_type and entry.get("action_type") != action_type:
                    continue
                if actor and entry.get("actor") != actor:
                    continue
                if status and entry.get("status") != status:
                    continue
                results.append(entry)

        return results

    def summary(self, days: int = 1) -> str:
        """Generate a text summary of recent log entries."""
        entries = self.query(days=days)
        if not entries:
            return f"No log entries in the last {days} day(s)."

        lines = [f"Audit Log Summary — Last {days} day(s)", f"Total entries: {len(entries)}", ""]

        # Group by action type
        by_type = {}
        for e in entries:
            action = e.get("action_type", "unknown")
            by_type.setdefault(action, []).append(e)

        for action, items in sorted(by_type.items()):
            success = sum(1 for i in items if i.get("status") in ("success", "posted"))
            failed = sum(1 for i in items if i.get("status") in ("failed",))
            lines.append(f"  {action}: {len(items)} total ({success} success, {failed} failed)")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit Logger for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--query", choices=["today", "week", "errors", "summary"], default="summary")
    args = parser.parse_args()

    logger = AuditLogger(args.vault)

    if args.query == "today":
        entries = logger.query(days=1)
        for e in entries:
            ts = e.get("timestamp", "")[:19]
            print(f"[{ts}] {e.get('action_type')} — {e.get('actor')} — {e.get('status')}")

    elif args.query == "week":
        entries = logger.query(days=7)
        for e in entries:
            ts = e.get("timestamp", "")[:19]
            print(f"[{ts}] {e.get('action_type')} — {e.get('actor')} — {e.get('status')}")

    elif args.query == "errors":
        entries = logger.query(days=7, status="failed")
        if entries:
            for e in entries:
                ts = e.get("timestamp", "")[:19]
                details = e.get("details", {})
                print(f"[{ts}] {e.get('actor')}: {details.get('error', e.get('action_type'))}")
        else:
            print("No errors in the last 7 days ✅")

    elif args.query == "summary":
        print(logger.summary(days=7))


if __name__ == "__main__":
    main()
