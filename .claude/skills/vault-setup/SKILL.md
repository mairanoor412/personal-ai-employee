---
name: vault-setup
description: This skill should be used when the user asks to "setup vault", "create obsidian vault", "initialize vault structure", "setup folders", or mentions creating the AI Employee vault from scratch.
version: 1.0.0
---

# Vault Setup Skill

Sets up the complete Obsidian vault structure for the Personal AI Employee system.

## What This Skill Does

Creates the full `AI_Employee_Vault/` directory structure with all required folders and starter files needed for the AI Employee to operate.

## Folder Structure to Create

```
AI_Employee_Vault/
├── Inbox/                  # Raw incoming items from watchers
├── Needs_Action/           # Items requiring Claude's attention
├── Plans/                  # Plan.md files created by Claude
├── Pending_Approval/       # Sensitive actions awaiting human approval
├── Approved/               # Human-approved actions ready for execution
├── Rejected/               # Human-rejected actions
├── Done/                   # Completed tasks archive
├── Logs/                   # Audit logs (JSON format, daily files)
├── Accounting/             # Financial records and transactions
├── Briefings/              # CEO Briefings and reports
├── Dashboard.md            # Real-time status summary
├── Company_Handbook.md     # Rules of engagement for AI behavior
└── Business_Goals.md       # Business objectives and KPIs
```

## Step-by-Step Process

1. Check if `AI_Employee_Vault/` already exists in the project root
2. If it exists, verify all required subfolders are present and create any missing ones
3. If it does not exist, create the full directory tree
4. Create starter `Dashboard.md` with default template
5. Create starter `Company_Handbook.md` with default rules
6. Create starter `Business_Goals.md` with template structure
7. Add a `.gitkeep` file in each empty folder so Git tracks them
8. Confirm completion by listing the created structure

## Important Rules

- NEVER overwrite existing files — only create if missing
- All paths are relative to the project root
- Use forward slashes for cross-platform compatibility
- Each folder must have a `.gitkeep` file if empty
- Dashboard.md, Company_Handbook.md, and Business_Goals.md must use the templates defined in the create-dashboard, create-handbook skills

## When to Use

- First-time project setup
- When vault structure is missing or incomplete
- When user wants to reset or verify vault integrity
