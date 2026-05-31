"""Tests for stage output normalization (schema defaulting + derived fields)."""
from __future__ import annotations

from src.services.normalizers import normalize_stage_output


def test_unknown_stage_passes_through_unchanged() -> None:
    payload = {"anything": 1}
    assert normalize_stage_output("not_a_stage", payload) is payload


def test_structured_analysis_fills_missing_keys() -> None:
    out = normalize_stage_output("structured_analysis", {})
    assert out["core_profile"]["one_sentence_summary"] == ""
    assert out["core_profile"]["tags"] == []
    assert out["gps_analysis"]["constraint_system"]["external_reality"] == []
    assert out["consultant_notes"]["confidence_level"] == "medium"
    assert out["possible_directions"] == []


def test_structured_analysis_preserves_existing_values() -> None:
    out = normalize_stage_output(
        "structured_analysis",
        {"core_profile": {"one_sentence_summary": "卡在转型期", "tags": ["转行"]}},
    )
    assert out["core_profile"]["one_sentence_summary"] == "卡在转型期"
    assert out["core_profile"]["tags"] == ["转行"]


def test_questioning_fills_question_defaults() -> None:
    out = normalize_stage_output(
        "questioning",
        {"questions": [{"question_text": "你理解的运营是什么？"}]},
    )
    q = out["questions"][0]
    assert q["priority"] == "medium"
    assert q["answer"] == ""
    assert q["reason"] == ""
    assert out["question_strategy"]["goal"] == ""


def test_route_planning_autofills_recommended_from_best_fit_score() -> None:
    payload = {
        "route_options": [
            {
                "route_name": "音乐平台内容运营",
                "fit_score": 85,
                "fit_reasons": ["可复用音乐行业认知", "内容能力可迁移", "赛道在招人"],
                "prep_actions": ["改简历", "做作品集", "投平台公司", "补数据分析", "练面试"],
            },
            {"route_name": "音乐教培运营", "fit_score": 60, "fit_reasons": ["门槛低"]},
        ]
    }
    out = normalize_stage_output("route_planning", payload)
    rec = out["recommended_route"]
    assert rec["route_name"] == "音乐平台内容运营"
    assert rec["why_recommended"] == ["可复用音乐行业认知", "内容能力可迁移", "赛道在招人"]
    # reverse action plan should be seeded from the best route's prep_actions
    assert rec["reverse_action_plan"]["now"] == ["改简历", "做作品集", "投平台公司"]
    assert rec["reverse_action_plan"]["next_1_to_3_months"] == ["补数据分析", "练面试"]
    # why_not_others mentions the weaker route
    assert any("音乐教培运营" in reason for reason in rec["why_not_others"])
    # bottom line advice derived from recommended route
    assert "音乐平台内容运营" in out["consultant_conclusion"]["bottom_line_advice"]


def test_route_planning_respects_explicit_recommendation() -> None:
    payload = {
        "route_options": [{"route_name": "A", "fit_score": 90}, {"route_name": "B", "fit_score": 10}],
        "recommended_route": {"route_name": "B", "why_recommended": ["咨询师指定"]},
    }
    out = normalize_stage_output("route_planning", payload)
    # Explicit recommendation must not be overwritten by the auto-fill.
    assert out["recommended_route"]["route_name"] == "B"
    assert out["recommended_route"]["why_recommended"] == ["咨询师指定"]


def test_route_planning_default_reachability() -> None:
    out = normalize_stage_output("route_planning", {"route_options": [{"route_name": "X"}]})
    assert out["route_options"][0]["reachability"] == "open_market"
    assert out["route_options"][0]["fit_score"] == 0


def test_final_report_markdown_passthrough() -> None:
    out = normalize_stage_output("final_report", {"report_markdown": "# 标题\n正文"})
    assert out["report_markdown"] == "# 标题\n正文"
    # Structured-report keys should not be injected when markdown is present.
    assert "core_findings" not in out


def test_final_report_structured_defaults() -> None:
    out = normalize_stage_output("final_report", {})
    assert out["title"] == "职业咨询回复报告"
    assert out["action_plan"]["immediate_actions"] == []
    assert out["route_recommendation"]["recommended_route"] == ""
