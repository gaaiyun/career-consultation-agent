"""Tests for provider-agnostic configuration resolution."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.settings import Settings, _get_config_value, _native_json_default


@pytest.fixture(autouse=True)
def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "LLM_TIMEOUT",
        "LLM_NATIVE_JSON",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "SILICONFLOW_API_KEY",
        "SILICONFLOW_BASE_URL",
        "SILICONFLOW_MODEL",
        "SILICONFLOW_TIMEOUT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_generic_key_preferred(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "generic-key")
    monkeypatch.setenv("SILICONFLOW_API_KEY", "legacy-key")
    assert _get_config_value("LLM_API_KEY", "OPENAI_API_KEY", "SILICONFLOW_API_KEY") == "generic-key"


def test_falls_back_to_legacy_siliconflow_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "legacy-key")
    assert _get_config_value("LLM_API_KEY", "OPENAI_API_KEY", "SILICONFLOW_API_KEY") == "legacy-key"


def test_openai_alias_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    resolved = _get_config_value(
        "LLM_BASE_URL", "OPENAI_BASE_URL", "SILICONFLOW_BASE_URL", default="x"
    )
    assert resolved == "https://api.deepseek.com"


def test_default_used_when_nothing_set() -> None:
    assert _get_config_value("LLM_BASE_URL", default="fallback") == "fallback"


def test_empty_value_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("SILICONFLOW_API_KEY", "real")
    assert _get_config_value("LLM_API_KEY", "SILICONFLOW_API_KEY") == "real"


def test_backward_compat_property_aliases() -> None:
    s = replace(Settings(), llm_api_key="k", llm_base_url="u", llm_model="m")
    assert s.siliconflow_api_key == "k"
    assert s.siliconflow_base_url == "u"
    assert s.siliconflow_model == "m"


def test_native_json_default_is_true_for_common_endpoints() -> None:
    assert _native_json_default("https://api.deepseek.com") is True
    assert _native_json_default("https://api.siliconflow.cn/v1") is True


def test_native_json_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_NATIVE_JSON", "false")
    assert Settings().native_json_mode is False
    monkeypatch.setenv("LLM_NATIVE_JSON", "1")
    assert Settings().native_json_mode is True


def test_supported_models_have_no_obviously_fake_ids() -> None:
    # Guard against the previously-shipped non-existent Qwen variant.
    assert "Qwen/Qwen3.5-397B-A17B" not in Settings().supported_models
