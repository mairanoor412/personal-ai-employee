# System Architecture

## High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                  PERCEPTION LAYER                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  File     │ │ WhatsApp │ │ LinkedIn │ │  Gmail   │  │
│  │  Watcher  │ │ Watcher  │ │ Watcher  │ │ Watcher  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │             │             │             │        │
│       └─────────────┴──────┬──────┴─────────────┘        │
│                            ▼                             │
│              ┌──────────────────────┐                    │
│              │   Obsidian Vault      │                    │
│              │   /Needs_Action/      │                    │
│              └──────────┬───────────┘                    │
├────────────────────────┼────────────────────────────────┤
│                  REASONING LAYER                        │
│              ┌──────────▼───────────┐                    │
│              │   Claude Code         │                    │
│              │   (AI Brain)          │                    │
│              │   Read → Think →      │                    │
│              │   Plan → Act          │                    │
│              └──────────┬───────────┘                    │
│                         │                                │
│              ┌──────────▼───────────┐                    │
│              │  /Pending_Approval/   │                    │
│              │  Human-in-the-Loop    │                    │
│              └──────────┬───────────┘                    │
├────────────────────────┼────────────────────────────────┤
│                  ACTION LAYER                            │
│       ┌────────────────┼────────────────┐               │
│       ▼                ▼                 ▼               │
│  ┌─────────┐   ┌──────────┐   ┌──────────────┐         │
│  │ Social   │   │  Email   │   │   Odoo ERP   │         │
│  │ Posters  │   │  MCP     │   │   Client     │         │
│  └─────────┘   └──────────┘   └──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

## Components

### Perception Layer (Watchers)
Monitors external channels and creates action files in the vault.
- **File Watcher** — Monitors DropFolder for new files
- **WhatsApp Watcher** — Detects unread WhatsApp messages via Playwright
- **LinkedIn Watcher** — Monitors LinkedIn notifications
- **Gmail Watcher** — Watches for new emails

### Reasoning Layer (Claude Code)
The AI brain that reads tasks, analyzes them, creates plans, and decides actions.
- Reads from `/Needs_Action/`
- Creates plans in `/Plans/`
- Routes sensitive actions through `/Pending_Approval/`
- Executes approved actions from `/Approved/`

### Action Layer (Posters & Integrations)
Executes approved actions on external platforms.
- **LinkedIn Poster** — Publishes posts via Playwright browser automation
- **Facebook Poster** — Posts to Facebook feed
- **Instagram Poster** — Posts with mobile emulation
- **Twitter Poster** — Tweets via X.com
- **Odoo Client** — ERP operations via JSON-RPC

### Memory Layer (Obsidian Vault)
Local markdown-based dashboard and file system.
- Folder-based workflow pipeline
- JSON audit logs
- Human-readable reports and briefings

## Data Flow

```
External Event → Watcher → /Needs_Action/ → Claude Code → /Plans/
    → /Pending_Approval/ → Human Review → /Approved/ → Action Script
    → /Done/ + /Logs/
```

## Security Model
- All data stored locally (no cloud sync)
- Browser sessions in gitignored folders
- Credentials never committed to git
- Human-in-the-loop for all sensitive actions