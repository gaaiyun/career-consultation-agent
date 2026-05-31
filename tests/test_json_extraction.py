"""Tests for the JSON extraction / repair logic in the LLM client.

These exercise only the pure parsing helpers, so no network or API key is used.
"""
from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.llm.client import OpenAICompatibleClient


@pytest.fixture
def client() -> OpenAICompatibleClient:
    return OpenAICompatibleClient(Settings())


def test_plain_json_object(client: OpenAICompatibleClient) -> None:
    assert client._extract_json('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_json_wrapped_in_code_fence(client: OpenAICompatibleClient) -> None:
    text = '这是结果：\n```json\n{"route": "运营", "score": 80}\n```\n以上。'
    assert client._extract_json(text) == {"route": "运营", "score": 80}


def test_json_with_leading_and_trailing_prose(client: OpenAICompatibleClient) -> None:
    text = '好的，输出如下 {"ok": true, "items": [1, 2, 3]} 完毕。'
    assert client._extract_json(text) == {"ok": True, "items": [1, 2, 3]}


def test_trailing_comma_is_repaired(client: OpenAICompatibleClient) -> None:
    text = '{"a": 1, "b": [1, 2,], }'
    assert client._extract_json(text) == {"a": 1, "b": [1, 2]}


def test_bom_and_control_chars_are_stripped(client: OpenAICompatibleClient) -> None:
    text = '﻿{"name": "音乐转运营"}\x00'
    assert client._extract_json(text) == {"name": "音乐转运营"}


def test_chinese_content_preserved(client: OpenAICompatibleClient) -> None:
    parsed = client._extract_json('{"summary": "来访者卡在专业与就业之间"}')
    assert parsed["summary"] == "来访者卡在专业与就业之间"


def test_nested_object_with_braces_in_strings(client: OpenAICompatibleClient) -> None:
    text = '{"note": "用 {placeholder} 表示", "inner": {"k": "v"}}'
    parsed = client._extract_json(text)
    assert parsed["inner"] == {"k": "v"}
    assert parsed["note"] == "用 {placeholder} 表示"


def test_non_json_raises(client: OpenAICompatibleClient) -> None:
    with pytest.raises(ValueError):
        client._extract_json("这里完全没有任何 JSON 内容。")


def test_array_top_level_is_rejected(client: OpenAICompatibleClient) -> None:
    # The pipeline expects a JSON *object* at the top level, not a bare array.
    with pytest.raises(ValueError):
        client._extract_json("[1, 2, 3]")


def test_balanced_json_extraction_stops_at_first_object(client: OpenAICompatibleClient) -> None:
    extracted = client._extract_balanced_json('{"a": {"b": 1}} trailing garbage {"c": 2}')
    assert extracted == '{"a": {"b": 1}}'
