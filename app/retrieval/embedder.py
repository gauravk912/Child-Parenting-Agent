from typing import List

from openai import OpenAI

from app.core.config import settings


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not settings.openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")

    if not texts:
        return []

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )

    return [item.embedding for item in response.data]