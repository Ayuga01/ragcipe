"""
Document ingestion service.

Supports PDF, TXT, JSON, and CSV recipe files.  Documents are chunked
with recipe-aware separators before being added to the vector store.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.vectorstore import get_vectorstore_service

logger = logging.getLogger(__name__)

# Separators tuned for recipe content
_RECIPE_SEPARATORS = [
    "\n\n",
    "\n",
    "---",
    "Recipe:",
    "Ingredients:",
    "Instructions:",
]

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=_RECIPE_SEPARATORS,
)


class IngestionService:
    """Processes and indexes recipe files into the vector store."""

    def __init__(self) -> None:
        self._vectorstore = get_vectorstore_service()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def ingest_file(self, file_path: str, file_type: str) -> int:
        """Ingest a single file by path.

        Args:
            file_path: Absolute path to the file.
            file_type: One of ``pdf``, ``txt``, ``json``, ``csv``.

        Returns:
            Number of chunks added to the vector store.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = file_type.lower().lstrip(".")

        if file_type == "pdf":
            documents = self._load_pdf(path)
        elif file_type == "txt":
            documents = self._load_txt(path)
        elif file_type == "json":
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return self.ingest_json(data)
        elif file_type == "csv":
            documents = self._load_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        chunks = _splitter.split_documents(documents)
        
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self._vectorstore.add_documents(chunks[i:i+batch_size])
            
        logger.info("Ingested %d chunks from %s", len(chunks), path.name)
        return len(chunks)

    def ingest_json(self, data: Any) -> int:
        """Ingest recipe data provided as a JSON structure.

        Accepts either a single recipe dict or a list of recipe dicts.
        Each recipe dict is expected to contain at least ``title`` and
        ``ingredients`` / ``instructions`` keys.

        Returns:
            Number of chunks added.
        """
        if isinstance(data, dict):
            data = [data]

        documents: list[Document] = []
        for recipe in data:
            text = self._recipe_dict_to_text(recipe)
            metadata = self._extract_metadata(recipe)
            documents.append(Document(page_content=text, metadata=metadata))

        chunks = _splitter.split_documents(documents)
        
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self._vectorstore.add_documents(chunks[i:i+batch_size])
            
        logger.info("Ingested %d chunks from JSON data", len(chunks))
        return len(chunks)

    # ------------------------------------------------------------------
    # Private loaders
    # ------------------------------------------------------------------

    @staticmethod
    def _load_pdf(path: Path) -> list[Document]:
        loader = PyPDFLoader(str(path))
        return loader.load()

    @staticmethod
    def _load_txt(path: Path) -> list[Document]:
        loader = TextLoader(str(path), encoding="utf-8")
        return loader.load()

    @staticmethod
    def _load_csv(path: Path) -> list[Document]:
        documents: list[Document] = []
        with open(path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                text_parts = [f"{k}: {v}" for k, v in row.items() if v]
                documents.append(
                    Document(
                        page_content="\n".join(text_parts),
                        metadata={"source": str(path), "type": "csv"},
                    )
                )
        return documents

    # ------------------------------------------------------------------
    # Metadata extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _recipe_dict_to_text(recipe: dict) -> str:
        """Convert a recipe dict to a human-readable text block."""
        parts: list[str] = []
        if title := recipe.get("title"):
            parts.append(f"Recipe: {title}")
        if cuisine := recipe.get("cuisine"):
            parts.append(f"Cuisine: {cuisine}")
        if ingredients := recipe.get("ingredients"):
            if isinstance(ingredients, list):
                parts.append("Ingredients:\n" + "\n".join(f"- {i}" for i in ingredients))
            else:
                parts.append(f"Ingredients: {ingredients}")
        if instructions := recipe.get("instructions"):
            if isinstance(instructions, list):
                parts.append(
                    "Instructions:\n"
                    + "\n".join(f"{n}. {s}" for n, s in enumerate(instructions, 1))
                )
            else:
                parts.append(f"Instructions: {instructions}")
        # Include any remaining keys
        skip = {"title", "cuisine", "ingredients", "instructions"}
        for key, val in recipe.items():
            if key not in skip and val:
                parts.append(f"{key}: {val}")
        return "\n\n".join(parts)

    @staticmethod
    def _extract_metadata(recipe: dict) -> dict[str, str]:
        """Pull structured metadata from a recipe dict."""
        meta: dict[str, str] = {"source": "json"}
        if cuisine := recipe.get("cuisine"):
            meta["cuisine"] = cuisine.lower() if isinstance(cuisine, str) else str(cuisine)
        if tags := recipe.get("dietary_tags"):
            meta["dietary_tags"] = (
                ",".join(tags) if isinstance(tags, list) else str(tags)
            )
        if diet := recipe.get("diet_type"):
            meta["diet_type"] = str(diet).lower()
        return meta
