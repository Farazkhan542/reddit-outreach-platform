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


class SubmitResult(BaseModel):
    thing_id: str
    permalink: str | None = None


class RedditClient(Protocol):
    """Everything the platform needs from Reddit. `mock` and (later) `live` both implement this."""

    async def search_new(
        self, subreddits: list[str], keywords: list[str], limit: int = 50
    ) -> list[RedditPost]: ...

    async def post_comment(self, access_token: str, parent_fullname: str, body: str) -> SubmitResult: ...

    async def send_dm(self, access_token: str, to_username: str, subject: str, body: str) -> SubmitResult: ...

    async def get_account_health(self, access_token: str) -> dict: ...
