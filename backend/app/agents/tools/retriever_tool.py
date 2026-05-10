"""
LangChain retriever tool — wraps the vectorstore retriever as a
LangChain-compatible tool for use in agent chains.
"""

from __future__ import annotations

from langchain_core.tools.retriever import create_retriever_tool

from app.services.vectorstore import get_vectorstore_service


def get_retriever_tool():
    """Create and return a LangChain retriever tool for recipe search.

    The tool is configured with a description that helps the LLM
    understand when and how to use it.
    """
    vs = get_vectorstore_service()
    retriever = vs.get_retriever(k=5)

    return create_retriever_tool(
        retriever=retriever,
        name="recipe_book_search",
        description=(
            "Search through the recipe book knowledge base. "
            "Use this tool to find recipes matching specific ingredients, "
            "cuisines, dietary restrictions, or cooking styles. "
            "Input should be a natural language query describing what "
            "kind of recipe you're looking for."
        ),
    )
