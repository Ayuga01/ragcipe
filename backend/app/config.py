"""
Application configuration using pydantic-settings.

Loads settings from environment variables and .env file.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for all API keys, model names, and paths."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- API Keys ---
    OPENAI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # --- Model Defaults ---
    OPENAI_MODEL: str = "gpt-5.4-mini"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- Storage & DB ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Clean the Supabase URL if the user accidentally included the REST endpoint
        if self.SUPABASE_URL.endswith("/rest/v1/") or self.SUPABASE_URL.endswith("/rest/v1"):
            self.SUPABASE_URL = self.SUPABASE_URL.replace("/rest/v1/", "").replace("/rest/v1", "")
        self.SUPABASE_URL = self.SUPABASE_URL.rstrip("/")

# Singleton instance used throughout the application
settings = Settings()
