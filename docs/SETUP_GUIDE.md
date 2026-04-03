# Setup Guide

## Prerequisites
- Python 3.12+
- UV package manager (`pip install uv`)
- Obsidian (free tier)
- Claude Code CLI (Anthropic)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd personal-ai-employee

# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## First Run

### 1. Setup Obsidian Vault
```bash
# Claude Code will create the vault structure
# Just ask: "setup vault"
```

### 2. Setup Watchers (first run requires browser login)

**WhatsApp Watcher:**
```bash
uv run python .claude/skills/whatsapp-watcher/scripts/whatsapp_watcher.py --vault ./AI_Employee_Vault
# Scan QR code on first run
```

**LinkedIn Poster:**
```bash
uv run python .claude/skills/linkedin-post/scripts/linkedin_poster.py --vault ./AI_Employee_Vault
# Login to LinkedIn on first run
```

**Facebook/Instagram/Twitter Posters:**
```bash
# Same pattern — login on first run, session saved for future use
uv run python .claude/skills/facebook-post/scripts/facebook_poster.py --vault ./AI_Employee_Vault
uv run python .claude/skills/instagram-post/scripts/instagram_poster.py --vault ./AI_Employee_Vault
uv run python .claude/skills/twitter-post/scripts/twitter_poster.py --vault ./AI_Employee_Vault
```

### 3. Run Reports
```bash
uv run python .claude/skills/social-summary/scripts/social_summary.py --vault ./AI_Employee_Vault
uv run python .claude/skills/ceo-briefing/scripts/ceo_briefing.py --vault ./AI_Employee_Vault
uv run python .claude/skills/weekly-audit/scripts/weekly_audit.py --vault ./AI_Employee_Vault
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright timeout | Increase timeout or check internet connection |
| Login required again | Delete session folder and re-login |
| WhatsApp QR expired | Restart watcher and scan new QR |
| Post button not found | Check if platform UI changed, update selectors |
| Permission denied | Run terminal as administrator |
