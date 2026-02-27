---
name: gmail-watcher
description: This skill should be used when the user asks to "watch gmail", "monitor emails", "setup gmail watcher", "check emails", or mentions Gmail monitoring, email detection, or inbox watching.
version: 1.0.0
---

# Gmail Watcher Skill

Monitors Gmail for new unread/important emails and creates action files in the Obsidian vault.

## What This Skill Does

Runs a Python sentinel script that periodically checks Gmail for unread important emails, extracts their content, and creates `.md` action files in `/Needs_Action/` for Claude to process.

## Prerequisites

- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials (`credentials.json`) from Google Cloud Console
- Python packages: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`

## Gmail API Setup Steps

1. Go to Google Cloud Console → APIs & Services → Enable Gmail API
2. Create OAuth 2.0 Client ID (Desktop Application)
3. Download `credentials.json` and place in project root
4. First run will open browser for OAuth consent — creates `token.json`
5. Add `credentials.json` and `token.json` to `.gitignore`

## Gmail Watcher Script Pattern

Located at `scripts/gmail_watcher.py`:

```python
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailWatcher:
    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.processed_ids = set()
        self.logger = logging.getLogger("GmailWatcher")
        self.service = self._authenticate()

    def _authenticate(self):
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
        results = self.service.users().messages().list(
            userId="me", q="is:unread is:important", maxResults=10
        ).execute()
        messages = results.get("messages", [])
        return [m for m in messages if m["id"] not in self.processed_ids]

    def create_action_file(self, message) -> Path:
        msg = self.service.users().messages().get(
            userId="me", id=message["id"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        content = f"""---
type: email
from: {headers.get("From", "Unknown")}
subject: {headers.get("Subject", "No Subject")}
received: {datetime.now().isoformat()}
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
        self.logger.info(f"Created action file: {filepath.name}")
        return filepath

    def run(self):
        self.logger.info("Gmail Watcher started")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                if items:
                    self.logger.info(f"Processed {len(items)} new emails")
            except HttpError as e:
                self.logger.error(f"Gmail API error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            time.sleep(self.check_interval)
```

## Action File Format

Each detected email creates a file like `EMAIL_<id>.md`:

```yaml
---
type: email
from: sender@example.com
subject: Invoice Request
received: 2026-01-07T10:30:00
priority: high
status: pending
---
```

## Important Rules

- NEVER store Gmail credentials in the vault or commit to Git
- Check interval: minimum 120 seconds (respect API rate limits)
- Only process emails matching `is:unread is:important` query
- Track processed IDs to avoid duplicate action files
- Log all watcher activity to `/Logs/`

## When to Use

- Setting up email monitoring for the first time
- Restarting the Gmail watcher after downtime
- Debugging email detection issues
