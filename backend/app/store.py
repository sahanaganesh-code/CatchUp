import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
import hashlib
from app.config import settings
from app.models import TranscriptChunk, Evidence
from app.gemini_client import embed_texts
import logging

logger = logging.getLogger(__name__)


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
    
    def get_all_chunks(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a session."""
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
        
        # Sort by timestamp
        chunks.sort(key=lambda x: x["timestamp"])
        return chunks
    
    def delete_session(self, session_id: str) -> None:
        """Delete all chunks for a session."""
        results = self.collection.get(where={"session_id": session_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted session {session_id}")


# Global instance
vector_store = VectorStore()
