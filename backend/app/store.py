from typing import List, Dict, Any
import hashlib
from sqlalchemy import select, delete
from app.config import settings
from app.models import TranscriptChunk
from app.gemini_client import embed_texts
from app.db import SessionLocal, TranscriptChunkRow
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Postgres + pgvector store for transcript chunks."""

    def _generate_chunk_id(self, session_id: str, timestamp: str, text: str) -> str:
        """Generate unique ID for a chunk."""
        content = f"{session_id}:{timestamp}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_chunks(self, session_id: str, chunks: List[TranscriptChunk]) -> None:
        """Add transcript chunks to the vector store."""
        if not chunks:
            return

        documents = [c.text for c in chunks]

        # Generate embeddings using Gemini with RETRIEVAL_DOCUMENT task type
        embeddings = embed_texts(documents, task_type="RETRIEVAL_DOCUMENT")

        with SessionLocal() as db:
            for chunk, embedding in zip(chunks, embeddings):
                row = TranscriptChunkRow(
                    id=self._generate_chunk_id(session_id, chunk.timestamp, chunk.text),
                    session_id=session_id,
                    timestamp=chunk.timestamp,
                    speaker=chunk.speaker or "Speaker",
                    text=chunk.text,
                    embedding=embedding,
                )
                db.merge(row)
            db.commit()

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
        query_embedding = embed_texts([query_text], task_type="RETRIEVAL_QUERY")[0]

        with SessionLocal() as db:
            distance = TranscriptChunkRow.embedding.cosine_distance(query_embedding)
            rows = db.execute(
                select(TranscriptChunkRow, distance.label("distance"))
                .where(TranscriptChunkRow.session_id == session_id)
                .order_by(distance)
                .limit(top_k)
            ).all()

        chunks = [
            {
                "text": row.TranscriptChunkRow.text,
                "timestamp": row.TranscriptChunkRow.timestamp,
                "speaker": row.TranscriptChunkRow.speaker or "Speaker",
                "distance": row.distance,
            }
            for row in rows
        ]

        logger.info(f"Retrieved {len(chunks)} chunks for query in session {session_id}")
        return chunks

    def get_all_chunks(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a session, sorted by timestamp."""
        with SessionLocal() as db:
            rows = db.execute(
                select(TranscriptChunkRow)
                .where(TranscriptChunkRow.session_id == session_id)
                .order_by(TranscriptChunkRow.timestamp)
            ).scalars().all()

        return [
            {"text": r.text, "timestamp": r.timestamp, "speaker": r.speaker or "Speaker"}
            for r in rows
        ]

    def delete_session(self, session_id: str) -> None:
        """Delete all chunks for a session."""
        with SessionLocal() as db:
            db.execute(delete(TranscriptChunkRow).where(TranscriptChunkRow.session_id == session_id))
            db.commit()
        logger.info(f"Deleted chunks for session {session_id}")


# Global instance
vector_store = VectorStore()
