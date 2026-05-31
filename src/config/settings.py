from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _get_streamlit_secret(key: str) -> str:
    if not any("streamlit" in arg.lower() for arg in sys.argv):
        return ""
    try:
        import streamlit as st  # Local import to avoid hard dependency during non-UI contexts.

        return str(st.secrets.get(key, ""))
    except Exception:
        return ""


def _get_config_value(*keys: str, default: str = "") -> str:
    """Return the first non-empty value found across env vars and Streamlit secrets.

    Each key is tried against both ``os.environ`` and Streamlit secrets before
    moving on. This lets us prefer the provider-agnostic ``LLM_*`` names while
    still honouring the legacy ``SILICONFLOW_*`` configuration.
    """
    for key in keys:
        value = os.getenv(key, "") or _get_streamlit_secret(key)
        if value:
            return value
    return default


def _native_json_default(base_url: str) -> bool:
    """Whether the endpoint reliably supports ``response_format={"type": "json_object"}``.

    DeepSeek's direct API and most OpenAI-compatible gateways support it; we let
    callers override via ``LLM_NATIVE_JSON``. We only auto-disable for endpoints
    that are known to choke on the parameter.
    """
    url = base_url.lower()
    if "siliconflow" in url:
        # SiliconFlow honours json_object for some models but not all; the client
        # already has a robust fallback, so we let it try and recover.
        return True
    return True


@dataclass(frozen=True)
class Settings:
    app_name: str = "Career Consultation Agent"
    data_dir: Path = Path(_get_config_value("APP_DATA_DIR", default="data"))
    sqlite_path: Path = Path(_get_config_value("SQLITE_PATH", default="data/cases.db"))
    prompts_dir: Path = Path(_get_config_value("PROMPTS_DIR", default="src/prompts"))

    # Provider-agnostic LLM config. We read the generic ``LLM_*`` names first and
    # fall back to the legacy ``SILICONFLOW_*`` ones so existing deployments keep
    # working without changes.
    llm_api_key: str = _get_config_value("LLM_API_KEY", "OPENAI_API_KEY", "SILICONFLOW_API_KEY")
    llm_base_url: str = _get_config_value(
        "LLM_BASE_URL",
        "OPENAI_BASE_URL",
        "SILICONFLOW_BASE_URL",
        default="https://api.siliconflow.cn/v1",
    )
    llm_model: str = _get_config_value(
        "LLM_MODEL",
        "OPENAI_MODEL",
        "SILICONFLOW_MODEL",
        default="deepseek-ai/DeepSeek-V3.2",
    )
    default_timeout: int = int(
        _get_config_value("LLM_TIMEOUT", "SILICONFLOW_TIMEOUT", default="90")
    )
    supported_models: tuple[str, ...] = (
        "deepseek-ai/DeepSeek-V3.2",
        "zai-org/GLM-4.6",
        "moonshotai/Kimi-K2-Thinking",
        "Qwen/Qwen3-235B-A22B-Instruct-2507",
    )

    # ------------------------------------------------------------------ #
    # Backwards-compatible aliases
    #
    # Earlier code (and external scripts) referenced ``siliconflow_*`` fields.
    # Keep them as read-only aliases so nothing breaks while the rest of the
    # codebase migrates to the provider-neutral names.
    # ------------------------------------------------------------------ #
    @property
    def siliconflow_api_key(self) -> str:
        return self.llm_api_key

    @property
    def siliconflow_base_url(self) -> str:
        return self.llm_base_url

    @property
    def siliconflow_model(self) -> str:
        return self.llm_model

    @property
    def native_json_mode(self) -> bool:
        override = _get_config_value("LLM_NATIVE_JSON")
        if override:
            return override.strip().lower() not in {"0", "false", "no", "off"}
        return _native_json_default(self.llm_base_url)

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
