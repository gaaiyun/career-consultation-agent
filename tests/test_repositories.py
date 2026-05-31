"""Tests for the SQLite persistence layer."""
from __future__ import annotations

from src.config.settings import Settings
from src.domain.models import Case, ExportRecord, PromptRun, StageResult, new_case_id
from src.storage.repositories import (
    CaseRepository,
    ExportRepository,
    PromptRunRepository,
    StageResultRepository,
)


def test_create_and_get_case(initialized_settings: Settings) -> None:
    repo = CaseRepository(initialized_settings)
    case = Case(case_id=new_case_id(), client_alias="测试A", source_text="原始文本", tags=["转行"])
    repo.create(case)

    fetched = repo.get(case.case_id)
    assert fetched is not None
    assert fetched.client_alias == "测试A"
    assert fetched.tags == ["转行"]
    assert fetched.current_stage == "intake"


def test_list_cases_orders_by_updated_desc(initialized_settings: Settings) -> None:
    repo = CaseRepository(initialized_settings)
    first = Case(case_id=new_case_id(), client_alias="first", source_text="x")
    second = Case(case_id=new_case_id(), client_alias="second", source_text="y")
    repo.create(first)
    repo.create(second)
    repo.update_stage(first.case_id, "structured_analysis")  # bumps updated_at

    cases = repo.list_cases()
    assert cases[0].case_id == first.case_id


def test_get_missing_case_returns_none(initialized_settings: Settings) -> None:
    assert CaseRepository(initialized_settings).get("nope") is None


def test_stage_versioning_increments(initialized_settings: Settings) -> None:
    repo = StageResultRepository(initialized_settings)
    cid = new_case_id()
    assert repo.next_version_no(cid, "structured_analysis") == 1

    repo.save(
        StageResult(case_id=cid, stage_name="structured_analysis", version_no=1,
                    input_payload={}, output_payload={"v": 1})
    )
    assert repo.next_version_no(cid, "structured_analysis") == 2

    repo.save(
        StageResult(case_id=cid, stage_name="structured_analysis", version_no=2,
                    input_payload={}, output_payload={"v": 2})
    )
    latest = repo.get_latest(cid, "structured_analysis")
    assert latest is not None
    assert latest["output_payload"] == {"v": 2}
    assert latest["version_no"] == 2


def test_list_by_case_returns_all_versions(initialized_settings: Settings) -> None:
    repo = StageResultRepository(initialized_settings)
    cid = new_case_id()
    repo.save(StageResult(case_id=cid, stage_name="questioning", version_no=1,
                          input_payload={}, output_payload={"a": 1}))
    repo.save(StageResult(case_id=cid, stage_name="route_planning", version_no=1,
                          input_payload={}, output_payload={"b": 2}))
    rows = repo.list_by_case(cid)
    assert len(rows) == 2


def test_prompt_run_persists(initialized_settings: Settings) -> None:
    repo = PromptRunRepository(initialized_settings)
    repo.save(
        PromptRun(
            case_id="c1", stage_name="structured_analysis", prompt_name="structured_analysis",
            model="m", temperature=0.2, input_summary="s", raw_response="{}",
            success=True, latency_ms=123,
        )
    )  # should not raise


def test_export_persists(initialized_settings: Settings) -> None:
    repo = ExportRepository(initialized_settings)
    repo.save(ExportRecord(case_id="c1", export_type="markdown", content="# report"))  # no raise
