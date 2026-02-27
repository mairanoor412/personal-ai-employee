# Personal AI Employee — Digital FTE

An autonomous AI agent that manages personal and business affairs 24/7 using **Claude Code** as the brain and **Obsidian** as the dashboard. Local-first, agent-driven, human-in-the-loop.

> Built for **Panaversity Hackathon 0** — Quarter 4

## Architecture

```
Perception (Watchers) → Reasoning (Claude Code) → Action (MCP Servers + Playwright)
```

- **Watchers**: Python scripts monitoring Gmail, WhatsApp, LinkedIn, file system
- **Claude Code**: Reads `/Needs_Action`, reasons, creates plans, executes actions
- **MCP Servers**: Email sending, browser automation via Model Context Protocol
- **Obsidian Vault**: Local markdown-based dashboard and memory
- **Human-in-the-Loop**: Sensitive actions require approval via `/Approved` folder
- **Odoo ERP**: Accounting integration via JSON-RPC (Gold tier)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Reasoning Engine | Claude Code |
| Dashboard/Memory | Obsidian (local markdown) |
| Watchers | Python 3.12+ |
| Package Manager | uv |
| File Monitoring | watchdog |
| Email Monitoring | Gmail API (google-api-python-client) |
| Browser Automation | Playwright (WhatsApp, LinkedIn, Facebook, Instagram, Twitter) |
| MCP Server | FastMCP (Python MCP SDK) |
| ERP/Accounting | Odoo Community (JSON-RPC) |
| Scheduling | Windows Task Scheduler |
| Version Control | Git / GitHub Desktop |

## Project Structure

```
personal-ai-employee/
├── AI_Employee_Vault/                  # Obsidian Vault (Dashboard + Memory)
│   ├── Inbox/                          # Raw incoming items
│   ├── Needs_Action/                   # Items for Claude to process
│   ├── Plans/                          # Plan.md files with task steps
│   ├── Pending_Approval/               # Awaiting human approval
│   ├── Approved/                       # Human-approved actions
│   ├── Rejected/                       # Declined actions
│   ├── Done/                           # Completed archive
│   ├── Logs/                           # Audit logs (JSON)
│   ├── Accounting/                     # Financial records (Odoo)
│   ├── Briefings/                      # CEO reports & summaries
│   ├── Dashboard.md                    # Real-time status summary
│   ├── Company_Handbook.md             # AI behavior rules
│   └── Business_Goals.md              # Business objectives & metrics
│
├── .claude/                            # Claude Code config
│   └── skills/                         # Agent Skills (29 total)
│       │
│       │  # ── Bronze Tier Skills (8) ──
│       ├── vault-setup/SKILL.md             # Vault structure creation
│       ├── create-dashboard/SKILL.md        # Dashboard.md management
│       ├── create-handbook/SKILL.md         # Company_Handbook.md rules
│       ├── gmail-watcher/                   # Gmail monitoring
│       │   ├── SKILL.md
│       │   ├── scripts/gmail_watcher.py
│       │   └── references/GMAIL_SETUP_GUIDE.md
│       ├── file-watcher/                    # File system monitoring
│       │   ├── SKILL.md
│       │   └── scripts/file_watcher.py
│       ├── process-inbox/SKILL.md           # Process /Needs_Action items
│       ├── create-action-file/SKILL.md      # Standardized action files
│       ├── vault-read-write/SKILL.md        # Vault file operations
│       │
│       │  # ── Silver Tier Skills (9) ──
│       ├── whatsapp-watcher/                # WhatsApp monitoring
│       │   ├── SKILL.md
│       │   └── scripts/whatsapp_watcher.py
│       ├── linkedin-watcher/                # LinkedIn monitoring
│       │   ├── SKILL.md
│       │   └── scripts/linkedin_watcher.py
│       ├── linkedin-post/                   # LinkedIn auto-posting
│       │   ├── SKILL.md
│       │   └── scripts/linkedin_poster.py
│       ├── create-plan/SKILL.md             # Plan.md creation
│       ├── email-mcp/                       # Email MCP server
│       │   ├── SKILL.md
│       │   └── scripts/email_mcp_server.py
│       ├── approval-workflow/SKILL.md       # Human-in-the-loop approvals
│       ├── process-approved/SKILL.md        # Execute approved actions
│       ├── scheduler/                       # Task scheduling
│       │   ├── SKILL.md
│       │   └── scripts/setup_scheduler.py
│       ├── reasoning-loop/SKILL.md          # Core Read-Think-Plan-Act cycle
│       │
│       ├── whatsapp-reply/                 # WhatsApp reply/send
│       │   ├── SKILL.md
│       │   └── scripts/whatsapp_reply.py
│       │
│       │  # ── Gold Tier Skills (11) ──
│       ├── odoo-integration/                # Odoo ERP accounting
│       │   ├── SKILL.md
│       │   └── scripts/odoo_client.py
│       ├── facebook-post/                   # Facebook auto-posting
│       │   ├── SKILL.md
│       │   └── scripts/facebook_poster.py
│       ├── instagram-post/                  # Instagram auto-posting (mobile)
│       │   ├── SKILL.md
│       │   └── scripts/instagram_poster.py
│       ├── twitter-post/                    # Twitter/X auto-posting
│       │   ├── SKILL.md
│       │   └── scripts/twitter_poster.py
│       ├── social-summary/                  # Social media analytics
│       │   ├── SKILL.md
│       │   └── scripts/social_summary.py
│       ├── ceo-briefing/                    # Weekly CEO briefing
│       │   ├── SKILL.md
│       │   └── scripts/ceo_briefing.py
│       ├── weekly-audit/                    # System health audit
│       │   ├── SKILL.md
│       │   └── scripts/weekly_audit.py
│       ├── error-recovery/                  # Error handling & recovery
│       │   ├── SKILL.md
│       │   └── scripts/error_recovery.py
│       ├── audit-logger/                    # Comprehensive audit logging
│       │   ├── SKILL.md
│       │   └── scripts/audit_logger.py
│       ├── ralph-wiggum-loop/               # Autonomous task completion
│       │   ├── SKILL.md
│       │   └── scripts/ralph_wiggum_loop.py
│       └── generate-docs/                   # Architecture documentation
│           ├── SKILL.md
│           └── scripts/generate_docs.py
│
├── DropFolder/                         # Watched folder for file drops
├── main.py                             # Entry point
├── pyproject.toml                      # Python project config (uv)
├── .env                                # Credentials (gitignored)
├── .gitignore                          # Excludes credentials, sessions, .venv
└── README.md

```

## Setup Instructions

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Obsidian](https://obsidian.md/) (free)
- [Claude Code](https://claude.com/claude-code) (active subscription)
- GitHub Desktop

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd personal-ai-employee

# Install dependencies
uv sync

# Install Playwright browsers (for WhatsApp/LinkedIn/social media)
uv run playwright install chromium

# Open vault in Obsidian
# Obsidian → "Open folder as vault" → select AI_Employee_Vault/
```

### Environment Variables

Create a `.env` file in the project root:

```env
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# Gold Tier (Odoo)
ODOO_URL=http://localhost:8069
ODOO_DB=your_database
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### Running Watchers

**File Watcher** (Bronze — Tested & Working):
```bash
uv run python .claude/skills/file-watcher/scripts/file_watcher.py --watch ./DropFolder --vault ./AI_Employee_Vault
```

**Gmail Watcher** (Bronze):
See [Gmail Setup Guide](.claude/skills/gmail-watcher/references/GMAIL_SETUP_GUIDE.md) for Google credentials.
```bash
uv run python .claude/skills/gmail-watcher/scripts/gmail_watcher.py --vault ./AI_Employee_Vault
```

**WhatsApp Watcher** (Silver — Tested & Working):
```bash
uv run python .claude/skills/whatsapp-watcher/scripts/whatsapp_watcher.py --vault ./AI_Employee_Vault
```
First run opens browser for QR code scan. Session is saved for future runs. Detects all unread messages and creates action files in `/Needs_Action/`.

**LinkedIn Watcher** (Silver — Tested & Working):
```bash
# Set credentials in .env first: LINKEDIN_EMAIL, LINKEDIN_PASSWORD
uv run python .claude/skills/linkedin-watcher/scripts/linkedin_watcher.py --vault ./AI_Employee_Vault
```
Monitors LinkedIn notifications every 5 minutes. First run requires manual login/security verification.

### WhatsApp Reply (Gold)

```bash
# Send approved WhatsApp replies (uses same session as watcher)
uv run python .claude/skills/whatsapp-reply/scripts/whatsapp_reply.py --vault ./AI_Employee_Vault
```
Creates reply file in `/Pending_Approval/` → human approves → moves to `/Approved/` → script sends message and moves to `/Done/`.

### Social Media Posting

**LinkedIn Posting** (Silver — Tested & Working):
```bash
uv run python .claude/skills/linkedin-post/scripts/linkedin_poster.py --vault ./AI_Employee_Vault
```
Uses Playwright bounding-box clicks for reliable automation. Posts are auto-moved to `/Done/` after publishing.

**Facebook / Instagram / Twitter Posting** (Gold):
```bash
# Same pattern as LinkedIn — create post in Pending_Approval, approve, then run poster
uv run python .claude/skills/facebook-post/scripts/facebook_poster.py --vault ./AI_Employee_Vault
uv run python .claude/skills/instagram-post/scripts/instagram_poster.py --vault ./AI_Employee_Vault
uv run python .claude/skills/twitter-post/scripts/twitter_poster.py --vault ./AI_Employee_Vault
```

### Odoo Integration (Gold)

```bash
# Test connection
uv run python .claude/skills/odoo-integration/scripts/odoo_client.py --action test

# List invoices
uv run python .claude/skills/odoo-integration/scripts/odoo_client.py --action list_invoices

# Get account balance
uv run python .claude/skills/odoo-integration/scripts/odoo_client.py --action balance
```

### Reports & Audits (Gold)

```bash
# Social media analytics summary
uv run python .claude/skills/social-summary/scripts/social_summary.py --vault ./AI_Employee_Vault

# Weekly CEO briefing
uv run python .claude/skills/ceo-briefing/scripts/ceo_briefing.py --vault ./AI_Employee_Vault

# System health audit
uv run python .claude/skills/weekly-audit/scripts/weekly_audit.py --vault ./AI_Employee_Vault

# Query audit logs
uv run python .claude/skills/audit-logger/scripts/audit_logger.py --vault ./AI_Employee_Vault --query summary
uv run python .claude/skills/audit-logger/scripts/audit_logger.py --vault ./AI_Employee_Vault --query errors

# Autonomous task processor (Ralph Wiggum Loop)
uv run python .claude/skills/ralph-wiggum-loop/scripts/ralph_wiggum_loop.py --vault ./AI_Employee_Vault

# Generate architecture documentation
uv run python .claude/skills/generate-docs/scripts/generate_docs.py --project-root .
```

### Running MCP Server

**Email MCP** (Silver):
```bash
uv run python .claude/skills/email-mcp/scripts/email_mcp_server.py
```

### Setting Up Scheduler

```bash
# Create all scheduled tasks (Windows Task Scheduler)
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py

# List tasks
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --list

# Remove all tasks
uv run python .claude/skills/scheduler/scripts/setup_scheduler.py --remove
```

## Tier Progress

### Bronze Tier — COMPLETE
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] Basic folder structure: /Inbox, /Needs_Action, /Done + 7 more
- [x] One working Watcher script (File System monitoring — tested & working)
- [x] Claude Code successfully reading from and writing to the vault
- [x] All AI functionality implemented as Agent Skills (8 skills)

### Silver Tier — COMPLETE
- [x] WhatsApp Watcher skill + script (Playwright-based) — **Tested & Working**
- [x] LinkedIn Watcher skill + script (Playwright-based) — **Tested & Working**
- [x] LinkedIn auto-post skill + script — **Tested & Working** (successfully published posts)
- [x] Claude reasoning loop skill (Read → Think → Plan → Act)
- [x] Plan.md creation skill with templates
- [x] Email MCP server skill (send, draft, search via FastMCP)
- [x] Human-in-the-loop approval workflow skill — **Tested & Working**
- [x] Process approved actions skill
- [x] Windows Task Scheduler skill + setup script
- [x] All 4 watchers tested (File, LinkedIn, WhatsApp, Gmail pending credentials)

### Gold Tier — COMPLETE
- [x] Odoo Community accounting integration skill + script (JSON-RPC)
- [x] Facebook auto-post skill + script (Playwright-based)
- [x] Instagram auto-post skill + script (Playwright mobile emulation)
- [x] Twitter/X auto-post skill + script (Playwright-based)
- [x] Social media analytics summary skill + script
- [x] Weekly CEO Briefing skill + script
- [x] Weekly System Audit skill + script
- [x] Error recovery and graceful degradation skill + script (3-level: retry/notify/skip)
- [x] Comprehensive audit logging skill + script (centralized JSON logger)
- [x] Ralph Wiggum autonomous loop skill + script (safety guards, priority sorting)
- [x] Architecture documentation generation skill + script
- [x] WhatsApp Reply skill + script (send approved replies via Playwright)
- [x] All 12 Gold tier scripts implemented (19 total Python scripts)

### Platinum Tier — TODO
- [ ] Full polish and production-ready deployment
- [ ] End-to-end demo video
- [ ] Complete documentation

## Agent Skills (29 Total)

All AI functionality is implemented as Agent Skills at `.claude/skills/`. Each skill follows:

```
.claude/skills/
└── skill-name/
    ├── SKILL.md          # Required — instructions for Claude
    ├── references/       # Optional — documentation
    └── scripts/          # Optional — Python helper scripts
```

### Bronze Tier Skills (8)

| Skill | Purpose | Status |
|-------|---------|--------|
| `vault-setup` | Creates and verifies Obsidian vault structure | Tested |
| `create-dashboard` | Creates and updates Dashboard.md | Tested |
| `create-handbook` | Creates Company_Handbook.md with AI behavior rules | Tested |
| `gmail-watcher` | Monitors Gmail for unread important emails | Needs credentials |
| `file-watcher` | Monitors drop folder for new files (watchdog) | **Working** |
| `process-inbox` | Processes items in /Needs_Action folder | Tested |
| `create-action-file` | Creates standardized .md action files | Tested |
| `vault-read-write` | Manages all vault file read/write/move operations | **Working** |

### Silver Tier Skills (9)

| Skill | Purpose | Status |
|-------|---------|--------|
| `whatsapp-watcher` | Monitors WhatsApp Web for unread messages (Playwright) | **Working** |
| `linkedin-watcher` | Monitors LinkedIn messages and notifications (Playwright) | **Working** |
| `linkedin-post` | Auto-posts approved content on LinkedIn | **Working** |
| `create-plan` | Creates Plan.md files for multi-step tasks | Tested |
| `email-mcp` | MCP server for sending/drafting/searching emails (FastMCP) | Init tested |
| `approval-workflow` | Creates approval requests in /Pending_Approval/ | **Working** |
| `process-approved` | Executes approved actions from /Approved/ | Tested |
| `scheduler` | Sets up Windows Task Scheduler for automation | Needs admin |
| `reasoning-loop` | Core AI loop: Read → Think → Plan → Act | Tested |

### Gold Tier Skills (12)

| Skill | Purpose | Status |
|-------|---------|--------|
| `odoo-integration` | Odoo ERP accounting via JSON-RPC (invoices, payments) | **Implemented** |
| `facebook-post` | Auto-posts approved content on Facebook (Playwright) | **Implemented** |
| `instagram-post` | Auto-posts on Instagram with mobile emulation (Playwright) | **Implemented** |
| `twitter-post` | Auto-posts tweets on Twitter/X (Playwright) | **Implemented** |
| `social-summary` | Social media analytics summary across all platforms | **Implemented** |
| `ceo-briefing` | Weekly CEO briefing with task metrics & financials | **Implemented** |
| `weekly-audit` | System health audit (stale tasks, errors, watcher status) | **Implemented** |
| `error-recovery` | Error handling with retry, notify, graceful degradation | **Implemented** |
| `audit-logger` | Comprehensive audit logging for all actions | **Implemented** |
| `ralph-wiggum-loop` | Autonomous task completion loop with safety guards | **Implemented** |
| `whatsapp-reply` | Sends approved WhatsApp replies via Playwright | **Implemented** |
| `generate-docs` | Generates architecture & setup documentation | **Implemented** |

## Workflow

```
1. Input arrives (file drop, email, WhatsApp, LinkedIn)
       ↓
2. Watcher detects → creates .md in /Needs_Action/
       ↓
3. Reasoning Loop: Claude reads → thinks → creates Plan.md
       ↓
4. Simple task? → Execute directly → /Done/
   Sensitive? → Write to /Pending_Approval/
       ↓
5. Human reviews in Obsidian
   ├── Approves → moves to /Approved/
   └── Rejects → moves to /Rejected/
       ↓
6. Process Approved: action executed via MCP/Playwright
       ↓
7. File moved to /Done/ → Dashboard.md updated → Logs written
```

## Demo — What Works Today

1. **Drop a file** in `DropFolder/` → File Watcher detects it → Creates action file in `/Needs_Action/`
2. **LinkedIn Watcher** monitors notifications every 5 minutes → Creates alerts in `/Needs_Action/`
3. **WhatsApp Watcher** monitors unread messages → Detects new chats → Creates action files in `/Needs_Action/`
4. **Create a LinkedIn post** → Goes to `/Pending_Approval/` → Human approves → Move to `/Approved/` → **LinkedIn Poster publishes it automatically**
5. **Approval Workflow** ensures no action happens without human consent
6. **All actions logged** in `AI_Employee_Vault/Logs/` as JSON

## Security

- Credentials (`credentials.json`, `token.json`, `.env`) are in `.gitignore`
- Browser sessions (`whatsapp_session/`, `linkedin_session/`, `facebook_session/`, `instagram_session/`, `twitter_session/`) are in `.gitignore`
- All actions logged to `AI_Employee_Vault/Logs/` in JSON format
- Sensitive actions require human approval (Human-in-the-Loop)
- AI behavior boundaries defined in `Company_Handbook.md`
- Permission thresholds: payments > $100, new contacts, bulk sends → require approval
- Email MCP: `send_email` requires approval, `draft_email` is safe
- Social media: ALL posts require approval before publishing
- Odoo: Creating invoices/payments requires approval, reading data is safe
- Error recovery: 3-level strategy (auto-retry → notify user → graceful degradation)

## License

Private — Hackathon 0 Project

---
*Built with Claude Code + Obsidian for Panaversity Hackathon 0*
