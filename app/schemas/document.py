from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TherapistNoteCreateRequest(BaseModel):
    child_id: UUID
    title: str = Field(..., min_length=3, max_length=200)
    text: str = Field(..., min_length=20, max_length=20000)


class TherapistNoteResponse(BaseModel):
    document_id: UUID
    child_id: UUID
    title: str
    doc_type: str
    source: str
    embedding_doc_id: Optional[str] = None
    chunk_count: int
    created_at: Optional[datetime] = None