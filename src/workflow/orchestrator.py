from __future__ import annotations

import json
import time
from typing import Any, Callable

from src.config.settings import Settings
from src.domain.models import ExportRecord, PromptRun, StageResult
from src.llm.model_router import ROUTING_SINGLE, resolve_model_for_stage
from src.llm.siliconflow_client import SiliconFlowClient
from src.prompts.registry import PromptRegistry
from src.services.formatters import to_markdown_report
from src.services.normalizers import normalize_stage_output
from src.storage.repositories import (
    CaseRepository,
    ExportRepository,
    PromptRunRepository,
    StageResultRepository,
)
from src.workflow.stages import FINAL_REPORT, QUESTIONING, ROUTE_PLANNING, STRUCTURED_ANALYSIS


SYSTEM_PROMPT = (
    "你是一个职业咨询师助手。你的职责是把来访者的碎片化叙述转化为结构化信息、"
    "矛盾追问、路线规划和正式回复稿。你要遵守 GPS+锚点 的咨询思路：先做定位系统、"
    "动力系统、约束系统拆解，再做逻辑校准和路线反推。不要虚构事实，不要越权做心理诊断。"
)

# Human notes are stored as stage_name pattern: "{stage_name}_notes"
_NOTES_SUFFIX = "_notes"


class ConsultationWorkflowService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.active_model = settings.siliconflow_model
        self.routing_key = ROUTING_SINGLE
        self.case_repo = CaseRepository(settings)
        self.stage_repo = StageResultRepository(settings)
        self.prompt_repo = PromptRunRepository(settings)
        self.export_repo = ExportRepository(settings)
        self.prompt_registry = PromptRegistry(settings)
        self.llm_client = SiliconFlowClient(settings)

    def set_active_model(self, model_name: str) -> None:
        self.active_model = model_name

    def set_routing_key(self, routing_key: str) -> None:
        self.routing_key = routing_key

    # ------------------------------------------------------------------ #
    # Human notes API
    # ------------------------------------------------------------------ #

    def save_human_notes(self, case_id: str, stage_name: str, notes: str) -> None:
        """Persist consultant's free-text notes for a stage.

        Notes are stored under a virtual stage name ``{stage_name}_notes``
        so they are versioned like other stage outputs without changing the schema.
        """
        notes_stage = f"{stage_name}{_NOTES_SUFFIX}"
        version_no = self.stage_repo.next_version_no(case_id, notes_stage)
        self.stage_repo.save(
            StageResult(
                case_id=case_id,
                stage_name=notes_stage,
                version_no=version_no,
                input_payload={"source": "human_notes"},
                output_payload={"notes": notes},
            )
        )

    def get_human_notes(self, case_id: str, stage_name: str) -> str:
        """Return the latest human notes for a stage, or empty string."""
        notes_stage = f"{stage_name}{_NOTES_SUFFIX}"
        result = self._latest_output(case_id, notes_stage)
        return result.get("notes", "") if result else ""

    # ------------------------------------------------------------------ #
    # Stage runners
    # ------------------------------------------------------------------ #

    def run_structured_analysis(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        variables = {"source_text": case.source_text}
        return self._run_stage(STRUCTURED_ANALYSIS, case_id, variables, model_name=model_name)

    def run_question_generation(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        structured_analysis = self._latest_output(case_id, STRUCTURED_ANALYSIS.name)
        if not structured_analysis:
            raise ValueError("Please complete structured analysis first.")

        # Use a compact summary instead of the full JSON to reduce prompt size
        # and improve stability of the questioning stage.
        analysis_summary = self._build_analysis_summary(structured_analysis)
        human_notes = self.get_human_notes(case_id, STRUCTURED_ANALYSIS.name)

        variables = {
            "source_text": case.source_text,
            "structured_analysis_summary": analysis_summary,
            "structured_analysis_human_notes": human_notes or "（无）",
        }
        return self._run_stage(QUESTIONING, case_id, variables, model_name=model_name)

    def save_question_answers(self, case_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.save_manual_stage_output(case_id, QUESTIONING.name, payload)
        return payload

    def run_route_planning(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        structured_analysis = self._latest_output(case_id, STRUCTURED_ANALYSIS.name)
        questions = self._latest_output(case_id, QUESTIONING.name)
        if not structured_analysis:
            raise ValueError("Please complete structured analysis first.")

        # Compact summary of the questioning stage output
        questioning_summary = self._build_questioning_summary(questions) if questions else "（无追问记录）"
        questioning_human_notes = self.get_human_notes(case_id, QUESTIONING.name)
        # Feasibility check notes are stored under the route_planning stage itself
        feasibility_notes = self.get_human_notes(case_id, "route_feasibility")

        variables = {
            "source_text": case.source_text,
            "structured_analysis_json": json.dumps(structured_analysis, ensure_ascii=False, indent=2),
            "questioning_summary": questioning_summary,
            "questioning_human_notes": questioning_human_notes or "（无）",
            "feasibility_check_notes": feasibility_notes or "（无）",
        }
        return self._run_stage(ROUTE_PLANNING, case_id, variables, model_name=model_name)

    def run_final_report(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        structured_analysis = self._latest_output(case_id, STRUCTURED_ANALYSIS.name)
        route_plan = self._latest_output(case_id, ROUTE_PLANNING.name)
        if not structured_analysis or not route_plan:
            raise ValueError("Please complete prior stages first.")

        route_planning_human_notes = self.get_human_notes(case_id, ROUTE_PLANNING.name)

        variables = {
            "source_text": case.source_text,
            "structured_analysis_json": json.dumps(structured_analysis, ensure_ascii=False, indent=2),
            "route_plan_json": json.dumps(route_plan, ensure_ascii=False, indent=2),
            "route_planning_human_notes": route_planning_human_notes or "（无）",
        }
        return self._run_stage(FINAL_REPORT, case_id, variables, model_name=model_name)

    # ------------------------------------------------------------------ #
    # Pipeline: run all remaining stages in order
    # ------------------------------------------------------------------ #

    def run_pipeline_remaining(
        self,
        case_id: str,
        on_stage_start: Callable[[str], None] | None = None,
        on_stage_done: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Run all stages that don't yet have output, in order.

        Returns the list of stage names that were executed.
        Calls on_stage_start / on_stage_done callbacks (if provided) so the
        caller can update a progress indicator.
        """
        stage_funcs: list[tuple[str, Callable]] = [
            (STRUCTURED_ANALYSIS.name, self.run_structured_analysis),
            (QUESTIONING.name, self.run_question_generation),
            (ROUTE_PLANNING.name, self.run_route_planning),
            (FINAL_REPORT.name, self.run_final_report),
        ]
        completed: list[str] = []
        for stage_name, func in stage_funcs:
            if self._latest_output(case_id, stage_name) is None:
                if on_stage_start:
                    on_stage_start(stage_name)
                func(case_id)
                completed.append(stage_name)
                if on_stage_done:
                    on_stage_done(stage_name)
        return completed

    def completed_stages(self, case_id: str) -> list[str]:
        """Return list of stage names that already have at least one output."""
        all_stages = [
            STRUCTURED_ANALYSIS.name,
            QUESTIONING.name,
            ROUTE_PLANNING.name,
            FINAL_REPORT.name,
        ]
        return [s for s in all_stages if self._latest_output(case_id, s) is not None]

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #

    def export_report_markdown(self, case_id: str) -> str:
        final_report = self._latest_output(case_id, FINAL_REPORT.name)
        if not final_report:
            raise ValueError("No final report available for export.")
        content = to_markdown_report(final_report)
        self.export_repo.save(ExportRecord(case_id=case_id, export_type="markdown", content=content))
        return content

    def get_latest_stage_output(self, case_id: str, stage_name: str) -> dict[str, Any] | None:
        return self._latest_output(case_id, stage_name)

    def list_stage_versions(self, case_id: str) -> list[dict[str, Any]]:
        return self.stage_repo.list_by_case(case_id)

    def save_manual_stage_output(
        self,
        case_id: str,
        stage_name: str,
        payload: dict[str, Any],
        *,
        input_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = normalize_stage_output(stage_name, payload)
        version_no = self.stage_repo.next_version_no(case_id, stage_name)
        self.stage_repo.save(
            StageResult(
                case_id=case_id,
                stage_name=stage_name,
                version_no=version_no,
                input_payload=input_payload or {"source": "manual_edit"},
                output_payload=payload,
            )
        )
        self.case_repo.update_stage(case_id, stage_name)
        return payload

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _build_analysis_summary(self, analysis: dict[str, Any]) -> str:
        """Build a compact text summary of structured analysis for the step 2 prompt.

        Deliberately excludes the full GPS JSON to keep the prompt short and
        avoid the truncation/timeout issues that occur when the full blob is
        embedded inside the questioning prompt.
        """
        parts: list[str] = []

        core = analysis.get("core_profile", {})
        if core.get("one_sentence_summary"):
            parts.append(f"核心画像：{core['one_sentence_summary']}")
        if core.get("tags"):
            parts.append(f"标签：{', '.join(core['tags'])}")

        contradictions = analysis.get("contradictions", [])
        if contradictions:
            parts.append("\n主要矛盾：")
            for c in contradictions:
                parts.append(
                    f"- 【{c.get('label', '')}】{c.get('description', '')} "
                    f"（关键性：{c.get('why_it_matters', '')}）"
                )

        gps = analysis.get("gps_analysis", {})
        constraint = gps.get("constraint_system", {})
        external = constraint.get("external_reality", [])
        internal = constraint.get("internal_obstacles", [])
        if external:
            parts.append(f"\n外部约束：{' / '.join(external[:4])}")
        if internal:
            parts.append(f"内在障碍：{' / '.join(internal[:4])}")

        notes = analysis.get("consultant_notes", {})
        missing = notes.get("missing_information", [])
        if missing:
            parts.append(f"\n最缺信息：{' / '.join(missing[:5])}")
        bias = notes.get("bias_risks", [])
        if bias:
            parts.append(f"认知偏差风险：{' / '.join(bias[:3])}")

        directions = analysis.get("possible_directions", [])
        if directions:
            parts.append("\n初步方向（待验证）：")
            for d in directions:
                parts.append(f"- {d}")

        return "\n".join(parts)

    def _build_questioning_summary(self, questioning: dict[str, Any]) -> str:
        """Build a compact text summary of questioning stage for the step 3 prompt."""
        parts: list[str] = []

        strategy = questioning.get("question_strategy", {})
        if strategy.get("goal"):
            parts.append(f"追问目标：{strategy['goal']}")

        questions = questioning.get("questions", [])
        if questions:
            parts.append("\n关键问题与回答：")
            for q in questions[:5]:
                text = q.get("question_text", "")
                answer = q.get("answer", "").strip()
                if text:
                    parts.append(f"- 问：{text}")
                    if answer:
                        parts.append(f"  答：{answer}")
                    else:
                        parts.append("  答：（未填写）")

        logic_checks = questioning.get("logic_checks", [])
        if logic_checks:
            parts.append("\n逻辑校验：")
            for lc in logic_checks[:3]:
                assumption = lc.get("assumption", "")
                risk = lc.get("risk", "")
                if assumption:
                    parts.append(f"- 假设：{assumption}")
                    if risk:
                        parts.append(f"  风险：{risk}")

        return "\n".join(parts)

    def _run_stage(
        self,
        stage,
        case_id: str,
        variables: dict[str, str],
        *,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        prompt = self.prompt_registry.render_prompt(stage.prompt_name, variables)
        start_time = time.perf_counter()
        raw_response = ""
        success = False
        if self.routing_key == ROUTING_SINGLE and model_name:
            used_model = model_name
        else:
            used_model = resolve_model_for_stage(
                stage.name,
                routing_key=self.routing_key,
                fallback_model=self.active_model or self.settings.siliconflow_model,
            )
        try:
            if stage.expects_json:
                output = self.llm_client.generate_json(
                    SYSTEM_PROMPT,
                    prompt,
                    model=used_model,
                    temperature=stage.temperature,
                    max_tokens=stage.max_tokens,
                )
                raw_response = json.dumps(output, ensure_ascii=False)
            else:
                report_markdown = self.llm_client.generate(
                    SYSTEM_PROMPT,
                    prompt,
                    model=used_model,
                    temperature=stage.temperature,
                    max_tokens=stage.max_tokens,
                )
                output = {"report_markdown": report_markdown}
                raw_response = report_markdown
            success = True
        except Exception as exc:
            raw_response = str(exc)
            raise
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            self.prompt_repo.save(
                PromptRun(
                    case_id=case_id,
                    stage_name=stage.name,
                    prompt_name=stage.prompt_name,
                    model=used_model,
                    temperature=stage.temperature,
                    input_summary=self._build_input_summary(variables),
                    raw_response=raw_response,
                    success=success,
                    latency_ms=latency_ms,
                )
            )

        version_no = self.stage_repo.next_version_no(case_id, stage.name)
        output = normalize_stage_output(stage.name, output)
        self.stage_repo.save(
            StageResult(
                case_id=case_id,
                stage_name=stage.name,
                version_no=version_no,
                input_payload=variables,
                output_payload=output,
            )
        )
        self.case_repo.update_stage(case_id, stage.name)
        return output

    def _build_input_summary(self, variables: dict[str, str]) -> str:
        summary_parts = []
        for key, value in variables.items():
            summary_parts.append(f"{key}:{value[:120]}")
        return " | ".join(summary_parts)

    def _latest_output(self, case_id: str, stage_name: str) -> dict[str, Any] | None:
        latest = self.stage_repo.get_latest(case_id, stage_name)
        return latest["output_payload"] if latest else None

    def _must_get_case(self, case_id: str):
        case = self.case_repo.get(case_id)
        if not case:
            raise ValueError(f"Case not found: {case_id}")
        return case
