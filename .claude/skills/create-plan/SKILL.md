---
name: create-plan
description: This skill should be used when the user asks to "create a plan", "make a plan", "plan this task", or when Claude needs to break down a complex task from /Needs_Action/ into actionable steps with a Plan.md file.
version: 1.0.0
---

# Create Plan Skill

Creates structured `Plan.md` files with checkboxes for multi-step tasks detected in `/Needs_Action/`.

## What This Skill Does

When Claude processes an item from `/Needs_Action/` that requires multiple steps, this skill creates a `Plan.md` file in `/Plans/` with clear objectives, steps, approval requirements, and completion criteria.

## Plan.md Template

```markdown
---
created: {{ISO_TIMESTAMP}}
source: {{path to original Needs_Action file}}
status: in_progress | pending_approval | completed
priority: urgent | high | medium | low
estimated_steps: {{number}}
---

# Plan: {{Brief Title}}

## Objective
{{What needs to be accomplished}}

## Context
- **Source**: {{where this task came from — email, whatsapp, file, manual}}
- **From**: {{who requested this}}
- **Deadline**: {{if any}}

## Steps
- [ ] Step 1: {{description}}
- [ ] Step 2: {{description}}
- [ ] Step 3: {{description}}
- [ ] Step 4: {{description}} (REQUIRES APPROVAL)
- [ ] Step 5: {{description}}

## Approval Required
{{List any steps that need human approval}}
- Step 4 requires approval because: {{reason}}
- See: /Pending_Approval/{{approval_file}}.md

## Completion Criteria
- [ ] All steps marked complete
- [ ] Results logged to /Logs/
- [ ] Source file moved to /Done/
- [ ] Dashboard.md updated

## Notes
{{Any additional context, warnings, or considerations}}
```

## Step-by-Step Process

1. **Read** the action file from `/Needs_Action/`
2. **Analyze** what needs to be done based on type and content
3. **Break down** into concrete, actionable steps
4. **Identify** which steps require human approval (check Company_Handbook.md thresholds)
5. **Write** the Plan.md to `/Plans/` folder
6. **Create** approval request files if needed (→ `/Pending_Approval/`)
7. **Update** Dashboard.md with new plan
8. **Log** plan creation to `/Logs/`

## Plan Naming Convention

Format: `PLAN_{TYPE}_{IDENTIFIER}_{DATE}.md`

Examples:
- `PLAN_EMAIL_invoice_client_a_20260225.md`
- `PLAN_WHATSAPP_meeting_request_20260225.md`
- `PLAN_TASK_website_update_20260225.md`

## Approval Detection Rules (from Company_Handbook.md)

A step requires approval when it involves:
- Sending email to new/unknown contacts
- Any payment or financial action > $50
- Social media posting
- Deleting or moving files outside vault
- Any irreversible external action

## Important Rules

- Every multi-step task MUST have a Plan.md
- Plans should be specific — no vague steps
- Each step should be independently completable
- Mark approval-required steps clearly with `(REQUIRES APPROVAL)`
- Update plan status as steps complete
- Move completed plans to `/Done/`

## When to Use

- When processing complex items from `/Needs_Action/`
- When a task has more than 2 steps
- When Claude's reasoning loop identifies multi-step work
- When user manually requests a task plan
