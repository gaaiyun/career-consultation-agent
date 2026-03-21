from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from src.config.settings import Settings
from src.llm.base import BaseLLMClient


class SiliconFlowClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.settings.siliconflow_api_key)

    @property
    def client(self) -> OpenAI:
        if not self.is_configured():
            raise RuntimeError("Missing SILICONFLOW_API_KEY environment variable.")
        if self._client is None:
            self._client = OpenAI(
                api_key=self.settings.siliconflow_api_key,
                base_url=self.settings.siliconflow_base_url,
                timeout=self.settings.default_timeout,
            )
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        timeout: int | None = None,
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model or self.settings.siliconflow_model,
            temperature=temperature,
            timeout=timeout or self.settings.default_timeout,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return completion.choices[0].message.content or ""

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        raw_text = self.generate(
            system_prompt,
            user_prompt,
            model=model,
            temperature=temperature,
            timeout=timeout,
        )
        return self._extract_json(raw_text)

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        code_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if code_block_match:
            return json.loads(code_block_match.group(1))

        object_match = re.search(r"(\{.*\})", text, re.S)
        if object_match:
            return json.loads(object_match.group(1))

        raise ValueError("Model response is not valid JSON.")
