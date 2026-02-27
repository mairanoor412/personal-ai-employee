# Audit Logger Skill

## Description
Comprehensive audit logging system — tracks every action, decision, and state change with timestamps for full accountability.

## When to Use
- After ANY action is performed (post, email, file move, approval)
- When reasoning loop makes a decision
- When errors occur
- When user requests audit trail

## Instructions

### Log Format (JSON)
Every action creates a log entry in `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-02-25T08:30:00.000Z",
  "action_type": "linkedin_post",
  "actor": "linkedin_poster",
  "status": "success",
  "details": {
    "file": "LINKEDIN_POST_test.md",
    "platform": "linkedin",
    "content_preview": "First 100 chars..."
  },
  "duration_ms": 15000,
  "approval": {
    "required": true,
    "approved_by": "human",
    "approved_at": "2026-02-25T08:25:00.000Z"
  }
}
```

### Action Types to Log
| Action Type | Actor | Description |
|-------------|-------|-------------|
| `file_detected` | file_watcher | New file in DropFolder |
| `whatsapp_detected` | whatsapp_watcher | New WhatsApp message |
| `linkedin_notification` | linkedin_watcher | LinkedIn notification |
| `gmail_detected` | gmail_watcher | New email |
| `linkedin_post` | linkedin_poster | Post published |
| `facebook_post` | facebook_poster | Post published |
| `twitter_post` | twitter_poster | Tweet published |
| `instagram_post` | instagram_poster | Post published |
| `email_sent` | email_mcp | Email sent |
| `email_drafted` | email_mcp | Email drafted |
| `approval_requested` | approval_workflow | Sent to Pending_Approval |
| `approval_granted` | human | Moved to Approved |
| `approval_rejected` | human | Moved to Rejected |
| `task_completed` | reasoning_loop | Task moved to Done |
| `plan_created` | create_plan | Plan.md created |
| `odoo_invoice` | odoo_client | Invoice created/read |
| `error` | any | Error occurred |
| `system_audit` | weekly_audit | Audit performed |

### Log Retention
- Daily log files: `YYYY-MM-DD.json`
- Keep logs for 90 days minimum
- Weekly summary in `/Briefings/`

### Querying Logs
Claude can read and analyze logs to answer questions like:
- "How many posts did I make this week?"
- "When was the last error?"
- "Show me all approved actions today"
