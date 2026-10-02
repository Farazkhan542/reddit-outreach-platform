"""Classifier: scores a post for genuine buying intent and extracts needs.

Mock implementation: phrase heuristics. Swap for an LLM agent with
output_type=IntentClassification when LLM_MODE=openai.
"""

import re

from app.agents.context import TenantContext
from app.agents.schemas import ExtractedNeeds, IntentClassification
from app.integrations.reddit import RedditPost

_INTENT_PHRASES = [
    "looking for", "need a", "recommend", "recommendations", "which", "should i buy",
    "budget", "where to buy", "worth buying", "under $",
]
_URGENCY_PHRASES = ["this week", "asap", "urgent", "next month", "today"]


class ClassifierAgent:
    async def run(self, ctx: TenantContext, post: RedditPost) -> IntentClassification:
        text = f"{post.title or ''} {post.body}".lower()

        hits = [p for p in _INTENT_PHRASES if p in text]
        keyword_hits = [k for k in ctx.keywords if k.lower() in text]
        score = min(1.0, 0.2 * len(hits) + 0.3 * len(keyword_hits))

        budget = re.search(r"\$\s?\d[\d,]*", text)
        urgency = next((p for p in _URGENCY_PHRASES if p in text), None)

        return IntentClassification(
            intent_score=round(score, 2),
            reasoning=f"[mock] intent phrases={hits} keyword matches={keyword_hits}",
            needs=ExtractedNeeds(
                budget=budget.group(0) if budget else None,
                urgency=urgency,
            ),
        )