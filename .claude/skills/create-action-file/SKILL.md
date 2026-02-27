---
name: create-action-file
description: This skill should be used when the user asks to "create action file", "add task to inbox", "create needs action item", "queue a task", or mentions creating markdown action files for the vault workflow.
version: 1.0.0
---

# Create Action File Skill

Creates properly formatted `.md` action files in `/Needs_Action/` from various sources.

## What This Skill Does

Generates standardized markdown files with YAML frontmatter that the AI Employee workflow can process. These files are the universal input format for the system.

## Action File Schema

Every action file MUST have this frontmatter structure:

```yaml
---
type: email | file_drop | whatsapp | finance | task | manual
from: {{source identifier}}
subject: {{brief description}}
received: {{ISO 8601 timestamp}}
priority: urgent | high | medium | low
status: pending
tags: [{{optional tags}}]
---
```

## Supported Types

### Email Action File
```markdown
---
type: email
from: sender@example.com
subject: Invoice Request
received: 2026-01-07T10:30:00
priority: high
status: pending
---

## Email Content
{{email body or snippet}}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

### File Drop Action File
```markdown
---
type: file_drop
original_name: report.pdf
file_type: .pdf
size_bytes: 245000
detected_at: 2026-01-07T10:30:00
status: pending
---

## File Details
- **Name**: report.pdf
- **Type**: .pdf
- **Size**: 245000 bytes

## Suggested Actions
- [ ] Review file contents
- [ ] Categorize and file
```

### Manual Task Action File
```markdown
---
type: manual
from: human
subject: {{task description}}
received: 2026-01-07T10:30:00
priority: medium
status: pending
---

## Task Description
{{detailed description}}

## Steps
- [ ] {{step 1}}
- [ ] {{step 2}}
```

### Finance Action File
```markdown
---
type: finance
from: bank_api
subject: New transaction detected
received: 2026-01-07T10:30:00
priority: high
status: pending
amount: {{dollar amount}}
---

## Transaction Details
- **Amount**: ${{amount}}
- **Description**: {{description}}
- **Date**: {{date}}

## Suggested Actions
- [ ] Categorize transaction
- [ ] Update Accounting records
- [ ] Flag if unusual
```

## File Naming Convention

Format: `{TYPE}_{IDENTIFIER}_{TIMESTAMP}.md`

Examples:
- `EMAIL_abc123def.md`
- `FILE_report.md`
- `TASK_update_website_20260107.md`
- `FINANCE_txn_456.md`

## Important Rules

- Every file MUST have valid YAML frontmatter
- `type`, `status`, and `priority` fields are REQUIRED
- Timestamps must be ISO 8601 format
- File names must not contain spaces (use underscores)
- Always set initial `status: pending`
- Place files ONLY in `/Needs_Action/`

## When to Use

- When watchers detect new items
- When user manually assigns a task
- When creating test/dummy data for development
- When another skill needs to queue work
