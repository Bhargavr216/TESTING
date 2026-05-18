from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class LocalAIConfig:
    enabled: bool = False
    provider: str = "ollama"  # "ollama" | "openai_compat"
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.1:8b"
    timeout_seconds: int = 20
    temperature: float = 0.2
    max_tokens: int = 256


class LocalAIClient:
    def __init__(self, config: LocalAIConfig):
        self.config = config

    def decide(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Ask local LLM to produce a JSON decision.
        Expected output JSON shape:
          {"type":"text","answer":"..."} OR
          {"type":"radio","choice":"<option text>"} OR
          {"type":"checkbox","choices":["<option text>", ...]}
        """
        if not self.config.enabled:
            return None

        system = (
            "You fill job-application chatbot questions using the provided candidate profile. "
            "Return ONLY valid JSON, no extra text. "
            "If uncertain, return an empty answer for the given type."
        )

        user = json.dumps(payload, ensure_ascii=False)

        if self.config.provider.lower() == "openai_compat":
            return self._call_openai_compat(system, user)

        # Default: Ollama
        return self._call_ollama(system, user)

    def _call_ollama(self, system: str, user: str) -> dict[str, Any] | None:
        url = self.config.base_url.rstrip("/") + "/api/chat"
        body = {
            "model": self.config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": self.config.temperature},
        }

        try:
            resp = requests.post(url, json=body, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            content = ((data or {}).get("message") or {}).get("content") or ""
            return _extract_json_object(content)
        except Exception:
            return None

    def _call_openai_compat(self, system: str, user: str) -> dict[str, Any] | None:
        url = self.config.base_url.rstrip("/") + "/v1/chat/completions"
        body = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        try:
            resp = requests.post(url, json=body, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            choices = (data or {}).get("choices") or []
            content = ""
            if choices:
                content = (((choices[0] or {}).get("message") or {}).get("content") or "").strip()
            return _extract_json_object(content)
        except Exception:
            return None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if not t:
        return None
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # Try to locate the first {...} block
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

