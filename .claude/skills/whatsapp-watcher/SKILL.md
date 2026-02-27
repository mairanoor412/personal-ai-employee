---
name: whatsapp-watcher
description: This skill should be used when the user asks to "watch whatsapp", "monitor whatsapp messages", "setup whatsapp watcher", or mentions WhatsApp monitoring, message detection, or chat watching.
version: 1.0.0
---

# WhatsApp Watcher Skill

Monitors WhatsApp Web for new messages containing important keywords and creates action files in the vault.

## What This Skill Does

Uses Playwright to automate WhatsApp Web, detect unread messages with specific keywords, and create `.md` action files in `/Needs_Action/` for Claude to process.

## Prerequisites

- Python packages: `playwright`
- Install: `uv add playwright && uv run playwright install chromium`
- WhatsApp account linked to WhatsApp Web
- First run requires manual QR code scan (persistent session saved for future runs)

## Important Keywords to Watch

```python
KEYWORDS = [
    "urgent", "asap", "invoice", "payment", "help",
    "deadline", "meeting", "quote", "price", "order",
    "emergency", "important", "respond", "reply", "confirm"
]
```

## WhatsApp Watcher Script Pattern

Located at `scripts/whatsapp_watcher.py`:

```python
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("WhatsAppWatcher")

KEYWORDS = [
    "urgent", "asap", "invoice", "payment", "help",
    "deadline", "meeting", "quote", "price", "order"
]


class WhatsAppWatcher:
    def __init__(self, vault_path: str, session_path: str = "./whatsapp_session", check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)
        self.check_interval = check_interval
        self.processed_chats = set()

    def check_for_updates(self, page) -> list:
        """Find unread chats with keyword matches."""
        messages = []
        try:
            # Wait for chat list to load
            page.wait_for_selector('[aria-label*="Chat list"]', timeout=10000)

            # Find all unread chat indicators
            unread_chats = page.query_selector_all('span[data-testid="icon-unread-count"]')

            for badge in unread_chats:
                chat_item = badge.evaluate_handle("el => el.closest('[data-testid=\"cell-frame-container\"]')")
                if not chat_item:
                    continue

                chat_text = chat_item.inner_text().lower()
                if any(kw in chat_text for kw in KEYWORDS):
                    # Extract sender name (first line of chat item)
                    lines = chat_item.inner_text().split("\n")
                    sender = lines[0] if lines else "Unknown"
                    preview = lines[-1] if len(lines) > 1 else ""
                    chat_id = f"{sender}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    if chat_id not in self.processed_chats:
                        messages.append({
                            "sender": sender,
                            "preview": preview,
                            "chat_id": chat_id,
                            "matched_keywords": [kw for kw in KEYWORDS if kw in chat_text]
                        })
                        self.processed_chats.add(chat_id)
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        return messages

    def create_action_file(self, message: dict) -> Path:
        """Create a markdown action file for a detected message."""
        now = datetime.now().isoformat()
        keywords_str = ", ".join(message["matched_keywords"])

        content = f"""---
type: whatsapp
from: {message['sender']}
subject: WhatsApp message with keywords [{keywords_str}]
received: {now}
priority: high
status: pending
matched_keywords: [{keywords_str}]
---

## WhatsApp Message
- **From**: {message['sender']}
- **Preview**: {message['preview']}
- **Keywords Detected**: {keywords_str}
- **Received**: {now}

## Suggested Actions
- [ ] Read full conversation
- [ ] Reply to sender
- [ ] Create task if actionable
- [ ] Archive after processing
"""
        filepath = self.needs_action / f"WHATSAPP_{message['chat_id']}.md"
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Created action file: {filepath.name}")
        self._log_action(message)
        return filepath

    def _log_action(self, message: dict):
        """Write audit log entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "whatsapp_detected",
            "actor": "whatsapp_watcher",
            "from": message["sender"],
            "keywords": message["matched_keywords"]
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def run(self):
        """Start WhatsApp Web monitoring."""
        logger.info("WhatsApp Watcher starting...")
        with sync_playwright() as p:
            # Launch persistent context (saves WhatsApp session)
            context = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Must be False for first QR scan
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://web.whatsapp.com")

            logger.info("Waiting for WhatsApp Web to load (scan QR if first time)...")
            page.wait_for_selector('[aria-label*="Chat list"]', timeout=120000)
            logger.info("WhatsApp Web loaded. Monitoring started.")

            try:
                while True:
                    messages = self.check_for_updates(page)
                    for msg in messages:
                        self.create_action_file(msg)
                    if messages:
                        logger.info(f"Processed {len(messages)} new messages")
                    time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("WhatsApp Watcher stopping...")
            finally:
                context.close()
```

## First Run Setup

1. Run the script: `uv run python .claude/skills/whatsapp-watcher/scripts/whatsapp_watcher.py`
2. Browser opens WhatsApp Web
3. Scan QR code with your phone
4. Session is saved in `whatsapp_session/` folder
5. Future runs skip QR scan (persistent session)

## Security Rules

- NEVER store WhatsApp session in Git (add `whatsapp_session/` to `.gitignore`)
- Session contains authentication data — treat as credentials
- First run must be `headless=False` for QR scan
- Subsequent runs can be `headless=True` after session is established
- Be aware of WhatsApp's terms of service regarding automation

## When to Use

- Setting up WhatsApp monitoring for the first time
- Restarting the WhatsApp watcher after downtime
- Modifying keyword detection list
