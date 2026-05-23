"""Recipe chat agent.

Handles user questions about a specific recipe.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.schemas import RecipeChatRequest

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are ChefAI, an expert culinary assistant.
You are helping the user with a specific recipe.

Here are the details of the recipe:
Title: {title}
Cuisine: {cuisine}
Cook Time: {cook_time}
Difficulty: {difficulty}
Servings: {servings}

Ingredients:
{ingredients}

Instructions:
{instructions}

Dietary Tags: {dietary_tags}

Your job is to answer the user's questions regarding this recipe.
- Keep your answers concise, helpful, and directly related to the recipe.
- If the user asks for a substitution, suggest a suitable one based on culinary best practices.
- If the user asks for clarification on a step, explain it clearly.
- Do not provide a completely different recipe unless explicitly asked.
"""


def recipe_chat_agent(request: RecipeChatRequest) -> dict[str, Any]:
    """Process a user question about a specific recipe."""
    recipe = request.recipe
    
    ingredients_text = "\n".join(f"- {ing}" for ing in recipe.ingredients)
    instructions_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(recipe.instructions))
    dietary_tags_text = ", ".join(recipe.dietary_tags) if recipe.dietary_tags else "None"

    system_content = _SYSTEM_PROMPT.format(
        title=recipe.title,
        cuisine=recipe.cuisine or "Not specified",
        cook_time=recipe.cook_time,
        difficulty=recipe.difficulty,
        servings=recipe.servings,
        ingredients=ingredients_text,
        instructions=instructions_text,
        dietary_tags=dietary_tags_text,
    )

    messages = [SystemMessage(content=system_content)]

    # Add chat history
    for msg in request.chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))

    # Add the current question
    messages.append(HumanMessage(content=request.question))

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
        )
        response = llm.invoke(messages)
        return {"answer": response.content}
    except Exception as exc:
        logger.error("Recipe chat failed: %s", exc, exc_info=True)
        return {"error": f"Recipe chat failed: {exc}"}
