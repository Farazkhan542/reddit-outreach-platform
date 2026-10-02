"""Offline stand-in for the Reddit Data API. Makes no network calls."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from app.integrations.reddit.base import RedditPost

_SAMPLE_POSTS = [
    ("Need a sturdy dining table for 6, budget around $800", "Moving into a new place next month. Any recommendations for solid wood?"),
    ("Looking for a budget phone under $200", "My old phone died. Mostly need good battery and decent camera."),
    ("Which refurbished laptop sellers are trustworthy?", "Want a used ThinkPad for uni, don't want to get scammed."),
    ("Finally finished my living room!", "Took six months but I love how the sofa turned out."),
    ("Recommendations for an ergonomic office chair?", "Back pain is killing me. Budget is flexible, need it this week."),
    ("Is it worth buying a phone on sale now or waiting?", "Just curious what people think about the upcoming releases."),
]


class MockRedditClient:
    async def search_new(
        self, subreddits: list[str], keywords: list[str], limit: int = 50
    ) -> list[RedditPost]:
        subs = subreddits or ["test"]
        now = datetime.now(timezone.utc)
        posts = []
        for title, body in random.sample(_SAMPLE_POSTS, k=min(limit, len(_SAMPLE_POSTS))):
            sub = random.choice(subs)
            post_id = uuid.uuid4().hex[:7]
            posts.append(
                RedditPost(
                    fullname=f"t3_{post_id}",
                    subreddit=sub,
                    author=f"user_{post_id[:4]}",
                    title=title,
                    body=body,
                    permalink=f"https://www.reddit.com/r/{sub}/comments/{post_id}/",
                    created_at=now - timedelta(minutes=random.randint(1, 120)),
                )
            )
        return posts

    async def get_account_health(self, access_token: str) -> dict:
        return {"karma": random.randint(50, 5000), "removal_rate": 0.0}
