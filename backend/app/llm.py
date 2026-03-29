from __future__ import annotations

import json
import os
from typing import Any


class OpenAIProvider:
    def __init__(self) -> None:
        self._client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.2")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return
        try:
            from openai import OpenAI
        except Exception:
            return
        try:
            self._client = OpenAI(api_key=api_key)
        except Exception:
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _extract_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text
        # Fallbacks for SDK variations.
        if hasattr(response, "output"):
            try:
                parts: list[str] = []
                for item in response.output:
                    if getattr(item, "type", None) == "message":
                        for content in getattr(item, "content", []):
                            if getattr(content, "type", None) in {"output_text", "text"}:
                                text = getattr(content, "text", None)
                                if text:
                                    parts.append(text)
                if parts:
                    return "\n".join(parts)
            except Exception:
                pass
        return str(response)

    def generate_text(self, *, instructions: str, prompt: str, temperature: float = 0.1) -> str | None:
        if not self.available:
            return None
        try:
            response = self._client.responses.create(
                model=self.model,
                instructions=instructions,
                input=prompt,
                temperature=temperature,
            )
            return self._extract_text(response).strip()
        except Exception:
            return None

    def generate_json(self, *, instructions: str, payload: dict[str, Any], temperature: float = 0.1) -> dict[str, Any] | None:
        text = self.generate_text(
            instructions=instructions,
            prompt=json.dumps(payload, indent=2),
            temperature=temperature,
        )
        if not text:
            return None
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                return None
            return json.loads(text[start : end + 1])
        except Exception:
            return None
