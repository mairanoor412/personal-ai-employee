"""
Email MCP Server - Exposes email tools to Claude Code via MCP protocol
Uses Gmail API for send, draft, and search operations.

Prerequisites:
    uv add mcp google-api-python-client google-auth google-auth-oauthlib

Usage:
    uv run python .claude/skills/email-mcp/scripts/email_mcp_server.py
"""

import os
import json
import base64
import logging
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path
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
    """Search Gmail emails with a query (e.g., 'from:user@example.com is:unread')."""
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
                "snippet": msg.get("snippet", "")[:100],
            })
        return json.dumps(email_summaries, indent=2)
    except Exception as e:
        return f"Error searching emails: {str(e)}"


if __name__ == "__main__":
    mcp.run()
