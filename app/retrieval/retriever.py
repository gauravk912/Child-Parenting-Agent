from typing import List
from uuid import UUID

from app.db.vectorstore import search_vector_store
from app.retrieval.embedder import embed_texts


def retrieve_therapist_note_snippets(
    child_id: UUID,
    query_text: str,
    top_k: int = 3,
) -> List[dict]:
    query_embeddings = embed_texts([query_text])
    if not query_embeddings:
        return []

    query_embedding = query_embeddings[0]

    return search_vector_store(
        query_embedding=query_embedding,
        child_id=str(child_id),
        top_k=top_k,
    )