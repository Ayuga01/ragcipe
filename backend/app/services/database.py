"""
Database service for managing relational data in Supabase.
Handles saving and retrieving user generated recipes.
"""

import logging
from typing import Any
from app.config import settings
from supabase.client import Client, create_client

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase URL or Key missing! Database operations will fail.")
            self.supabase: Client | None = None
        else:
            self.supabase = create_client(self.supabase_url, self.supabase_key)

    def save_recipe(self, session_id: str, recipe: dict) -> dict:
        """Save a generated recipe to the saved_recipes table."""
        if not self.supabase:
            raise ValueError("Supabase client not initialized.")
            
        data = {
            "session_id": session_id,
            "recipe_data": recipe,
            "title": recipe.get("title", "Untitled Recipe")
        }
        
        response = self.supabase.table("saved_recipes").insert(data).execute()
        return response.data[0] if response.data else {}

    def get_saved_recipes(self, session_id: str) -> list[dict]:
        """Fetch all saved recipes for a given session."""
        if not self.supabase:
            raise ValueError("Supabase client not initialized.")
            
        response = self.supabase.table("saved_recipes").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
        return response.data or []

    def delete_recipe(self, session_id: str, recipe_id: str) -> bool:
        """Delete a saved recipe."""
        if not self.supabase:
            raise ValueError("Supabase client not initialized.")
            
        response = self.supabase.table("saved_recipes").delete().match({"id": recipe_id, "session_id": session_id}).execute()
        return len(response.data) > 0


_instance: DatabaseService | None = None

def get_database_service() -> DatabaseService:
    global _instance
    if _instance is None:
        _instance = DatabaseService()
    return _instance
