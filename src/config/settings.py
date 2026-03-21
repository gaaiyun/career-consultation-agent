from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _get_streamlit_secret(key: str) -> str:
    try:
        import streamlit as st  # Local import to avoid hard dependency during non-UI contexts.

        return str(st.secrets.get(key, ""))
    except Exception:
        return ""


def _get_config_value(key: str, default: str = "") -> str:
    return os.getenv(key, "") or _get_streamlit_secret(key) or default


@dataclass(frozen=True)
class Settings:
    app_name: str = "Career Consultation Agent"
    data_dir: Path = Path("data")
    sqlite_path: Path = Path("data/cases.db")
    prompts_dir: Path = Path("src/prompts")
    siliconflow_api_key: str = _get_config_value("SILICONFLOW_API_KEY", "")
    siliconflow_base_url: str = _get_config_value("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    siliconflow_model: str = _get_config_value("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3.2")
    default_timeout: int = int(_get_config_value("SILICONFLOW_TIMEOUT", "60"))

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
