"""
Image analysis node — uses Google Gemini 2.5 Flash to identify
food ingredients from a base64-encoded image.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.models.state import RecipeGraphState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert food ingredient identifier.
Analyze the provided image and identify ALL visible food ingredients.

Return your response as a JSON array of objects, each with:
- "name": the ingredient name (lowercase, singular form)
- "confidence": a float 0-1 indicating how confident you are

Example:
[
  {"name": "tomato", "confidence": 0.95},
  {"name": "onion", "confidence": 0.90}
]

Rules:
1. Be thorough — list every ingredient you can see.
2. Use common English names.
3. Distinguish between similar items (e.g. green onion vs yellow onion).
4. If you see packaged goods, identify the food inside.
5. Return ONLY the JSON array, no other text.
"""


def _as_image_data_url(image_data: str) -> str:
    """Return a Gemini-compatible image data URL.

    The frontend keeps captured images as browser data URLs. Some API callers
    may still send only the base64 payload, so support both shapes.
    """
    cleaned = image_data.strip()
    if cleaned.startswith("data:image/"):
        return cleaned
    return f"data:image/jpeg;base64,{cleaned}"


def image_analysis_node(state: RecipeGraphState) -> dict:
    """Detect ingredients from an image using Gemini vision model.

    Reads ``state["image_data"]`` (base64 string) and returns
    ``detected_ingredients`` plus an informational message.
    """
    image_data = state.get("image_data")
    if not image_data:
        logger.warning("image_analysis_node called without image_data.")
        return {
            "detected_ingredients": [],
            "messages": [
                HumanMessage(content="No image provided — skipping image analysis."),
            ],
        }

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {"type": "text", "text": "Identify all food ingredients in this image."},
                    {
                        "type": "image_url",
                        "image_url": {"url": _as_image_data_url(image_data)},
                    },
                ]
            ),
        ]

        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # Parse JSON — handle markdown fenced blocks just in case
        json_text = raw_text
        if "```" in json_text:
            json_text = json_text.split("```")[1]
            if json_text.startswith("json"):
                json_text = json_text[4:]
            json_text = json_text.strip()

        ingredients_data: list[dict] = json.loads(json_text)
        ingredient_details = []
        for item in ingredients_data:
            name = str(item.get("name", "")).lower().strip()
            if not name:
                continue
            ingredient_details.append(
                {
                    "name": name,
                    "confidence": float(item.get("confidence", 0.9)),
                }
            )
        ingredient_names = [item["name"] for item in ingredient_details]

        logger.info("Detected %d ingredients from image.", len(ingredient_names))

        return {
            "detected_ingredients": ingredient_names,
            "detected_ingredient_details": ingredient_details,
            "messages": [
                HumanMessage(
                    content=f"Detected ingredients from image: {', '.join(ingredient_names)}"
                ),
            ],
        }

    except Exception as exc:
        logger.error("Image analysis failed: %s", exc, exc_info=True)
        return {
            "detected_ingredients": [],
            "error": f"Image analysis failed: {exc}",
            "messages": [
                HumanMessage(content=f"Image analysis error: {exc}"),
            ],
        }
