---
name: process-inbox
description: This skill should be used when the user asks to "process inbox", "check needs action", "process pending items", "handle tasks", or mentions processing the Needs_Action folder, triaging items, or handling queued work.
version: 1.0.0
---

# Process Inbox Skill

Reads all items in `/Needs_Action/`, categorizes them, prioritizes, and creates plans or takes action.

## What This Skill Does

Scans the `AI_Employee_Vault/Needs_Action/` folder, reads each `.md` file's frontmatter to understand its type and priority, then either:
- Creates a `Plan.md` in `/Plans/` for complex tasks
- Moves simple items directly to `/Done/` after processing
- Creates approval requests in `/Pending_Approval/` for sensitive actions

## Step-by-Step Process

1. **Scan**: List all `.md` files in `/Needs_Action/`
2. **Read**: Parse each file's YAML frontmatter (`type`, `priority`, `status`)
3. **Categorize** by type:
   - `email` → Check Company_Handbook.md rules for auto-reply vs approval
   - `file_drop` → Determine file type and appropriate action
   - `whatsapp` → Check keywords and urgency
   - `finance` → Flag for review based on amount thresholds
4. **Prioritize**: Sort by priority (URGENT > HIGH > MEDIUM > LOW)
5. **Act** on each item:
   - **Auto-processable**: Execute action, move to `/Done/`
   - **Needs planning**: Create `Plan.md` in `/Plans/` with steps
   - **Needs approval**: Create approval file in `/Pending_Approval/`
6. **Update Dashboard**: Refresh Dashboard.md with new counts
7. **Log**: Write processing summary to `/Logs/`

## Plan.md Template (for complex tasks)

```markdown
---
created: {{TIMESTAMP}}
source: /Needs_Action/{{SOURCE_FILE}}
status: pending
---

# Plan: {{TASK_DESCRIPTION}}

## Objective
{{What needs to be accomplished}}

## Steps
- [ ] Step 1: {{description}}
- [ ] Step 2: {{description}}
- [ ] Step 3: {{description}}

## Approval Required
{{yes/no — if yes, explain what needs approval}}

## Estimated Completion
{{timeframe}}
```

## Categorization Rules

| Type | Priority | Action |
|------|----------|--------|
| Email from known contact | HIGH | Auto-draft reply, log |
| Email from unknown | MEDIUM | Create approval request |
| File drop (.pdf, .docx) | MEDIUM | Categorize, summarize |
| File drop (.csv, .xlsx) | HIGH | Parse, add to Accounting |
| Payment related | URGENT | Always create approval |
| General inquiry | LOW | Queue for batch processing |

## Important Rules

- ALWAYS check Company_Handbook.md rules before taking action
- NEVER auto-execute financial transactions
- Process URGENT items first, then HIGH, MEDIUM, LOW
- Move processed files from `/Needs_Action/` to `/Done/` with timestamp
- If unsure about an action, create an approval request
- Update Dashboard.md after processing

## When to Use

- Periodically (every few minutes) to process new items
- After a watcher detects new items
- When user asks to process pending work
- As part of the Ralph Wiggum autonomous loop
