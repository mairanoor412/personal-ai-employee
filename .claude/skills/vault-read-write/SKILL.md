---
name: vault-read-write
description: This skill should be used when the user asks to "read vault", "write to vault", "update vault file", "move file in vault", or mentions reading from, writing to, or managing files within the Obsidian AI_Employee_Vault.
version: 1.0.0
---

# Vault Read-Write Skill

Enables Claude Code to systematically read from and write to the Obsidian vault while maintaining data integrity.

## What This Skill Does

Provides standardized patterns for all vault file operations: reading, writing, moving, and managing markdown files across vault folders.

## Vault Path

The vault root is at: `AI_Employee_Vault/` (relative to project root)

## Folder Purposes

| Folder | Read | Write | Move To | Purpose |
|--------|------|-------|---------|---------|
| `/Inbox/` | Yes | Watchers only | → Needs_Action | Raw incoming items |
| `/Needs_Action/` | Yes | Watchers, Skills | → Plans, Done | Items to process |
| `/Plans/` | Yes | Claude only | → Pending_Approval, Done | Task plans |
| `/Pending_Approval/` | Yes | Claude only | → Approved, Rejected | Awaiting human |
| `/Approved/` | Yes | Human only | → Done | Ready to execute |
| `/Rejected/` | Yes | Human only | → Done | Declined actions |
| `/Done/` | Yes | System | — | Completed archive |
| `/Logs/` | Yes | System | — | Audit trail |
| `/Accounting/` | Yes | Finance skill | — | Financial records |
| `/Briefings/` | Yes | Briefing skill | — | CEO reports |

## Read Operations

### Read a single file
```
Read AI_Employee_Vault/Dashboard.md
```

### Scan a folder for all .md files
```
Glob AI_Employee_Vault/Needs_Action/*.md
```

### Parse frontmatter from action files
Read the file, extract YAML between `---` markers, parse type/priority/status.

## Write Operations

### Create a new file
- Always check if file exists first
- Use the create-action-file skill format for action files
- Include YAML frontmatter with required fields

### Update an existing file
- Read the file first
- Modify only the relevant sections
- Update `last_updated` timestamp in frontmatter
- Never delete content without explicit instruction

### Move files between folders
Moving = the core workflow mechanism:
```
/Needs_Action/EMAIL_123.md  →  /Done/EMAIL_123.md      (processed)
/Needs_Action/TASK_abc.md   →  /Plans/PLAN_abc.md       (needs planning)
/Plans/PLAN_abc.md           →  /Pending_Approval/...    (needs approval)
/Approved/PAYMENT_xyz.md     →  /Done/PAYMENT_xyz.md     (executed)
```

When moving, update the frontmatter:
```yaml
status: completed
completed_at: {{TIMESTAMP}}
moved_from: /Needs_Action/
```

## File Integrity Rules

1. **Never overwrite** without reading first
2. **Always backup** before bulk operations
3. **Validate frontmatter** — every `.md` must have valid YAML
4. **Preserve encoding** — always use UTF-8
5. **Atomic moves** — move file, then update frontmatter, then log
6. **Log everything** — every write/move operation gets logged to `/Logs/`

## Logging Pattern

After every write/move, append to today's log file:

```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action": "move",
  "source": "/Needs_Action/EMAIL_123.md",
  "destination": "/Done/EMAIL_123.md",
  "actor": "process-inbox"
}
```

Log file path: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

## Important Rules

- NEVER write credentials, tokens, or secrets to vault files
- NEVER delete files without human approval (move to /Done/ instead)
- Always use forward slashes in paths for cross-platform support
- Dashboard.md is single-writer (only update-dashboard skill writes it)
- Company_Handbook.md is human-owned (AI can suggest, not overwrite)

## When to Use

- Every time Claude needs to interact with the vault
- When processing items across workflow folders
- When creating, updating, or moving vault files
- As the foundation skill called by all other skills
