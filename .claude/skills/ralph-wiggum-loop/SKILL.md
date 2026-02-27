# Ralph Wiggum Loop Skill

## Description
Autonomous task completion loop — continuously processes tasks from `/Needs_Action/` until all are done or require human input. Named after the persistent (if confused) Simpsons character.

## When to Use
- User asks to "process all tasks", "run autonomous loop", "handle everything"
- Multiple items piled up in `/Needs_Action/`
- User wants hands-off processing of routine tasks

## Instructions

### How It Works
```
WHILE tasks exist in /Needs_Action/:
    1. READ next task file
    2. ANALYZE task type and complexity
    3. IF simple (no approval needed):
         → Execute directly → Move to /Done/
    4. IF needs plan:
         → Create Plan.md → Execute steps → Move to /Done/
    5. IF needs approval:
         → Move to /Pending_Approval/ → SKIP (wait for human)
    6. IF error:
         → Log error → Create error report → SKIP
    7. REPEAT until /Needs_Action/ is empty or all remaining need human input
```

### Task Priority Order
1. **Critical** — errors, urgent messages (keyword match)
2. **High** — WhatsApp/email with keywords
3. **Medium** — LinkedIn notifications, file drops
4. **Low** — routine updates, log entries

### Auto-Executable Actions (No approval needed)
- Reading and summarizing files
- Creating plan.md files
- Updating Dashboard.md
- Moving files between vault folders
- Generating reports and briefings
- Logging actions

### Actions Requiring Approval
- Sending emails
- Publishing social media posts
- Creating invoices
- Payments
- Contacting new people
- Any action in Company_Handbook.md approval list

### Safety Guards
- Maximum 50 tasks per loop run (prevent infinite loops)
- 5 second pause between tasks (prevent rate limiting)
- Stop if 3 consecutive errors occur
- Never auto-approve anything — always route to human
- Log every decision and action

### Output
- Processed tasks → `/Done/`
- Pending approvals → `/Pending_Approval/`
- Errors → `/Needs_Action/ERROR_*.md`
- All actions logged to `/Logs/`
- Dashboard updated after loop completes
