# Gmail API Setup Guide

## Step 1: Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (name: "AI Employee")
3. Click "Enable APIs & Services"
4. Search for "Gmail API" and enable it

## Step 2: OAuth 2.0 Credentials
1. Go to APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth client ID"
3. If asked, configure the OAuth consent screen first:
   - User Type: External
   - App name: "AI Employee"
   - Add your email as test user
4. Application type: "Desktop app"
5. Name: "AI Employee Desktop"
6. Click "Create"
7. Download the JSON file
8. Rename it to `credentials.json`
9. Place it in the project root:
   ```
   personal-ai-employee/
   └── credentials.json    ← HERE
   ```

## Step 3: First Run
```bash
cd personal-ai-employee
uv run python skills/gmail-watcher/scripts/gmail_watcher.py --vault ./AI_Employee_Vault
```

- Browser will open for Google OAuth consent
- Allow access to Gmail (read-only)
- `token.json` will be created automatically
- Watcher will start checking emails every 120 seconds

## Step 4: Verify
- Check terminal for "Gmail Watcher started" message
- Send yourself an important email
- Check `AI_Employee_Vault/Needs_Action/` for new `EMAIL_*.md` files

## Security Reminders
- NEVER commit `credentials.json` or `token.json` to Git
- Both files are in `.gitignore`
- Token expires periodically and auto-refreshes
- Revoke access at: https://myaccount.google.com/permissions
