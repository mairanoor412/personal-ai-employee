---
name: file-watcher
description: This skill should be used when the user asks to "watch files", "monitor folder", "setup file watcher", "watch for new files", or mentions file system monitoring, drop folder, or filesystem events.
version: 1.0.0
---

# File Watcher Skill

Monitors a designated drop folder for new files and creates action items in the Obsidian vault.

## What This Skill Does

Runs a Python script using the `watchdog` library to monitor a specified folder. When new files are dropped in, it copies them to `/Needs_Action/` and creates a metadata `.md` file for Claude to process.

## Prerequisites

- Python package: `watchdog`
- Install: `uv add watchdog` or `pip install watchdog`

## File Watcher Script Pattern

Located at `scripts/file_watcher.py`:

```python
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logger = logging.getLogger("FileWatcher")

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        source = Path(event.src_path)
        self.logger.info(f"New file detected: {source.name}")

        # Copy file to Needs_Action
        dest = self.needs_action / f"FILE_{source.name}"
        shutil.copy2(source, dest)

        # Create metadata markdown file
        self._create_metadata(source, dest)

    def _create_metadata(self, source: Path, dest: Path):
        meta_path = self.needs_action / f"FILE_{source.stem}.md"
        now = datetime.now().isoformat()
        size = source.stat().st_size
        suffix = source.suffix.lower()

        content = f"""---
type: file_drop
original_name: {source.name}
file_type: {suffix}
size_bytes: {size}
detected_at: {now}
status: pending
---

## File Details
- **Name**: {source.name}
- **Type**: {suffix}
- **Size**: {size} bytes
- **Detected**: {now}

## Suggested Actions
- [ ] Review file contents
- [ ] Categorize and file appropriately
- [ ] Process if actionable
"""
        meta_path.write_text(content, encoding="utf-8")
        self.logger.info(f"Created metadata: {meta_path.name}")


class FileWatcher:
    def __init__(self, watch_path: str, vault_path: str):
        self.watch_path = watch_path
        self.vault_path = vault_path
        self.observer = Observer()
        self.logger = logging.getLogger("FileWatcher")

    def run(self):
        handler = DropFolderHandler(self.vault_path)
        self.observer.schedule(handler, self.watch_path, recursive=False)
        self.observer.start()
        self.logger.info(f"File Watcher started on: {self.watch_path}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
```

## Metadata File Format

Each detected file creates `FILE_<name>.md`:

```yaml
---
type: file_drop
original_name: document.pdf
file_type: .pdf
size_bytes: 245000
detected_at: 2026-01-07T10:30:00
status: pending
---
```

## Important Rules

- Only monitor the designated drop folder, NOT the entire vault
- Copy files (don't move) so originals remain intact
- Create `.md` metadata for every detected file
- Ignore temporary files (starting with `.` or `~`)
- Ignore directory creation events
- Log all detections to `/Logs/`

## When to Use

- Setting up file system monitoring for first time
- When user wants to watch a specific folder for incoming documents
- Debugging file detection issues
