"""
Instagram Poster - Publishes approved posts to Instagram
Uses desktop browser (Instagram supports desktop posting since 2021)
Only processes files from /Approved/ folder (Human-in-the-Loop)

Prerequisites:
    uv add playwright
    Instagram session established (first run requires manual login)

Usage:
    uv run python .claude/skills/instagram-post/scripts/instagram_poster.py --vault ./AI_Employee_Vault
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
logger = logging.getLogger("InstagramPoster")


class InstagramPoster:
    def __init__(self, vault_path: str, session_path: str = "./instagram_session"):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)

    def extract_post_content(self, filepath: Path) -> dict:
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")
        in_content = False
        post_lines = []
        image_path = None

        for line in lines:
            if line.startswith("## Post Content") or line.startswith("## Caption"):
                in_content = True
                continue
            elif line.startswith("## Post Settings") or (line.startswith("## ") and in_content):
                in_content = False
            elif in_content:
                post_lines.append(line)
            if "Image Path" in line or "image_path" in line:
                # Handle both "image_path: C:/path" and "Image Path: C:/path"
                for prefix in ["image_path:", "Image Path:"]:
                    if prefix in line:
                        image_path = line.split(prefix, 1)[1].strip()
                        break

        return {
            "caption": "\n".join(post_lines).strip(),
            "image_path": image_path,
        }

    def publish_post(self, page, caption: str, image_path: str = None) -> bool:
        try:
            # ── STEP 1: Navigate to Instagram ──
            logger.info("Step 1: Opening Instagram...")
            page.goto("https://www.instagram.com/", timeout=60000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            time.sleep(5)

            # ── STEP 1.5: Close any blocking dialogs (notifications, etc) ──
            for _ in range(3):
                try:
                    dialogs = page.locator('[role="dialog"]')
                    if not dialogs.first.is_visible(timeout=2000):
                        break
                    dialog_text = dialogs.first.inner_text()[:300].lower()

                    # "Turn on Notifications" dialog — click Not Now
                    if "notification" in dialog_text or "turn on" in dialog_text:
                        logger.info("  Closing notifications dialog...")
                        try:
                            not_now = page.get_by_role("button", name="Not Now")
                            not_now.click(timeout=5000)
                        except Exception:
                            page.keyboard.press("Escape")
                        time.sleep(2)
                        continue

                    break
                except Exception:
                    break

            # ── STEP 2: Click Create / New post button ──
            logger.info("Step 2: Opening new post creator...")
            new_post_clicked = False

            # Strategy 1: aria-label selectors
            create_selectors = [
                '[aria-label="New post"]',
                '[aria-label="Create"]',
                'svg[aria-label="New post"]',
                'svg[aria-label="Create"]',
            ]

            for selector in create_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        el.click(timeout=5000)
                        logger.info(f"  Clicked: {selector}")
                        new_post_clicked = True
                        break
                except Exception:
                    continue

            # Strategy 2: Find via sidebar nav links (desktop Instagram has sidebar)
            if not new_post_clicked:
                try:
                    # Desktop Instagram sidebar has links with text "Create"
                    create_link = page.get_by_text("Create", exact=True).first
                    if create_link.is_visible(timeout=3000):
                        create_link.click(timeout=5000)
                        logger.info("  Clicked 'Create' text link")
                        new_post_clicked = True
                except Exception:
                    pass

            # Strategy 3: JS — find all SVGs and clickable elements
            if not new_post_clicked:
                try:
                    clicked = page.evaluate("""
                        () => {
                            // Look for SVG with create/new post label
                            const svgs = document.querySelectorAll('svg');
                            for (const svg of svgs) {
                                const label = svg.getAttribute('aria-label') || '';
                                if (label.toLowerCase().includes('new') || label.toLowerCase().includes('create')) {
                                    const parent = svg.closest('a, button, [role="button"], [role="link"], span');
                                    if (parent) { parent.click(); return 'svg:' + label; }
                                }
                            }
                            // Look for sidebar link with "Create"
                            const links = document.querySelectorAll('a, [role="link"]');
                            for (const link of links) {
                                const text = link.textContent?.trim();
                                if (text === 'Create') {
                                    link.click();
                                    return 'link:Create';
                                }
                            }
                            return null;
                        }
                    """)
                    if clicked:
                        logger.info(f"  Clicked via JS: {clicked}")
                        new_post_clicked = True
                except Exception:
                    pass

            # Strategy 4: Debug — log all interactive elements
            if not new_post_clicked:
                try:
                    debug_info = page.evaluate("""
                        () => {
                            const svgs = document.querySelectorAll('svg');
                            const svgLabels = Array.from(svgs).map(s => s.getAttribute('aria-label')).filter(Boolean);
                            const links = document.querySelectorAll('a');
                            const linkTexts = Array.from(links).slice(0, 20).map(a => ({
                                text: a.textContent?.trim()?.substring(0, 30),
                                href: a.getAttribute('href'),
                                ariaLabel: a.getAttribute('aria-label')
                            }));
                            return { svgLabels, linkTexts, url: window.location.href };
                        }
                    """)
                    logger.info(f"  DEBUG page info: {json.dumps(debug_info)}")
                except Exception:
                    pass

                logger.error("  Could not find 'New post' button!")
                page.screenshot(path="debug_instagram_step2.png")
                return False

            time.sleep(4)

            # ── STEP 3: Upload image ──
            if image_path and Path(image_path).exists():
                logger.info(f"Step 3: Uploading image: {image_path}")
                try:
                    # Wait for file input to appear in the "Create new post" dialog
                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(image_path)
                    time.sleep(4)
                    logger.info("  Image uploaded")

                    # Click "Next" buttons (crop → filters → caption)
                    for step_name in ["crop", "filters"]:
                        try:
                            next_btn = page.get_by_role("button", name="Next")
                            if next_btn.is_visible(timeout=5000):
                                next_btn.click(timeout=5000)
                                logger.info(f"  Clicked Next ({step_name})")
                                time.sleep(2)
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"  Image upload failed: {e}")
                    return False
            else:
                logger.warning("Step 3: No image provided!")
                logger.warning("  Instagram REQUIRES an image. Attempting to continue...")
                # Try to see if there's a "Select from computer" button anyway
                page.screenshot(path="debug_instagram_no_image.png")

            # ── STEP 4: Add caption ──
            logger.info("Step 4: Adding caption...")
            caption_editor = None
            caption_selectors = [
                '[aria-label="Write a caption..."]',
                '[aria-label*="caption"]',
                'textarea[aria-label*="caption"]',
                '[placeholder*="caption"]',
                '[contenteditable="true"]',
                'textarea',
            ]

            for selector in caption_selectors:
                try:
                    caption_editor = page.wait_for_selector(selector, timeout=5000)
                    if caption_editor:
                        logger.info(f"  Found caption editor: {selector}")
                        break
                except Exception:
                    continue

            if caption_editor:
                page.evaluate("(el) => { el.scrollIntoView(); el.focus(); el.click(); }", caption_editor)
                time.sleep(1)
                page.keyboard.type(caption, delay=15)
                time.sleep(2)
                logger.info("  Caption typed successfully")
            else:
                logger.warning("  Could not find caption editor — may not have reached caption step")
                page.screenshot(path="debug_instagram_no_caption.png")

            # ── STEP 5: Click Share button ──
            logger.info("Step 5: Clicking Share button...")
            share_clicked = False

            # Strategy 1: button role
            try:
                share_btn = page.get_by_role("button", name="Share", exact=True)
                if share_btn.is_visible(timeout=5000):
                    share_btn.click(timeout=5000)
                    logger.info("  Clicked Share button")
                    share_clicked = True
            except Exception:
                pass

            # Strategy 2: text match
            if not share_clicked:
                try:
                    share_el = page.get_by_text("Share", exact=True).last
                    box = share_el.bounding_box()
                    if box:
                        page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        logger.info("  Clicked Share via text match")
                        share_clicked = True
                except Exception:
                    pass

            # Strategy 3: JS click
            if not share_clicked:
                try:
                    clicked = page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button, [role="button"], div[tabindex="0"]');
                            for (const btn of buttons) {
                                const text = btn.textContent?.trim();
                                if (text === 'Share') {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if clicked:
                        logger.info("  Clicked Share via JS")
                        share_clicked = True
                except Exception:
                    pass

            if share_clicked:
                time.sleep(10)
                logger.info("Post published successfully!")
                return True
            else:
                page.screenshot(path="debug_instagram_share.png")
                logger.error("  Could not find Share button.")
                return False

        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return False

    def process_approved_posts(self):
        approved_posts = list(self.approved_dir.glob("INSTAGRAM_POST_*.md"))
        if not approved_posts:
            logger.info("No approved Instagram posts found")
            return

        logger.info(f"Found {len(approved_posts)} approved post(s) to publish")

        try:
            with sync_playwright() as p:
                # Use DESKTOP mode (not mobile emulation)
                context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://www.instagram.com/", timeout=60000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
                time.sleep(5)

                # Check if login needed
                needs_login = False
                try:
                    page_text = page.evaluate("() => document.body.innerText?.substring(0, 1000) || ''")
                    current_url = page.url
                    # Check for login page indicators
                    login_indicators = [
                        "Forgot password" in page_text,
                        "Create new account" in page_text,
                        "Log in" in page_text and "Instagram" in page_text,
                        "login" in current_url,
                        "accounts/login" in current_url,
                        "sign up" in page_text.lower(),
                    ]
                    # Check for logged-in indicators
                    logged_in_check = page.evaluate("""
                        () => ({
                            hasCreate: !!document.querySelector('svg[aria-label="New post"]') ||
                                       !!document.querySelector('svg[aria-label="Create"]'),
                            hasHome: !!document.querySelector('svg[aria-label="Home"]'),
                            hasArticle: !!document.querySelector('article'),
                        })
                    """)
                    is_logged_in = logged_in_check.get("hasCreate") or \
                                   (logged_in_check.get("hasHome") and logged_in_check.get("hasArticle"))

                    if any(login_indicators) and not is_logged_in:
                        needs_login = True
                    logger.info(f"URL: {current_url}, needs_login: {needs_login}, logged_in_check: {logged_in_check}")
                except Exception:
                    needs_login = True

                if needs_login:
                    # Navigate to login page
                    if "login" not in page.url:
                        page.goto("https://www.instagram.com/accounts/login/", timeout=30000)
                        time.sleep(3)

                    logger.info("Please login to Instagram in the browser window...")
                    logger.info("Waiting up to 2 minutes for login...")

                    # Wait for redirect to feed after login
                    try:
                        page.wait_for_function("""
                            () => {
                                const url = window.location.href;
                                const onLogin = url.includes('login') || url.includes('accounts');
                                if (onLogin) return false;
                                // Check if we see feed content
                                const hasSvg = !!document.querySelector('svg[aria-label="New post"]') ||
                                               !!document.querySelector('svg[aria-label="Create"]');
                                const hasArticle = !!document.querySelector('article');
                                return hasSvg || hasArticle;
                            }
                        """, timeout=120000)
                        logger.info("Login successful!")
                        time.sleep(5)
                    except Exception:
                        logger.error("Login timeout!")
                        page.screenshot(path="debug_instagram_login_timeout.png")
                        context.close()
                        return

                for filepath in approved_posts:
                    post_data = self.extract_post_content(filepath)
                    if not post_data["caption"]:
                        logger.warning(f"No content found in {filepath.name}")
                        continue

                    logger.info(f"Publishing: {filepath.name}")
                    success = self.publish_post(page, post_data["caption"], post_data.get("image_path"))

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
            "action_type": "instagram_post",
            "actor": "instagram_poster",
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
    parser = argparse.ArgumentParser(description="Instagram Poster for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./instagram_session", help="Path to Instagram session")
    args = parser.parse_args()

    poster = InstagramPoster(vault_path=args.vault, session_path=args.session)
    poster.process_approved_posts()


if __name__ == "__main__":
    main()
