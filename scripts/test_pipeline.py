"""Quick pipeline test - runs steps 1 and 2 on case_02 (music transition)."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SILICONFLOW_API_KEY", "sk-qbywdfjgxkaxwxhcnbvnmhwiuguwgzrldrstlzsfivomsxub")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings
from src.domain.models import Case, new_case_id
from src.storage.db import init_db
from src.storage.repositories import CaseRepository
from src.workflow.orchestrator import ConsultationWorkflowService


def main() -> None:
    s = get_settings()
    init_db(s)
    repo = CaseRepository(s)
    svc = ConsultationWorkflowService(s)

    # Load case_02 (music major - the problematic one)
    with open("examples/case_02_music_major_transition.txt", encoding="utf-8") as f:
        text = f.read()

    case_id = new_case_id()
    case = Case(case_id=case_id, client_alias="test_music_02", source_text=text)
    repo.create(case)
    print(f"Case created: {case_id}")

    # Step 1
    print("\n--- Step 1: structured_analysis ---")
    result1 = svc.run_structured_analysis(case_id)
    summary = result1.get("core_profile", {}).get("one_sentence_summary", "")
    contradictions = result1.get("contradictions", [])
    print(f"Summary: {summary[:100]}")
    print(f"Contradictions: {len(contradictions)}")
    for c in contradictions:
        print(f"  - {c.get('label', '')}: {c.get('description', '')[:60]}")

    # Step 2
    print("\n--- Step 2: questioning (compact summary) ---")
    summary_text = svc._build_analysis_summary(result1)
    print(f"Analysis summary length: {len(summary_text)} chars (was ~2000+ chars full JSON)")
    result2 = svc.run_question_generation(case_id)
    questions = result2.get("questions", [])
    print(f"Got {len(questions)} questions:")
    for q in questions:
        print(f"  Q: {q.get('question_text', '')[:80]}")

    # Step 3
    print("\n--- Step 3: route_planning ---")
    result3 = svc.run_route_planning(case_id)
    routes = result3.get("route_options", [])
    print(f"Got {len(routes)} routes:")
    for r in routes:
        reach = r.get("reachability", "?")
        score = r.get("fit_score", 0)
        print(f"  [{reach}] {r.get('route_name', '')} (score={score})")

    recommended = result3.get("recommended_route", {})
    print(f"Recommended: {recommended.get('route_name', '')}")
    print(f"Bottom line: {result3.get('consultant_conclusion', {}).get('bottom_line_advice', '')[:100]}")

    # Step 4
    print("\n--- Step 4: final_report ---")
    result4 = svc.run_final_report(case_id)
    report = result4.get("report_markdown", "")
    print(f"Report length: {len(report)} chars")
    print(f"First 300 chars:\n{report[:300]}")

    print("\n=== ALL STEPS PASSED ===")


if __name__ == "__main__":
    main()
