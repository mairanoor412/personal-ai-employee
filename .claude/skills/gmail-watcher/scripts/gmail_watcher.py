"""
Gmail Watcher - Monitors Gmail for unread important emails
Creates action files in AI_Employee_Vault/Needs_Action/

Prerequisites:
    1. Enable Gmail API in Google Cloud Console
    2. Create OAuth 2.0 credentials (Desktop App)
    3. Download credentials.json to project root
    4. Install: uv add google-auth google-auth-oauthlib google-api-python-client

Usage:
    python scripts/gmail_watcher.py --vault ./AI_Employee_Vault --interval 120
"""

import os
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("GmailWatcher")


class GmailWatcher:
    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.processed_ids: set[str] = set()
        self.service = self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def check_for_updates(self) -> list:
        """Fetch unread important emails not yet processed."""
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q="is:unread is:important", maxResults=10)
            .execute()
        )
        messages = results.get("messages", [])
        return [m for m in messages if m["id"] not in self.processed_ids]

    def create_action_file(self, message: dict) -> Path:
        """Create a markdown action file for a detected email."""
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        now = datetime.now().isoformat()

        content = f"""---
type: email
from: {headers.get("From", "Unknown")}
subject: {headers.get("Subject", "No Subject")}
received: {now}
priority: high
status: pending
---

## Email Content
{msg.get("snippet", "")}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
        filepath = self.needs_action / f"EMAIL_{message['id']}.md"
        filepath.write_text(content, encoding="utf-8")
        self.processed_ids.add(message["id"])
        self._log_action("email_detected", filepath.name, headers)
        logger.info(f"Created action file: {filepath.name}")
        return filepath

    def _log_action(self, action_type: str, filename: str, details: dict):
        """Write audit log entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "gmail_watcher",
            "file": filename,
            "details": {
                "from": details.get("From", ""),
                "subject": details.get("Subject", ""),
            },
        }

        # Append to daily log
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def run(self):
        """Main loop - check Gmail at regular intervals."""
        logger.info(
            f"Gmail Watcher started (interval: {self.check_interval}s)"
        )
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                if items:
                    logger.info(f"Processed {len(items)} new emails")
            except HttpError as e:
                logger.error(f"Gmail API error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
            time.sleep(self.check_interval)


def main():
    parser = argparse.ArgumentParser(description="Gmail Watcher for AI Employee")
    parser.add_argument(
        "--vault",
        default="./AI_Employee_Vault",
        help="Path to Obsidian vault",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Check interval in seconds (min: 120)",
    )
    args = parser.parse_args()

    interval = max(args.interval, 120)  # Enforce minimum 120s
    watcher = GmailWatcher(vault_path=args.vault, check_interval=interval)
    watcher.run()


if __name__ == "__main__":
    main()
