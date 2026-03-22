from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

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
        max_tokens: int | None = None,
    ) -> str:
        completion = self._create_completion(
            model=model or self.settings.siliconflow_model,
            temperature=temperature,
            timeout=timeout or self.settings.default_timeout,
            max_tokens=max_tokens,
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
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        active_model = model or self.settings.siliconflow_model
        use_native_json_mode = "deepseek-ai/DeepSeek-V3.2" not in active_model

        if use_native_json_mode:
            completion = self._create_completion(
                model=active_model,
                temperature=temperature,
                timeout=timeout or self.settings.default_timeout,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_text = completion.choices[0].message.content or ""
            try:
                return self._extract_json(raw_text)
            except Exception:
                raw_text = self.generate(
                    system_prompt,
                    f"{user_prompt}\n\n上一轮输出不是合法 JSON。请重新输出且只输出一个合法 JSON 对象，不要输出解释、前后缀或 markdown 代码块。",
                    model=active_model,
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
        else:
            raw_text = self.generate(
                system_prompt,
                f"{user_prompt}\n\n再次强调：只输出一个合法 JSON 对象，不要输出解释、前后缀或 markdown 代码块。",
                model=active_model,
                temperature=temperature,
                timeout=timeout,
                max_tokens=max_tokens,
            )
        return self._extract_json(raw_text)

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = self._sanitize_json_text(text)
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
            candidate = self._repair_json_candidate(object_match.group(1))
            return json.loads(candidate)

        raise ValueError("Model response is not valid JSON.")

    def _repair_json_candidate(self, candidate: str) -> str:
        candidate = candidate.strip()
        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        candidate = re.sub(r'([}\]0-9"\u4e00-\u9fff])(\s*)"([A-Za-z0-9_]+)"\s*:', r"\1,\2\"\3\":", candidate)
        return self._extract_balanced_json(candidate)

    def _sanitize_json_text(self, text: str) -> str:
        text = text.strip().replace("\ufeff", "")
        return "".join(char for char in text if char >= " " or char in "\n\r\t")

    def _create_completion(self, **kwargs):
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return self.client.chat.completions.create(**kwargs)
            except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected completion failure.")

    def _extract_balanced_json(self, text: str) -> str:
        start = text.find("{")
        if start == -1:
            return text

        depth = 0
        in_string = False
        escaped = False
        end = None
        for idx in range(start, len(text)):
            char = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break

        return text[start:end] if end else text
