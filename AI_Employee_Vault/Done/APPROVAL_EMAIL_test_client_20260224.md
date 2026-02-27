---
type: approval_request
action: email_send
to: test_client@example.com
subject: January 2026 Invoice - $1,500
priority: high
created: 2026-02-24T10:00:00Z
expires: 2026-02-25T10:00:00Z
status: completed
completed_at: 2026-02-24T12:00:00Z
executed_by: process-approved (DRY RUN - no credentials)
source_plan: /Plans/PLAN_EMAIL_invoice_test_client_20260224.md
---

# Approval Required: Send Email

## Action Details
- **What**: Send invoice email to test client
- **Why**: Client requested January invoice
- **Source**: WhatsApp message from test client

## Email Details
- **To**: test_client@example.com
- **Subject**: January 2026 Invoice - $1,500
- **Body Preview**: Please find attached your invoice for January 2026.

## Full Email Body
Dear Client,

Please find attached your invoice for January 2026.

Amount: $1,500.00
Due Date: February 15, 2026

Thank you for your business.

Best regards,
AI Employee

## Risk Assessment
- **Reversible**: No (email cannot be unsent)
- **External Impact**: Client receives invoice
- **Cost**: None (informational)

## To Approve
Move this file to the `/Approved/` folder.

## To Reject
Move this file to the `/Rejected/` folder.
