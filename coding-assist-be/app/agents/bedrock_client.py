import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings


class BedrockClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._model_id = settings.bedrock_model_id
        self._max_tokens = settings.bedrock_max_tokens
        self._temperature = settings.bedrock_temperature
        self._client = OpenAI(
            api_key=settings.openai_api_key or None,
            base_url=settings.openai_base_url,
        )

    def generate_hint(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self._client.responses.create(
            model=self._model_id,
            input=[{"role": "user", "content": user_prompt}],
            instructions=system_prompt,
            max_output_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        text_response = (getattr(response, "output_text", "") or "").strip()
        if not text_response:
            raise ValueError("Empty model output")
        return _parse_hint_json(text_response)


def _parse_hint_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    parsed = json.loads(cleaned)
    allowed_levels = {"diagnosis", "next_step", "complexity"}
    hint_level = str(parsed.get("hint_level", "diagnosis")).strip().lower()
    if hint_level not in allowed_levels:
        hint_level = "diagnosis"
    next_hint_level = str(parsed.get("next_hint_level", "next_step")).strip().lower()
    if next_hint_level not in allowed_levels:
        if hint_level == "diagnosis":
            next_hint_level = "next_step"
        elif hint_level == "next_step":
            next_hint_level = "complexity"
        else:
            next_hint_level = "complexity"
    try:
        confidence = float(parsed.get("confidence", 0.82))
    except (TypeError, ValueError):
        confidence = 0.82
    confidence = max(0.0, min(1.0, confidence))
    return {
        "hint_level": hint_level,
        "next_hint_level": next_hint_level,
        "confidence": confidence,
        "guided_hint": str(parsed.get("guided_hint", "")).strip(),
        "strategy": str(parsed.get("strategy", "")).strip(),
        "complexity_suggestion": str(parsed.get("complexity_suggestion", "")).strip(),
    }
