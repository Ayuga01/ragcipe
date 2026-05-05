"""
LangGraph state definition for the recipe generation graph.

Uses TypedDict with the ``add_messages`` annotation so that
LangGraph automatically merges message lists across nodes.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class RecipeGraphState(TypedDict):
    """Shared state flowing through every node in the recipe graph."""

    # Accumulated LLM conversation messages
    messages: Annotated[list[BaseMessage], add_messages]

    # Raw base64-encoded image (None when text-only flow)
    image_data: str | None

    # Ingredients detected from the image
    detected_ingredients: list[str]

    # Detailed detections with confidence scores
    detected_ingredient_details: list[dict]

    # Ingredients explicitly provided by the user
    user_ingredients: list[str]

    # User dietary preferences serialised as dict
    dietary_profile: dict

    # Recipes retrieved from the ChromaDB vector store
    retrieved_recipes: list[dict]

    # Recipes found via Tavily web search
    web_recipes: list[dict]

    # Final curated / generated recipes
    final_recipes: list[dict]

    # Ingredients required by recipes but missing from user's list
    missing_ingredients: list[str]

    # Suggested substitutions for missing ingredients
    substitutions: list[dict]

    # Error message (None when everything is fine)
    error: str | None
