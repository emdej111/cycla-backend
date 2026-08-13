"""Thin wrapper around the Anthropic API for the two AI-driven features:
personalized cycle insights (after 3+ tracked cycles) and medical document
analysis. Both responses are always paired with MEDICAL_DISCLAIMER by the
caller — this module never claims to diagnose or treat.
"""

import json
from functools import lru_cache
from typing import Any

import anthropic

from src.core.config import get_settings

MEDICAL_DISCLAIMER = "This is not medical advice. Consult your healthcare provider."

_PERSONALIZATION_SYSTEM_PROMPT = """You are Cycla, an AI assistant specialized in menstrual cycle health \
personalization. You analyze a user's historical cycle and check-in data to surface personalized, \
evidence-informed observations and gentle recommendations for their current cycle phase.

Rules:
- You are NOT a doctor. Never diagnose a medical condition, never name a disease as a certainty, \
never prescribe medication or dosages.
- Base your observations only on the patterns present in the provided data.
- If something in the data looks medically concerning (e.g. very heavy bleeding, severe pain, \
mentions of very abnormal cycle lengths), gently suggest discussing it with a healthcare provider.
- Keep tone warm, concise, and non-alarmist.
- Respond ONLY with a JSON object with keys: "summary" (string), "recommendations" (array of strings), \
"patterns_detected" (array of strings, can be empty)."""

_DOCUMENT_SYSTEM_PROMPT = """You are Cycla, an AI assistant that helps users understand their own \
medical documents (lab results, ultrasound reports, gynecological notes) related to menstrual and \
reproductive health.

Rules:
- You are NOT a doctor. Never provide a diagnosis. Summarize and explain terminology in plain language.
- Flag values that fall outside a typically referenced normal range as "worth discussing with a provider", \
never as a diagnosis.
- Respond ONLY with a JSON object with keys: "summary" (string), "key_values" (array of objects with \
"name", "value", "reference_range", "flag"), "flags" (array of strings highlighting anything notable)."""


@lru_cache
def _get_client() -> anthropic.Anthropic:
    settings = get_settings()
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _extract_json(text: str) -> dict[str, Any]:
    """Claude is instructed to return raw JSON; fall back to a wrapped
    summary if it ever returns something that doesn't parse cleanly.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"summary": text, "recommendations": [], "patterns_detected": []}


def get_personalized_insight(
    user_data: dict[str, Any],
    cycle_history: list[dict[str, Any]],
    current_phase: str,
) -> dict[str, Any]:
    """Called once a user has 3+ tracked cycles. Sends anonymized pattern
    data (no raw journal free-text) to Claude and returns a personalized
    insight payload matching the Insight.content shape.
    """
    settings = get_settings()
    client = _get_client()

    user_prompt = (
        f"Current cycle phase: {current_phase}\n\n"
        f"User profile: {json.dumps(user_data, default=str)}\n\n"
        f"Cycle history (up to last 12 cycles, with check-in aggregates): "
        f"{json.dumps(cycle_history, default=str)}\n\n"
        "Provide a personalized insight for today given the current phase and the recurring patterns "
        "you can identify in this history."
    )

    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=_PERSONALIZATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in message.content if getattr(block, "type", None) == "text")
    result = _extract_json(text)
    result.setdefault("summary", "")
    result.setdefault("recommendations", [])
    result.setdefault("patterns_detected", [])
    return result


def analyze_medical_document(document_text: str, user_profile: dict[str, Any]) -> dict[str, Any]:
    """Analyzes extracted text from an uploaded medical document (PDF/image
    OCR) in the context of the user's gynecological profile.
    """
    settings = get_settings()
    client = _get_client()

    user_prompt = (
        f"User gynecological profile: {json.dumps(user_profile, default=str)}\n\n"
        f"Document text:\n{document_text}\n\n"
        "Summarize this document and extract any key values relevant to menstrual/reproductive health."
    )

    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=1536,
        system=_DOCUMENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in message.content if getattr(block, "type", None) == "text")
    result = _extract_json(text)
    result.setdefault("summary", "")
    result.setdefault("key_values", [])
    result.setdefault("flags", [])
    return result


def get_chat_response(
    message: str,
    conversation_history: list[dict[str, str]],
    context: dict[str, Any],
) -> str:
    """Context-aware chat reply. `context` typically includes current phase,
    cycle day, and (if available) recent check-in summary.
    """
    settings = get_settings()
    client = _get_client()

    system_prompt = (
        "You are Cycla, a warm and knowledgeable menstrual health companion. You help users understand "
        "their cycle, symptoms, and how to feel better, using the context provided about their current "
        "cycle phase and recent check-ins. You are NOT a doctor: never diagnose conditions, never "
        "prescribe medication, and encourage users to see a healthcare provider for anything concerning. "
        f"Current user context: {json.dumps(context, default=str)}"
    )

    messages = [*conversation_history, {"role": "user", "content": message}]

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=800,
        system=system_prompt,
        messages=messages,
    )
    return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
