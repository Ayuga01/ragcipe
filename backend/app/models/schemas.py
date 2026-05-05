"""
Pydantic request / response schemas for the Recipe Generator API.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Dietary profile — user's food preferences & restrictions
# ---------------------------------------------------------------------------

class DietaryProfile(BaseModel):
    """Comprehensive dietary preference object sent with every recipe request."""

    diet_type: Literal[
        "vegetarian", "vegan", "eggetarian",
        "pescatarian", "non-vegetarian", "flexitarian",
    ] = "non-vegetarian"

    cuisines: list[str] = Field(default_factory=lambda: ["any"])

    protein_preference: Literal[
        "high_protein", "moderate", "low_protein", "no_preference",
    ] = "no_preference"

    calorie_preference: Literal[
        "low_calorie", "moderate", "high_calorie", "no_preference",
    ] = "no_preference"

    carb_preference: Literal[
        "low_carb", "keto", "moderate", "no_preference",
    ] = "no_preference"

    spice_level: Literal[
        "no_spice", "mild", "medium", "spicy", "extra_spicy",
    ] = "medium"

    sweetness: Literal[
        "savory_only", "slightly_sweet", "moderate", "sweet", "dessert",
    ] = "moderate"

    allergies: list[str] = Field(default_factory=lambda: ["none"])
    intolerances: list[str] = Field(default_factory=lambda: ["none"])
    religious_restrictions: list[str] = Field(default_factory=lambda: ["none"])

    cooking_time: Literal[
        "under_15_min", "under_30_min", "under_60_min", "no_limit",
    ] = "no_limit"

    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    serving_size: int = 2
    disliked_ingredients: list[str] = Field(default_factory=list)
    additional_notes: str = ""


# ---------------------------------------------------------------------------
# Ingredient detection (image → ingredients)
# ---------------------------------------------------------------------------

class DetectIngredientsRequest(BaseModel):
    """Image for ingredient detection as base64 or a data URL."""
    image_data: str


class DetectIngredientsResponse(BaseModel):
    """Detected ingredients with confidence scores."""
    ingredients: list[dict]  # [{"name": str, "confidence": float}, ...]
    raw_description: str


# ---------------------------------------------------------------------------
# Recipe generation
# ---------------------------------------------------------------------------

class GenerateRecipesRequest(BaseModel):
    """Input for the full recipe generation pipeline."""
    ingredients: list[str] = Field(default_factory=list)
    dietary_profile: DietaryProfile = Field(default_factory=DietaryProfile)
    image_data: str | None = None


class Recipe(BaseModel):
    """A single recipe returned by the system."""
    title: str
    ingredients: list[str]
    instructions: list[str]
    cook_time: str
    difficulty: str
    servings: int
    source: Literal["recipe book", "web"]
    cuisine: str = ""
    dietary_tags: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)
    substitutions: list[dict] = Field(default_factory=list)


class GenerateRecipesResponse(BaseModel):
    """Full response containing generated recipes and detected ingredients."""
    recipes: list[Recipe]
    detected_ingredients: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ingredient substitution
# ---------------------------------------------------------------------------

class SubstituteRequest(BaseModel):
    """Request for ingredient substitution suggestions."""
    recipe: Recipe
    available_ingredients: list[str]
    dietary_profile: DietaryProfile = Field(default_factory=DietaryProfile)


class SubstituteResponse(BaseModel):
    """A single substitution suggestion."""
    original_ingredient: str
    substitutions: list[dict]  # [{"name": str, "reason": str, "confidence": float}]


# ---------------------------------------------------------------------------
# Recipe Chat
# ---------------------------------------------------------------------------

class RecipeChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RecipeChatRequest(BaseModel):
    recipe: Recipe
    question: str
    chat_history: list[RecipeChatMessage] = Field(default_factory=list)


class RecipeChatResponse(BaseModel):
    answer: str
