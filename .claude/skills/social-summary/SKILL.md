# Social Media Summary Skill

## Description
Generates a consolidated social media analytics summary across all platforms (LinkedIn, Facebook, Instagram, Twitter).

## When to Use
- User asks to "show social media summary", "social analytics"
- Weekly audit needs social media data
- CEO briefing requires social media section

## Instructions

### What It Does
1. Reads all social media logs from `AI_Employee_Vault/Logs/`
2. Counts posts per platform (LinkedIn, Facebook, Instagram, Twitter)
3. Tracks approval rates (approved vs rejected)
4. Lists recent posts with timestamps
5. Generates summary report in `/Briefings/`

### Report Format
```markdown
# Social Media Summary — Week of [date]

## Posts Published
| Platform | Posts | Approved | Rejected |
|----------|-------|----------|----------|
| LinkedIn | 3     | 3        | 0        |
| Facebook | 2     | 2        | 0        |
| Instagram| 1     | 1        | 0        |
| Twitter  | 4     | 3        | 1        |
| **Total**| **10**| **9**    | **1**    |

## Recent Activity
- [date] LinkedIn: "Post title..." ✅
- [date] Twitter: "Tweet content..." ✅

## Recommendations
- Increase posting frequency on Instagram
- Best engagement time: weekday mornings
```

### Data Sources
- `AI_Employee_Vault/Logs/*.json` — Action logs with timestamps
- `AI_Employee_Vault/Done/LINKEDIN_POST_*.md` — Completed LinkedIn posts
- `AI_Employee_Vault/Done/FACEBOOK_POST_*.md` — Completed Facebook posts
- `AI_Employee_Vault/Done/TWITTER_POST_*.md` — Completed Twitter posts
- `AI_Employee_Vault/Done/INSTAGRAM_POST_*.md` — Completed Instagram posts

### Output
Save report to: `AI_Employee_Vault/Briefings/Social_Summary_[date].md`
