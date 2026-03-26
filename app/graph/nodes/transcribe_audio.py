from app.services.transcription_service import transcribe_text_input


def transcribe_audio(state):
    raw_text = transcribe_text_input(
        transcript_text=state.get("transcript_text"),
        parent_summary=state["parent_summary"],
    )

    return {
        **state,
        "raw_text": raw_text,
    }