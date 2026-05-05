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
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Storage ---
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"


# Singleton instance used throughout the application
settings = Settings()
