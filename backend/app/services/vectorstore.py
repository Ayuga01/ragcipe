"""
Vector store service wrapping Supabase via LangChain.

Provides document storage, **hybrid retrieval** (BM25 keyword search +
dense semantic search fused via Reciprocal Rank Fusion), and collection
statistics for the recipe knowledge base.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from supabase.client import Client, create_client
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

TABLE_NAME = "documents"
QUERY_NAME = "match_documents"

# Default constant for Reciprocal Rank Fusion (RRF)
_RRF_K = 60


def _docs_match_filter(doc: Document, filters: dict | None) -> bool:
    """Check if a document's metadata satisfies a metadata filter."""
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
    """Custom hybrid retriever combining BM25 + semantic search via RRF."""

    bm25_retriever: BM25Retriever
    semantic_retriever: Any  # VectorStoreRetriever
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5
    top_k: int = 5
    metadata_filter: dict | None = None

    def _get_relevant_documents(self, query: str, **kwargs) -> list[Document]:
        """Retrieve and fuse results from BM25 and semantic retrievers."""
        bm25_docs_raw = self.bm25_retriever.invoke(query)
        if self.metadata_filter:
            bm25_docs = [
                d for d in bm25_docs_raw
                if _docs_match_filter(d, self.metadata_filter)
            ]
        else:
            bm25_docs = bm25_docs_raw

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
        scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, Document] = {}

        for docs, weight in ranked_lists:
            for rank, doc in enumerate(docs, start=1):
                doc_key = doc.page_content
                scores[doc_key] += weight / (k + rank)
                if doc_key not in doc_map:
                    doc_map[doc_key] = doc

        sorted_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
        return [doc_map[key] for key in sorted_keys[:top_k]]


class VectorStoreService:
    """Manages a persistent Supabase-backed vector store with hybrid retrieval."""

    def __init__(self) -> None:
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY

        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
        )

        # Fallback to avoid crashing locally if keys aren't set yet
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase URL or Key missing! Vector operations will fail.")
            self.supabase: Client | None = None
            self._vectorstore = None
            self._all_documents: list[Document] = []
        else:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            self._vectorstore = SupabaseVectorStore(
                client=self.supabase,
                embedding=self._embeddings,
                table_name=TABLE_NAME,
                query_name=QUERY_NAME,
            )
            self._all_documents: list[Document] = self._load_all_documents()

        self._bm25_retriever: BM25Retriever | None = None

        logger.info(
            "VectorStoreService initialised — loaded %d documents for BM25 index",
            len(self._all_documents),
        )

    def _load_all_documents(self) -> list[Document]:
        try:
            response = self.supabase.table(TABLE_NAME).select("content, metadata").execute()
            docs = []
            for row in response.data:
                docs.append(Document(page_content=row["content"], metadata=row["metadata"] or {}))
            return docs
        except Exception as exc:
            logger.warning("Failed to load documents for BM25: %s", exc)
            return []

    def _rebuild_bm25(self) -> None:
        if self._all_documents:
            self._bm25_retriever = BM25Retriever.from_documents(self._all_documents)
        else:
            self._bm25_retriever = None

    def _get_bm25_retriever(self, k: int = 5) -> BM25Retriever | None:
        if self._bm25_retriever is None:
            self._rebuild_bm25()
        if self._bm25_retriever is not None:
            self._bm25_retriever.k = k
        return self._bm25_retriever

    def get_retriever(self, k: int = 5, filters: dict[str, Any] | None = None):
        if not self.supabase:
            raise ValueError("Vector store not initialized. Check Supabase keys.")
            
        class DirectSupabaseRetriever(BaseRetriever):
            supabase: Any
            k: int
            filters: dict | None
            embeddings: Any
            
            def _get_relevant_documents(self, query: str, **kwargs) -> list[Document]:
                query_embedding = self.embeddings.embed_query(query)
                res = self.supabase.rpc(
                    QUERY_NAME,
                    {
                        "query_embedding": query_embedding,
                        "match_count": self.k,
                        "filter": self.filters or {}
                    }
                ).execute()
                
                docs = []
                for row in res.data:
                    docs.append(Document(page_content=row["content"], metadata=row["metadata"] or {}))
                return docs

        return DirectSupabaseRetriever(
            supabase=self.supabase, 
            k=k, 
            filters=filters, 
            embeddings=self._embeddings
        )

    def get_hybrid_retriever(
        self,
        k: int = 5,
        filters: dict[str, Any] | None = None,
        *,
        semantic_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ) -> HybridRetriever | Any:
        
        if not self._vectorstore:
            raise ValueError("Vector store not initialized. Check Supabase keys.")

        semantic = self.get_retriever(k=k, filters=filters)
        bm25 = self._get_bm25_retriever(k=k)

        if bm25 is None:
            return semantic

        hybrid = HybridRetriever(
            bm25_retriever=bm25,
            semantic_retriever=semantic,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
            top_k=k,
            metadata_filter=filters,
        )
        return hybrid

    def add_documents(self, documents: list[Document]) -> None:
        if not documents or not self._vectorstore:
            return

        self._vectorstore.add_documents(documents)
        self._all_documents.extend(documents)
        self._bm25_retriever = None

    def get_collection_stats(self) -> dict[str, Any]:
        count = len(self._all_documents)
        return {
            "collection_name": TABLE_NAME,
            "document_count": count,
            "bm25_document_count": count,
            "persist_directory": "Supabase Cloud",
        }


_instance: VectorStoreService | None = None

def get_vectorstore_service() -> VectorStoreService:
    global _instance
    if _instance is None:
        _instance = VectorStoreService()
    return _instance
