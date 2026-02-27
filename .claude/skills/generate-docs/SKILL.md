# Generate Documentation Skill

## Description
Generates comprehensive architecture documentation for the Personal AI Employee project — system design, data flow, skill catalog, and setup guides.

## When to Use
- User asks to "generate docs", "create documentation", "document the system"
- Before hackathon submission/demo
- After major changes to architecture

## Instructions

### Documents to Generate

#### 1. Architecture Overview (`docs/ARCHITECTURE.md`)
```markdown
# System Architecture

## High-Level Design
Perception → Reasoning → Action pipeline

## Components
- Watchers (perception layer)
- Claude Code (reasoning engine)
- MCP Servers (action layer)
- Obsidian Vault (memory/dashboard)
- Human-in-the-Loop (approval gate)

## Data Flow Diagram
[ASCII diagram of data flow]
```

#### 2. Skill Catalog (`docs/SKILLS_CATALOG.md`)
- List all skills with descriptions
- Group by tier (Bronze/Silver/Gold)
- Include usage examples for each

#### 3. Setup Guide (`docs/SETUP_GUIDE.md`)
- Step-by-step installation
- Environment variables
- First-run instructions for each watcher
- Troubleshooting common issues

#### 4. API Reference (`docs/API_REFERENCE.md`)
- MCP server endpoints
- Odoo client methods
- Watcher configurations

### How to Generate
1. Scan all `.claude/skills/*/SKILL.md` files
2. Read `README.md` for current state
3. Read `pyproject.toml` for dependencies
4. Read vault structure for folder descriptions
5. Compile into organized documentation

### Output
Save all docs to: `docs/` folder in project root
Update README.md with links to documentation
