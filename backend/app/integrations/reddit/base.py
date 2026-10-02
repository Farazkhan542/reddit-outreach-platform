from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class RedditPost(BaseModel):
    fullname: str  # t3_xxx for posts, t1_xxx for comments
    subreddit: str
    author: str
    title: str | None = None
    body: str = ""
    permalink: str
    created_at: datetime


class RedditClient(Protocol):
    """Everything the platform needs from Reddit: read-only. `mock` and (later) `live` implement this.

    There are deliberately no write methods. The app never posts, votes or messages;
    people post approved replies themselves on reddit.com.
    """

    async def search_new(
        self, subreddits: list[str], keywords: list[str], limit: int = 50
    ) -> list[RedditPost]: ...

    async def get_account_health(self, access_token: str) -> dict: ...
