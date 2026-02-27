---
name: email-mcp
description: This skill should be used when the user asks to "send email", "setup email mcp", "create email server", or mentions MCP server for email, sending emails via Claude, or email automation.
version: 1.0.0
---

# Email MCP Server Skill

A Model Context Protocol (MCP) server that enables Claude Code to send, draft, and search emails via Gmail API.

## What This Skill Does

Creates a Python-based MCP server using FastMCP that exposes email tools (send, draft, search) to Claude Code. Claude can then invoke these tools to perform email actions as part of its workflow.

## Prerequisites

- Python packages: `mcp`, `google-api-python-client`, `google-auth`, `google-auth-oauthlib`
- Install: `uv add mcp`
- Gmail API credentials (`credentials.json` + `token.json`) already set up (see gmail-watcher skill)
- Gmail API scopes must include `gmail.send` and `gmail.compose`

## MCP Server Script

Located at `scripts/email_mcp_server.py`:

```python
import os
import base64
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailMCP")

# Initialize MCP server
mcp = FastMCP("Email MCP Server")


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail. Use only after human approval."""
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        logger.info(f"Email sent to {to}, ID: {sent['id']}")
        return f"Email sent successfully to {to}. Message ID: {sent['id']}"
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return f"Error sending email: {str(e)}"


@mcp.tool()
def draft_email(to: str, subject: str, body: str) -> str:
    """Create a draft email in Gmail (does NOT send)."""
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()
        logger.info(f"Draft created for {to}, ID: {draft['id']}")
        return f"Draft created for {to}. Draft ID: {draft['id']}"
    except Exception as e:
        return f"Error creating draft: {str(e)}"


@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    """Search Gmail emails with a query string (e.g., 'from:user@example.com is:unread')."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No emails found matching the query."

        email_summaries = []
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            email_summaries.append({
                "id": msg_ref["id"],
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "No Subject"),
                "snippet": msg.get("snippet", "")[:100]
            })
        return json.dumps(email_summaries, indent=2)
    except Exception as e:
        return f"Error searching emails: {str(e)}"


if __name__ == "__main__":
    mcp.run()
```

## Claude Code MCP Configuration

Add to your Claude Code MCP settings (`.mcp.json` in project root):

```json
{
  "mcpServers": {
    "email": {
      "command": "uv",
      "args": ["run", "python", ".claude/skills/email-mcp/scripts/email_mcp_server.py"],
      "env": {
        "GMAIL_CREDENTIALS": "./credentials.json"
      }
    }
  }
}
```

## Available Tools

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `send_email` | Send email immediately | YES — always |
| `draft_email` | Save as draft (safe) | No |
| `search_emails` | Search inbox | No |

## Security Rules

- `send_email` MUST only be called after human approval
- `draft_email` is safe — creates draft without sending
- NEVER send to unknown contacts without approval
- NEVER include sensitive data (passwords, bank info) in emails
- Log all email actions to `/Logs/`
- Rate limit: max 10 emails per hour

## When to Use

- When Claude needs to send emails as part of a plan
- When processing approved email actions from `/Approved/`
- When searching for email context during reasoning
