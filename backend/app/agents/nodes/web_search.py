"""
Web search node — uses Tavily to find recipes on the internet,
then structures the results with the configured OpenAI chat model.
"""

from __future__ import annotations

import json
import logging

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

_STRUCTURE_PROMPT = """You are a recipe data extraction assistant.
Given raw web search results about recipes, extract structured recipe data.

IMPORTANT: Extract as many DISTINCT recipes as possible — aim for at least
5 different recipes. Each web result may contain one or more recipes; extract
them all. If multiple results describe the same dish, keep only the most
detailed version.

Return a JSON array where each recipe has:
- "title": recipe name
- "ingredients": list of ingredient strings (with quantities)
- "instructions": list of step-by-step strings
- "cook_time": estimated cooking time
- "difficulty": "easy", "medium", or "hard"
- "servings": integer
- "cuisine": cuisine type
- "dietary_tags": list of tags like "vegetarian", "gluten-free", etc.
- "source": "web"

If a field cannot be determined from the source, use a reasonable default.
Return ONLY the JSON array, no other text.
"""


def _build_search_query(ingredients: list[str], profile: dict) -> str:
    """Build a rich search query for Tavily."""
    parts = [f"recipe with {', '.join(ingredients[:8])}"]

    diet = profile.get("diet_type", "non-vegetarian")
    if diet != "non-vegetarian":
        parts.append(diet.replace("_", " "))

    cuisines = profile.get("cuisines", ["any"])
    if cuisines and cuisines != ["any"]:
        parts.append(f"{', '.join(cuisines)} cuisine")

    protein = profile.get("protein_preference", "no_preference")
    if protein != "no_preference":
        parts.append(protein.replace("_", " "))

    spice = profile.get("spice_level", "medium")
    if spice not in ("medium", "no_preference"):
        parts.append(f"{spice} spice")

    cooking_time = profile.get("cooking_time", "no_limit")
    if cooking_time != "no_limit":
        parts.append(cooking_time.replace("_", " "))

    return " ".join(parts)


def web_search_node(state: RecipeGraphState) -> dict:
    """Search the web for recipes and structure results via the configured model."""
    ingredients: list[str] = state.get("user_ingredients") or []
    profile: dict = state.get("dietary_profile") or {}

    if not ingredients:
        return {
            "web_recipes": [],
            "messages": [
                HumanMessage(content="No ingredients for web search."),
            ],
        }

    if not settings.TAVILY_API_KEY:
        logger.info("Tavily API key not configured — skipping web search.")
        return {
            "web_recipes": [],
            "messages": [
                HumanMessage(content="Web search skipped because Tavily is not configured."),
            ],
        }

    query = _build_search_query(ingredients, profile)
    logger.info("Tavily search query: %s", query)

    try:
        search_tool = TavilySearchResults(
            max_results=8,
            search_depth="advanced",
            tavily_api_key=settings.TAVILY_API_KEY,
        )
        raw_results = search_tool.invoke(query)

        if not raw_results:
            return {
                "web_recipes": [],
                "messages": [HumanMessage(content="Web search returned no results.")],
            }

        # Use the configured OpenAI chat model to structure the raw results
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
        )

        results_text = "\n\n".join(
            f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', '')}\n"
            f"Content: {r.get('content', '')}"
            for r in raw_results
            if isinstance(r, dict)
        )

        response = llm.invoke(
            [
                SystemMessage(content=_STRUCTURE_PROMPT),
                HumanMessage(
                    content=f"Structure these web results into recipes:\n\n{results_text}"
                ),
            ]
        )

        raw_text = response.content.strip()
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        web_recipes: list[dict] = json.loads(raw_text)
        logger.info("Structured %d web recipes.", len(web_recipes))

        return {
            "web_recipes": web_recipes,
            "messages": [
                HumanMessage(
                    content=f"Found {len(web_recipes)} recipes from web search."
                ),
            ],
        }

    except Exception as exc:
        logger.error("Web search failed: %s", exc, exc_info=True)
        return {
            "web_recipes": [],
            "messages": [HumanMessage(content=f"Web search error: {exc}")],
        }
