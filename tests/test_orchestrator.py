"""End-to-end workflow tests using a fake LLM client (no network, no API key).

These prove the orchestration wiring: prompt assembly, stage ordering,
human-note injection into downstream prompts, versioning, and manual edits.
"""
from __future__ import annotations

from typing import Any

import pytest

from src.config.settings import Settings
from src.domain.models import Case, new_case_id
from src.llm.base import BaseLLMClient
from src.storage.repositories import CaseRepository
from src.workflow.orchestrator import ConsultationWorkflowService
from src.workflow.stages import (
    FINAL_REPORT,
    QUESTIONING,
    ROUTE_PLANNING,
    STRUCTURED_ANALYSIS,
)


class FakeLLMClient(BaseLLMClient):
    """Records every prompt it receives and returns canned stage payloads."""

    def __init__(self, *_args, **_kwargs) -> None:
        self.calls: list[dict[str, Any]] = []

    def is_configured(self) -> bool:
        return True

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        self.calls.append({"kind": "text", "system": system_prompt, "user": user_prompt, **kwargs})
        return "# 终版报告\n\n这是一段测试报告正文。"

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict[str, Any]:
        self.calls.append({"kind": "json", "system": system_prompt, "user": user_prompt, **kwargs})
        # Branch on each stage's distinctive top-level schema key. These appear
        # only in that stage's own template (inside its ```json``` block), never
        # in the compact summaries that downstream prompts embed -- so the order
        # of checks does not matter and cannot be confused by injected context.
        if '"question_strategy"' in user_prompt:
            return {
                "question_strategy": {"goal": "校准目标岗位", "priority_rule": "先问最影响路线的"},
                "questions": [{"question_text": "你理解的运营具体是什么？", "priority": "high"}],
                "logic_checks": [{"assumption": "必须转行", "risk": "可能是定位问题"}],
            }
        if '"planning_summary"' in user_prompt:
            return {
                "planning_summary": {"decision_frame": "条件+需求", "core_tradeoff": "稳定 vs 成长"},
                "route_options": [
                    {"route_name": "音乐平台内容运营", "fit_score": 85,
                     "fit_reasons": ["可复用行业认知"], "prep_actions": ["改简历"]},
                    {"route_name": "音乐教培运营", "fit_score": 60},
                ],
            }
        # default: structured analysis ("core_profile" is its first schema key)
        return {
            "core_profile": {"one_sentence_summary": "音乐生想转运营但缺方向", "tags": ["转行", "应届"]},
            "contradictions": [
                {"label": "能力错位", "description": "想转运营但没作品", "why_it_matters": "影响路线"}
            ],
            "possible_directions": ["音乐平台内容运营"],
        }


@pytest.fixture
def service(initialized_settings: Settings) -> tuple[ConsultationWorkflowService, FakeLLMClient, str]:
    svc = ConsultationWorkflowService(initialized_settings)
    fake = FakeLLMClient()
    svc.llm_client = fake  # inject fake, no network

    case_id = new_case_id()
    CaseRepository(initialized_settings).create(
        Case(case_id=case_id, client_alias="音乐转运营", source_text="我是音乐学应届生，想转运营但很迷茫……")
    )
    return svc, fake, case_id


def test_structured_analysis_runs_and_persists(service) -> None:
    svc, _fake, cid = service
    out = svc.run_structured_analysis(cid)
    assert out["core_profile"]["one_sentence_summary"]
    # persisted as version 1
    latest = svc.get_latest_stage_output(cid, STRUCTURED_ANALYSIS.name)
    assert latest is not None
    assert latest["core_profile"]["tags"] == ["转行", "应届"]


def test_questioning_requires_structured_first(service) -> None:
    svc, _fake, cid = service
    with pytest.raises(ValueError):
        svc.run_question_generation(cid)


def test_full_pipeline_runs_all_stages_in_order(service) -> None:
    svc, _fake, cid = service
    executed = svc.run_pipeline_remaining(cid)
    assert executed == [
        STRUCTURED_ANALYSIS.name,
        QUESTIONING.name,
        ROUTE_PLANNING.name,
        FINAL_REPORT.name,
    ]
    assert svc.completed_stages(cid) == executed
    # final report exportable
    md = svc.export_report_markdown(cid)
    assert "终版报告" in md


def test_pipeline_skips_already_completed(service) -> None:
    svc, _fake, cid = service
    svc.run_structured_analysis(cid)
    executed = svc.run_pipeline_remaining(cid)
    assert STRUCTURED_ANALYSIS.name not in executed
    assert executed[0] == QUESTIONING.name


def test_human_notes_injected_into_downstream_prompt(service) -> None:
    svc, fake, cid = service
    svc.run_structured_analysis(cid)
    svc.save_human_notes(cid, STRUCTURED_ANALYSIS.name, "咨询师判断：真正问题是缺作品，不是能力差")
    fake.calls.clear()
    svc.run_question_generation(cid)
    # the questioning prompt should carry the consultant's note verbatim
    last = fake.calls[-1]
    assert "缺作品" in last["user"]


def test_feasibility_notes_injected_into_route_prompt(service) -> None:
    svc, fake, cid = service
    svc.run_structured_analysis(cid)
    svc.run_question_generation(cid)
    svc.save_human_notes(cid, "route_feasibility", "音乐版权专员岗位极少，不要列为主推")
    fake.calls.clear()
    svc.run_route_planning(cid)
    assert "音乐版权专员岗位极少" in fake.calls[-1]["user"]


def test_manual_edit_creates_new_version(service) -> None:
    svc, _fake, cid = service
    svc.run_structured_analysis(cid)
    svc.save_manual_stage_output(
        cid, STRUCTURED_ANALYSIS.name, {"core_profile": {"one_sentence_summary": "人工修订"}}
    )
    latest = svc.get_latest_stage_output(cid, STRUCTURED_ANALYSIS.name)
    assert latest["core_profile"]["one_sentence_summary"] == "人工修订"
    # two versions now exist (AI + manual)
    versions = [
        v for v in svc.list_stage_versions(cid) if v["stage_name"] == STRUCTURED_ANALYSIS.name
    ]
    assert len(versions) == 2


def test_route_planning_recommended_autofilled_via_normalizer(service) -> None:
    svc, _fake, cid = service
    svc.run_structured_analysis(cid)
    svc.run_question_generation(cid)
    out = svc.run_route_planning(cid)
    # best fit_score route promoted to recommended by the normalizer
    assert out["recommended_route"]["route_name"] == "音乐平台内容运营"


def test_prompt_run_logged_with_model(service) -> None:
    svc, _fake, cid = service
    svc.run_structured_analysis(cid)
    # the orchestrator records a PromptRun row; default single-model routing
    # uses the configured model. We assert the call carried a model kwarg.
    assert svc.llm_client.calls[-1].get("model")


def test_export_without_report_raises(service) -> None:
    svc, _fake, cid = service
    with pytest.raises(ValueError):
        svc.export_report_markdown(cid)
