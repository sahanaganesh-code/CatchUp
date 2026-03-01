import chromadb
import re
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import hashlib
import time
from app.config import settings
from app.models import TranscriptChunk
from app.gemini_client import embed_texts
import logging

logger = logging.getLogger(__name__)

# In-memory cache for frequent queries (Person 2: caching layer)
# Key: (session_id, query_text, top_k), Value: (chunks, expiry_time)
_query_cache: Dict[tuple, tuple] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes
CACHE_MAX_ENTRIES = 200


def _cache_key(session_id: str, query_text: str, top_k: int) -> tuple:
    return (session_id, query_text.strip().lower(), top_k)


def _cache_get(session_id: str, query_text: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
    key = _cache_key(session_id, query_text, top_k)
    if key not in _query_cache:
        return None
    chunks, expiry = _query_cache[key]
    if time.time() > expiry:
        del _query_cache[key]
        return None
    return chunks


def _cache_set(session_id: str, query_text: str, top_k: int, chunks: List[Dict[str, Any]]) -> None:
    while len(_query_cache) >= CACHE_MAX_ENTRIES:
        oldest = min(_query_cache.items(), key=lambda x: x[1][1])
        del _query_cache[oldest[0]]
    key = _cache_key(session_id, query_text, top_k)
    _query_cache[key] = (chunks, time.time() + CACHE_TTL_SECONDS)


class VectorStore:
    """
    ChromaDB vector store for transcript chunks.
    Optimized: batch-friendly add, query cache, efficient indexing.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # HNSW cosine for semantic search; consistent metadata for filtering
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
            # Optimize indexing: ensure we have enough elements for HNSW
            embedding_function=None,  # we supply embeddings from Gemini
        )
        logger.info(f"Initialized ChromaDB collection: {settings.chroma_collection_name} (Gemini embeddings)")

    def _generate_chunk_id(self, session_id: str, timestamp: str, text: str) -> str:
        """Generate unique ID for a chunk (stable for dedup)."""
        content = f"{session_id}:{timestamp}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_chunks(self, session_id: str, chunks: List[TranscriptChunk]) -> None:
        """Add transcript chunks to the vector store (batch; single embedding call)."""
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = self._generate_chunk_id(session_id, chunk.timestamp, chunk.text)
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                "session_id": session_id,
                "timestamp": chunk.timestamp,
                "speaker": (chunk.speaker or "Unknown")[:200],  # ChromaDB metadata length limit
            })

        # Single batch embedding call (optimized)
        embeddings = embed_texts(documents, task_type="RETRIEVAL_DOCUMENT")

        # ChromaDB add is upsert by id; we use stable ids to avoid duplicates
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(chunks)} chunks for session {session_id} with Gemini embeddings")

    def query_chunks(
        self,
        session_id: str,
        query_text: str,
        top_k: int = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """Query relevant chunks for a session. Uses in-memory cache for repeated queries."""
        if top_k is None:
            top_k = settings.retrieval_top_k

        if use_cache:
            cached = _cache_get(session_id, query_text, top_k)
            if cached is not None:
                logger.debug(f"Query cache hit for session {session_id}")
                return cached

        query_embeddings = embed_texts([query_text], task_type="RETRIEVAL_QUERY")
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where={"session_id": session_id},
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                chunks.append({
                    "text": doc,
                    "timestamp": metadata["timestamp"],
                    "speaker": metadata.get("speaker", "Unknown"),
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })

        if use_cache and chunks:
            _cache_set(session_id, query_text, top_k, chunks)
        logger.info(f"Retrieved {len(chunks)} chunks for query in session {session_id}")
        return chunks

    def query_chunks_by_keywords(
        self, session_id: str, query_text: str, top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks by keyword overlap. No API calls — uses only stored documents.
        Use when qa_use_local=True to avoid Gemini for Q&A.
        """
        if top_k is None:
            top_k = settings.retrieval_top_k
        all_chunks = self.get_all_chunks(session_id)
        if not all_chunks:
            return []
        q_words = set(re.findall(r"\b\w+\b", query_text.lower())) - {"what", "how", "when", "where", "who", "which", "why", "the", "a", "an", "is", "are", "was", "were", "do", "does", "did", "can", "could", "will", "would"}
        if not q_words:
            return all_chunks[:top_k]
        scored = []
        for c in all_chunks:
            text = (c.get("text") or "").lower()
            c_words = set(re.findall(r"\b\w+\b", text))
            overlap = len(q_words & c_words) / len(q_words) if q_words else 0
            if len(text.strip()) >= 15:
                scored.append((overlap, c))
        scored.sort(key=lambda x: (-x[0], x[1]["timestamp"]))
        return [c for _, c in scored[:top_k]]

    def get_all_chunks(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a session (no embedding; sorted by timestamp)."""
        results = self.collection.get(
            where={"session_id": session_id},
            include=["documents", "metadatas"],
        )

        chunks = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                chunks.append({
                    "text": doc,
                    "timestamp": metadata["timestamp"],
                    "speaker": metadata.get("speaker", "Unknown"),
                })

        chunks.sort(key=lambda x: x["timestamp"])
        return chunks

    def delete_session(self, session_id: str) -> None:
        """Delete all chunks for a session. Invalidates cache for this session."""
        results = self.collection.get(where={"session_id": session_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            # Drop cache entries for this session
            to_drop = [k for k in _query_cache if k[0] == session_id]
            for k in to_drop:
                del _query_cache[k]
            logger.info(f"Deleted session {session_id}")
        else:
            logger.info(f"No chunks to delete for session {session_id}")


# Global instance
vector_store = VectorStore()
