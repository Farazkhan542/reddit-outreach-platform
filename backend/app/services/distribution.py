"""Assigns qualified leads to team members to spread posting volume across accounts."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DistributionStrategy, Lead, LeadAssignment, LeadStatus, RedditAccount, User


async def _eligible_users(db: AsyncSession, org_id: uuid.UUID) -> list[tuple[User, RedditAccount | None]]:
    rows = await db.execute(
        select(User, RedditAccount)
        .outerjoin(RedditAccount, RedditAccount.user_id == User.id)
        .where(User.org_id == org_id, User.is_active.is_(True))
    )
    return [(u, a) for u, a in rows.all() if a is None or a.is_active]


async def assign_lead(
    db: AsyncSession,
    lead: Lead,
    strategy: DistributionStrategy,
    assigned_by_id: uuid.UUID | None = None,
) -> LeadAssignment | None:
    if strategy == DistributionStrategy.manual_claim:
        return None

    candidates = await _eligible_users(db, lead.org_id)
    if not candidates:
        return None

    if strategy == DistributionStrategy.least_recently_active:
        # Accounts that have never acted (or no account yet) go first.
        def last_active(ua: tuple[User, RedditAccount | None]) -> float:
            account = ua[1]
            return account.last_action_at.timestamp() if account and account.last_action_at else 0.0

        user, account = min(candidates, key=last_active)
    else:  # round_robin: fewest current assignments wins
        counts = dict(
            (await db.execute(
                select(LeadAssignment.user_id, func.count())
                .where(LeadAssignment.org_id == lead.org_id)
                .group_by(LeadAssignment.user_id)
            )).all()
        )
        user, account = min(candidates, key=lambda ua: counts.get(ua[0].id, 0))

    return await create_assignment(db, lead, user.id, account.id if account else None, assigned_by_id)


async def create_assignment(
    db: AsyncSession,
    lead: Lead,
    user_id: uuid.UUID,
    reddit_account_id: uuid.UUID | None,
    assigned_by_id: uuid.UUID | None = None,
) -> LeadAssignment:
    existing = await db.scalar(select(LeadAssignment).where(LeadAssignment.lead_id == lead.id))
    if existing:
        existing.user_id = user_id
        existing.reddit_account_id = reddit_account_id
        existing.assigned_by_id = assigned_by_id
        assignment = existing
    else:
        assignment = LeadAssignment(
            org_id=lead.org_id,
            lead_id=lead.id,
            user_id=user_id,
            reddit_account_id=reddit_account_id,
            assigned_by_id=assigned_by_id,
        )
        db.add(assignment)
    lead.status = LeadStatus.assigned
    return assignment
