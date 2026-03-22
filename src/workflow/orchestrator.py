from __future__ import annotations

import json
import time
from typing import Any

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

    def run_structured_analysis(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        variables = {"source_text": case.source_text}
        return self._run_stage(STRUCTURED_ANALYSIS, case_id, variables, model_name=model_name)

    def run_question_generation(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        structured_analysis = self._latest_output(case_id, STRUCTURED_ANALYSIS.name)
        if not structured_analysis:
            raise ValueError("Please complete structured analysis first.")
        variables = {
            "source_text": case.source_text,
            "structured_analysis_json": json.dumps(structured_analysis, ensure_ascii=False, indent=2),
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
        variables = {
            "source_text": case.source_text,
            "structured_analysis_json": json.dumps(structured_analysis, ensure_ascii=False, indent=2),
            "follow_up_questions_json": json.dumps(questions or {"questions": []}, ensure_ascii=False, indent=2),
        }
        return self._run_stage(ROUTE_PLANNING, case_id, variables, model_name=model_name)

    def run_final_report(self, case_id: str, model_name: str | None = None) -> dict[str, Any]:
        case = self._must_get_case(case_id)
        structured_analysis = self._latest_output(case_id, STRUCTURED_ANALYSIS.name)
        route_plan = self._latest_output(case_id, ROUTE_PLANNING.name)
        if not structured_analysis or not route_plan:
            raise ValueError("Please complete prior stages first.")
        variables = {
            "source_text": case.source_text,
            "structured_analysis_json": json.dumps(structured_analysis, ensure_ascii=False, indent=2),
            "route_plan_json": json.dumps(route_plan, ensure_ascii=False, indent=2),
        }
        return self._run_stage(FINAL_REPORT, case_id, variables, model_name=model_name)

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
