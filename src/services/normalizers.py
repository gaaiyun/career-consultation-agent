from __future__ import annotations

from typing import Any


def normalize_stage_output(stage_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalizers = {
        "structured_analysis": _normalize_structured_analysis,
        "questioning": _normalize_questioning,
        "route_planning": _normalize_route_planning,
        "final_report": _normalize_final_report,
    }
    normalizer = normalizers.get(stage_name)
    if not normalizer:
        return payload
    return normalizer(payload)


def _normalize_structured_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    payload.setdefault("core_profile", {})
    payload["core_profile"].setdefault("one_sentence_summary", "")
    payload["core_profile"].setdefault("tags", [])

    payload.setdefault("gps_analysis", {})
    positioning = payload["gps_analysis"].setdefault("positioning_system", {})
    static_coordinates = positioning.setdefault("static_coordinates", {})
    static_coordinates.setdefault("education_background", [])
    static_coordinates.setdefault("professional_assets", [])
    static_coordinates.setdefault("current_status", "")

    dynamic_path = positioning.setdefault("dynamic_path", {})
    dynamic_path.setdefault("work_timeline", [])
    dynamic_path.setdefault("achievement_events", [])
    dynamic_path.setdefault("transition_logic", [])

    motivation = payload["gps_analysis"].setdefault("motivation_system", {})
    motivation.setdefault("interest_circle", [])
    motivation.setdefault("ability_circle", [])
    motivation.setdefault("value_circle", [])
    motivation.setdefault("anchor_summary", "")

    constraints = payload["gps_analysis"].setdefault("constraint_system", {})
    constraints.setdefault("external_reality", [])
    constraints.setdefault("internal_obstacles", [])

    payload.setdefault("contradictions", [])
    payload.setdefault("preliminary_insights", [])
    payload.setdefault("possible_directions", [])
    payload.setdefault("clarification_questions", [])
    payload.setdefault("consultant_notes", {})
    payload["consultant_notes"].setdefault("confidence_level", "medium")
    payload["consultant_notes"].setdefault("missing_information", [])
    payload["consultant_notes"].setdefault("bias_risks", [])
    return payload


def _normalize_questioning(payload: dict[str, Any]) -> dict[str, Any]:
    payload.setdefault("question_strategy", {})
    payload["question_strategy"].setdefault("goal", "")
    payload["question_strategy"].setdefault("priority_rule", "")
    payload.setdefault("questions", [])
    payload.setdefault("logic_checks", [])
    payload.setdefault("consultant_prompting_notes", [])
    for question in payload["questions"]:
        question.setdefault("question_text", "")
        question.setdefault("reason", "")
        question.setdefault("linked_contradiction", "")
        question.setdefault("priority", "medium")
        question.setdefault("expected_signal", "")
        question.setdefault("answer", question.get("answer", ""))
    return payload


def _normalize_route_planning(payload: dict[str, Any]) -> dict[str, Any]:
    payload.setdefault("planning_summary", {})
    payload["planning_summary"].setdefault("decision_frame", "")
    payload["planning_summary"].setdefault("core_tradeoff", "")
    payload.setdefault("route_options", [])
    for route in payload["route_options"]:
        route.setdefault("route_name", "")
        route.setdefault("route_positioning", "")
        route.setdefault("fit_score", 0)
        route.setdefault("fit_reasons", [])
        route.setdefault("advantages", [])
        route.setdefault("risks", [])
        route.setdefault("required_conditions", [])
        route.setdefault("prep_actions", [])
        route.setdefault("time_horizon", "")
    payload.setdefault("recommended_route", {})
    payload["recommended_route"].setdefault("route_name", "")
    payload["recommended_route"].setdefault("why_recommended", [])
    payload["recommended_route"].setdefault("why_not_others", [])
    payload["recommended_route"].setdefault("reverse_action_plan", {})
    reverse_action_plan = payload["recommended_route"]["reverse_action_plan"]
    reverse_action_plan.setdefault("now", [])
    reverse_action_plan.setdefault("next_1_to_3_months", [])
    reverse_action_plan.setdefault("next_3_to_12_months", [])
    payload.setdefault("consultant_conclusion", {})
    payload["consultant_conclusion"].setdefault("bottom_line_advice", "")
    payload["consultant_conclusion"].setdefault("watch_points", [])
    return payload


def _normalize_final_report(payload: dict[str, Any]) -> dict[str, Any]:
    payload.setdefault("title", "职业咨询回复报告")
    payload.setdefault("opening", "")
    payload.setdefault("summary_of_case", "")
    payload.setdefault("core_findings", [])
    payload.setdefault("route_recommendation", {})
    payload["route_recommendation"].setdefault("recommended_route", "")
    payload["route_recommendation"].setdefault("recommendation_detail", "")
    payload["route_recommendation"].setdefault("alternative_routes", [])
    payload.setdefault("action_plan", {})
    payload["action_plan"].setdefault("immediate_actions", [])
    payload["action_plan"].setdefault("near_term_actions", [])
    payload["action_plan"].setdefault("mid_term_actions", [])
    payload.setdefault("risk_reminders", [])
    payload.setdefault("questions_for_next_round", [])
    payload.setdefault("closing", "")
    return payload
