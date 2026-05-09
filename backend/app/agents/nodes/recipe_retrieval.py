"""
Recipe retrieval node — queries the ChromaDB vector store using
**hybrid retrieval** (BM25 keyword search + dense semantic search)
for recipes matching the user's ingredients and dietary profile.

Applies strict post-retrieval filtering:
  1. Cuisine must match (if the user selected one).
  2. No more than 4 recipe ingredients may be missing from the user's
     available set.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage

from app.models.state import RecipeGraphState
from app.services.vectorstore import get_vectorstore_service

logger = logging.getLogger(__name__)


# ── Metadata filter builders ────────────────────────────────────────


def _build_metadata_filter(profile: dict) -> dict | None:
    """Build a ChromaDB ``where`` filter from the dietary profile.

    Returns ``None`` when no meaningful filter can be constructed so
    the retriever falls back to pure semantic search.
    """
    conditions: list[dict] = []

    diet_type = profile.get("diet_type", "non-vegetarian")
    if diet_type and diet_type != "non-vegetarian":
        conditions.append({"diet_type": {"$eq": diet_type}})

    cuisines = profile.get("cuisines", ["any"])
    if cuisines and cuisines != ["any"]:
        lowered = [c.lower() for c in cuisines]
        if len(lowered) == 1:
            conditions.append({"cuisine": {"$eq": lowered[0]}})
        else:
            conditions.append({"cuisine": {"$in": lowered}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _build_search_query(ingredients: list[str], profile: dict) -> str:
    """Construct a natural-language search query for the retriever."""
    parts = [f"Recipe using: {', '.join(ingredients)}"]

    diet = profile.get("diet_type", "non-vegetarian")
    if diet != "non-vegetarian":
        parts.append(f"Diet: {diet}")

    cuisines = profile.get("cuisines", ["any"])
    if cuisines and cuisines != ["any"]:
        parts.append(f"Cuisine: {', '.join(cuisines)}")

    if profile.get("cooking_time", "no_limit") != "no_limit":
        parts.append(f"Time: {profile['cooking_time']}")

    return ". ".join(parts)


# ── Post-retrieval filters ──────────────────────────────────────────

_INGREDIENT_LINE_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)

# Common filler words / quantities to strip when comparing ingredients
_STRIP_WORDS = {
    "cup", "cups", "tablespoon", "tablespoons", "teaspoon", "teaspoons",
    "grams", "gram", "kg", "ml", "liter", "liters", "ounce", "ounces",
    "pound", "pounds", "pinch", "cloves", "clove", "sliced", "chopped",
    "diced", "minced", "cubed", "cooked", "fresh", "dried", "ground",
    "optional", "to", "taste", "and", "or", "of", "a", "an", "the",
    "small", "medium", "large", "whole", "half",
}


def _normalise_ingredient(text: str) -> str:
    """Extract the core ingredient name from a line like '2 cups chickpeas'."""
    text = text.lower().strip()
    # Remove leading quantities (digits, fractions, decimals)
    text = re.sub(r"^[\d\s/.\-½¼¾⅓⅔]+", "", text).strip()
    # Remove parenthetical notes
    text = re.sub(r"\(.*?\)", "", text).strip()
    # Remove trailing commas and filler words
    words = [w.strip(",") for w in text.split() if w.strip(",") not in _STRIP_WORDS]
    return " ".join(words).strip()


def _extract_recipe_ingredients(content: str) -> list[str]:
    """Extract normalised ingredient names from recipe text content."""
    matches = _INGREDIENT_LINE_RE.findall(content)
    return [_normalise_ingredient(m) for m in matches if _normalise_ingredient(m)]


def _count_missing_ingredients(
    recipe_ingredients: list[str],
    user_ingredients: set[str],
) -> int:
    """Count how many recipe ingredients are NOT in the user's available set.

    Uses fuzzy substring matching: a recipe ingredient is considered
    "available" if any user ingredient appears as a substring (or vice
    versa).
    """
    missing = 0
    for ri in recipe_ingredients:
        found = any(
            ui in ri or ri in ui
            for ui in user_ingredients
        )
        if not found:
            missing += 1
    return missing


def _cuisine_matches(
    recipe_meta: dict,
    target_cuisines: set[str] | None,
) -> bool:
    """Return True if the recipe's cuisine matches the user's selection."""
    if not target_cuisines:
        return True
    recipe_cuisine = (recipe_meta.get("cuisine") or "").lower()
    return recipe_cuisine in target_cuisines


def _apply_strict_filters(
    recipes: list[dict],
    user_ingredients: list[str],
    profile: dict,
    max_missing: int = 4,
) -> list[dict]:
    """Apply strict post-retrieval filters.

    Removes recipes that:
    1. Don't match the user's selected cuisine (if any).
    2. Have more than ``max_missing`` ingredients not in the user's set.
    """
    cuisines = profile.get("cuisines", ["any"])
    target_cuisines: set[str] | None = None
    if cuisines and cuisines != ["any"]:
        target_cuisines = {c.lower() for c in cuisines}

    user_set = {_normalise_ingredient(i) for i in user_ingredients}

    kept: list[dict] = []
    for recipe in recipes:
        meta = recipe.get("metadata", {})
        content = recipe.get("content", "")

        # ── Filter 1: cuisine must match ──
        if not _cuisine_matches(meta, target_cuisines):
            recipe_cuisine = meta.get("cuisine", "unknown")
            logger.debug(
                "Filtered out recipe (cuisine mismatch): %s ≠ %s",
                recipe_cuisine,
                target_cuisines,
            )
            continue

        # ── Filter 2: ingredient overlap ──
        recipe_ingredients = _extract_recipe_ingredients(content)
        if recipe_ingredients:
            missing = _count_missing_ingredients(recipe_ingredients, user_set)
            if missing > max_missing:
                logger.debug(
                    "Filtered out recipe (%d missing ingredients > %d max): %s",
                    missing,
                    max_missing,
                    content[:80],
                )
                continue

        kept.append(recipe)

    logger.info(
        "Strict post-filter: %d → %d recipes "
        "(cuisine=%s, max_missing=%d, user_ingredients=%d)",
        len(recipes),
        len(kept),
        target_cuisines or "any",
        max_missing,
        len(user_set),
    )
    return kept


# ── Main node ───────────────────────────────────────────────────────


def recipe_retrieval_node(state: RecipeGraphState) -> dict:
    """Retrieve matching recipes from the vector store using hybrid search.

    Strategy:
    1. Run hybrid retrieval (BM25 + semantic) — try filtered first,
       then unfiltered if nothing comes back.
    2. Apply **strict post-retrieval filters**: cuisine match +
       ingredient overlap (≤ 4 missing).
    3. Return only recipes that pass both filters; the downstream
       router will decide whether to supplement via web search.
    """
    ingredients: list[str] = state.get("user_ingredients") or []
    profile: dict = state.get("dietary_profile") or {}

    if not ingredients:
        logger.warning("recipe_retrieval_node: no ingredients to search for.")
        return {
            "retrieved_recipes": [],
            "messages": [
                HumanMessage(content="No ingredients available for retrieval."),
            ],
        }

    vs = get_vectorstore_service()
    query = _build_search_query(ingredients, profile)
    metadata_filter = _build_metadata_filter(profile)

    # Retrieve a larger candidate set so post-filtering has room to work
    retrieve_k = 10
    docs = []

    # ── Pass 1: filtered hybrid retrieval ──
    if metadata_filter:
        try:
            retriever = vs.get_hybrid_retriever(
                k=retrieve_k,
                filters=metadata_filter,
                semantic_weight=0.5,
                bm25_weight=0.5,
            )
            docs = retriever.invoke(query)
            logger.info(
                "Filtered hybrid retrieval returned %d candidates.", len(docs)
            )
        except Exception:
            logger.info("Filtered hybrid retrieval failed.")
            docs = []

    # ── Pass 2: unfiltered hybrid retrieval (fallback) ──
    if not docs:
        try:
            retriever = vs.get_hybrid_retriever(k=retrieve_k)
            docs = retriever.invoke(query)
            logger.info(
                "Unfiltered hybrid retrieval returned %d candidates.", len(docs)
            )
        except Exception:
            logger.info(
                "Hybrid retrieval failed — falling back to pure semantic."
            )
            retriever = vs.get_retriever(k=retrieve_k)
            docs = retriever.invoke(query)

    # Convert to recipe dicts
    raw_recipes: list[dict] = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "source": "recipe_book",
        }
        for doc in docs
    ]

    # ── Strict post-retrieval filtering ──
    filtered_recipes = _apply_strict_filters(
        raw_recipes,
        ingredients,
        profile,
        max_missing=4,
    )

    logger.info(
        "Final retrieval: %d / %d recipes passed strict filters. "
        "Filter: %s",
        len(filtered_recipes),
        len(raw_recipes),
        metadata_filter,
    )

    return {
        "retrieved_recipes": filtered_recipes,
        "messages": [
            HumanMessage(
                content=f"Retrieved {len(filtered_recipes)} recipes from the "
                f"knowledge base after strict filtering "
                f"(cuisine + ingredient overlap)."
            ),
        ],
    }
