"""Drafter: writes a post-specific, helpful reply for human review.

Mock implementation only echoes the post's specifics so reviewers can see the flow.
The real agent must ground every draft in the post content (no reused templates),
per Reddit's "no duplicate content" rule.
"""

from app.agents.context import TenantContext
from app.agents.schemas import DraftReply, IntentClassification
from app.integrations.reddit import RedditPost


class DrafterAgent:
    async def run(
        self, ctx: TenantContext, post: RedditPost, classification: IntentClassification
    ) -> DraftReply:
        needs = classification.needs
        details = ", ".join(
            part for part in [
                f"budget {needs.budget}" if needs.budget else None,
                f"timeline {needs.urgency}" if needs.urgency else None,
            ] if part
        )
        body = (
            f"[MOCK DRAFT - tone: {ctx.tone}]\n"
            f"Re: \"{post.title}\" in r/{post.subreddit}\n"
            f"Would address: {details or 'the specific needs in the post'}; "
            f"relevant offering: {ctx.product_description or ctx.niche or 'n/a'}."
        )
        return DraftReply(body=body)
