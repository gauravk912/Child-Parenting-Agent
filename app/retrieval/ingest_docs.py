from typing import Dict, Any
from uuid import UUID

from app.db.vectorstore import append_vector_records
from app.retrieval.chunking import chunk_text
from app.retrieval.embedder import embed_texts


def ingest_document_for_retrieval(
    document_id: UUID,
    child_id: UUID,
    title: str,
    raw_text: str,
) -> Dict[str, Any]:
    chunks = chunk_text(raw_text)
    embeddings = embed_texts(chunks)

    vector_records = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector_records.append(
            {
                "document_id": str(document_id),
                "child_id": str(child_id),
                "title": title,
                "chunk_index": idx,
                "chunk_text": chunk,
                "embedding": embedding,
            }
        )

    append_vector_records(vector_records)

    return {
        "embedding_doc_id": str(document_id),
        "chunk_count": len(chunks),
    }