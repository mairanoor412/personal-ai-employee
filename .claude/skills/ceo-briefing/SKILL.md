# CEO Briefing Skill

## Description
Generates a weekly CEO briefing report summarizing all AI Employee activities, business metrics, and recommendations.

## When to Use
- User asks to "create briefing", "CEO report", "weekly summary"
- Scheduler triggers weekly briefing (e.g., every Friday)
- User asks "what happened this week?"

## Instructions

### What It Does
1. Scans all vault folders for activity data
2. Reads logs from `AI_Employee_Vault/Logs/`
3. Counts tasks processed, approved, rejected
4. Summarizes social media activity
5. Reports financial data (if Odoo connected)
6. Generates actionable recommendations

### Report Template
```markdown
# CEO Briefing — Week of [start_date] to [end_date]

## Executive Summary
[1-2 sentence overview of the week]

## Task Metrics
| Metric | Count |
|--------|-------|
| Tasks Received | X |
| Tasks Completed | X |
| Pending Approval | X |
| Rejected | X |

## Communication Summary
- **Emails processed**: X
- **WhatsApp alerts**: X
- **LinkedIn notifications**: X

## Social Media
- **Posts published**: X (LinkedIn: X, Facebook: X, Twitter: X)
- **Approval rate**: X%

## Financial Summary (Odoo)
- **Invoices created**: X
- **Total revenue**: $X
- **Pending payments**: $X

## Key Actions Taken
1. [Action 1 with result]
2. [Action 2 with result]

## Recommendations
1. [Recommendation based on data]
2. [Recommendation based on patterns]

## Upcoming
- [Scheduled tasks for next week]
```

### Data Sources
- `AI_Employee_Vault/Logs/*.json` — All action logs
- `AI_Employee_Vault/Done/` — Completed tasks
- `AI_Employee_Vault/Rejected/` — Rejected items
- `AI_Employee_Vault/Pending_Approval/` — Pending items
- `AI_Employee_Vault/Accounting/` — Financial reports

### Output
Save to: `AI_Employee_Vault/Briefings/CEO_Briefing_[date].md`
Update: `AI_Employee_Vault/Dashboard.md` with latest summary
