# Instagram Post Skill

## Description
Auto-posts approved content to Instagram using Playwright browser automation (mobile viewport emulation).

## When to Use
- User asks to "post on instagram", "create instagram post"
- Approved post file `INSTAGRAM_POST_*.md` found in `/Approved/`

## Instructions

### Prerequisites
- Playwright installed: `uv run playwright install chromium`
- Instagram session established (first run requires manual login)
- Session saved in `instagram_session/` directory
- Mobile viewport emulation (Instagram Web requires mobile view for posting)

### Post File Format
```markdown
# Instagram Post Request

## Post Content
Your caption here...

## Post Settings
- **Type**: Photo / Reel / Story
- **Image Path**: path/to/image.jpg (required for photo posts)
```

### Workflow
1. Check `/Approved/` for `INSTAGRAM_POST_*.md` files
2. Extract caption and image path from markdown
3. Open Instagram via Playwright with mobile viewport
4. Click "+" (new post) button
5. Upload image, add caption
6. Click "Share" button
7. Move file to `/Done/` on success
8. Log action to `/Logs/`

### Technical Notes
- Instagram Web posting requires mobile User-Agent emulation
- Viewport: `{"width": 390, "height": 844}` (iPhone 12 Pro)
- User-Agent: Mobile Chrome on iOS
- Image upload via file chooser dialog

### Approval Rules
- ALL Instagram posts require human approval
- Post must be in `/Approved/` folder before publishing

### Helper Script
Run: `uv run python .claude/skills/instagram-post/scripts/instagram_poster.py --vault ./AI_Employee_Vault`
