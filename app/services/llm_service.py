from pathlib import Path
import json
import logging
import re
from typing import Any, Dict, Optional, List

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "graph" / "prompts"


def load_prompt_template(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def _get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")
    return OpenAI(api_key=settings.openai_api_key)


def _extract_json_object(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty LLM response when JSON was expected.")

    text = text.strip()

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    direct = re.search(r"(\{.*\})", text, re.DOTALL)
    if direct:
        return json.loads(direct.group(1))

    raise ValueError("Could not parse JSON object from LLM response.")


def generate_crisis_response(prompt_text: str) -> str:
    logger.info("Calling OpenAI model=%s for crisis response", settings.openai_model)
    client = _get_client()

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt_text,
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI returned an empty response.")

    return text.strip()


def generate_weekly_report_summary(prompt_text: str) -> str:
    logger.info("Calling OpenAI model=%s for weekly report summary", settings.openai_model)
    client = _get_client()

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt_text,
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI returned an empty weekly report response.")

    return text.strip()


def classify_crisis_structured(
    child_name: Optional[str],
    parent_message: str,
) -> Dict[str, Any]:
    logger.info("Calling OpenAI model=%s for structured crisis classification", settings.openai_model)
    client = _get_client()

    prompt = f"""
You are a structured crisis triage assistant for a trauma-informed parenting support system.

Classify the parent message into a structured JSON object.

Return ONLY valid JSON with these keys:
{{
  "route": "crisis" or "emergency",
  "severity": "moderate" or "high" or "emergency",
  "needs_emergency_support": true or false,
  "confidence": number between 0 and 1,
  "reasoning_summary": "short explanation"
}}

Rules:
- Use "emergency" only when there are signs of medical emergency, severe danger, breathing issues, loss of consciousness, major injury, weapon use, or immediate inability to keep people safe.
- Use "high" for dangerous escalation like throwing objects, aggression, unsafe behavior, or intense public dysregulation.
- Use "moderate" for distress without strong danger indicators.
- Be cautious and safety-oriented.
- Return only JSON.

Child name: {child_name or "unknown child"}
Parent message: {parent_message}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    text = getattr(response, "output_text", None)
    parsed = _extract_json_object(text)

    return {
        "route": parsed.get("route", "crisis"),
        "severity": parsed.get("severity", "moderate"),
        "needs_emergency_support": bool(parsed.get("needs_emergency_support", False)),
        "confidence": float(parsed.get("confidence", 0.0)),
        "reasoning_summary": parsed.get("reasoning_summary", "LLM classification used."),
    }


def extract_debrief_structured(raw_text: str) -> Dict[str, Any]:
    logger.info("Calling OpenAI model=%s for structured debrief extraction", settings.openai_model)
    client = _get_client()

    prompt = f"""
You are a structured debrief extraction assistant for a trauma-informed parenting support system.

Extract the following fields from the parent’s debrief text.

Return ONLY valid JSON with these keys:
{{
  "antecedent": string or null,
  "behavior": string or null,
  "consequence": string or null,
  "confidence": number between 0 and 1,
  "reasoning_summary": "short explanation"
}}

Definitions:
- antecedent = what happened right before the child became upset
- behavior = what the child did during the incident
- consequence = what happened after / how the situation ended

If a field is unclear, return null.
Return only JSON.

Debrief text:
{raw_text}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    text = getattr(response, "output_text", None)
    parsed = _extract_json_object(text)

    return {
        "antecedent": parsed.get("antecedent"),
        "behavior": parsed.get("behavior"),
        "consequence": parsed.get("consequence"),
        "confidence": float(parsed.get("confidence", 0.0)),
        "reasoning_summary": parsed.get("reasoning_summary", "LLM extraction used."),
    }


def normalize_incident_memory(
    parent_summary: str,
    antecedent: Optional[str],
    behavior: Optional[str],
    consequence: Optional[str],
    location: Optional[str],
    interventions_tried: List[str],
) -> Dict[str, Any]:
    logger.info("Calling OpenAI model=%s for incident memory normalization", settings.openai_model)
    client = _get_client()

    prompt = f"""
You are a structured memory-normalization assistant.

Convert the incident into reusable normalized labels.

Return ONLY valid JSON with these keys:
{{
  "trigger_labels": ["..."],
  "context_labels": ["..."],
  "behavior_labels": ["..."],
  "intervention_labels": ["..."],
  "confidence": number between 0 and 1,
  "reasoning_summary": "short explanation"
}}

Rules:
- Use short reusable lowercase labels.
- Max 5 items per list.
- Do not return long phrases unless necessary.
- Examples:
  - "after school transition"
  - "crowded environment"
  - "store outing"
  - "screaming"
  - "throwing objects"
  - "quiet corner"

Parent summary: {parent_summary}
Antecedent: {antecedent}
Behavior: {behavior}
Consequence: {consequence}
Location: {location}
Interventions tried: {interventions_tried}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    text = getattr(response, "output_text", None)
    parsed = _extract_json_object(text)

    def _clean(xs):
        out = []
        if isinstance(xs, list):
            for item in xs[:5]:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip().lower())
        return out

    return {
        "trigger_labels": _clean(parsed.get("trigger_labels", [])),
        "context_labels": _clean(parsed.get("context_labels", [])),
        "behavior_labels": _clean(parsed.get("behavior_labels", [])),
        "intervention_labels": _clean(parsed.get("intervention_labels", [])),
        "confidence": float(parsed.get("confidence", 0.0)),
        "reasoning_summary": parsed.get("reasoning_summary", "LLM normalization used."),
    }


def plan_crisis_tool_usage(
    child_name: Optional[str],
    severity: Optional[str],
    parent_message: str,
    sensory_triggers: Optional[str],
    school_notes: Optional[str],
) -> Dict[str, Any]:
    logger.info("Calling OpenAI model=%s for crisis tool planning", settings.openai_model)
    client = _get_client()

    prompt = f"""
You are a planning assistant for a crisis support system.

Decide which retrieval sources are worth using for this crisis.

Return ONLY valid JSON:
{{
  "use_graph_memory": true or false,
  "use_tavily_evidence": true or false,
  "use_therapist_notes": true or false,
  "confidence": number between 0 and 1,
  "reasoning_summary": "short explanation"
}}

Guidance:
- Graph memory is useful for repeated patterns or known recurring contexts.
- Therapist notes are useful when child-specific regulation strategies matter.
- Tavily evidence is useful when external grounding may add value, especially for public/safety/escalation scenarios.
- Avoid unnecessary tool use for very simple cases.

Child name: {child_name or "unknown"}
Severity: {severity or "unknown"}
Known sensory triggers: {sensory_triggers or "unknown"}
School notes: {school_notes or "unknown"}
Parent message: {parent_message}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    text = getattr(response, "output_text", None)
    parsed = _extract_json_object(text)

    return {
        "use_graph_memory": bool(parsed.get("use_graph_memory", True)),
        "use_tavily_evidence": bool(parsed.get("use_tavily_evidence", False)),
        "use_therapist_notes": bool(parsed.get("use_therapist_notes", True)),
        "confidence": float(parsed.get("confidence", 0.0)),
        "reasoning_summary": parsed.get("reasoning_summary", "LLM planner used."),
    }