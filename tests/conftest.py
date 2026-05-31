from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import Settings  # noqa: E402
from src.storage.db import init_db  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """A Settings instance pointed at an isolated temp SQLite database."""
    base = Settings(
        data_dir=tmp_path,
        sqlite_path=tmp_path / "cases.db",
        prompts_dir=ROOT / "src" / "prompts",
    )
    base.ensure_directories()
    return base


@pytest.fixture
def initialized_settings(settings: Settings) -> Settings:
    init_db(settings)
    return settings


def make_settings(**overrides) -> Settings:
    """Helper to build a Settings with specific overrides (e.g. llm_base_url)."""
    base = Settings()
    return replace(base, **overrides)
