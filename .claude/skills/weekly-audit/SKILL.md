# Weekly Audit Skill

## Description
Performs a weekly audit of all AI Employee operations — checks for errors, stale tasks, missed actions, and system health.

## When to Use
- User asks to "run audit", "check system health", "weekly audit"
- Scheduler triggers weekly audit (e.g., every Sunday)
- User suspects something is wrong

## Instructions

### What It Audits
1. **Stale Tasks** — Files in `/Needs_Action/` older than 48 hours
2. **Pending Approvals** — Files in `/Pending_Approval/` older than 24 hours
3. **Error Logs** — Any errors in `Logs/*.json`
4. **Watcher Health** — Check if watchers ran recently
5. **Vault Integrity** — All required folders exist
6. **Log Completeness** — Actions have corresponding log entries

### Audit Report Format
```markdown
# Weekly Audit — [date]

## System Health: [GOOD / WARNING / CRITICAL]

## Stale Tasks (older than 48h)
- [filename] — created [date] — [X days old]

## Pending Approvals (older than 24h)
- [filename] — waiting since [date]

## Errors This Week
- [date] [error description]

## Watcher Status
| Watcher | Last Run | Status |
|---------|----------|--------|
| File Watcher | [date] | OK / STALE |
| LinkedIn Watcher | [date] | OK / STALE |
| WhatsApp Watcher | [date] | OK / STALE |
| Gmail Watcher | [date] | OK / NOT CONFIGURED |

## Vault Integrity
- All 10 folders: [OK / MISSING: folder_name]
- Dashboard.md: [OK / OUTDATED]
- Company_Handbook.md: [OK / MISSING]

## Recommendations
1. [Action items based on audit findings]
```

### Output
Save to: `AI_Employee_Vault/Briefings/Weekly_Audit_[date].md`
Update Dashboard.md with audit status
