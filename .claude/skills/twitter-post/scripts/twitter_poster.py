"""
Twitter/X Poster - Publishes approved tweets to Twitter/X
Only processes files from /Approved/ folder (Human-in-the-Loop)

Prerequisites:
    uv add playwright
    Twitter session established (first run requires manual login)

Usage:
    uv run python .claude/skills/twitter-post/scripts/twitter_poster.py --vault ./AI_Employee_Vault
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
logger = logging.getLogger("TwitterPoster")


class TwitterPoster:
    def __init__(self, vault_path: str, session_path: str = "./twitter_session"):
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
            if line.startswith("## Post Content") or line.startswith("## Tweet"):
                in_content = True
                continue
            elif line.startswith("## Post Settings") or (line.startswith("## ") and in_content):
                in_content = False
            elif in_content:
                post_lines.append(line)
        return "\n".join(post_lines).strip()

    def publish_post(self, page, content: str) -> bool:
        try:
            # ── STEP 1: Navigate to Twitter/X ──
            logger.info("Step 1: Opening Twitter/X...")
            page.goto("https://x.com/home", timeout=60000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            time.sleep(5)

            # ── STEP 2: Find tweet composer ──
            logger.info("Step 2: Finding tweet composer...")
            editor = None

            # Twitter's compose area is usually visible on the home feed
            editor_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[role="textbox"][data-testid="tweetTextarea_0"]',
                '[aria-label="Post text"]',
                '[role="textbox"][contenteditable="true"]',
            ]

            for selector in editor_selectors:
                try:
                    editor = page.wait_for_selector(selector, timeout=5000)
                    if editor:
                        logger.info(f"  Found editor: {selector}")
                        break
                except Exception:
                    continue

            # If not found, try clicking compose button first
            if not editor:
                logger.info("  Editor not visible, clicking compose button...")
                try:
                    compose_btn = page.locator('[data-testid="SideNav_NewTweet_Button"]').first
                    if compose_btn.is_visible(timeout=3000):
                        compose_btn.click(timeout=5000)
                        time.sleep(3)
                except Exception:
                    try:
                        page.locator('[href="/compose/post"]').first.click(timeout=3000)
                        time.sleep(3)
                    except Exception:
                        pass

                # Try again
                for selector in editor_selectors:
                    try:
                        editor = page.wait_for_selector(selector, timeout=5000)
                        if editor:
                            logger.info(f"  Found editor after compose: {selector}")
                            break
                    except Exception:
                        continue

            if not editor:
                logger.error("  Could not find tweet editor!")
                page.screenshot(path="debug_twitter_no_editor.png")
                return False

            # ── STEP 3: Type content ──
            logger.info("Step 3: Typing tweet content...")
            page.evaluate("(el) => { el.scrollIntoView(); el.focus(); el.click(); }", editor)
            time.sleep(1)
            page.keyboard.type(content, delay=15)
            time.sleep(3)
            logger.info("  Content typed successfully")

            # ── STEP 4: Click Post/Tweet button ──
            logger.info("Step 4: Clicking Post button...")
            post_clicked = False

            # Twitter's post button
            try:
                post_btn = page.locator('[data-testid="tweetButton"]').first
                if post_btn.is_visible(timeout=5000) and not post_btn.is_disabled():
                    post_btn.click(timeout=5000)
                    logger.info("  Clicked via data-testid='tweetButton'")
                    post_clicked = True
            except Exception as e:
                logger.info(f"  tweetButton failed: {e}")

            if not post_clicked:
                try:
                    post_btn = page.locator('[data-testid="tweetButtonInline"]').first
                    if post_btn.is_visible(timeout=3000) and not post_btn.is_disabled():
                        post_btn.click(timeout=5000)
                        logger.info("  Clicked via tweetButtonInline")
                        post_clicked = True
                except Exception:
                    pass

            if not post_clicked:
                try:
                    post_btn = page.get_by_role("button", name="Post", exact=True)
                    if post_btn.is_visible(timeout=3000):
                        post_btn.click(timeout=5000)
                        logger.info("  Clicked Post via get_by_role")
                        post_clicked = True
                except Exception:
                    pass

            if post_clicked:
                time.sleep(5)
                logger.info("Tweet published successfully!")
                return True
            else:
                page.screenshot(path="debug_twitter_post_btn.png")
                logger.error("  Could not find Post button.")
                return False

        except Exception as e:
            logger.error(f"Failed to publish tweet: {e}")
            return False

    def process_approved_posts(self):
        approved_posts = list(self.approved_dir.glob("TWITTER_POST_*.md"))
        if not approved_posts:
            logger.info("No approved Twitter posts found")
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
                page.goto("https://x.com/home", timeout=60000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass

                if "login" in page.url or "/i/flow/login" in page.url:
                    logger.info("Please login to Twitter/X in the browser window...")
                    page.wait_for_url("**/home**", timeout=120000)

                for filepath in approved_posts:
                    content = self.extract_post_content(filepath)
                    if not content:
                        logger.warning(f"No content found in {filepath.name}")
                        continue

                    if len(content) > 280:
                        logger.warning(f"  Tweet is {len(content)} chars (over 280 limit for free accounts)")

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
            "action_type": "twitter_post",
            "actor": "twitter_poster",
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
    parser = argparse.ArgumentParser(description="Twitter Poster for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to Obsidian vault")
    parser.add_argument("--session", default="./twitter_session", help="Path to Twitter session")
    args = parser.parse_args()

    poster = TwitterPoster(vault_path=args.vault, session_path=args.session)
    poster.process_approved_posts()


if __name__ == "__main__":
    main()
