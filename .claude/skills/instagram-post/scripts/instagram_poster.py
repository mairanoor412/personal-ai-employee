"""
Instagram Poster - Publishes approved posts to Instagram
Uses mobile viewport emulation (Instagram requires mobile for posting)
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

# Mobile device emulation for Instagram
MOBILE_DEVICE = {
    "viewport": {"width": 390, "height": 844},
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}


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
                parts = line.split(":", 1)
                if len(parts) > 1:
                    image_path = parts[1].strip()

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

            # ── STEP 2: Click "+" (new post) button ──
            logger.info("Step 2: Opening new post...")
            new_post_clicked = False

            # Try various selectors for the create/new post button
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

            if not new_post_clicked:
                # Try bottom nav bar "+" button (mobile view)
                try:
                    plus_btn = page.locator('[role="menuitem"]').nth(2)
                    if plus_btn.is_visible(timeout=3000):
                        plus_btn.click(timeout=5000)
                        logger.info("  Clicked bottom nav + button")
                        new_post_clicked = True
                except Exception:
                    pass

            if not new_post_clicked:
                logger.error("  Could not find 'New post' button!")
                page.screenshot(path="debug_instagram_step2.png")
                return False

            time.sleep(4)

            # ── STEP 3: Upload image (if provided) ──
            if image_path and Path(image_path).exists():
                logger.info(f"Step 3: Uploading image: {image_path}")
                try:
                    file_input = page.locator('input[type="file"]')
                    file_input.set_input_files(image_path)
                    time.sleep(3)
                    logger.info("  Image uploaded")

                    # Click "Next" buttons to get to caption screen
                    for i in range(2):
                        try:
                            next_btn = page.get_by_role("button", name="Next")
                            if next_btn.is_visible(timeout=3000):
                                next_btn.click(timeout=5000)
                                time.sleep(2)
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"  Image upload failed: {e}")
                    return False
            else:
                logger.info("Step 3: No image — text post only")
                # Instagram requires an image, so this might fail
                logger.warning("  Instagram requires an image for posts!")

            # ── STEP 4: Add caption ──
            logger.info("Step 4: Adding caption...")
            caption_editor = None
            caption_selectors = [
                '[aria-label="Write a caption..."]',
                '[aria-label*="caption"]',
                '[placeholder*="caption"]',
                '[contenteditable="true"]',
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
                logger.warning("  Could not find caption editor")

            # ── STEP 5: Click Share/Post button ──
            logger.info("Step 5: Clicking Share button...")
            share_clicked = False

            try:
                share_btn = page.get_by_role("button", name="Share", exact=True)
                if share_btn.is_visible(timeout=5000):
                    share_btn.click(timeout=5000)
                    logger.info("  Clicked Share button")
                    share_clicked = True
            except Exception:
                pass

            if not share_clicked:
                try:
                    share_el = page.get_by_text("Share", exact=True).last
                    box = share_el.bounding_box()
                    if box:
                        page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        share_clicked = True
                except Exception:
                    pass

            if share_clicked:
                time.sleep(8)
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
                context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    **MOBILE_DEVICE,
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://www.instagram.com/", timeout=60000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass

                if "login" in page.url or "accounts" in page.url:
                    logger.info("Please login to Instagram in the browser window...")
                    page.wait_for_url("**/instagram.com/**", timeout=120000)

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
