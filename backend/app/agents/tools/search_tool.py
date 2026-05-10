"""
Tavily web search tool configuration.
"""

from __future__ import annotations

from langchain_community.tools.tavily_search import TavilySearchResults

from app.config import settings


def get_search_tool(
    max_results: int = 5,
    search_depth: str = "advanced",
) -> TavilySearchResults:
    """Create and return a configured Tavily search tool.

    Args:
        max_results: Maximum number of search results to return.
        search_depth: ``"basic"`` or ``"advanced"``.

    Returns:
        A ready-to-use TavilySearchResults instance.
    """
    return TavilySearchResults(
        max_results=max_results,
        search_depth=search_depth,
        tavily_api_key=settings.TAVILY_API_KEY,
    )
