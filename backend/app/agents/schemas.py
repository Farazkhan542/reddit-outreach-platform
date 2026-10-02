"""Structured outputs for each agent. These become `output_type`s when moving to the OpenAI Agents SDK."""

from pydantic import BaseModel, Field


class NicheConfigSuggestion(BaseModel):
    niche: str
    subreddits: list[str]
    keywords: list[str]
    personas: list[str]


class ExtractedNeeds(BaseModel):
    budget: str | None = None
    urgency: str | None = None
    location: str | None = None
    requirements: list[str] = Field(default_factory=list)


class IntentClassification(BaseModel):
    intent_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    needs: ExtractedNeeds


class DraftReply(BaseModel):
    body: str  # a public comment draft; a person posts it manually if they approve it
