"""
LinkedIn Poster - Publishes approved posts to LinkedIn
Only processes files from /Approved/ folder (Human-in-the-Loop)

Prerequisites:
    uv add playwright
    LinkedIn session established (via linkedin-watcher)

Usage:
    uv run python .claude/skills/linkedin-post/scripts/linkedin_poster.py --vault ./AI_Employee_Vault
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
logger = logging.getLogger("LinkedInPoster")


class LinkedInPoster:
    def __init__(self, vault_path: str, session_path: str = "./linkedin_session"):
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
            # ── STEP 1: Open post composer ──
            logger.info("Step 1: Opening post composer...")
            page.goto("https://www.linkedin.com/feed/", timeout=60000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            time.sleep(5)

            # First, log what the "Start a post" element actually is
            element_info = page.evaluate("""
                () => {
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        if (el.children.length === 0 && el.textContent.trim() === 'Start a post') {
                            return {
                                tag: el.tagName,
                                role: el.getAttribute('role'),
                                className: el.className.toString().substring(0, 100),
                                parentTag: el.parentElement ? el.parentElement.tagName : null,
                                parentRole: el.parentElement ? el.parentElement.getAttribute('role') : null,
                                parentClass: el.parentElement ? el.parentElement.className.toString().substring(0, 100) : null,
                                grandParentTag: el.parentElement?.parentElement ? el.parentElement.parentElement.tagName : null,
                                grandParentRole: el.parentElement?.parentElement ? el.parentElement.parentElement.getAttribute('role') : null,
                            };
                        }
                    }
                    return null;
                }
            """)
            logger.info(f"  'Start a post' element info: {json.dumps(element_info, indent=2)}")

            # Click using multiple strategies
            clicked = False

            # Strategy A: Click via bounding box coordinates (most reliable)
            try:
                el = page.get_by_text("Start a post", exact=True)
                box = el.bounding_box()
                if box:
                    logger.info(f"  Bounding box: x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    logger.info("  Clicked via bounding box coordinates")
                    clicked = True
            except Exception as e:
                logger.info(f"  Bounding box click failed: {e}")

            # Strategy B: Click parent element (the clickable container)
            if not clicked:
                try:
                    result = page.evaluate("""
                        () => {
                            const all = document.querySelectorAll('*');
                            for (const el of all) {
                                if (el.children.length === 0 && el.textContent.trim() === 'Start a post') {
                                    // Click the element, parent, and grandparent
                                    let target = el;
                                    for (let i = 0; i < 3; i++) {
                                        if (target) {
                                            target.click();
                                            target = target.parentElement;
                                        }
                                    }
                                    return 'clicked up to grandparent';
                                }
                            }
                            return null;
                        }
                    """)
                    if result:
                        logger.info(f"  JS parent click: {result}")
                        clicked = True
                except Exception as e:
                    logger.info(f"  JS parent click failed: {e}")

            if not clicked:
                logger.error("  Could not click 'Start a post'!")
                page.screenshot(path="debug_linkedin_step1.png")
                return False

            time.sleep(5)

            # Check what changed after click - look for ANY overlay/modal/editor
            page_state = page.evaluate("""
                () => {
                    return {
                        hasDialog: !!document.querySelector('[role="dialog"]'),
                        hasModal: !!document.querySelector('[class*="modal"]'),
                        hasOverlay: !!document.querySelector('[class*="overlay"]'),
                        hasShareBox: !!document.querySelector('[class*="share-creation"]'),
                        hasTextbox: !!document.querySelector('[role="textbox"][contenteditable="true"]'),
                        hasContentEditable: !!document.querySelector('[contenteditable="true"]'),
                        textboxCount: document.querySelectorAll('[role="textbox"]').length,
                        ceCount: document.querySelectorAll('[contenteditable="true"]').length,
                    };
                }
            """)
            logger.info(f"  Page state after click: {json.dumps(page_state, indent=2)}")

            # If no dialog but we have a contenteditable, the "dialog" might just be inline
            if not page_state.get('hasDialog') and not page_state.get('hasTextbox') and not page_state.get('hasContentEditable'):
                logger.error("  Nothing opened after click!")
                page.screenshot(path="debug_linkedin_after_click.png")
                logger.error("  Screenshot saved: debug_linkedin_after_click.png")
                return False

            logger.info("  Post composer is open!")

            # ── STEP 2: Find the editor inside the dialog ──
            logger.info("Step 2: Looking for editor...")

            # Wait extra for dialog content to fully render
            time.sleep(3)

            # Debug: log what's inside the dialog
            dialog_contents = page.evaluate("""
                () => {
                    const dialog = document.querySelector('[role="dialog"]');
                    if (!dialog) return {error: 'no dialog'};
                    const children = dialog.querySelectorAll('*');
                    const interesting = [];
                    for (const el of children) {
                        const tag = el.tagName;
                        const role = el.getAttribute('role');
                        const ce = el.getAttribute('contenteditable');
                        const placeholder = el.getAttribute('placeholder') || el.getAttribute('aria-placeholder') || el.getAttribute('data-placeholder');
                        const ariaLabel = el.getAttribute('aria-label');
                        if (role || ce || placeholder || tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'IFRAME') {
                            interesting.push({
                                tag: tag,
                                role: role,
                                contenteditable: ce,
                                placeholder: placeholder,
                                ariaLabel: ariaLabel,
                                className: el.className.toString().substring(0, 60),
                            });
                        }
                    }
                    return {
                        totalElements: children.length,
                        hasIframe: !!dialog.querySelector('iframe'),
                        interestingElements: interesting,
                    };
                }
            """)
            logger.info(f"  Dialog contents: {json.dumps(dialog_contents, indent=2)}")

            # Take screenshot of the open dialog
            page.screenshot(path="debug_linkedin_dialog_open.png")
            logger.info("  Screenshot of open dialog saved")

            editor = None
            editor_selectors = [
                '[role="dialog"] [role="textbox"]',
                '[role="dialog"] [contenteditable="true"]',
                '[role="dialog"] [aria-placeholder]',
                '[role="dialog"] [data-placeholder]',
                '[role="dialog"] textarea',
                '[role="dialog"] .ql-editor',
                '[role="textbox"][contenteditable="true"]',
                '[contenteditable="true"]',
                '.ql-editor[contenteditable="true"]',
            ]

            # Try each selector with wait
            for selector in editor_selectors:
                try:
                    editor = page.wait_for_selector(selector, timeout=5000)
                    if editor:
                        logger.info(f"  Found editor: {selector}")
                        break
                except Exception:
                    continue

            # If still not found, wait longer and try again (lazy loading)
            if not editor:
                logger.info("  Editor not found yet, waiting 5 more seconds...")
                time.sleep(5)
                page.screenshot(path="debug_linkedin_dialog_wait.png")

                # Re-check dialog contents
                dialog_contents2 = page.evaluate("""
                    () => {
                        const dialog = document.querySelector('[role="dialog"]');
                        if (!dialog) return 'no dialog';
                        return {
                            ceCount: dialog.querySelectorAll('[contenteditable]').length,
                            textboxCount: dialog.querySelectorAll('[role="textbox"]').length,
                            iframeCount: dialog.querySelectorAll('iframe').length,
                            textareaCount: dialog.querySelectorAll('textarea').length,
                            inputCount: dialog.querySelectorAll('input[type="text"]').length,
                        };
                    }
                """)
                logger.info(f"  Dialog after extra wait: {json.dumps(dialog_contents2, indent=2)}")

                for selector in editor_selectors:
                    try:
                        editor = page.wait_for_selector(selector, timeout=3000)
                        if editor:
                            logger.info(f"  Found editor on retry: {selector}")
                            break
                    except Exception:
                        continue

            if not editor:
                logger.error("  Could not find editor in dialog.")
                page.screenshot(path="debug_linkedin_no_editor.png")
                return False

            # ── STEP 3: Type content ──
            logger.info("Step 3: Typing post content...")
            page.evaluate("(el) => { el.scrollIntoView(); el.focus(); el.click(); }", editor)
            time.sleep(1)
            page.keyboard.type(content, delay=15)
            time.sleep(3)
            logger.info("  Content typed successfully")

            # ── STEP 4: Find and click the Post/Submit button ──
            # NOTE: The post composer is NOT inside [role="dialog"] — that matches
            # video player dialogs. The Post button is on the page directly.
            logger.info("Step 4: Clicking Post button...")

            # Wait for Post button to become enabled (it's disabled when editor is empty)
            time.sleep(2)

            post_clicked = False

            # Method 1: Find "Post" button by exact text using Playwright (best)
            try:
                # Get exact "Post" button — exclude "Repost", "Start a post"
                post_btn = page.get_by_role("button", name="Post", exact=True)
                if post_btn.is_visible(timeout=5000):
                    # Check if enabled
                    is_disabled = post_btn.is_disabled()
                    logger.info(f"  Found 'Post' button, disabled={is_disabled}")
                    if not is_disabled:
                        post_btn.click(timeout=5000)
                        logger.info("  Clicked Post button via get_by_role")
                        post_clicked = True
                    else:
                        logger.warning("  Post button is disabled — content may not have been entered")
            except Exception as e:
                logger.info(f"  get_by_role failed: {e}")

            # Method 2: Bounding box click on Post button (like Step 1)
            if not post_clicked:
                try:
                    post_el = page.get_by_text("Post", exact=True).last
                    box = post_el.bounding_box()
                    if box:
                        logger.info(f"  Post button box: x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                        page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        logger.info("  Clicked Post button via bounding box")
                        post_clicked = True
                except Exception as e:
                    logger.info(f"  Bounding box method failed: {e}")

            # Method 3: JS — find button whose text is exactly "Post" on the whole page
            if not post_clicked:
                result = page.evaluate("""
                    () => {
                        const allButtons = document.querySelectorAll('button');
                        for (const btn of allButtons) {
                            const text = btn.textContent.trim();
                            if (text === 'Post' && !btn.disabled) {
                                btn.scrollIntoView();
                                btn.click();
                                return 'success';
                            }
                        }
                        // Debug: list buttons with "post" in text
                        const postBtns = Array.from(allButtons)
                            .filter(b => b.textContent.toLowerCase().includes('post'))
                            .map(b => ({ text: b.textContent.trim().substring(0, 40), disabled: b.disabled }));
                        return 'NOT_FOUND: ' + JSON.stringify(postBtns);
                    }
                """)
                if result and result.startswith("success"):
                    logger.info(f"  JS click: {result}")
                    post_clicked = True
                else:
                    logger.error(f"  JS result: {result}")

            if post_clicked:
                time.sleep(8)  # Wait longer for post to actually publish
                # Verify: check if composer closed (post was submitted)
                composer_gone = page.evaluate("""
                    () => {
                        const textboxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
                        return textboxes.length === 0;
                    }
                """)
                if composer_gone:
                    logger.info("Post published successfully! (composer closed)")
                else:
                    logger.warning("Post button clicked but composer may still be open")
                    page.screenshot(path="debug_linkedin_after_post.png")
                return True
            else:
                page.screenshot(path="debug_linkedin_post_btn.png")
                logger.error("  Could not find Post button. Screenshot saved.")
                return False

        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            page.screenshot(path="debug_linkedin_error.png")
            return False

    def process_approved_posts(self):
        approved_posts = list(self.approved_dir.glob("LINKEDIN_POST_*.md"))
        if not approved_posts:
            logger.info("No approved LinkedIn posts found")
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
                page.goto("https://www.linkedin.com/feed/", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    logger.info("networkidle timeout (normal for LinkedIn), continuing...")
                    page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Check if login needed
                if "login" in page.url:
                    logger.info("Session expired — please login in browser window")
                    page.wait_for_url("**/feed/**", timeout=120000)

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
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg or "Target closed" in error_msg:
                logger.error("")
                logger.error("=" * 60)
                logger.error("ERROR: LinkedIn session is already in use!")
                logger.error("")
                logger.error("The LinkedIn Watcher is probably running.")
                logger.error("Please STOP the watcher first (Ctrl+C),")
                logger.error("then run this poster again.")
                logger.error("=" * 60)
            else:
                logger.error(f"Failed to process posts: {e}")

    def _log_action(self, filename: str, result: str):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "linkedin_post",
            "actor": "linkedin_poster",
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
    parser = argparse.ArgumentParser(description="LinkedIn Poster for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./linkedin_session", help="Path to LinkedIn session")
    args = parser.parse_args()

    poster = LinkedInPoster(vault_path=args.vault, session_path=args.session)
    poster.process_approved_posts()


if __name__ == "__main__":
    main()
