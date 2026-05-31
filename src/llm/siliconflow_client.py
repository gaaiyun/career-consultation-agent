"""Backwards-compatible shim.

The LLM client is now provider-agnostic and lives in :mod:`src.llm.client`.
This module is kept so existing imports of ``SiliconFlowClient`` keep working.
"""
from __future__ import annotations

from src.llm.client import OpenAICompatibleClient, SiliconFlowClient

__all__ = ["OpenAICompatibleClient", "SiliconFlowClient"]
