# Error Recovery Skill

## Description
Handles errors gracefully — detects failures, retries operations, notifies user, and prevents cascading failures.

## When to Use
- A watcher script crashes or times out
- A post fails to publish
- MCP server connection drops
- Odoo connection fails
- Any automated action returns an error

## Instructions

### Error Handling Strategy

#### Level 1: Auto-Retry (No human needed)
- Network timeouts → retry 3 times with exponential backoff
- Session expired → re-authenticate and retry
- File locked → wait 5 seconds and retry
- Playwright element not found → refresh page and retry

#### Level 2: Notify User (Create action file)
- After 3 retries fail → create error report in `/Needs_Action/`
- Authentication failure → ask user to update credentials
- Permission denied → ask user to check access

#### Level 3: Graceful Degradation (Skip and continue)
- One platform fails → continue with others
- One post fails → skip and process next
- Non-critical watcher down → log and continue

### Error Report Format
```markdown
---
type: error_report
source: [watcher/poster/mcp/odoo]
severity: [low/medium/high/critical]
timestamp: [ISO timestamp]
status: pending
---

## Error Report

- **Source**: [component name]
- **Error**: [error message]
- **Attempts**: [retry count]
- **Last Attempt**: [timestamp]

## Context
[What was happening when error occurred]

## Suggested Fix
- [ ] [Suggested action 1]
- [ ] [Suggested action 2]
```

### Recovery Patterns
1. **Watcher crash** → Scheduler restarts it on next cycle
2. **Post failure** → File stays in `/Approved/`, retried next run
3. **Odoo disconnect** → Cache data locally, sync when reconnected
4. **Browser session expired** → Delete session folder, re-login on next run

### Output
- Error reports → `AI_Employee_Vault/Needs_Action/ERROR_*.md`
- Error logs → `AI_Employee_Vault/Logs/`
