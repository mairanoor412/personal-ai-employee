---
name: process-approved
description: This skill should be used when the user asks to "process approved items", "execute approved actions", "check approved folder", or when the system needs to watch the /Approved/ folder and execute the approved actions.
version: 1.0.0
---

# Process Approved Skill

Watches the `/Approved/` folder and executes approved actions using the appropriate MCP servers or scripts.

## What This Skill Does

When a human moves a file from `/Pending_Approval/` to `/Approved/`, this skill detects it, reads the action details, and executes the approved action using the correct tool (email MCP, LinkedIn poster, etc.).

## Workflow

```
File appears in /Approved/
    ↓
Read frontmatter → determine action type
    ↓
Route to correct executor:
├── action: email_send    → email-mcp (send_email tool)
├── action: social_post   → linkedin-post (publish_post)
├── action: payment       → payment handler (future)
└── action: other         → manual handling
    ↓
Execute action
    ↓
Move file to /Done/ with completion metadata
    ↓
Update Dashboard.md + write to /Logs/
```

## Step-by-Step Process

1. **Scan** `/Approved/` folder for `APPROVAL_*.md` files
2. **Read** the file and parse YAML frontmatter
3. **Determine** action type from `action` field
4. **Execute** the action:
   - `email_send` → call email MCP `send_email` tool with `to`, `subject`, and body
   - `social_post` → call linkedin-post skill to publish content
   - `payment` → log for manual processing (Bronze/Silver tier)
   - `file_delete` → execute file operation
5. **Update** frontmatter: `status: completed`, add `completed_at` timestamp
6. **Move** file from `/Approved/` to `/Done/`
7. **Log** execution result to `/Logs/`
8. **Update** Dashboard.md — decrement "Approvals Waiting", add to "Recent Activity"

## Frontmatter Parsing

Read these fields from approved files:

```yaml
action: email_send | payment | social_post | file_delete
to: recipient (for emails)
subject: subject line (for emails)
amount: dollar amount (for payments)
platform: linkedin | facebook | twitter (for social posts)
```

## Action Routing Map

| `action` Value | Executor | Required Fields |
|---------------|----------|-----------------|
| `email_send` | email-mcp → `send_email` | `to`, `subject`, body in content |
| `social_post` | linkedin-post → `publish_post` | `platform`, post content |
| `payment` | Log only (manual) | `amount`, `recipient` |
| `file_delete` | File system operation | file path in content |

## Error Handling

If execution fails:
- Do NOT move file to `/Done/`
- Update frontmatter: `status: failed`, add `error` field
- Move to `/Needs_Action/` for re-processing
- Log error to `/Logs/`
- Alert human via Dashboard.md

## Important Rules

- ONLY process files that are in `/Approved/` folder
- NEVER re-execute an already completed action
- Verify the file has valid frontmatter before executing
- Check for expiry — if `expires` timestamp has passed, skip and log
- ONE execution per file — no retries without new approval
- Log EVERY execution attempt (success or failure)

## When to Use

- When the orchestrator detects new files in `/Approved/`
- After human approves an action in Obsidian
- As part of the reasoning loop's action phase
