"""
File Watcher - Monitors a drop folder for new files
Creates action files in AI_Employee_Vault/Needs_Action/

Prerequisites:
    Install: uv add watchdog

Usage:
    python scripts/file_watcher.py --watch ./DropFolder --vault ./AI_Employee_Vault
"""

import time
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("FileWatcher")


class DropFolderHandler(FileSystemEventHandler):
    """Handles file creation events in the watched folder."""

    # Files to ignore
    IGNORE_PREFIXES = (".", "~", "$")
    IGNORE_SUFFIXES = (".tmp", ".swp", ".lock")

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"

    def on_created(self, event: FileSystemEvent) -> None:
        """Called when a new file is created in the watched folder."""
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Skip ignored files
        if any(source.name.startswith(p) for p in self.IGNORE_PREFIXES):
            return
        if any(source.name.endswith(s) for s in self.IGNORE_SUFFIXES):
            return

        logger.info(f"New file detected: {source.name}")

        # Copy file to Needs_Action
        dest = self.needs_action / f"FILE_{source.name}"
        try:
            shutil.copy2(source, dest)
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return

        # Create metadata markdown file
        self._create_metadata(source)
        self._log_action(source)

    def _create_metadata(self, source: Path):
        """Create a markdown metadata file for the detected file."""
        meta_path = self.needs_action / f"FILE_{source.stem}.md"
        now = datetime.now().isoformat()

        try:
            size = source.stat().st_size
        except OSError:
            size = 0

        content = f"""---
type: file_drop
original_name: {source.name}
file_type: {source.suffix.lower()}
size_bytes: {size}
detected_at: {now}
status: pending
---

## File Details
- **Name**: {source.name}
- **Type**: {source.suffix.lower()}
- **Size**: {size} bytes
- **Detected**: {now}

## Suggested Actions
- [ ] Review file contents
- [ ] Categorize and file appropriately
- [ ] Process if actionable
"""
        meta_path.write_text(content, encoding="utf-8")
        logger.info(f"Created metadata: {meta_path.name}")

    def _log_action(self, source: Path):
        """Write audit log entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "file_detected",
            "actor": "file_watcher",
            "file": source.name,
            "details": {
                "size": source.stat().st_size if source.exists() else 0,
                "type": source.suffix,
            },
        }

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


class FileWatcher:
    """Main file watcher that monitors a drop folder."""

    def __init__(self, watch_path: str, vault_path: str):
        self.watch_path = watch_path
        self.vault_path = vault_path
        self.observer = Observer()

    def run(self):
        """Start monitoring the watch folder."""
        handler = DropFolderHandler(self.vault_path)
        self.observer.schedule(handler, self.watch_path, recursive=False)
        self.observer.start()
        logger.info(f"File Watcher started on: {self.watch_path}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("File Watcher stopping...")
            self.observer.stop()
        self.observer.join()
        logger.info("File Watcher stopped")


def main():
    parser = argparse.ArgumentParser(description="File Watcher for AI Employee")
    parser.add_argument(
        "--watch",
        default="./DropFolder",
        help="Folder to watch for new files",
    )
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to Obsidian vault",
    )
    args = parser.parse_args()

    # Ensure watch folder exists
    Path(args.watch).mkdir(parents=True, exist_ok=True)

    watcher = FileWatcher(watch_path=args.watch, vault_path=args.vault)
    watcher.run()


if __name__ == "__main__":
    main()
