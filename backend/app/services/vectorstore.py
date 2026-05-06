"""
Vector store service wrapping ChromaDB via LangChain.

Provides document storage, **hybrid retrieval** (BM25 keyword search +
dense semantic search fused via Reciprocal Rank Fusion), and collection
statistics for the recipe knowledge base.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "recipe_collection"

# Default constant for Reciprocal Rank Fusion (RRF)
_RRF_K = 60


def _docs_match_filter(doc: Document, filters: dict | None) -> bool:
    """Check if a document's metadata satisfies a ChromaDB-style filter.

    Supports ``$eq`` operators and ``$and`` combinators — the two
    forms produced by ``recipe_retrieval._build_metadata_filter``.
    """
    if filters is None:
        return True

    meta = doc.metadata or {}

    if "$and" in filters:
        return all(_docs_match_filter(doc, sub) for sub in filters["$and"])

    for key, condition in filters.items():
        if key.startswith("$"):
            continue
        meta_val = meta.get(key)
        if isinstance(condition, dict):
            # e.g. {"$eq": "vegetarian"}
            expected = condition.get("$eq")
            if expected is not None and meta_val != expected:
                return False
        else:
            # Plain equality
            if meta_val != condition:
                return False

    return True


class HybridRetriever(BaseRetriever):
    """Custom hybrid retriever combining BM25 + semantic search via RRF.

    Reciprocal Rank Fusion (RRF) merges ranked results from multiple
    retrievers using the formula:

        score(doc) = Σ  weight_i / (k + rank_i(doc))

    where ``k`` is a constant (default 60) that dampens the effect of
    high rankings.
    """

    bm25_retriever: BM25Retriever
    semantic_retriever: Any  # VectorStoreRetriever
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5
    top_k: int = 5
    metadata_filter: dict | None = None

    def _get_relevant_documents(self, query: str, **kwargs) -> list[Document]:
        """Retrieve and fuse results from BM25 and semantic retrievers."""
        # BM25 returns all matches — we post-filter by metadata
        bm25_docs_raw = self.bm25_retriever.invoke(query)
        if self.metadata_filter:
            bm25_docs = [
                d for d in bm25_docs_raw
                if _docs_match_filter(d, self.metadata_filter)
            ]
            logger.debug(
                "BM25: %d raw → %d after metadata filter",
                len(bm25_docs_raw),
                len(bm25_docs),
            )
        else:
            bm25_docs = bm25_docs_raw

        # Semantic retriever already has metadata filter applied via ChromaDB
        semantic_docs = self.semantic_retriever.invoke(query)

        return self._reciprocal_rank_fusion(
            ranked_lists=[
                (bm25_docs, self.bm25_weight),
                (semantic_docs, self.semantic_weight),
            ],
            top_k=self.top_k,
        )

    @staticmethod
    def _reciprocal_rank_fusion(
        ranked_lists: list[tuple[list[Document], float]],
        top_k: int,
        k: int = _RRF_K,
    ) -> list[Document]:
        """Apply Reciprocal Rank Fusion across multiple ranked doc lists.

        Args:
            ranked_lists: List of (documents, weight) tuples.
            top_k: Max number of documents to return.
            k: RRF constant (higher = more uniform weighting).

        Returns:
            Fused and re-ranked document list.
        """
        # Score accumulator keyed by page_content (unique identifier)
        scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, Document] = {}

        for docs, weight in ranked_lists:
            for rank, doc in enumerate(docs, start=1):
                doc_key = doc.page_content
                scores[doc_key] += weight / (k + rank)
                # Keep the first occurrence (preserves metadata)
                if doc_key not in doc_map:
                    doc_map[doc_key] = doc

        # Sort by fused score (descending) and return top_k
        sorted_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
        return [doc_map[key] for key in sorted_keys[:top_k]]


class VectorStoreService:
    """Manages a persistent ChromaDB-backed vector store with hybrid retrieval.

    Hybrid retrieval combines:
    - **BM25** (sparse / keyword-based) for exact ingredient & term matching.
    - **Semantic search** (dense embeddings) for meaning-level similarity.

    Results from both retrievers are fused using **Reciprocal Rank Fusion
    (RRF)** to merge and re-rank the two result lists.
    """

    def __init__(self) -> None:
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        self._vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self._embeddings,
            persist_directory=str(persist_dir),
        )

        # Load all existing documents from ChromaDB into memory for BM25
        self._all_documents: list[Document] = self._load_all_documents()
        self._bm25_retriever: BM25Retriever | None = None

        logger.info(
            "VectorStoreService initialised — collection=%s, persist_dir=%s, "
            "loaded %d documents for BM25 index",
            COLLECTION_NAME,
            persist_dir,
            len(self._all_documents),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_all_documents(self) -> list[Document]:
        """Load all documents stored in ChromaDB into memory.

        These are used to initialise the BM25 keyword index.
        """
        try:
            collection = self._vectorstore._collection  # noqa: SLF001
            count = collection.count()
            if count == 0:
                return []

            result = collection.get(
                include=["documents", "metadatas"],
                limit=count,
            )

            docs: list[Document] = []
            documents = result.get("documents") or []
            metadatas = result.get("metadatas") or []

            for text, meta in zip(documents, metadatas):
                if text:
                    docs.append(
                        Document(
                            page_content=text,
                            metadata=meta or {},
                        )
                    )
            return docs

        except Exception as exc:
            logger.warning("Failed to load documents for BM25: %s", exc)
            return []

    def _rebuild_bm25(self) -> None:
        """(Re)build the in-memory BM25 retriever from ``_all_documents``."""
        if self._all_documents:
            self._bm25_retriever = BM25Retriever.from_documents(
                self._all_documents,
            )
        else:
            self._bm25_retriever = None

    def _get_bm25_retriever(self, k: int = 5) -> BM25Retriever | None:
        """Return a BM25Retriever over all stored documents.

        Lazily builds the index on first call; rebuilds after new docs
        are added.
        """
        if self._bm25_retriever is None:
            self._rebuild_bm25()
        if self._bm25_retriever is not None:
            self._bm25_retriever.k = k
        return self._bm25_retriever

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_retriever(
        self,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ):
        """Return a pure semantic (dense) LangChain retriever.

        Kept for backward-compatibility; prefer ``get_hybrid_retriever``
        for production queries.

        Args:
            k: Number of documents to retrieve.
            filters: ChromaDB ``where`` filter dict.

        Returns:
            A LangChain VectorStoreRetriever.
        """
        search_kwargs: dict[str, Any] = {"k": k}
        if filters:
            search_kwargs["filter"] = filters
        return self._vectorstore.as_retriever(search_kwargs=search_kwargs)

    def get_hybrid_retriever(
        self,
        k: int = 5,
        filters: dict[str, Any] | None = None,
        *,
        semantic_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ) -> HybridRetriever | Any:
        """Return a **hybrid** retriever combining BM25 + semantic search.

        Uses a custom ``HybridRetriever`` that applies **Reciprocal Rank
        Fusion (RRF)** to merge ranked lists from both sub-retrievers.

        Both BM25 and semantic search respect the provided metadata
        filters (BM25 via post-filtering, semantic via ChromaDB's
        native ``where`` clause).

        Args:
            k: Number of documents each sub-retriever should return.
            filters: Metadata filter dict applied to both retrievers.
            semantic_weight: Weight for the semantic retriever in the
                RRF fusion (0.0–1.0).
            bm25_weight: Weight for the BM25 retriever in the RRF
                fusion (0.0–1.0).

        Returns:
            A ``HybridRetriever`` if BM25 docs are available, else
            falls back to a pure semantic retriever.
        """
        semantic = self.get_retriever(k=k, filters=filters)
        bm25 = self._get_bm25_retriever(k=k)

        if bm25 is None:
            logger.info(
                "No documents in BM25 index — falling back to pure semantic retriever."
            )
            return semantic

        hybrid = HybridRetriever(
            bm25_retriever=bm25,
            semantic_retriever=semantic,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
            top_k=k,
            metadata_filter=filters,
        )
        logger.info(
            "Hybrid retriever ready — BM25 weight=%.2f, semantic weight=%.2f, "
            "metadata_filter=%s",
            bm25_weight,
            semantic_weight,
            filters,
        )
        return hybrid

    def add_documents(self, documents: list[Document]) -> None:
        """Add a batch of LangChain Documents to both stores.

        - Adds to the persistent ChromaDB vector store (semantic).
        - Appends to the in-memory document list and invalidates the
          BM25 index so it is rebuilt on next retrieval.
        """
        if not documents:
            logger.warning("add_documents called with empty list — skipping.")
            return

        # Semantic store (persistent)
        self._vectorstore.add_documents(documents)

        # BM25 store (in-memory) — add and invalidate cached index
        self._all_documents.extend(documents)
        self._bm25_retriever = None  # Force rebuild on next retrieval
        logger.info(
            "Added %d documents to %s (total BM25 docs: %d).",
            len(documents),
            COLLECTION_NAME,
            len(self._all_documents),
        )

    def get_collection_stats(self) -> dict[str, Any]:
        """Return basic statistics about the stored collection."""
        collection = self._vectorstore._collection  # noqa: SLF001
        count = collection.count()
        return {
            "collection_name": COLLECTION_NAME,
            "document_count": count,
            "bm25_document_count": len(self._all_documents),
            "persist_directory": settings.CHROMA_PERSIST_DIR,
        }


# Module-level lazy singleton
_instance: VectorStoreService | None = None


def get_vectorstore_service() -> VectorStoreService:
    """Return (and lazily create) the singleton VectorStoreService."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        _instance = VectorStoreService()
    return _instance
