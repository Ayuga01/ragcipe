"""
Input parser node — normalises, deduplicates, and merges ingredient
lists from both image detection and explicit user input.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage

from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

# Simple irregular plurals for basic singularisation
_IRREGULAR: dict[str, str] = {
    "tomatoes": "tomato",
    "potatoes": "potato",
    "cherries": "cherry",
    "berries": "berry",
    "strawberries": "strawberry",
    "blueberries": "blueberry",
    "raspberries": "raspberry",
    "mangoes": "mango",
    "leaves": "leaf",
    "loaves": "loaf",
    "halves": "half",
    "knives": "knife",
}


def _singularise(word: str) -> str:
    """Naive English singularisation good enough for ingredient names."""
    w = word.lower().strip()
    if w in _IRREGULAR:
        return _IRREGULAR[w]
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ves"):
        return w[:-3] + "f"
    if w.endswith("ses") or w.endswith("xes") or w.endswith("zes"):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _normalise(name: str) -> str:
    """Lowercase, strip whitespace / punctuation, and singularise."""
    cleaned = re.sub(r"[^a-z\s]", "", name.lower().strip())
    cleaned = " ".join(cleaned.split())  # collapse whitespace
    return _singularise(cleaned)


def input_parser_node(state: RecipeGraphState) -> dict:
    """Merge detected + user ingredients, apply dietary filters.

    Returns a state update with a deduplicated ``user_ingredients``
    list and an informational message.
    """
    detected: list[str] = state.get("detected_ingredients") or []
    user: list[str] = state.get("user_ingredients") or []
    profile: dict = state.get("dietary_profile") or {}

    # Normalise everything
    normalised: set[str] = set()
    for item in detected + user:
        normed = _normalise(item)
        if normed:
            normalised.add(normed)

    # Remove disliked ingredients
    disliked = {_normalise(d) for d in profile.get("disliked_ingredients", []) if d}
    filtered = sorted(normalised - disliked)

    logger.info(
        "InputParser: %d detected + %d user → %d merged (%d disliked removed).",
        len(detected),
        len(user),
        len(filtered),
        len(normalised) - len(filtered),
    )

    return {
        "user_ingredients": filtered,
        "messages": [
            HumanMessage(
                content=(
                    f"Merged ingredients ({len(filtered)}): {', '.join(filtered)}"
                )
            ),
        ],
    }
