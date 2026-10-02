"""Scout: pulls new candidate posts for a tenant's subreddits and keywords."""

from app.agents.context import TenantContext
from app.integrations.reddit import RedditClient, RedditPost


class ScoutAgent:
    def __init__(self, reddit: RedditClient):
        self.reddit = reddit

    async def run(self, ctx: TenantContext, limit: int = 50) -> list[RedditPost]:
        return await self.reddit.search_new(ctx.subreddits, ctx.keywords, limit=limit)
