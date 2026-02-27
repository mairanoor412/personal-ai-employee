# Twitter/X Post Skill

## Description
Auto-posts approved content to Twitter/X using Playwright browser automation.

## When to Use
- User asks to "post on twitter", "tweet", "post on X"
- Approved post file `TWITTER_POST_*.md` found in `/Approved/`

## Instructions

### Prerequisites
- Playwright installed: `uv run playwright install chromium`
- Twitter/X session established (first run requires manual login)
- Session saved in `twitter_session/` directory

### Post File Format
```markdown
# Twitter Post Request

## Post Content
Your tweet here (max 280 characters for free, 25000 for premium)...

## Post Settings
- **Type**: Tweet / Thread
- **Visibility**: Everyone / Circle
```

### Workflow
1. Check `/Approved/` for `TWITTER_POST_*.md` files
2. Extract tweet content from markdown
3. Open Twitter/X via Playwright with persistent session
4. Click compose tweet button
5. Type content in tweet editor
6. Click "Post" button
7. Move file to `/Done/` on success
8. Log action to `/Logs/`

### Technical Notes
- Twitter compose button: `[data-testid="tweetButtonInline"]` or `[href="/compose/post"]`
- Tweet editor: `[data-testid="tweetTextarea_0"]`
- Post button: `[data-testid="tweetButton"]`
- Character limit check before posting

### Approval Rules
- ALL tweets require human approval
- Post must be in `/Approved/` folder before publishing

### Helper Script
Run: `uv run python .claude/skills/twitter-post/scripts/twitter_poster.py --vault ./AI_Employee_Vault`
