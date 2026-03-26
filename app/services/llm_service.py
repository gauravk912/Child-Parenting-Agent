from pathlib import Path
import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "graph" / "prompts"


def load_prompt_template(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def generate_crisis_response(prompt_text: str) -> str:
    if not settings.openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")

    logger.info("Calling OpenAI model=%s for crisis response", settings.openai_model)

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt_text,
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI returned an empty response.")

    return text.strip()


def generate_weekly_report_summary(prompt_text: str) -> str:
    if not settings.openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")

    logger.info("Calling OpenAI model=%s for weekly report summary", settings.openai_model)

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt_text,
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI returned an empty weekly report response.")

    return text.strip()