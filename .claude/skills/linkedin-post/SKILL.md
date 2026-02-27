---
name: linkedin-post
description: This skill should be used when the user asks to "post on linkedin", "create linkedin post", "schedule linkedin content", "publish on linkedin", or mentions LinkedIn posting, content creation, or social media marketing.
version: 1.0.0
---

# LinkedIn Post Skill

Automatically creates and posts content on LinkedIn to generate business visibility and sales leads.

## What This Skill Does

Uses Playwright to automate posting on LinkedIn. Posts are created based on templates, scheduled content, or AI-generated business content. All posts require approval before publishing.

## Prerequisites

- Python packages: `playwright`
- LinkedIn session established (via linkedin-watcher skill)
- Post content must be pre-approved (moved to `/Approved/`)

## Workflow (Human-in-the-Loop)

```
1. AI generates post content → writes to /Pending_Approval/LINKEDIN_POST_*.md
2. Human reviews in Obsidian
3. Human moves to /Approved/ (approve) or /Rejected/ (reject)
4. process-approved skill detects → triggers linkedin-post to publish
5. After posting → file moved to /Done/, Dashboard updated
```

## Post Template Format

```markdown
---
type: linkedin_post
action: publish
platform: linkedin
scheduled_for: 2026-02-25T09:00:00
status: pending_approval
content_type: text | article | image
---

## Post Content
Your LinkedIn post content goes here.

This can include:
- Multiple paragraphs
- Hashtags at the bottom
- Call to action

#AI #Business #Automation

## Post Settings
- **Visibility**: public | connections
- **Comments**: enabled
```

## LinkedIn Post Script Pattern

Located at `scripts/linkedin_poster.py`:

```python
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("LinkedInPoster")


class LinkedInPoster:
    def __init__(self, vault_path: str, session_path: str = "./linkedin_session"):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.session_path = Path(session_path)

    def extract_post_content(self, filepath: Path) -> str:
        """Extract post content from markdown file."""
        content = filepath.read_text(encoding="utf-8")
        # Extract content between ## Post Content and ## Post Settings
        lines = content.split("\n")
        in_content = False
        post_lines = []
        for line in lines:
            if line.startswith("## Post Content"):
                in_content = True
                continue
            elif line.startswith("## Post Settings") or line.startswith("## "):
                in_content = False
            elif in_content:
                post_lines.append(line)
        return "\n".join(post_lines).strip()

    def publish_post(self, page, content: str) -> bool:
        """Publish a text post on LinkedIn."""
        try:
            page.goto("https://www.linkedin.com/feed/")
            page.wait_for_load_state("networkidle")

            # Click "Start a post" button
            page.click('button:has-text("Start a post")')
            time.sleep(2)

            # Type content in the post editor
            editor = page.wait_for_selector('[role="textbox"][contenteditable="true"]', timeout=10000)
            editor.fill(content)
            time.sleep(1)

            # Click Post button
            page.click('button:has-text("Post")')
            time.sleep(3)

            logger.info("Post published successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return False

    def process_approved_posts(self):
        """Find and publish all approved LinkedIn posts."""
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.linkedin.com/feed/")

            for filepath in self.approved_dir.glob("LINKEDIN_POST_*.md"):
                content = self.extract_post_content(filepath)
                if not content:
                    logger.warning(f"No content found in {filepath.name}")
                    continue

                success = self.publish_post(page, content)
                if success:
                    # Move to Done
                    dest = self.done_dir / filepath.name
                    filepath.rename(dest)
                    self._log_action(filepath.name, "posted")
                    logger.info(f"Moved {filepath.name} to Done")

            context.close()

    def _log_action(self, filename: str, result: str):
        """Write audit log entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": "linkedin_post",
            "actor": "linkedin_poster",
            "file": filename,
            "result": result
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
```

## Content Generation Guidelines

When AI generates LinkedIn post content:
- Keep posts 150-300 words
- Include 3-5 relevant hashtags
- Add a call-to-action (CTA) at the end
- Professional but engaging tone
- Focus on business value and insights
- Post during optimal hours: 9AM-12PM, Tue-Thu

## Security Rules

- ALL posts MUST go through `/Pending_Approval/` first
- NEVER auto-post without human approval
- NEVER post personal or confidential business information
- Add `linkedin_session/` to `.gitignore`
- Rate limit: maximum 2 posts per day

## When to Use

- When user wants to create LinkedIn content
- When scheduled posts need to be published
- When generating business marketing content
