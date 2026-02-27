"""
WhatsApp Watcher - Monitors WhatsApp Web for important messages
Creates action files in AI_Employee_Vault/Needs_Action/

Prerequisites:
    uv add playwright
    uv run playwright install chromium

Usage:
    uv run python .claude/skills/whatsapp-watcher/scripts/whatsapp_watcher.py --vault ./AI_Employee_Vault
"""

import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("WhatsAppWatcher")

KEYWORDS = [
    "urgent", "asap", "invoice", "payment", "help",
    "deadline", "meeting", "quote", "price", "order",
    "emergency", "important", "respond", "reply", "confirm",
]

# JavaScript to find all unread chats with contact names
FIND_UNREAD_JS = """
() => {
    const results = [];

    // Strategy 1: Find all elements with aria-label containing "unread"
    const unreadBadges = document.querySelectorAll('[aria-label*="unread"]');

    for (const badge of unreadBadges) {
        // Walk up the DOM to find the chat row (go up many levels)
        let parent = badge;
        let sender = null;
        let preview = null;

        // Walk up to 15 levels to find span[title]
        for (let i = 0; i < 15; i++) {
            parent = parent.parentElement;
            if (!parent) break;

            // Look for span[title] at this level
            if (!sender) {
                const titleSpans = parent.querySelectorAll('span[title]');
                for (const span of titleSpans) {
                    const title = span.getAttribute('title');
                    if (title && title.length > 1 && !title.match(/^\\d+$/)) {
                        if (!sender) {
                            sender = title;
                        } else if (!preview) {
                            preview = title;
                        }
                    }
                }
            }

            // Stop if we found the listitem or a known container
            if (parent.getAttribute('role') === 'listitem' ||
                parent.getAttribute('role') === 'row' ||
                parent.getAttribute('data-testid') === 'cell-frame-container') {
                // Do one more search at this level
                const titleSpans = parent.querySelectorAll('span[title]');
                const titles = [];
                for (const span of titleSpans) {
                    const t = span.getAttribute('title');
                    if (t && t.length > 0) titles.push(t);
                }
                if (titles.length > 0) sender = titles[0];
                if (titles.length > 1) preview = titles[titles.length - 1];
                break;
            }
        }

        if (sender && !results.find(r => r.sender === sender)) {
            results.push({
                sender: sender,
                preview: preview || "",
                unreadCount: badge.textContent || "1"
            });
        }
    }

    return results;
}
"""


class WhatsAppWatcher:
    def __init__(self, vault_path: str, session_path: str = "./whatsapp_session", check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)
        self.check_interval = check_interval

    def check_for_updates(self, page) -> list:
        messages = []
        try:
            page.wait_for_selector('[aria-label*="Chat list"]', timeout=10000)

            # Use JavaScript to find unread chats with contact names
            unread_data = page.evaluate(FIND_UNREAD_JS)

            logger.info(f"  Found {len(unread_data)} unread chat(s)")

            for chat in unread_data:
                sender = chat.get("sender", "Unknown")
                preview = chat.get("preview", "")
                chat_text = f"{sender} {preview}".lower()
                matched_kw = [kw for kw in KEYWORDS if kw in chat_text]

                chat_id = f"{sender.replace(' ', '_')}"

                # Skip only if action file already exists in Needs_Action
                action_file = self.needs_action / f"WHATSAPP_{chat_id}.md"
                if action_file.exists():
                    continue

                messages.append({
                    "sender": sender,
                    "preview": preview,
                    "chat_id": chat_id,
                    "matched_keywords": matched_kw,
                    "has_keywords": len(matched_kw) > 0,
                })
                logger.info(f"  New message from: {sender} | Keywords: {matched_kw if matched_kw else 'none'}")

        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        return messages

    def create_action_file(self, message: dict) -> Path:
        now = datetime.now().isoformat()
        keywords_str = ", ".join(message["matched_keywords"])

        content = f"""---
type: whatsapp
from: {message['sender']}
subject: WhatsApp message from {message['sender']}
received: {now}
priority: high
status: pending
matched_keywords: [{keywords_str}]
---

## WhatsApp Message
- **From**: {message['sender']}
- **Preview**: {message['preview']}
- **Keywords Detected**: {keywords_str if keywords_str else 'none'}
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
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "whatsapp_detected",
            "actor": "whatsapp_watcher",
            "from": message["sender"],
            "keywords": message["matched_keywords"],
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
        logger.info("WhatsApp Watcher starting...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
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
                        logger.info(f"Processed {len(messages)} new message(s)")
                    else:
                        logger.info("No new unread messages")
                    time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("WhatsApp Watcher stopping...")
            finally:
                context.close()


def main():
    parser = argparse.ArgumentParser(description="WhatsApp Watcher for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./whatsapp_session", help="Path to WhatsApp session")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    args = parser.parse_args()

    watcher = WhatsAppWatcher(
        vault_path=args.vault,
        session_path=args.session,
        check_interval=args.interval,
    )
    watcher.run()


if __name__ == "__main__":
    main()
