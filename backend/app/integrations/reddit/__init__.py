from app.core.config import get_settings
from app.integrations.reddit.base import RedditClient, RedditPost
from app.integrations.reddit.mock import MockRedditClient


def get_reddit_client() -> RedditClient:
    mode = get_settings().reddit_mode
    if mode == "mock":
        return MockRedditClient()
    # TODO: implement LiveRedditClient (asyncpraw / direct OAuth2) once Reddit API access is approved.
    raise NotImplementedError(f"Reddit mode '{mode}' is not implemented yet")


__all__ = ["RedditClient", "RedditPost", "get_reddit_client"]
