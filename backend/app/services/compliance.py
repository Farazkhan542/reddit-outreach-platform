import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReplyKind, SubredditRule


async def get_rule(db: AsyncSession, org_id: uuid.UUID, subreddit: str) -> SubredditRule | None:
    return await db.scalar(
        select(SubredditRule).where(
            SubredditRule.org_id == org_id, SubredditRule.subreddit == subreddit.lower()
        )
    )


async def can_reply(db: AsyncSession, org_id: uuid.UUID, subreddit: str, kind: ReplyKind) -> tuple[bool, str]:
    """Return (allowed, reason). Unknown subreddits are allowed but flagged for the reviewer."""
    rule = await get_rule(db, org_id, subreddit)
    if rule is None:
        return True, "no rule on file for this subreddit - reviewer should check its rules"
    if kind == ReplyKind.dm and not rule.allows_dms:
        return False, f"r/{subreddit} rule disallows DMs"
    if not rule.allows_commercial_replies:
        return False, f"r/{subreddit} disallows commercial replies"
    return True, "ok"
