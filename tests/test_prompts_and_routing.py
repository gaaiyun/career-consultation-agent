"""Tests for prompt rendering, model routing, and stage definitions."""
from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.llm.model_router import (
    ROUTING_GLM_ONLY,
    ROUTING_HYBRID,
    ROUTING_PROFILES,
    ROUTING_SINGLE,
    resolve_model_for_stage,
)
from src.prompts.registry import PromptRegistry
from src.workflow.stages import (
    FINAL_REPORT,
    QUESTIONING,
    ROUTE_PLANNING,
    STAGE_ORDER,
    STRUCTURED_ANALYSIS,
)


# ---------------------------------------------------------------------- #
# Prompt registry
# ---------------------------------------------------------------------- #


@pytest.fixture
def registry() -> PromptRegistry:
    return PromptRegistry(Settings())


def test_all_stage_prompts_exist(registry: PromptRegistry) -> None:
    for stage in (STRUCTURED_ANALYSIS, QUESTIONING, ROUTE_PLANNING, FINAL_REPORT):
        text = registry.get_prompt(stage.prompt_name)
        assert text.strip(), f"prompt {stage.prompt_name} is empty"


def test_render_substitutes_variables(registry: PromptRegistry) -> None:
    rendered = registry.render_prompt("structured_analysis", {"source_text": "我是测试来访者"})
    assert "我是测试来访者" in rendered
    assert "{{ source_text }}" not in rendered


def test_render_leaves_unknown_placeholders(registry: PromptRegistry) -> None:
    rendered = registry.render_prompt("route_planning", {"source_text": "X"})
    # variables we didn't pass remain as placeholders (caller always passes all)
    assert "{{ structured_analysis_json }}" in rendered


def test_missing_prompt_raises(registry: PromptRegistry) -> None:
    with pytest.raises(FileNotFoundError):
        registry.get_prompt("does_not_exist")


# ---------------------------------------------------------------------- #
# Model routing
# ---------------------------------------------------------------------- #


def test_single_model_routing_uses_fallback() -> None:
    model = resolve_model_for_stage(
        STRUCTURED_ANALYSIS.name, routing_key=ROUTING_SINGLE, fallback_model="my-model"
    )
    assert model == "my-model"


def test_glm_only_routing_maps_every_stage_to_glm() -> None:
    for stage in (STRUCTURED_ANALYSIS, QUESTIONING, ROUTE_PLANNING, FINAL_REPORT):
        model = resolve_model_for_stage(
            stage.name, routing_key=ROUTING_GLM_ONLY, fallback_model="fallback"
        )
        assert model == "zai-org/GLM-4.6"


def test_hybrid_routing_splits_report_to_deepseek() -> None:
    assert (
        resolve_model_for_stage(
            FINAL_REPORT.name, routing_key=ROUTING_HYBRID, fallback_model="fallback"
        )
        == "deepseek-ai/DeepSeek-V3.2"
    )
    assert (
        resolve_model_for_stage(
            STRUCTURED_ANALYSIS.name, routing_key=ROUTING_HYBRID, fallback_model="fallback"
        )
        == "zai-org/GLM-4.6"
    )


def test_unknown_routing_key_falls_back() -> None:
    assert (
        resolve_model_for_stage("anything", routing_key="bogus", fallback_model="fb")
        == "fb"
    )


def test_routing_profiles_cover_all_real_stages() -> None:
    real_stages = {STRUCTURED_ANALYSIS.name, QUESTIONING.name, ROUTE_PLANNING.name, FINAL_REPORT.name}
    for key, profile in ROUTING_PROFILES.items():
        if key == ROUTING_SINGLE:
            continue
        assert set(profile.stage_models.keys()) == real_stages


def test_stage_order_is_consistent() -> None:
    assert STAGE_ORDER == [
        "intake",
        STRUCTURED_ANALYSIS.name,
        QUESTIONING.name,
        ROUTE_PLANNING.name,
        FINAL_REPORT.name,
    ]
