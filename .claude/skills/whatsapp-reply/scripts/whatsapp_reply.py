"""
WhatsApp Reply — Sends approved replies via WhatsApp Web (Playwright).
Only processes files from /Approved/ folder (Human-in-the-Loop).

Uses the same whatsapp_session as WhatsApp Watcher — no extra login needed.

Prerequisites:
    uv add playwright
    WhatsApp session established (QR scanned via whatsapp-watcher)

Usage:
    uv run python .claude/skills/whatsapp-reply/scripts/whatsapp_reply.py --vault ./AI_Employee_Vault
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
logger = logging.getLogger("WhatsAppReply")


class WhatsAppReply:
    def __init__(self, vault_path: str, session_path: str = "./whatsapp_session"):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)

    def extract_reply_data(self, filepath: Path) -> dict:
        """Extract contact name and message from reply file."""
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")

        contact = None
        message_lines = []
        in_message = False

        for line in lines:
            # Extract contact name
            if "**Contact**:" in line or "**To**:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    contact = parts[1].strip().strip("*")
            elif line.startswith("to:") and not contact:
                contact = line.split(":", 1)[1].strip()

            # Extract message content
            if line.startswith("## Message Content") or line.startswith("## Reply Content"):
                in_message = True
                continue
            elif line.startswith("## Reply Settings") or (line.startswith("## ") and in_message):
                in_message = False
            elif in_message:
                message_lines.append(line)

        return {
            "contact": contact,
            "message": "\n".join(message_lines).strip(),
        }

    def find_and_open_chat(self, page, contact_name: str) -> bool:
        """Search for a contact and open their chat."""
        try:
            # ── Find search box ──
            logger.info(f"  Searching for contact: {contact_name}")
            search_box = None

            search_selectors = [
                '[data-testid="chat-list-search"]',
                '[aria-label="Search input textbox"]',
                '[title="Search input textbox"]',
                'div[contenteditable="true"][data-tab="3"]',
            ]

            # Click search icon first
            try:
                search_icon = page.locator('[data-testid="search"]').first
                if search_icon.is_visible(timeout=3000):
                    search_icon.click(timeout=3000)
                    time.sleep(1)
            except Exception:
                pass

            for selector in search_selectors:
                try:
                    search_box = page.wait_for_selector(selector, timeout=5000)
                    if search_box:
                        logger.info(f"  Found search box: {selector}")
                        break
                except Exception:
                    continue

            if not search_box:
                # Try the side panel search
                try:
                    search_box = page.locator('[contenteditable="true"]').first
                    if search_box.is_visible(timeout=3000):
                        logger.info("  Found search via contenteditable")
                except Exception:
                    pass

            if not search_box:
                logger.error("  Could not find search box!")
                page.screenshot(path="debug_whatsapp_search.png")
                return False

            # ── Type contact name ──
            page.evaluate("(el) => { el.focus(); el.click(); }", search_box)
            time.sleep(0.5)

            # Clear any existing text
            page.keyboard.press("Control+a")
            page.keyboard.press("Backspace")
            time.sleep(0.3)

            page.keyboard.type(contact_name, delay=50)
            time.sleep(3)

            # ── Click on the matching contact ──
            contact_clicked = False

            # Try to find the contact in search results
            try:
                # Look for exact match in search results
                result = page.locator(f'span[title="{contact_name}"]').first
                if result.is_visible(timeout=5000):
                    result.click(timeout=5000)
                    contact_clicked = True
                    logger.info(f"  Opened chat with: {contact_name}")
            except Exception:
                pass

            if not contact_clicked:
                # Try partial match
                try:
                    results = page.locator('[data-testid="cell-frame-container"]')
                    count = results.count()
                    for i in range(min(count, 5)):
                        item = results.nth(i)
                        text = item.inner_text().lower()
                        if contact_name.lower() in text:
                            item.click(timeout=5000)
                            contact_clicked = True
                            logger.info(f"  Opened chat via cell-frame match")
                            break
                except Exception:
                    pass

            if not contact_clicked:
                # Try clicking first search result
                try:
                    first_result = page.locator('[data-testid="chatlist-panel-body"] [role="listitem"]').first
                    if first_result.is_visible(timeout=3000):
                        first_result.click(timeout=5000)
                        contact_clicked = True
                        logger.info("  Clicked first search result")
                except Exception:
                    pass

            if not contact_clicked:
                logger.error(f"  Could not find contact: {contact_name}")
                page.screenshot(path="debug_whatsapp_contact.png")
                return False

            time.sleep(2)
            return True

        except Exception as e:
            logger.error(f"  Error finding contact: {e}")
            return False

    def send_message(self, page, message: str) -> bool:
        """Type and send a message in the currently open chat."""
        try:
            # ── Find message input box ──
            logger.info("  Finding message input...")
            msg_box = None

            msg_selectors = [
                '[data-testid="conversation-compose-box-input"]',
                'div[contenteditable="true"][data-tab="10"]',
                'div[contenteditable="true"][data-tab="6"]',
                '[aria-label="Type a message"]',
                'footer [contenteditable="true"]',
            ]

            for selector in msg_selectors:
                try:
                    msg_box = page.wait_for_selector(selector, timeout=5000)
                    if msg_box:
                        logger.info(f"  Found message box: {selector}")
                        break
                except Exception:
                    continue

            if not msg_box:
                logger.error("  Could not find message input box!")
                page.screenshot(path="debug_whatsapp_msgbox.png")
                return False

            # ── Type message ──
            logger.info("  Typing message...")
            page.evaluate("(el) => { el.focus(); el.click(); }", msg_box)
            time.sleep(0.5)

            # Handle multi-line messages: Shift+Enter for newlines
            lines = message.split("\n")
            for i, line in enumerate(lines):
                page.keyboard.type(line, delay=10)
                if i < len(lines) - 1:
                    page.keyboard.press("Shift+Enter")
            time.sleep(1)

            # ── Click Send button ──
            logger.info("  Clicking Send...")
            send_clicked = False

            try:
                send_btn = page.locator('[data-testid="send"]').first
                if send_btn.is_visible(timeout=5000):
                    send_btn.click(timeout=5000)
                    send_clicked = True
                    logger.info("  Clicked send via data-testid")
            except Exception:
                pass

            if not send_clicked:
                try:
                    send_btn = page.locator('[aria-label="Send"]').first
                    if send_btn.is_visible(timeout=3000):
                        send_btn.click(timeout=5000)
                        send_clicked = True
                        logger.info("  Clicked send via aria-label")
                except Exception:
                    pass

            if not send_clicked:
                # Try pressing Enter as fallback
                page.keyboard.press("Enter")
                send_clicked = True
                logger.info("  Sent via Enter key")

            time.sleep(3)

            if send_clicked:
                logger.info("  Message sent successfully!")
                return True
            else:
                logger.error("  Could not send message")
                page.screenshot(path="debug_whatsapp_send.png")
                return False

        except Exception as e:
            logger.error(f"  Error sending message: {e}")
            return False

    def process_approved_replies(self):
        """Process all approved WhatsApp reply files."""
        approved_replies = list(self.approved_dir.glob("WHATSAPP_REPLY_*.md"))
        if not approved_replies:
            logger.info("No approved WhatsApp replies found")
            return

        logger.info(f"Found {len(approved_replies)} approved reply(s) to send")

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://web.whatsapp.com", timeout=60000)

                # Wait for WhatsApp to load
                logger.info("Waiting for WhatsApp Web to load...")
                try:
                    page.wait_for_selector('[aria-label*="Chat list"]', timeout=60000)
                except Exception:
                    logger.error("WhatsApp Web did not load. Is session valid?")
                    context.close()
                    return

                logger.info("WhatsApp Web loaded")
                time.sleep(3)

                for filepath in approved_replies:
                    reply_data = self.extract_reply_data(filepath)

                    if not reply_data["contact"]:
                        logger.warning(f"No contact found in {filepath.name}")
                        continue
                    if not reply_data["message"]:
                        logger.warning(f"No message found in {filepath.name}")
                        continue

                    logger.info(f"Sending reply: {filepath.name}")
                    logger.info(f"  To: {reply_data['contact']}")
                    logger.info(f"  Message: {reply_data['message'][:50]}...")

                    # Step 1: Find and open the chat
                    chat_opened = self.find_and_open_chat(page, reply_data["contact"])
                    if not chat_opened:
                        self._log_action(filepath.name, reply_data["contact"], "failed")
                        continue

                    # Step 2: Send the message
                    sent = self.send_message(page, reply_data["message"])

                    if sent:
                        dest = self.done_dir / filepath.name
                        filepath.rename(dest)
                        self._log_action(filepath.name, reply_data["contact"], "sent")
                        logger.info(f"  Moved {filepath.name} to Done")
                    else:
                        self._log_action(filepath.name, reply_data["contact"], "failed")

                    # Go back to chat list for next reply
                    try:
                        back_btn = page.locator('[data-testid="back"]').first
                        if back_btn.is_visible(timeout=2000):
                            back_btn.click()
                            time.sleep(1)
                    except Exception:
                        page.goto("https://web.whatsapp.com", timeout=30000)
                        time.sleep(5)

                context.close()

        except Exception as e:
            logger.error(f"Failed to process replies: {e}")

    def _log_action(self, filename: str, contact: str, result: str):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "whatsapp_reply",
            "actor": "whatsapp_reply",
            "file": filename,
            "contact": contact,
            "result": result,
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="WhatsApp Reply for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./whatsapp_session", help="Path to WhatsApp session")
    args = parser.parse_args()

    replier = WhatsAppReply(vault_path=args.vault, session_path=args.session)
    replier.process_approved_replies()


if __name__ == "__main__":
    main()
