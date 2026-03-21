from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import get_settings
from src.llm.model_router import ROUTING_GLM_ONLY, ROUTING_HYBRID
from src.workflow.orchestrator import ConsultationWorkflowService
from src.domain.models import Case, new_case_id
from src.storage.db import init_db
from src.storage.repositories import CaseRepository


def main() -> None:
    settings = get_settings()
    init_db(settings)
    case_repo = CaseRepository(settings)
    workflow = ConsultationWorkflowService(settings)

    source_text = Path("examples/case_01_ruc_han_language.txt").read_text(encoding="utf-8")
    case = Case(case_id=new_case_id(), client_alias="routing_test_case", source_text=source_text)
    case_repo.create(case)

    results = {}

    for routing in [ROUTING_GLM_ONLY, ROUTING_HYBRID]:
        workflow.set_routing_key(routing)
        results[routing] = {}

        start = time.time()
        try:
            structured = workflow.run_structured_analysis(case.case_id)
            results[routing]["structured_analysis"] = {
                "success": True,
                "elapsed_seconds": round(time.time() - start, 2),
                "summary": structured.get("core_profile", {}).get("one_sentence_summary", ""),
            }
            print(f"[OK] {routing} structured", flush=True)
        except Exception as exc:
            results[routing]["structured_analysis"] = {
                "success": False,
                "elapsed_seconds": round(time.time() - start, 2),
                "error": str(exc),
            }
            print(f"[ERR] {routing} structured -> {exc}", flush=True)

    Path("tmp").mkdir(exist_ok=True)
    Path("tmp/test_routing_profiles.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
