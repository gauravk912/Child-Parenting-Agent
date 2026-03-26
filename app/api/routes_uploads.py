import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.models.document import Document
from app.retrieval.ingest_docs import ingest_document_for_retrieval
from app.schemas.document import TherapistNoteCreateRequest, TherapistNoteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/therapist-note", response_model=TherapistNoteResponse, status_code=status.HTTP_201_CREATED)
def upload_therapist_note(
    payload: TherapistNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logger.info("Therapist note upload received for child_id=%s", payload.child_id)

    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    document = Document(
        child_id=payload.child_id,
        doc_type="therapist_note",
        title=payload.title,
        source="manual_text",
        raw_text=payload.text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    ingest_result = ingest_document_for_retrieval(
        document_id=document.id,
        child_id=payload.child_id,
        title=document.title,
        raw_text=document.raw_text,
    )

    document.embedding_doc_id = ingest_result["embedding_doc_id"]
    db.commit()
    db.refresh(document)

    return TherapistNoteResponse(
        document_id=document.id,
        child_id=document.child_id,
        title=document.title,
        doc_type=document.doc_type,
        source=document.source,
        embedding_doc_id=document.embedding_doc_id,
        chunk_count=ingest_result["chunk_count"],
        created_at=document.created_at,
    )