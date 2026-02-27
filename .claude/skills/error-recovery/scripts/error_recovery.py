"""
Error Recovery — 3-level error handling for AI Employee.

Level 1: Auto-retry with exponential backoff
Level 2: Notify user via action file
Level 3: Graceful degradation (skip and continue)

Usage:
    Import and use as a decorator/wrapper in other scripts:
        from error_recovery import with_retry, ErrorRecovery
"""

import json
import time
import logging
import functools
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("ErrorRecovery")


class ErrorRecovery:
    def __init__(self, vault_path: str = "./AI_Employee_Vault"):
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.logs_dir = self.vault / "Logs"
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def retry_with_backoff(self, func, *args, max_retries: int = 3, base_delay: float = 2.0, **kwargs):
        """Level 1: Auto-retry with exponential backoff."""
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")
                return result
            except Exception as e:
                last_error = e
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        # All retries failed — escalate to Level 2
        logger.error(f"All {max_retries} retries failed. Escalating to user notification.")
        self.notify_user(
            source=func.__name__ if hasattr(func, "__name__") else "unknown",
            error=str(last_error),
            attempts=max_retries,
        )
        return None

    def notify_user(self, source: str, error: str, attempts: int = 0, severity: str = "medium"):
        """Level 2: Create error report in Needs_Action for human review."""
        timestamp = datetime.now()
        filename = f"ERROR_{source}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.needs_action / filename

        content = f"""---
type: error_report
source: {source}
severity: {severity}
timestamp: {timestamp.isoformat()}
status: pending
---

## Error Report

- **Source**: {source}
- **Error**: {error}
- **Attempts**: {attempts}
- **Last Attempt**: {timestamp.isoformat()}

## Context
Automated operation failed after {attempts} retry attempt(s).

## Suggested Fix
- [ ] Check if the service is accessible
- [ ] Verify credentials/session is valid
- [ ] Review error logs for more details
- [ ] Re-run the operation manually
"""
        filepath.write_text(content, encoding="utf-8")
        self._log_error(source, error, severity)
        logger.info(f"Error report created: {filepath}")

    def graceful_skip(self, item_name: str, error: str):
        """Level 3: Log the failure and skip to next item."""
        logger.warning(f"Skipping {item_name}: {error}")
        self._log_error(item_name, error, "low")

    def _log_error(self, source: str, error: str, severity: str):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "error",
            "actor": "error_recovery",
            "source": source,
            "error": error,
            "severity": severity,
            "result": "logged",
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def with_retry(max_retries: int = 3, base_delay: float = 2.0, vault_path: str = "./AI_Employee_Vault"):
    """Decorator for automatic retry with error recovery."""
    recovery = ErrorRecovery(vault_path)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return recovery.retry_with_backoff(
                func, *args, max_retries=max_retries, base_delay=base_delay, **kwargs
            )
        return wrapper
    return decorator


def main():
    """Demo / self-test of error recovery levels."""
    recovery = ErrorRecovery()

    print("=== Level 1: Auto-Retry Demo ===")
    call_count = 0

    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Network timeout (attempt {call_count})")
        return "Success!"

    result = recovery.retry_with_backoff(flaky_function, max_retries=3, base_delay=0.5)
    print(f"Result: {result}")

    print("\n=== Level 2: Notify User Demo ===")
    recovery.notify_user(
        source="demo_script",
        error="Could not connect to LinkedIn after 3 attempts",
        attempts=3,
        severity="medium",
    )
    print("Error report created in Needs_Action/")

    print("\n=== Level 3: Graceful Skip Demo ===")
    recovery.graceful_skip("TWITTER_POST_test.md", "Rate limited by Twitter API")
    print("Skipped and logged")


if __name__ == "__main__":
    main()
