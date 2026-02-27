# Facebook Post Skill

## Description
Auto-posts approved content to Facebook page/profile using Playwright browser automation.

## When to Use
- User asks to "post on facebook", "create facebook post"
- Approved post file `FACEBOOK_POST_*.md` found in `/Approved/`
- Social media calendar triggers a scheduled post

## Instructions

### Prerequisites
- Playwright installed: `uv run playwright install chromium`
- Facebook session established (first run requires manual login)
- Session saved in `facebook_session/` directory

### Post File Format
```markdown
# Facebook Post Request

## Post Content
Your post text here...

## Post Settings
- **Visibility**: Public / Friends
- **Type**: Text only / With image
```

### Workflow
1. Check `/Approved/` for `FACEBOOK_POST_*.md` files
2. Extract post content from markdown
3. Open Facebook via Playwright with persistent session
4. Navigate to feed, open post composer
5. Type content using bounding box click + keyboard.type
6. Click "Post" button
7. Move file to `/Done/` on success
8. Log action to `/Logs/`

### Approval Rules
- ALL Facebook posts require human approval
- Post must be in `/Approved/` folder before publishing

### Helper Script
Run: `uv run python .claude/skills/facebook-post/scripts/facebook_poster.py --vault ./AI_Employee_Vault`
