from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"

    jwt_secret: str = "dev-only-insecure-secret-change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    fernet_key: str = ""

    database_url: str = "postgresql+asyncpg://outreach:outreach@localhost:5432/outreach"
    redis_url: str = "redis://localhost:6379/0"
    db_auto_create: bool = False

    # External integrations stay mocked until access is granted.
    reddit_mode: Literal["mock", "live"] = "mock"
    llm_mode: Literal["mock", "openai"] = "mock"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_redirect_uri: str = ""
    reddit_user_agent: str = "outreach-platform/0.1"
    openai_api_key: str = ""

    # Pipeline defaults
    default_poll_interval_minutes: int = 15
    intent_threshold: float = 0.6

    @property
    def is_dev(self) -> bool:
        return self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
