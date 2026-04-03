"""
Facebook Poster - Publishes approved posts to Facebook
Only processes files from /Approved/ folder (Human-in-the-Loop)

Prerequisites:
    uv add playwright
    Facebook session established (first run requires manual login)

Usage:
    uv run python .claude/skills/facebook-post/scripts/facebook_poster.py --vault ./AI_Employee_Vault
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
logger = logging.getLogger("FacebookPoster")


class FacebookPoster:
    def __init__(self, vault_path: str, session_path: str = "./facebook_session"):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)

    def extract_post_content(self, filepath: Path) -> str:
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")
        in_content = False
        post_lines = []
        for line in lines:
            if line.startswith("## Post Content"):
                in_content = True
                continue
            elif line.startswith("## Post Settings") or (line.startswith("## ") and in_content):
                in_content = False
            elif in_content:
                post_lines.append(line)
        return "\n".join(post_lines).strip()

    def publish_post(self, page, content: str) -> bool:
        try:
            # ── STEP 1: Navigate to Facebook feed ──
            logger.info("Step 1: Opening Facebook feed...")
            page.goto("https://www.facebook.com/", timeout=60000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            time.sleep(5)

            # ── STEP 1.5: Close any blocking dialogs (notifications, review audience, etc) ──
            for _ in range(5):
                try:
                    dialogs = page.locator('[role="dialog"]')
                    if not dialogs.first.is_visible(timeout=2000):
                        break
                    dialog_text = dialogs.first.inner_text()[:300].lower()

                    # "Review audience" dialog — click Continue
                    if "review audience" in dialog_text or "continue" in dialog_text:
                        logger.info("  Found 'Review audience' dialog, clicking Continue...")
                        try:
                            cont_btn = page.get_by_role("button", name="Continue", exact=True)
                            cont_btn.click(timeout=5000)
                        except Exception:
                            page.get_by_text("Continue", exact=True).click(timeout=5000)
                        time.sleep(3)
                        continue

                    # Notifications dialog — press Escape
                    if "notification" in dialog_text or "push" in dialog_text or "turn on" in dialog_text:
                        logger.info("  Closing notifications dialog...")
                        page.keyboard.press("Escape")
                        time.sleep(2)
                        continue

                    # Any other unknown dialog — press Escape
                    if "what's on your mind" not in dialog_text and "create post" not in dialog_text:
                        logger.info(f"  Unknown dialog, pressing Escape: {dialog_text[:80]}")
                        page.keyboard.press("Escape")
                        time.sleep(2)
                        continue

                    break
                except Exception:
                    break

            # ── STEP 2: Click "What's on your mind?" to open composer ──
            logger.info("Step 2: Opening post composer...")
            composer_ready = False

            for attempt in range(3):
                logger.info(f"  Attempt {attempt + 1} to open composer...")

                # Click "What's on your mind"
                try:
                    el = page.get_by_text("What's on your mind", exact=False).first
                    box = el.bounding_box()
                    if box:
                        page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        logger.info("  Clicked 'What's on your mind' via bounding box")
                except Exception as e:
                    logger.info(f"  Bounding box click failed: {e}")

                time.sleep(4)

                # Check if the correct dialog opened (should have "Create post" or post-related content)
                page_state = page.evaluate("""
                    () => {
                        const dialogs = document.querySelectorAll('[role="dialog"]');
                        const results = [];
                        for (const d of dialogs) {
                            const text = d.textContent?.substring(0, 300) || '';
                            const hasPostBtn = !!d.querySelector('[aria-label="Post"]') ||
                                               text.includes('Post') || text.includes('Create post');
                            const hasTextbox = !!d.querySelector('[role="textbox"]');
                            results.push({
                                text: text.substring(0, 150),
                                hasPostBtn,
                                hasTextbox,
                                isNotification: text.includes('Notification') || text.includes('push') || text.includes('Turn on')
                            });
                        }
                        return { dialogs: results, dialogCount: dialogs.length };
                    }
                """)
                logger.info(f"  Dialogs found: {page_state.get('dialogCount')}")

                # Close notification dialogs if any
                for d in page_state.get("dialogs", []):
                    if d.get("isNotification"):
                        logger.info("  Found notification dialog, pressing Escape...")
                        page.keyboard.press("Escape")
                        time.sleep(2)
                        continue

                    if d.get("hasTextbox") and not d.get("isNotification"):
                        logger.info("  Post composer dialog found!")
                        composer_ready = True
                        break

                if composer_ready:
                    break

                logger.info("  Composer not ready, retrying...")
                time.sleep(2)

            if not composer_ready:
                logger.error("  Could not open post composer!")
                page.screenshot(path="debug_facebook_step2.png")
                return False

            time.sleep(2)

            # ── STEP 3: Find editor and type content ──
            logger.info("Step 3: Typing post content...")
            editor = None
            editor_selectors = [
                '[role="dialog"] [role="textbox"]',
                '[role="textbox"][contenteditable="true"]',
                '[contenteditable="true"][aria-label*="on your mind"]',
                '[contenteditable="true"]',
            ]

            for selector in editor_selectors:
                try:
                    editor = page.wait_for_selector(selector, timeout=5000)
                    if editor:
                        logger.info(f"  Found editor: {selector}")
                        break
                except Exception:
                    continue

            if not editor:
                logger.error("  Could not find editor.")
                page.screenshot(path="debug_facebook_no_editor.png")
                return False

            page.evaluate("(el) => { el.scrollIntoView(); el.focus(); el.click(); }", editor)
            time.sleep(1)
            page.keyboard.type(content, delay=15)
            time.sleep(3)
            logger.info("  Content typed successfully")
            page.screenshot(path="debug_facebook_after_type.png")

            # ── STEP 4: Click Post button ──
            logger.info("Step 4: Clicking Post button...")
            post_clicked = False

            # Log all buttons in the POST composer dialog (not notification dialog)
            try:
                buttons_info = page.evaluate("""
                    () => {
                        // Find the dialog that has a textbox (post composer, not notifications)
                        const dialogs = document.querySelectorAll('[role="dialog"]');
                        let container = document;
                        for (const d of dialogs) {
                            if (d.querySelector('[role="textbox"]') && !d.textContent.includes('Notification')) {
                                container = d;
                                break;
                            }
                        }
                        const buttons = container.querySelectorAll('button, [role="button"]');
                        return Array.from(buttons).map(b => ({
                            text: b.textContent?.trim()?.substring(0, 50),
                            ariaLabel: b.getAttribute('aria-label'),
                            disabled: b.disabled || b.getAttribute('aria-disabled') === 'true',
                            tag: b.tagName
                        })).filter(b => b.text);
                    }
                """)
                logger.info(f"  Buttons found: {json.dumps(buttons_info[:15])}")
            except Exception:
                pass

            # Strategy 1: get_by_role inside dialog
            try:
                post_btn = page.locator('[role="dialog"]').get_by_role("button", name="Post", exact=True)
                if post_btn.is_visible(timeout=3000):
                    box = post_btn.bounding_box()
                    if box:
                        page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        logger.info("  Clicked Post inside dialog via bounding box")
                        post_clicked = True
            except Exception as e:
                logger.info(f"  Dialog Post failed: {e}")

            # Strategy 2: get_by_role on whole page
            if not post_clicked:
                try:
                    post_btn = page.get_by_role("button", name="Post", exact=True)
                    if post_btn.is_visible(timeout=3000):
                        box = post_btn.bounding_box()
                        if box:
                            page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            logger.info("  Clicked Post via page-level bounding box")
                            post_clicked = True
                except Exception as e:
                    logger.info(f"  Page Post failed: {e}")

            # Strategy 3: Find by aria-label
            if not post_clicked:
                try:
                    post_btn = page.locator('[aria-label="Post"]').first
                    if post_btn.is_visible(timeout=3000):
                        post_btn.click(timeout=5000)
                        logger.info("  Clicked Post via aria-label")
                        post_clicked = True
                except Exception:
                    pass

            # Strategy 4: JS click on button with "Post" text
            if not post_clicked:
                try:
                    clicked = page.evaluate("""
                        () => {
                            const dialog = document.querySelector('[role="dialog"]');
                            const container = dialog || document;
                            const buttons = container.querySelectorAll('button, [role="button"]');
                            for (const btn of buttons) {
                                const text = btn.textContent?.trim();
                                if (text === 'Post' && !btn.disabled) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if clicked:
                        logger.info("  Clicked Post via JS")
                        post_clicked = True
                except Exception:
                    pass

            if post_clicked:
                time.sleep(10)
                # Verify: check if dialog closed (means post was submitted)
                try:
                    dialog_visible = page.locator('[role="dialog"]').is_visible(timeout=3000)
                    if dialog_visible:
                        logger.warning("  Dialog still open — post may not have been submitted")
                        page.screenshot(path="debug_facebook_dialog_still_open.png")
                    else:
                        logger.info("  Dialog closed — post submitted!")
                except Exception:
                    pass
                logger.info("Post published successfully!")
                return True
            else:
                page.screenshot(path="debug_facebook_post_btn.png")
                logger.error("  Could not find Post button.")
                return False

        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return False

    def process_approved_posts(self):
        approved_posts = list(self.approved_dir.glob("FACEBOOK_POST_*.md"))
        if not approved_posts:
            logger.info("No approved Facebook posts found")
            return

        logger.info(f"Found {len(approved_posts)} approved post(s) to publish")

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://www.facebook.com/", timeout=60000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass

                # Check if login needed
                if "login" in page.url:
                    logger.info("Please login to Facebook in the browser window...")
                    page.wait_for_url("**/facebook.com/**", timeout=120000)

                for filepath in approved_posts:
                    content = self.extract_post_content(filepath)
                    if not content:
                        logger.warning(f"No content found in {filepath.name}")
                        continue

                    logger.info(f"Publishing: {filepath.name}")
                    success = self.publish_post(page, content)

                    if success:
                        dest = self.done_dir / filepath.name
                        filepath.rename(dest)
                        self._log_action(filepath.name, "posted")
                        logger.info(f"Moved {filepath.name} to Done")
                    else:
                        self._log_action(filepath.name, "failed")

                context.close()

        except Exception as e:
            logger.error(f"Failed to process posts: {e}")

    def _log_action(self, filename: str, result: str):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "facebook_post",
            "actor": "facebook_poster",
            "file": filename,
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
    parser = argparse.ArgumentParser(description="Facebook Poster for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./facebook_session", help="Path to Facebook session")
    args = parser.parse_args()

    poster = FacebookPoster(vault_path=args.vault, session_path=args.session)
    poster.process_approved_posts()


if __name__ == "__main__":
    main()
