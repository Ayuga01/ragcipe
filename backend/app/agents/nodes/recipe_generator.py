"""Recipe generator node.

Uses the configured OpenAI chat model to synthesise and polish a final set of
recipes from retrieved + web results, respecting the user's ingredients and
dietary profile.

Applies hard post-generation filtering so that ONLY recipes matching the
user's selected cuisines are returned.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a world-class chef and recipe curator.

Given:
1. A set of retrieved recipes from a recipe book knowledge base
2. Recipes found on the web
3. The user's available ingredients
4. The user's dietary profile (diet type, allergies, preferences, etc.)

CRITICAL CUISINE RULE:
- Look at the "cuisines" field in the dietary profile.
- If the user selected specific cuisines, you MUST ONLY output recipes that
  belong to those exact cuisines. Do NOT include recipes from any other
  cuisine — not even if they appear in the provided context.
- If a recipe from the context does not belong to the user's selected
  cuisines, SKIP it entirely.
- If cuisines is ["any"], you may include recipes from any cuisine.

RECIPE COUNT RULE:
- Include ALL recipes from the context that match the user's cuisine and
  dietary requirements. Do NOT arbitrarily drop or skip matching recipes.
- Aim to output at least 4-6 recipes. Include every valid recipe available.

Your job is to format and polish ONLY the recipes provided to you in the context
that match the user's selected cuisines.
DO NOT invent or generate any recipes that are not present in the provided context.
For the provided recipes, you must:
- Adapt them to primarily use the user's available ingredients where possible
- Ensure they respect ALL dietary restrictions (allergies, intolerances, diet type)
- Tune them to match the user's preferences (spice level, cooking time)
- Output them clearly structured and easy to follow

For each recipe, output a JSON object with:
- "title": string
- "ingredients": list of ingredient strings (with quantities)
- "instructions": list of step-by-step strings
- "cook_time": string (e.g. "30 minutes")
- "difficulty": "easy" | "medium" | "hard"
- "servings": integer
- "cuisine": string (MUST be one of the user's selected cuisines)
- "dietary_tags": list of strings (e.g. ["vegetarian", "gluten-free"])
- "source": "recipe book" | "web" (Use "recipe book" if from the retrieved knowledge base, and "web" if from web search results)
- "missing_ingredients": list of ingredients required but NOT in the user's available set

Return ONLY a JSON array of recipe objects. No other text.
"""


def _filter_by_cuisine(
    recipes: list[dict],
    profile: dict,
) -> list[dict]:
    """Hard post-generation filter: drop any recipe whose cuisine
    doesn't match the user's selected cuisines.

    Uses **substring matching** so that LLM outputs like
    "Classic French", "Korean BBQ", or "Mexican-inspired" still match
    the user's selection of "french", "korean", or "mexican".
    """
    cuisines = profile.get("cuisines", ["any"])
    if not cuisines or cuisines == ["any"]:
        return recipes

    allowed = [c.lower().strip() for c in cuisines]

    kept: list[dict] = []
    for recipe in recipes:
        recipe_cuisine = (recipe.get("cuisine") or "").lower().strip()
        # Match if ANY allowed cuisine appears as a substring of the
        # recipe cuisine, or vice versa.
        match = any(
            a in recipe_cuisine or recipe_cuisine in a
            for a in allowed
        )
        if match:
            kept.append(recipe)
        else:
            logger.info(
                "Post-filter dropped recipe '%s' (cuisine '%s' not in %s)",
                recipe.get("title", "?"),
                recipe_cuisine,
                allowed,
            )

    return kept


def recipe_generator_node(state: RecipeGraphState) -> dict:
    """Generate polished final recipes from all available sources."""
    ingredients: list[str] = state.get("user_ingredients") or []
    profile: dict = state.get("dietary_profile") or {}
    retrieved: list[dict] = state.get("retrieved_recipes") or []
    web: list[dict] = state.get("web_recipes") or []

    # Build context for the LLM
    context_parts: list[str] = []

    context_parts.append(f"Available ingredients: {', '.join(ingredients)}")
    context_parts.append(f"Dietary profile: {json.dumps(profile, indent=2)}")

    # Explicitly remind the LLM about cuisine restriction
    cuisines = profile.get("cuisines", ["any"])
    if cuisines and cuisines != ["any"]:
        context_parts.append(
            f"⚠️ IMPORTANT: The user ONLY wants recipes from these cuisines: "
            f"{', '.join(cuisines)}. Do NOT include recipes from any other cuisine."
        )

    if retrieved:
        context_parts.append("--- Retrieved recipes from knowledge base ---")
        for i, r in enumerate(retrieved, 1):
            content = r.get("content", str(r))
            context_parts.append(f"[Book Recipe {i}]\n{content}")

    if web:
        context_parts.append("--- Recipes from web search ---")
        for i, r in enumerate(web, 1):
            context_parts.append(f"[Web Recipe {i}]\n{json.dumps(r, indent=2)}")

    if not retrieved and not web:
        logger.info("No recipes found in DB or Web. Aborting generation as per user preference.")
        return {
            "final_recipes": [],
            "missing_ingredients": [],
            "error": "No related recipes found in the database or via web search.",
            "messages": [HumanMessage(content="No related recipes found.")],
        }

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
        )

        response = llm.invoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content="\n\n".join(context_parts)),
            ]
        )

        raw_text = response.content.strip()
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        final_recipes: list[dict] = json.loads(raw_text)

        # ── Hard post-generation cuisine filter ──
        final_recipes = _filter_by_cuisine(final_recipes, profile)

        # Collect all missing ingredients across recipes
        all_missing: list[str] = []
        available_set = {ing.lower().strip() for ing in ingredients}
        for recipe in final_recipes:
            recipe_missing = recipe.get("missing_ingredients", [])
            if not recipe_missing:
                # Auto-detect missing ingredients
                recipe_missing = [
                    ing
                    for ing in recipe.get("ingredients", [])
                    if not any(avail in ing.lower() for avail in available_set)
                ]
                recipe["missing_ingredients"] = recipe_missing
            all_missing.extend(recipe_missing)

        # Deduplicate
        unique_missing = list(dict.fromkeys(all_missing))

        logger.info(
            "Generated %d recipes with %d missing ingredients.",
            len(final_recipes),
            len(unique_missing),
        )

        return {
            "final_recipes": final_recipes,
            "missing_ingredients": unique_missing,
            "messages": [
                HumanMessage(
                    content=(
                        f"Generated {len(final_recipes)} recipes. "
                        f"Missing ingredients: {', '.join(unique_missing) or 'none'}"
                    )
                ),
            ],
        }

    except Exception as exc:
        logger.error("Recipe generation failed: %s", exc, exc_info=True)
        return {
            "final_recipes": [],
            "missing_ingredients": [],
            "error": f"Recipe generation failed: {exc}",
            "messages": [HumanMessage(content=f"Recipe generation error: {exc}")],
        }
