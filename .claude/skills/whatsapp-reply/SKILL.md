# WhatsApp Reply Skill

## Description
Sends approved WhatsApp replies via Playwright browser automation. Processes reply files from /Approved/ folder (Human-in-the-Loop).

## When to Use
- User asks to "reply on whatsapp", "send whatsapp message", "respond to whatsapp"
- Approved reply files exist in /Approved/ folder with WHATSAPP_REPLY prefix
- After WhatsApp watcher detects a message and user wants to respond

## Instructions

### Prerequisites
- `uv add playwright`
- WhatsApp Web session established (QR scanned via whatsapp-watcher)
- Reply file approved and moved to `/Approved/`

### Reply File Format
Create in `/Pending_Approval/`:
```markdown
---
type: whatsapp_reply
to: Contact Name
status: pending_approval
created: 2026-02-27T10:00:00
---

## Reply To
- **Contact**: Contact Name (must match WhatsApp chat name exactly)

## Message Content
Your reply message here.
Can be multiple lines.

## Reply Settings
- **Platform**: WhatsApp
- **Action**: send_message
```

### Workflow
1. WhatsApp Watcher detects message → creates file in `/Needs_Action/`
2. Claude (or human) drafts reply → creates file in `/Pending_Approval/`
3. Human reviews and approves → moves to `/Approved/`
4. WhatsApp Reply script processes `/Approved/WHATSAPP_REPLY_*.md`
5. Opens WhatsApp Web → finds contact → types message → sends
6. Moves file to `/Done/` on success

### Running
```bash
uv run python .claude/skills/whatsapp-reply/scripts/whatsapp_reply.py --vault ./AI_Employee_Vault
```

### Safety
- ONLY processes files from `/Approved/` folder
- Human must approve every reply before sending
- Uses existing WhatsApp session (same as watcher)
- All actions logged to `/Logs/`
