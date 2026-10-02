"""Niche Interpreter: turns "I sell refurbished phones" into a starter tenant configuration.

Mock implementation: keyword lookup. Replace `run` with an OpenAI Agents SDK `Agent`
(output_type=NicheConfigSuggestion) when LLM_MODE=openai.
"""

from app.agents.schemas import NicheConfigSuggestion

_PRESETS = {
    "furniture": NicheConfigSuggestion(
        niche="furniture",
        subreddits=["furniture", "HomeImprovement", "malelivingspace", "InteriorDesign"],
        keywords=["looking for a table", "need a sofa", "recommend a chair", "where to buy furniture"],
        personas=["first-time homeowner", "renter furnishing a new apartment"],
    ),
    "phone": NicheConfigSuggestion(
        niche="mobile phones",
        subreddits=["PickAnAndroidForMe", "iphone", "Android", "BuyItForLife"],
        keywords=["budget phone", "which phone should I buy", "phone under $", "refurbished phone"],
        personas=["budget-conscious student", "parent buying a first phone"],
    ),
    "laptop": NicheConfigSuggestion(
        niche="electronics",
        subreddits=["SuggestALaptop", "buildapc", "thinkpad"],
        keywords=["laptop recommendation", "need a laptop for", "refurbished laptop"],
        personas=["university student", "remote worker"],
    ),
}


class NicheInterpreterAgent:
    async def run(self, description: str) -> NicheConfigSuggestion:
        text = description.lower()
        for key, preset in _PRESETS.items():
            if key in text:
                return preset
        return NicheConfigSuggestion(
            niche=description[:100],
            subreddits=[],
            keywords=[f"looking for {w}" for w in text.split()[-2:]],
            personas=[],
        )
