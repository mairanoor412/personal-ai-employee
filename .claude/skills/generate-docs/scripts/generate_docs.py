"""
Generate Documentation — Auto-generates architecture docs for the AI Employee project.

Scans skills, vault structure, and codebase to produce comprehensive documentation.

Usage:
    uv run python .claude/skills/generate-docs/scripts/generate_docs.py --project-root .
"""

import argparse
from pathlib import Path
from datetime import datetime


def scan_skills(skills_dir: Path) -> list[dict]:
    """Scan all skill directories and extract metadata."""
    skills = []
    if not skills_dir.exists():
        return skills

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text(encoding="utf-8")
        lines = content.split("\n")

        name = skill_dir.name
        title = ""
        description = ""
        for line in lines:
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("## Description"):
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    description = lines[idx + 1].strip()

        has_script = bool(list((skill_dir / "scripts").glob("*.py"))) if (skill_dir / "scripts").exists() else False

        skills.append({
            "name": name,
            "title": title or name.replace("-", " ").title(),
            "description": description,
            "has_script": has_script,
        })

    return skills


def scan_vault_structure(vault_dir: Path) -> list[str]:
    """List vault folder structure."""
    if not vault_dir.exists():
        return []
    folders = []
    for item in sorted(vault_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            file_count = len(list(item.glob("*")))
            folders.append(f"{item.name}/ ({file_count} files)")
    return folders


def generate_architecture(project_root: Path, skills: list[dict]) -> str:
    """Generate ARCHITECTURE.md content."""
    lines = [
        "# System Architecture",
        "",
        "## High-Level Design",
        "",
        "```",
        "┌─────────────────────────────────────────────────────────┐",
        "│                  PERCEPTION LAYER                       │",
        "│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │",
        "│  │  File     │ │ WhatsApp │ │ LinkedIn │ │  Gmail   │  │",
        "│  │  Watcher  │ │ Watcher  │ │ Watcher  │ │ Watcher  │  │",
        "│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │",
        "│       │             │             │             │        │",
        "│       └─────────────┴──────┬──────┴─────────────┘        │",
        "│                            ▼                             │",
        "│              ┌──────────────────────┐                    │",
        "│              │   Obsidian Vault      │                    │",
        "│              │   /Needs_Action/      │                    │",
        "│              └──────────┬───────────┘                    │",
        "├────────────────────────┼────────────────────────────────┤",
        "│                  REASONING LAYER                        │",
        "│              ┌──────────▼───────────┐                    │",
        "│              │   Claude Code         │                    │",
        "│              │   (AI Brain)          │                    │",
        "│              │   Read → Think →      │                    │",
        "│              │   Plan → Act          │                    │",
        "│              └──────────┬───────────┘                    │",
        "│                         │                                │",
        "│              ┌──────────▼───────────┐                    │",
        "│              │  /Pending_Approval/   │                    │",
        "│              │  Human-in-the-Loop    │                    │",
        "│              └──────────┬───────────┘                    │",
        "├────────────────────────┼────────────────────────────────┤",
        "│                  ACTION LAYER                            │",
        "│       ┌────────────────┼────────────────┐               │",
        "│       ▼                ▼                 ▼               │",
        "│  ┌─────────┐   ┌──────────┐   ┌──────────────┐         │",
        "│  │ Social   │   │  Email   │   │   Odoo ERP   │         │",
        "│  │ Posters  │   │  MCP     │   │   Client     │         │",
        "│  └─────────┘   └──────────┘   └──────────────┘         │",
        "└─────────────────────────────────────────────────────────┘",
        "```",
        "",
        "## Components",
        "",
        "### Perception Layer (Watchers)",
        "Monitors external channels and creates action files in the vault.",
        "- **File Watcher** — Monitors DropFolder for new files",
        "- **WhatsApp Watcher** — Detects unread WhatsApp messages via Playwright",
        "- **LinkedIn Watcher** — Monitors LinkedIn notifications",
        "- **Gmail Watcher** — Watches for new emails",
        "",
        "### Reasoning Layer (Claude Code)",
        "The AI brain that reads tasks, analyzes them, creates plans, and decides actions.",
        "- Reads from `/Needs_Action/`",
        "- Creates plans in `/Plans/`",
        "- Routes sensitive actions through `/Pending_Approval/`",
        "- Executes approved actions from `/Approved/`",
        "",
        "### Action Layer (Posters & Integrations)",
        "Executes approved actions on external platforms.",
        "- **LinkedIn Poster** — Publishes posts via Playwright browser automation",
        "- **Facebook Poster** — Posts to Facebook feed",
        "- **Instagram Poster** — Posts with mobile emulation",
        "- **Twitter Poster** — Tweets via X.com",
        "- **Odoo Client** — ERP operations via JSON-RPC",
        "",
        "### Memory Layer (Obsidian Vault)",
        "Local markdown-based dashboard and file system.",
        "- Folder-based workflow pipeline",
        "- JSON audit logs",
        "- Human-readable reports and briefings",
        "",
        "## Data Flow",
        "",
        "```",
        "External Event → Watcher → /Needs_Action/ → Claude Code → /Plans/",
        "    → /Pending_Approval/ → Human Review → /Approved/ → Action Script",
        "    → /Done/ + /Logs/",
        "```",
        "",
        "## Security Model",
        "- All data stored locally (no cloud sync)",
        "- Browser sessions in gitignored folders",
        "- Credentials never committed to git",
        "- Human-in-the-loop for all sensitive actions",
    ]
    return "\n".join(lines)


def generate_skills_catalog(skills: list[dict]) -> str:
    """Generate SKILLS_CATALOG.md content."""
    # Categorize by tier based on skill name patterns
    bronze = []
    silver = []
    gold = []

    bronze_names = {"vault-setup", "vault-read-write", "create-action-file", "create-plan",
                    "create-dashboard", "create-handbook", "process-inbox", "process-approved"}
    silver_names = {"file-watcher", "linkedin-watcher", "linkedin-post", "whatsapp-watcher",
                    "gmail-watcher", "email-mcp", "approval-workflow", "reasoning-loop", "scheduler"}

    for skill in skills:
        if skill["name"] in bronze_names:
            bronze.append(skill)
        elif skill["name"] in silver_names:
            silver.append(skill)
        else:
            gold.append(skill)

    lines = [
        "# Skills Catalog",
        "",
        f"Total Skills: {len(skills)}",
        "",
        f"## Bronze Tier ({len(bronze)} skills) — Foundation",
    ]
    for s in bronze:
        status = "Implemented" if s["has_script"] else "Instructions only"
        lines.append(f"- **{s['title']}** (`{s['name']}`) — {s['description']} [{status}]")

    lines.append("")
    lines.append(f"## Silver Tier ({len(silver)} skills) — Automation")
    for s in silver:
        status = "Implemented" if s["has_script"] else "Instructions only"
        lines.append(f"- **{s['title']}** (`{s['name']}`) — {s['description']} [{status}]")

    lines.append("")
    lines.append(f"## Gold Tier ({len(gold)} skills) — Intelligence")
    for s in gold:
        status = "Implemented" if s["has_script"] else "Instructions only"
        lines.append(f"- **{s['title']}** (`{s['name']}`) — {s['description']} [{status}]")

    return "\n".join(lines)


def generate_setup_guide() -> str:
    """Generate SETUP_GUIDE.md content."""
    return """# Setup Guide

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
"""


def main():
    parser = argparse.ArgumentParser(description="Documentation Generator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    args = parser.parse_args()

    root = Path(args.project_root)
    skills_dir = root / ".claude" / "skills"
    vault_dir = root / "AI_Employee_Vault"
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)

    # Scan skills
    skills = scan_skills(skills_dir)
    print(f"Found {len(skills)} skills")

    # Generate docs
    arch = generate_architecture(root, skills)
    catalog = generate_skills_catalog(skills)
    setup = generate_setup_guide()

    # Write files
    (docs_dir / "ARCHITECTURE.md").write_text(arch, encoding="utf-8")
    print(f"Generated: docs/ARCHITECTURE.md")

    (docs_dir / "SKILLS_CATALOG.md").write_text(catalog, encoding="utf-8")
    print(f"Generated: docs/SKILLS_CATALOG.md")

    (docs_dir / "SETUP_GUIDE.md").write_text(setup, encoding="utf-8")
    print(f"Generated: docs/SETUP_GUIDE.md")

    print(f"\nAll documentation generated in docs/ folder")


if __name__ == "__main__":
    main()
