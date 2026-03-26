from typing import Optional


def transcribe_text_input(transcript_text: Optional[str], parent_summary: str) -> str:
    """
    If transcript text is present, use it.
    Otherwise, fall back to the parent summary.
    Later this can be replaced with a real audio transcription pipeline.
    """
    if transcript_text and transcript_text.strip():
        return transcript_text.strip()

    return parent_summary.strip()