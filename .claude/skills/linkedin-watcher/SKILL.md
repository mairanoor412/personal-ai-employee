---
name: linkedin-watcher
description: This skill should be used when the user asks to "watch linkedin", "monitor linkedin", "check linkedin messages", or mentions LinkedIn monitoring, connection requests, or LinkedIn notifications.
version: 1.0.0
---

# LinkedIn Watcher Skill

Monitors LinkedIn for new messages, connection requests, and notifications using Playwright browser automation.

## What This Skill Does

Uses Playwright to automate LinkedIn Web, detect new messages and notifications, and create `.md` action files in `/Needs_Action/` for Claude to process.

## Prerequisites

- Python packages: `playwright`
- Install: `uv add playwright && uv run playwright install chromium`
- LinkedIn account credentials (stored in `.env`, NEVER in vault)

## LinkedIn Watcher Script Pattern

Located at `scripts/linkedin_watcher.py`:

```python
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("LinkedInWatcher")


class LinkedInWatcher:
    def __init__(self, vault_path: str, session_path: str = "./linkedin_session", check_interval: int = 300):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)
        self.check_interval = check_interval
        self.processed_ids = set()

    def login(self, page):
        """Login to LinkedIn using stored credentials."""
        page.goto("https://www.linkedin.com/login")
        page.fill('input[name="session_key"]', os.getenv("LINKEDIN_EMAIL", ""))
        page.fill('input[name="session_password"]', os.getenv("LINKEDIN_PASSWORD", ""))
        page.click('button[type="submit"]')
        page.wait_for_url("**/feed/**", timeout=30000)
        logger.info("LinkedIn login successful")

    def check_messages(self, page) -> list:
        """Check for new LinkedIn messages."""
        messages = []
        try:
            page.goto("https://www.linkedin.com/messaging/")
            page.wait_for_selector(".msg-conversations-container__conversations-list", timeout=10000)

            # Find unread conversations
            unread = page.query_selector_all(".msg-conversation-card--unread")
            for conv in unread:
                sender = conv.query_selector(".msg-conversation-card__participant-names")
                preview = conv.query_selector(".msg-conversation-card__message-snippet")

                sender_name = sender.inner_text().strip() if sender else "Unknown"
                msg_preview = preview.inner_text().strip() if preview else ""
                msg_id = f"linkedin_msg_{sender_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                if msg_id not in self.processed_ids:
                    messages.append({
                        "type": "linkedin_message",
                        "sender": sender_name,
                        "preview": msg_preview,
                        "msg_id": msg_id
                    })
                    self.processed_ids.add(msg_id)
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        return messages

    def check_notifications(self, page) -> list:
        """Check for new LinkedIn notifications."""
        notifications = []
        try:
            page.goto("https://www.linkedin.com/notifications/")
            page.wait_for_selector(".nt-card", timeout=10000)

            cards = page.query_selector_all(".nt-card--unread")[:5]
            for card in cards:
                text = card.inner_text().strip()
                notif_id = f"linkedin_notif_{hash(text)}_{datetime.now().strftime('%Y%m%d')}"

                if notif_id not in self.processed_ids:
                    notifications.append({
                        "type": "linkedin_notification",
                        "content": text[:200],
                        "notif_id": notif_id
                    })
                    self.processed_ids.add(notif_id)
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
        return notifications

    def create_action_file(self, item: dict) -> Path:
        """Create a markdown action file for detected LinkedIn activity."""
        now = datetime.now().isoformat()

        if item["type"] == "linkedin_message":
            content = f"""---
type: linkedin_message
from: {item['sender']}
subject: LinkedIn message from {item['sender']}
received: {now}
priority: medium
status: pending
---

## LinkedIn Message
- **From**: {item['sender']}
- **Preview**: {item['preview']}
- **Received**: {now}

## Suggested Actions
- [ ] Read full message on LinkedIn
- [ ] Reply to sender
- [ ] Create follow-up task if needed
"""
            filepath = self.needs_action / f"LINKEDIN_MSG_{item['msg_id']}.md"
        else:
            content = f"""---
type: linkedin_notification
subject: LinkedIn notification
received: {now}
priority: low
status: pending
---

## LinkedIn Notification
{item['content']}

## Suggested Actions
- [ ] Review notification
- [ ] Take action if needed
"""
            filepath = self.needs_action / f"LINKEDIN_NOTIF_{item['notif_id']}.md"

        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Created action file: {filepath.name}")
        return filepath

    def run(self):
        """Start LinkedIn monitoring."""
        logger.info("LinkedIn Watcher starting...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Check if already logged in
            page.goto("https://www.linkedin.com/feed/")
            if "login" in page.url:
                self.login(page)

            logger.info("LinkedIn monitoring started")
            try:
                while True:
                    messages = self.check_messages(page)
                    notifications = self.check_notifications(page)

                    for item in messages + notifications:
                        self.create_action_file(item)

                    total = len(messages) + len(notifications)
                    if total:
                        logger.info(f"Processed {total} LinkedIn items")
                    time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("LinkedIn Watcher stopping...")
            finally:
                context.close()
```

## Environment Variables Required

```bash
# .env file
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

## Security Rules

- NEVER store LinkedIn credentials in vault or Git
- Add `linkedin_session/` to `.gitignore`
- Check interval minimum 300 seconds (5 min) — LinkedIn rate limits aggressively
- Use persistent session to avoid repeated logins
- Be aware of LinkedIn's automation policies

## When to Use

- Setting up LinkedIn monitoring for first time
- Checking for business leads and messages
- Monitoring connection requests and notifications
