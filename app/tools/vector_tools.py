from typing import List
from uuid import UUID

from app.retrieval.retriever import retrieve_therapist_note_snippets


def get_therapist_note_tool_context(
    child_id: UUID,
    query_text: str,
    top_k: int = 3,
) -> List[dict]:
    return retrieve_therapist_note_snippets(
        child_id=child_id,
        query_text=query_text,
        top_k=top_k,
    )