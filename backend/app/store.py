import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import time
from app.config import settings
from app.models import TranscriptChunk, Evidence
from app.gemini_client import embed_texts
import logging

logger = logging.getLogger(__name__)

# Optional in-memory cache for get_all_chunks (reduces ChromaDB load). TTL seconds.
_chunks_cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
CHUNKS_CACHE_TTL = 60


class VectorStore:
    """ChromaDB vector store for transcript chunks."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB collection: {settings.chroma_collection_name} (Gemini embeddings)")
    
    def _generate_chunk_id(self, session_id: str, timestamp: str, text: str) -> str:
        """Generate unique ID for a chunk."""
        content = f"{session_id}:{timestamp}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_chunks(self, session_id: str, chunks: List[TranscriptChunk]) -> None:
        """Add transcript chunks to the vector store."""
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
                "speaker": chunk.speaker or "Unknown"
            })
        
        # Generate embeddings using Gemini with RETRIEVAL_DOCUMENT task type
        embeddings = embed_texts(documents, task_type="RETRIEVAL_DOCUMENT")
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"Added {len(chunks)} chunks for session {session_id} with Gemini embeddings")
    
    def query_chunks(
        self, 
        session_id: str, 
        query_text: str, 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Query relevant chunks for a session."""
        if top_k is None:
            top_k = settings.retrieval_top_k
        
        # Generate query embedding using Gemini with RETRIEVAL_QUERY task type
        query_embeddings = embed_texts([query_text], task_type="RETRIEVAL_QUERY")
        
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where={"session_id": session_id}
        )
        
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                chunks.append({
                    "text": doc,
                    "timestamp": metadata["timestamp"],
                    "speaker": metadata.get("speaker", "Unknown"),
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        logger.info(f"Retrieved {len(chunks)} chunks for query in session {session_id}")
        return chunks
    
    def get_all_chunks(self, session_id: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get all chunks for a session. Uses optional in-memory cache (TTL 60s) when use_cache=True."""
        if use_cache and session_id in _chunks_cache:
            cached, ts = _chunks_cache[session_id]
            if time.time() - ts < CHUNKS_CACHE_TTL:
                return cached
        results = self.collection.get(
            where={"session_id": session_id}
        )
        chunks = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                chunks.append({
                    "text": doc,
                    "timestamp": metadata["timestamp"],
                    "speaker": metadata.get("speaker", "Unknown")
                })
        chunks.sort(key=lambda x: x["timestamp"])
        if use_cache:
            _chunks_cache[session_id] = (chunks, time.time())
        return chunks
    
    def delete_session(self, session_id: str) -> None:
        """Delete all chunks for a session."""
        results = self.collection.get(where={"session_id": session_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted session {session_id}")
        _chunks_cache.pop(session_id, None)

    def list_session_ids(self) -> List[str]:
        """Return distinct session_ids that have chunks in the collection (for coordination)."""
        try:
            # ChromaDB get with no filter returns all; we only need metadatas for session_id
            data = self.collection.get(include=["metadatas"])
            if not data or not data.get("metadatas"):
                return []
            seen = set()
            for meta in data["metadatas"]:
                sid = meta.get("session_id")
                if sid:
                    seen.add(sid)
            return sorted(seen)
        except Exception as e:
            logger.warning(f"list_session_ids failed: {e}")
            return []


# Global instance
vector_store = VectorStore()
