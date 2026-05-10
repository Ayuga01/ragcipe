"""
LangGraph orchestrator — builds and compiles the multi-agent recipe
generation graph.

Flow:
    START
      ├─ (has image?) → image_analysis → input_parser
      └─ (no image)  → input_parser
    input_parser → recipe_retrieval
    recipe_retrieval
      ├─ (< 3 recipes) → web_search → recipe_generator
      └─ (≥ 3 recipes) → recipe_generator
    recipe_generator
      ├─ (has missing ingredients) → substitute_agent → END
      └─ (no missing)             → END
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.image_analysis import image_analysis_node
from app.agents.nodes.input_parser import input_parser_node
from app.agents.nodes.recipe_generator import recipe_generator_node
from app.agents.nodes.recipe_retrieval import recipe_retrieval_node
from app.agents.nodes.substitute_agent import substitute_agent_node
from app.agents.nodes.web_search import web_search_node
from app.models.schemas import DietaryProfile
from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Conditional edge helpers
# --------------------------------------------------------------------------


def _route_start(state: RecipeGraphState) -> str:
    """Route from START: go to image analysis if image data is present."""
    if state.get("image_data"):
        return "image_analysis"
    return "input_parser"


def _route_after_retrieval(state: RecipeGraphState) -> str:
    """Route after retrieval: supplement with web search if too few
    recipes match the user's requested cuisine / diet."""
    retrieved = state.get("retrieved_recipes") or []
    profile = state.get("dietary_profile") or {}

    # If we have no results at all, always go to web
    if len(retrieved) < 2:
        return "web_search"

    # Check whether the results actually match the user's cuisine request
    cuisines = profile.get("cuisines", ["any"])
    if cuisines and cuisines != ["any"]:
        target_cuisines = {c.lower() for c in cuisines}
        matching = sum(
            1 for r in retrieved
            if r.get("metadata", {}).get("cuisine", "").lower() in target_cuisines
        )
        if matching < 2:
            return "web_search"

    return "recipe_generator"


def _route_after_generation(state: RecipeGraphState) -> str:
    """Route after generation: substitute if there are missing ingredients."""
    missing = state.get("missing_ingredients") or []
    if missing:
        return "substitute_agent"
    return END


# --------------------------------------------------------------------------
# Graph construction
# --------------------------------------------------------------------------


def build_recipe_graph() -> StateGraph:
    """Construct, wire, and return the compiled recipe StateGraph."""
    graph = StateGraph(RecipeGraphState)

    # --- Add nodes ---
    graph.add_node("image_analysis", image_analysis_node)
    graph.add_node("input_parser", input_parser_node)
    graph.add_node("recipe_retrieval", recipe_retrieval_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("recipe_generator", recipe_generator_node)
    graph.add_node("substitute_agent", substitute_agent_node)

    # --- Edges ---
    graph.add_conditional_edges(START, _route_start)
    graph.add_edge("image_analysis", "input_parser")
    graph.add_edge("input_parser", "recipe_retrieval")
    graph.add_conditional_edges("recipe_retrieval", _route_after_retrieval)
    graph.add_edge("web_search", "recipe_generator")
    graph.add_conditional_edges("recipe_generator", _route_after_generation)
    graph.add_edge("substitute_agent", END)

    return graph.compile()


# Compiled graph singleton
recipe_graph = build_recipe_graph()


# --------------------------------------------------------------------------
# Convenience runner
# --------------------------------------------------------------------------


async def run_recipe_graph(
    ingredients: list[str],
    dietary_profile: DietaryProfile | dict | None = None,
    image_data: str | None = None,
) -> dict[str, Any]:
    """High-level helper to invoke the recipe graph.

    Args:
        ingredients: User-provided ingredient list.
        dietary_profile: Dietary preferences (Pydantic model or dict).
        image_data: Optional base64-encoded image.

    Returns:
        The final graph state dict.
    """
    if dietary_profile is None:
        profile_dict = DietaryProfile().model_dump()
    elif isinstance(dietary_profile, DietaryProfile):
        profile_dict = dietary_profile.model_dump()
    else:
        profile_dict = dietary_profile

    initial_state: dict[str, Any] = {
        "messages": [],
        "image_data": image_data,
        "detected_ingredients": [],
        "detected_ingredient_details": [],
        "user_ingredients": ingredients,
        "dietary_profile": profile_dict,
        "retrieved_recipes": [],
        "web_recipes": [],
        "final_recipes": [],
        "missing_ingredients": [],
        "substitutions": [],
        "error": None,
    }

    logger.info("Running recipe graph with %d ingredients.", len(ingredients))
    result = await recipe_graph.ainvoke(initial_state)
    return result
