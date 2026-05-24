"""
FastAPI application entry point.

Initialises the app, CORS middleware, lifespan events, and mounts
the API router.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.services.vectorstore import get_vectorstore_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    logger.info("Starting up — initialising vector store …")
    get_vectorstore_service()
    logger.info("Vector store ready.")
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Multimodal Recipe Generator API",
    description=(
        "A RAG-based multimodal recipe generator that combines image "
        "analysis (Gemini), recipe book retrieval (ChromaDB), web search "
        "(Tavily), and LLM reasoning (OpenAI) to generate personalised "
        "recipes with dietary-aware ingredient substitutions."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow Vite dev server
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router)


@app.get("/")
async def root():
    """Root redirect / info endpoint."""
    return {
        "message": "Multimodal Recipe Generator API",
        "docs": "/docs",
        "health": "/api/health",
    }
