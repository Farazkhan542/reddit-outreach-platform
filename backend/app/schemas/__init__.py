import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import DistributionStrategy, LeadStatus, ReplyStatus, Role


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth / org ----
class DevLoginIn(BaseModel):
    email: EmailStr
    org_name: str | None = None  # creates a new org (as owner) if the email is new


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    display_name: str | None
    role: Role
    is_active: bool


class InviteIn(BaseModel):
    email: EmailStr
    role: Role = Role.member


class OrgOut(ORM):
    id: uuid.UUID
    name: str


class RedditAccountOut(ORM):
    id: uuid.UUID
    user_id: uuid.UUID
    reddit_username: str
    karma: int
    removal_rate: float
    last_action_at: datetime | None
    is_active: bool


# ---- Tenant config ----
class TenantConfigBase(BaseModel):
    niche: str = ""
    product_description: str = ""
    subreddits: list[str] = []
    keywords: list[str] = []
    personas: list[str] = []
    tone: str = "friendly, helpful, not salesy"
    distribution_strategy: DistributionStrategy = DistributionStrategy.round_robin
    intent_threshold: float = 0.6
    poll_interval_minutes: int = 15
    is_live: bool = False


class TenantConfigOut(TenantConfigBase, ORM):
    id: uuid.UUID
    org_id: uuid.UUID


class InterpretIn(BaseModel):
    description: str


class SubredditRuleIn(BaseModel):
    subreddit: str
    allows_commercial_replies: bool = False
    notes: str | None = None


class SubredditRuleOut(SubredditRuleIn, ORM):
    id: uuid.UUID


# ---- Leads / replies ----
class LeadOut(ORM):
    id: uuid.UUID
    reddit_fullname: str
    subreddit: str
    author: str
    title: str | None
    body: str
    permalink: str
    posted_at: datetime | None
    intent_score: float | None
    intent_reasoning: str | None
    extracted_needs: dict
    status: LeadStatus
    created_at: datetime


class AssignIn(BaseModel):
    user_id: uuid.UUID


class ReplyOut(ORM):
    id: uuid.UUID
    lead_id: uuid.UUID
    draft_body: str
    final_body: str | None
    status: ReplyStatus
    approved_by_id: uuid.UUID | None
    approved_at: datetime | None
    posted_at: datetime | None
    posted_url: str | None
    created_at: datetime


class ReplyEditIn(BaseModel):
    final_body: str


class MarkPostedIn(BaseModel):
    posted_url: str | None = None  # link to the comment the reviewer posted, if they have it


class AnalyticsOut(BaseModel):
    leads_total: int
    leads_qualified: int
    replies_pending: int
    replies_posted: int
    approval_rate: float | None
