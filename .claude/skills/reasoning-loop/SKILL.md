---
name: reasoning-loop
description: This skill should be used when Claude needs to autonomously process tasks from /Needs_Action/, reason about them, create plans, request approvals, and execute actions in a continuous Read-Think-Plan-Act cycle.
version: 1.0.0
---

# Reasoning Loop Skill

Implements Claude's core reasoning cycle: Read → Think → Plan → Act. This is the "brain" of the AI Employee.

## What This Skill Does

Orchestrates Claude's autonomous processing loop:
1. Scan `/Needs_Action/` for new items
2. Reason about each item (what type, what's needed)
3. Create a Plan.md for multi-step tasks
4. Execute simple tasks or route to approval
5. Update Dashboard and Logs

## The Reasoning Cycle

```
┌─────────────────────────────┐
│         READ                │
│  Scan /Needs_Action/        │
│  Read each .md file         │
│  Parse frontmatter          │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│         THINK               │
│  Categorize by type         │
│  Assess priority            │
│  Check Company_Handbook.md  │
│  Determine complexity       │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│         PLAN                │
│  Simple task? → Execute     │
│  Complex? → Create Plan.md  │
│  Needs approval? → Route    │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│         ACT                 │
│  Execute auto-approved      │
│  Create approval requests   │
│  Update Dashboard.md        │
│  Move completed to /Done/   │
│  Log everything             │
└──────────┬──────────────────┘
           ↓
       (Loop back to READ)
```

## Step-by-Step Process

### Phase 1: READ
```
1. Glob AI_Employee_Vault/Needs_Action/*.md
2. For each file:
   a. Read file content
   b. Parse YAML frontmatter (type, priority, status)
   c. Skip files with status != "pending"
   d. Sort by priority (urgent > high > medium > low)
```

### Phase 2: THINK
```
For each pending item:
1. Identify type: email, whatsapp, file_drop, finance, task, manual
2. Read Company_Handbook.md for applicable rules
3. Determine:
   - Can this be auto-handled? (check thresholds)
   - Does it need a plan? (multi-step = yes)
   - Does it need approval? (check approval rules)
4. Read Business_Goals.md for context if relevant
```

### Phase 3: PLAN
```
If simple (1-2 steps, auto-approvable):
   → Execute directly, move to /Done/

If complex (3+ steps):
   → Use create-plan skill to write Plan.md
   → If any step needs approval → use approval-workflow skill

If needs approval:
   → Create approval file in /Pending_Approval/
   → Wait (do not execute)
```

### Phase 4: ACT
```
1. Execute auto-approved actions:
   - Reply to known contacts (email-mcp)
   - Categorize files (vault-read-write)
   - Update records (vault-read-write)

2. For approved items (from /Approved/):
   - Use process-approved skill

3. After every action:
   - Update source file frontmatter (status: completed)
   - Move to /Done/
   - Update Dashboard.md
   - Write to /Logs/
```

## Priority Processing Order

1. **URGENT**: Process immediately
2. **HIGH**: Process in current cycle
3. **MEDIUM**: Process if time permits
4. **LOW**: Batch process (daily)

## Decision Matrix

| Item Type | Auto-Approve? | Action |
|-----------|--------------|--------|
| Email from known contact | Yes | Draft reply, send |
| Email from unknown | No | Create approval request |
| WhatsApp with keyword | No | Create plan, may need approval |
| File drop | Yes | Categorize, log |
| Payment request | No | Always create approval |
| Social media task | No | Always create approval |
| Manual task | Depends | Check handbook thresholds |

## Integration with Other Skills

| Phase | Skills Used |
|-------|------------|
| READ | `vault-read-write` — scan folders |
| THINK | `vault-read-write` — read handbook, goals |
| PLAN | `create-plan` — write Plan.md |
| ACT (auto) | `email-mcp`, `vault-read-write` |
| ACT (approval) | `approval-workflow` → `process-approved` |
| TRACK | `create-dashboard` — update status |
| LOG | `vault-read-write` — write logs |

## Completion Tracking

After processing all items:
```markdown
## Cycle Summary
- Items processed: {{count}}
- Plans created: {{count}}
- Approvals requested: {{count}}
- Actions executed: {{count}}
- Errors: {{count}}
- Next cycle: {{timestamp}}
```

## Important Rules

- ALWAYS read Company_Handbook.md before making decisions
- NEVER execute payment actions without approval
- NEVER skip the approval step for sensitive actions
- Process URGENT items first, regardless of order
- Log every decision and action
- If unsure about an action → request approval (safer)
- Update Dashboard.md after EVERY cycle

## When to Use

- This is the CORE skill — used every time Claude processes the vault
- Called by the scheduler every 15 minutes
- Called manually when user asks Claude to "process inbox" or "check tasks"
- Used by the Ralph Wiggum loop (Gold tier) for continuous operation
