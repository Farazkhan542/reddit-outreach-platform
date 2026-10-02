"""Sends an approved reply from the assigned member's Reddit account."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decrypt_token
from app.integrations.reddit import get_reddit_client
from app.models import Lead, LeadAssignment, LeadStatus, RedditAccount, Reply, ReplyKind, ReplyStatus


class SendError(Exception):
    pass


async def send_reply(db: AsyncSession, reply: Reply) -> Reply:
    if reply.status != ReplyStatus.approved:
        raise SendError("only approved replies can be sent")

    lead = await db.get(Lead, reply.lead_id)
    assignment = await db.scalar(select(LeadAssignment).where(LeadAssignment.lead_id == reply.lead_id))
    account = await db.get(RedditAccount, assignment.reddit_account_id) if assignment and assignment.reddit_account_id else None

    if account and account.access_token_enc:
        token = decrypt_token(account.access_token_enc)
    elif get_settings().reddit_mode == "mock":
        token = "mock-token"
    else:
        raise SendError("assigned member has no connected Reddit account")

    client = get_reddit_client()
    body = reply.final_body or reply.draft_body
    try:
        if reply.kind == ReplyKind.dm:
            result = await client.send_dm(token, lead.author, lead.title or "Re: your post", body)
        else:
            result = await client.post_comment(token, lead.reddit_fullname, body)
    except Exception as exc:  # noqa: BLE001 - surface any client failure on the reply
        reply.status = ReplyStatus.failed
        reply.error = str(exc)
        await db.commit()
        raise SendError(str(exc)) from exc

    now = datetime.now(timezone.utc)
    reply.status = ReplyStatus.sent
    reply.sent_at = now
    reply.reddit_thing_id = result.thing_id
    reply.sent_from_account_id = account.id if account else None
    lead.status = LeadStatus.contacted
    if account:
        account.last_action_at = now
    await db.commit()
    return reply
