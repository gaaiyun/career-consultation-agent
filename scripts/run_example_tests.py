from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import get_settings
from src.domain.models import Case, new_case_id
from src.llm.model_router import ROUTING_SINGLE
from src.storage.db import init_db
from src.storage.repositories import CaseRepository
from src.workflow.orchestrator import ConsultationWorkflowService


EXAMPLES = [
    ("case_01_ruc_han_language.txt", "RUC汉语言"),
    ("case_02_music_major_transition.txt", "音乐转运营"),
    ("case_03_b2b_content_operator.txt", "B端内容运营"),
    ("case_04_ruc_labor_econ_gap.txt", "人大劳经GAP"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=[item[0] for item in EXAMPLES], default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--routing", default=ROUTING_SINGLE)
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings)
    case_repo = CaseRepository(settings)
    workflow = ConsultationWorkflowService(settings)
    workflow.set_routing_key(args.routing)
    if args.model:
        workflow.set_active_model(args.model)

    if not workflow.llm_client.is_configured():
        raise RuntimeError("Missing SILICONFLOW_API_KEY")

    examples_dir = Path("examples")
    results_dir = Path("tmp/test_outputs")
    results_dir.mkdir(parents=True, exist_ok=True)

    selected_examples = [item for item in EXAMPLES if args.case in (None, item[0])]

    for filename, alias in selected_examples:
        text = (examples_dir / filename).read_text(encoding="utf-8")
        case = Case(case_id=new_case_id(), client_alias=alias, source_text=text)
        case_repo.create(case)

        print(f"[START] {filename}", flush=True)
        structured = workflow.run_structured_analysis(case.case_id, model_name=args.model)
        print(f"[DONE] structured_analysis -> {filename}", flush=True)
        questioning = workflow.run_question_generation(case.case_id, model_name=args.model)
        print(f"[DONE] questioning -> {filename}", flush=True)
        route_plan = workflow.run_route_planning(case.case_id, model_name=args.model)
        print(f"[DONE] route_planning -> {filename}", flush=True)
        final_report = workflow.run_final_report(case.case_id, model_name=args.model)
        print(f"[DONE] final_report -> {filename}", flush=True)

        output = {
            "case_id": case.case_id,
            "alias": alias,
            "routing": args.routing,
            "model": args.model or settings.siliconflow_model,
            "structured_analysis": structured,
            "questioning": questioning,
            "route_planning": route_plan,
            "final_report": final_report,
        }
        (results_dir / f"{filename}.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[COMPLETE] {filename}", flush=True)


if __name__ == "__main__":
    main()
