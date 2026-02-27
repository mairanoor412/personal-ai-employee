---
name: approval-workflow
description: This skill should be used when Claude needs to request human approval for sensitive actions like sending emails, making payments, posting on social media, or any action that exceeds auto-approve thresholds defined in Company_Handbook.md.
version: 1.0.0
---

# Approval Workflow Skill

Creates approval request files in `/Pending_Approval/` for sensitive actions that require human review before execution.

## What This Skill Does

When Claude determines an action exceeds auto-approve thresholds (from Company_Handbook.md), it creates a structured approval request file instead of executing the action directly. The human reviews in Obsidian and moves the file to `/Approved/` or `/Rejected/`.

## Workflow

```
Claude detects sensitive action needed
    ↓
Creates APPROVAL_*.md in /Pending_Approval/
    ↓
Human reviews in Obsidian
    ↓
├── Moves to /Approved/  → Action executes
└── Moves to /Rejected/  → Action cancelled, logged
```

## Approval Request Template

```markdown
---
type: approval_request
action: {{email_send | payment | social_post | file_delete | other}}
priority: {{urgent | high | medium | low}}
created: {{ISO_TIMESTAMP}}
expires: {{ISO_TIMESTAMP +24h}}
status: pending
source_plan: {{path to Plan.md if exists}}
---

# Approval Required: {{Brief Description}}

## Action Details
- **What**: {{Detailed description of the action}}
- **Why**: {{Reason this action is needed}}
- **Source**: {{What triggered this — email, whatsapp, task}}

## Specific Parameters
{{Action-specific details — varies by type}}

## Risk Assessment
- **Reversible**: Yes / No
- **External Impact**: {{Who/what is affected}}
- **Cost**: {{If financial}}

## To Approve
Move this file to the `/Approved/` folder.

## To Reject
Move this file to the `/Rejected/` folder.

## Auto-Expires
This request expires on {{expiry date}}. If not acted upon, it will be archived.
```

## Type-Specific Templates

### Email Send Approval
```markdown
---
type: approval_request
action: email_send
to: recipient@example.com
subject: Email subject line
priority: high
created: 2026-02-25T10:00:00Z
expires: 2026-02-26T10:00:00Z
status: pending
---

# Approval Required: Send Email

## Email Details
- **To**: recipient@example.com
- **Subject**: Email subject line
- **Body Preview**: First 200 characters of the email...

## Full Email Body
{{Complete email content that will be sent}}

## To Approve
Move this file to `/Approved/`.
```

### Payment Approval
```markdown
---
type: approval_request
action: payment
amount: 500.00
currency: USD
recipient: Client A
priority: high
created: 2026-02-25T10:00:00Z
expires: 2026-02-26T10:00:00Z
status: pending
---

# Approval Required: Payment

## Payment Details
- **Amount**: $500.00
- **To**: Client A (Bank: XXXX1234)
- **Reference**: Invoice #1234
- **Reason**: Monthly service payment

## To Approve
Move this file to `/Approved/`.
```

### Social Media Post Approval
```markdown
---
type: approval_request
action: social_post
platform: linkedin
priority: medium
created: 2026-02-25T10:00:00Z
expires: 2026-02-26T10:00:00Z
status: pending
---

# Approval Required: LinkedIn Post

## Post Content
{{Full post content here}}

## Post Settings
- **Platform**: LinkedIn
- **Visibility**: Public
- **Scheduled**: 2026-02-25T09:00:00

## To Approve
Move this file to `/Approved/`.
```

## File Naming Convention

Format: `APPROVAL_{ACTION}_{IDENTIFIER}_{DATE}.md`

Examples:
- `APPROVAL_EMAIL_client_a_20260225.md`
- `APPROVAL_PAYMENT_invoice_1234_20260225.md`
- `APPROVAL_POST_linkedin_20260225.md`

## Auto-Approve vs Requires Approval (from Company_Handbook.md)

| Action | Auto-Approve | Requires Approval |
|--------|-------------|-------------------|
| Email replies | Known contacts | New contacts, bulk |
| Payments | < $50 recurring known vendors | > $100, new payees |
| Social media | — | ALL posts |
| File operations | Create, read | Delete, move outside |

## Step-by-Step Process

1. **Check** Company_Handbook.md for threshold rules
2. **Determine** if action exceeds auto-approve threshold
3. **Create** approval file in `/Pending_Approval/` using appropriate template
4. **Update** Dashboard.md — increment "Approvals Waiting" count
5. **Log** approval request to `/Logs/`
6. **Wait** — do NOT execute the action until file appears in `/Approved/`

## Important Rules

- NEVER execute a sensitive action without an approval file
- Approval files EXPIRE after 24 hours by default
- ONE approval file per action — no batching
- Include ALL details needed for human to make a decision
- After rejection: log reason, move to /Done/, do NOT retry

## When to Use

- When any action exceeds Company_Handbook.md thresholds
- When sending emails to unknown contacts
- When making ANY payment
- When posting on ANY social media platform
- When deleting files or taking irreversible actions
