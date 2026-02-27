"""
LinkedIn Watcher - Monitors LinkedIn for messages and notifications
Creates action files in AI_Employee_Vault/Needs_Action/

Prerequisites:
    uv add playwright
    uv run playwright install chromium
    Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env

Usage:
    uv run python .claude/skills/linkedin-watcher/scripts/linkedin_watcher.py --vault ./AI_Employee_Vault
"""

import os
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load .env file from project root
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
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
        email = os.getenv("LINKEDIN_EMAIL", "")
        password = os.getenv("LINKEDIN_PASSWORD", "")

        if not email or not password:
            logger.error("LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set in .env file!")
            logger.error("Create a .env file in project root with:")
            logger.error('  LINKEDIN_EMAIL=your_email')
            logger.error('  LINKEDIN_PASSWORD=your_password')
            raise ValueError("LinkedIn credentials not found in .env")

        logger.info(f"Logging in as: {email}")
        page.goto("https://www.linkedin.com/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="session_key"]', email)
        page.fill('input[name="session_password"]', password)
        page.click('button[type="submit"]')

        # Wait for login — LinkedIn may show verification/captcha
        # Give user 120 seconds to complete any security checks
        logger.info("Waiting for login... If you see a security check in the browser, complete it manually.")
        try:
            page.wait_for_url("**/feed/**", timeout=120000)
        except Exception:
            # Check if we landed somewhere else (verification, challenge, etc.)
            current_url = page.url
            if "checkpoint" in current_url or "challenge" in current_url:
                logger.warning("LinkedIn security verification detected!")
                logger.warning("Please complete the verification in the browser window.")
                logger.warning("Waiting up to 3 minutes...")
                page.wait_for_url("**/feed/**", timeout=180000)
            elif "feed" in current_url:
                pass  # Already on feed, ignore error
            else:
                logger.error(f"Login failed. Current URL: {current_url}")
                raise

        logger.info("LinkedIn login successful!")

    def check_messages(self, page) -> list:
        messages = []
        try:
            page.goto("https://www.linkedin.com/messaging/")
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)  # Let messaging UI fully render

            # Try multiple selectors (LinkedIn changes these often)
            unread_selectors = [
                ".msg-conversation-card--unread",
                "[class*='conversation-card'][class*='unread']",
                "li[class*='unread']",
            ]

            unread = []
            for selector in unread_selectors:
                unread = page.query_selector_all(selector)
                if unread:
                    break

            for conv in unread:
                try:
                    text = conv.inner_text().strip()
                    lines = text.split("\n")
                    sender_name = lines[0].strip() if lines else "Unknown"
                    msg_preview = lines[-1].strip() if len(lines) > 1 else ""
                    msg_id = f"linkedin_msg_{sender_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    if msg_id not in self.processed_ids:
                        messages.append({
                            "type": "linkedin_message",
                            "sender": sender_name,
                            "preview": msg_preview,
                            "msg_id": msg_id,
                        })
                        self.processed_ids.add(msg_id)
                except Exception:
                    continue

            if not unread:
                logger.info("No unread LinkedIn messages found")
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        return messages

    def check_notifications(self, page) -> list:
        notifications = []
        try:
            page.goto("https://www.linkedin.com/notifications/")
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)  # Let notifications UI fully render

            # Try multiple selectors for notifications
            notif_selectors = [
                ".nt-card--unread",
                "[class*='nt-card'][class*='unread']",
                ".notification-card--unread",
                "article[class*='unread']",
            ]

            cards = []
            for selector in notif_selectors:
                cards = page.query_selector_all(selector)
                if cards:
                    break

            # If no specific unread selector works, get all notification cards
            if not cards:
                general_selectors = [
                    ".nt-card",
                    "[class*='nt-card']",
                    ".notification-card",
                    "article[data-urn]",
                ]
                for selector in general_selectors:
                    cards = page.query_selector_all(selector)
                    if cards:
                        cards = cards[:5]  # Only take first 5
                        break

            for card in cards[:5]:
                try:
                    text = card.inner_text().strip()
                    if not text:
                        continue
                    notif_id = f"linkedin_notif_{hash(text)}_{datetime.now().strftime('%Y%m%d')}"

                    if notif_id not in self.processed_ids:
                        notifications.append({
                            "type": "linkedin_notification",
                            "content": text[:200],
                            "notif_id": notif_id,
                        })
                        self.processed_ids.add(notif_id)
                except Exception:
                    continue

            if not cards:
                logger.info("No LinkedIn notifications found (selectors may need update)")
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
        return notifications

    def create_action_file(self, item: dict) -> Path:
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
        self._log_action(item)
        return filepath

    def _log_action(self, item: dict):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": f"linkedin_{item['type']}",
            "actor": "linkedin_watcher",
            "details": item,
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
        logger.info("LinkedIn Watcher starting...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 800},
            )
            page = context.pages[0] if context.pages else context.new_page()

            page.goto("https://www.linkedin.com/feed/")
            page.wait_for_load_state("networkidle")

            # Check if login is needed
            if "login" in page.url or "checkpoint" in page.url:
                self.login(page)

            logger.info("LinkedIn monitoring started! Checking every %d seconds.", self.check_interval)
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


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Watcher for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./linkedin_session", help="Path to LinkedIn session")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")
    args = parser.parse_args()

    watcher = LinkedInWatcher(
        vault_path=args.vault,
        session_path=args.session,
        check_interval=args.interval,
    )
    watcher.run()


if __name__ == "__main__":
    main()
