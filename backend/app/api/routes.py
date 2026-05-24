"""
FastAPI route definitions for the Recipe Generator API.
"""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.graph import run_recipe_graph
from app.agents.nodes.image_analysis import image_analysis_node
from app.agents.nodes.substitute_agent import substitute_agent_node
from app.models.schemas import (
    DetectIngredientsRequest,
    DetectIngredientsResponse,
    GenerateRecipesRequest,
    GenerateRecipesResponse,
    Recipe,
    RecipeChatRequest,
    RecipeChatResponse,
    SubstituteRequest,
    SubstituteResponse,
    SaveRecipeRequest,
    SavedRecipeResponse,
    DeleteRecipeRequest,
)
from app.agents.nodes.recipe_chat import recipe_chat_agent
from app.services.ingestion import IngestionService
from app.services.vectorstore import get_vectorstore_service
from app.services.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recipes"])

# Allowed upload extensions for recipe ingestion
_ALLOWED_EXTENSIONS = {"pdf", "txt", "json", "csv"}


def _ingredient_key(value: str) -> str:
    """Normalise ingredient text for loose matching."""
    return re.sub(r"[^a-z0-9\s]", "", value.lower()).strip()


def _ingredients_match(left: str, right: str) -> bool:
    """Return True when two ingredient descriptions likely refer to the same item."""
    left_key = _ingredient_key(left)
    right_key = _ingredient_key(right)
    if not left_key or not right_key:
        return False
    return left_key == right_key or left_key in right_key or right_key in left_key


def _attach_substitutions_to_recipes(
    recipes: list[dict],
    substitutions: list[dict],
) -> list[dict]:
    """Attach graph-level substitution suggestions to the recipes that need them."""
    if not substitutions:
        return recipes

    for recipe in recipes:
        missing = recipe.get("missing_ingredients") or []
        recipe_substitutions = list(recipe.get("substitutions") or [])
        if not missing:
            recipe["substitutions"] = recipe_substitutions
            continue

        seen = {
            (
                _ingredient_key(str(sub.get("original", ""))),
                _ingredient_key(str(sub.get("substitute", sub.get("name", "")))),
            )
            for sub in recipe_substitutions
        }

        for sub in substitutions:
            original = str(sub.get("original", ""))
            if not any(_ingredients_match(original, item) for item in missing):
                continue

            key = (
                _ingredient_key(original),
                _ingredient_key(str(sub.get("substitute", sub.get("name", "")))),
            )
            if key in seen:
                continue

            recipe_substitutions.append(sub)
            seen.add(key)

        recipe["substitutions"] = recipe_substitutions

    return recipes


# --------------------------------------------------------------------------
# Health & utility
# --------------------------------------------------------------------------


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "recipe-generator"}


@router.get("/collection-stats")
async def collection_stats() -> dict[str, Any]:
    """Return vector store collection statistics."""
    try:
        vs = get_vectorstore_service()
        return vs.get_collection_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# Ingredient detection
# --------------------------------------------------------------------------


@router.post("/detect-ingredients", response_model=DetectIngredientsResponse)
async def detect_ingredients(request: DetectIngredientsRequest):
    """Detect food ingredients from a base64-encoded image."""
    if not request.image_data:
        raise HTTPException(status_code=400, detail="image_data is required.")

    state: dict[str, Any] = {
        "image_data": request.image_data,
        "detected_ingredients": [],
        "messages": [],
    }

    result = image_analysis_node(state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    # Build the response
    ingredients = result.get("detected_ingredients", [])
    ingredient_dicts = result.get("detected_ingredient_details") or [
        {"name": name, "confidence": 0.9} for name in ingredients
    ]

    raw_desc = (
        result["messages"][-1].content
        if result.get("messages")
        else f"Detected: {', '.join(ingredients)}"
    )

    return DetectIngredientsResponse(
        ingredients=ingredient_dicts,
        raw_description=raw_desc,
    )


# --------------------------------------------------------------------------
# Recipe generation
# --------------------------------------------------------------------------


@router.post("/generate-recipes", response_model=GenerateRecipesResponse)
async def generate_recipes(request: GenerateRecipesRequest):
    """Run the full recipe generation pipeline."""
    if not request.ingredients and not request.image_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 'ingredients' or 'image_data'.",
        )

    try:
        result = await run_recipe_graph(
            ingredients=request.ingredients,
            dietary_profile=request.dietary_profile,
            image_data=request.image_data,
        )
    except Exception as exc:
        logger.error("Recipe graph failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    # Convert raw recipe dicts → validated Recipe models
    raw_recipes: list[dict] = result.get("final_recipes") or []
    raw_recipes = _attach_substitutions_to_recipes(
        raw_recipes,
        result.get("substitutions") or [],
    )
    recipes: list[Recipe] = []
    for r in raw_recipes:
        try:
            recipes.append(
                Recipe(
                    title=r.get("title", "Untitled Recipe"),
                    ingredients=r.get("ingredients", []),
                    instructions=r.get("instructions", []),
                    cook_time=r.get("cook_time", "Unknown"),
                    difficulty=r.get("difficulty", "medium"),
                    servings=r.get("servings", 2),
                    source=r.get("source", "generated"),
                    cuisine=r.get("cuisine", ""),
                    dietary_tags=r.get("dietary_tags", []),
                    missing_ingredients=r.get("missing_ingredients", []),
                    substitutions=r.get("substitutions", []),
                )
            )
        except Exception as exc:
            logger.warning("Skipping invalid recipe: %s", exc)

    return GenerateRecipesResponse(
        recipes=recipes,
        detected_ingredients=result.get("detected_ingredients", []),
    )


# --------------------------------------------------------------------------
# Ingredient substitution
# --------------------------------------------------------------------------


@router.post("/suggest-alternatives", response_model=list[SubstituteResponse])
async def suggest_alternatives(request: SubstituteRequest):
    """Suggest substitutions for a recipe's missing ingredients."""
    recipe_dict = request.recipe.model_dump()
    missing = [
        ing
        for ing in recipe_dict.get("ingredients", [])
        if not any(
            avail.lower() in ing.lower() for avail in request.available_ingredients
        )
    ]

    if not missing:
        return []

    state: dict[str, Any] = {
        "missing_ingredients": missing,
        "user_ingredients": request.available_ingredients,
        "dietary_profile": request.dietary_profile.model_dump(),
        "substitutions": [],
        "messages": [],
    }

    result = substitute_agent_node(state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    # Group substitutions by original ingredient
    raw_subs: list[dict] = result.get("substitutions", [])
    grouped: dict[str, list[dict]] = {}
    for sub in raw_subs:
        original = sub.get("original", "unknown")
        grouped.setdefault(original, []).append(
            {
                "name": sub.get("substitute", ""),
                "reason": sub.get("reason", ""),
                "confidence": sub.get("confidence", 0.5),
            }
        )

    return [
        SubstituteResponse(original_ingredient=orig, substitutions=subs)
        for orig, subs in grouped.items()
    ]


# --------------------------------------------------------------------------
# Recipe Chat
# --------------------------------------------------------------------------

@router.post("/recipe-chat", response_model=RecipeChatResponse)
async def recipe_chat(request: RecipeChatRequest):
    """Answer questions about a specific recipe."""
    result = recipe_chat_agent(request)
    
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
        
    return RecipeChatResponse(answer=result.get("answer", ""))


# --------------------------------------------------------------------------
# Recipe ingestion
# --------------------------------------------------------------------------


@router.post("/ingest-recipes")
async def ingest_recipes(file: UploadFile = File(...)):
    """Ingest a recipe file (PDF, TXT, JSON, CSV) into the vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = Path(file.filename).suffix.lstrip(".").lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{extension}. "
            f"Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    try:
        content = await file.read()

        # Write to a temporary file so loaders can read from disk
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{extension}",
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        service = IngestionService()
        chunks_added = service.ingest_file(tmp_path, extension)

        # Clean up
        Path(tmp_path).unlink(missing_ok=True)

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_added": chunks_added,
        }

    except Exception as exc:
        logger.error("Ingestion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# Saved Recipes (Supabase Relational)
# --------------------------------------------------------------------------

@router.post("/recipes/save", response_model=SavedRecipeResponse)
async def save_recipe(request: SaveRecipeRequest):
    """Save a recipe for a user session."""
    try:
        db = get_database_service()
        data = db.save_recipe(request.session_id, request.recipe.model_dump())
        if not data:
            raise HTTPException(status_code=500, detail="Failed to save recipe")
        return SavedRecipeResponse(**data)
    except Exception as exc:
        logger.error("Error saving recipe: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/recipes/saved", response_model=list[SavedRecipeResponse])
async def get_saved_recipes(session_id: str):
    """Get all saved recipes for a user session."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        db = get_database_service()
        records = db.get_saved_recipes(session_id)
        return [SavedRecipeResponse(**r) for r in records]
    except Exception as exc:
        logger.error("Error fetching saved recipes: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/recipes/delete")
async def delete_saved_recipe(request: DeleteRecipeRequest):
    """Delete a saved recipe."""
    try:
        db = get_database_service()
        success = db.delete_recipe(request.session_id, request.recipe_id)
        if not success:
            raise HTTPException(status_code=404, detail="Recipe not found or permission denied")
        return {"status": "success"}
    except Exception as exc:
        logger.error("Error deleting recipe: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
