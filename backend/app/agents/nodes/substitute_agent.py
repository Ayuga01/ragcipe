"""
Substitute agent node — suggests ingredient substitutions for any
missing ingredients, respecting the user's dietary profile.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a professional chef specializing in ingredient substitutions.

Given:
1. Missing ingredients that a recipe requires but the user does not have
2. The user's available ingredients
3. The user's dietary profile (allergies, intolerances, diet type, etc.)

Suggest practical substitutions for each missing ingredient.

IMPORTANT rules:
- NEVER suggest an ingredient the user is allergic to
- NEVER suggest an ingredient that violates their intolerances
- NEVER suggest an ingredient that violates their diet type
  (e.g. no meat for vegetarians, no dairy for vegans)
- Prefer substitutions from the user's available ingredients
- Provide a clear reason why the substitution works

Return a JSON array where each object has:
- "original": the missing ingredient name
- "substitute": the suggested replacement
- "reason": why this substitution works
- "confidence": float 0-1 indicating how good the substitution is

Return ONLY the JSON array. No other text.
"""


def substitute_agent_node(state: RecipeGraphState) -> dict:
    """Suggest dietary-aware substitutions for missing ingredients."""
    missing: list[str] = state.get("missing_ingredients") or []
    ingredients: list[str] = state.get("user_ingredients") or []
    profile: dict = state.get("dietary_profile") or {}

    if not missing:
        logger.info("No missing ingredients — skipping substitution.")
        return {
            "substitutions": [],
            "messages": [
                HumanMessage(content="No missing ingredients — no substitutions needed."),
            ],
        }

    context = (
        f"Missing ingredients: {', '.join(missing)}\n\n"
        f"User's available ingredients: {', '.join(ingredients)}\n\n"
        f"Dietary profile:\n{json.dumps(profile, indent=2)}"
    )

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )

        response = llm.invoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=context),
            ]
        )

        raw_text = response.content.strip()
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        substitutions: list[dict] = json.loads(raw_text)
        logger.info("Generated %d substitution suggestions.", len(substitutions))

        return {
            "substitutions": substitutions,
            "messages": [
                HumanMessage(
                    content=f"Suggested {len(substitutions)} ingredient substitutions."
                ),
            ],
        }

    except Exception as exc:
        logger.error("Substitution agent failed: %s", exc, exc_info=True)
        return {
            "substitutions": [],
            "error": f"Substitution failed: {exc}",
            "messages": [HumanMessage(content=f"Substitution error: {exc}")],
        }
