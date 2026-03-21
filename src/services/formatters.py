from __future__ import annotations

import json
from typing import Any


def to_pretty_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def to_markdown_report(report_payload: dict[str, Any]) -> str:
    if "report_markdown" in report_payload:
        return report_payload.get("report_markdown", "")

    title = report_payload.get("title", "职业咨询回复报告")
    opening = report_payload.get("opening", "")
    summary_of_case = report_payload.get("summary_of_case", "")
    core_findings = report_payload.get("core_findings", [])
    route_recommendation = report_payload.get("route_recommendation", {})
    recommended_route = route_recommendation.get("recommended_route", "")
    recommendation_detail = route_recommendation.get("recommendation_detail", "")
    alternative_routes = route_recommendation.get("alternative_routes", [])
    action_plan = report_payload.get("action_plan", {})
    immediate_actions = action_plan.get("immediate_actions", [])
    near_term_actions = action_plan.get("near_term_actions", [])
    mid_term_actions = action_plan.get("mid_term_actions", [])
    risk_reminders = report_payload.get("risk_reminders", [])
    questions_for_next_round = report_payload.get("questions_for_next_round", [])
    closing = report_payload.get("closing", "")

    lines = [f"# {title}", "", opening]
    if summary_of_case:
        lines.extend(["", "## 核心画像", summary_of_case])

    lines.extend(["", "## 核心判断"])
    if core_findings:
        for item in core_findings:
            if isinstance(item, dict):
                theme = item.get("theme", "判断")
                detail = item.get("detail", "")
                lines.append(f"- {theme}：{detail}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- 暂无")

    lines.extend(["", "## 推荐路线", recommended_route or "待补充"])
    if recommendation_detail:
        lines.append(recommendation_detail)
    if alternative_routes:
        lines.extend(["", "## 备选路线"])
        lines.extend([f"- {item}" for item in alternative_routes])

    lines.extend(["", "## 行动计划", "### 立刻开始"])
    lines.extend([f"- {item}" for item in immediate_actions] or ["- 暂无"])
    lines.extend(["", "### 未来1到3个月"])
    lines.extend([f"- {item}" for item in near_term_actions] or ["- 暂无"])
    lines.extend(["", "### 未来3到12个月"])
    lines.extend([f"- {item}" for item in mid_term_actions] or ["- 暂无"])

    lines.extend(["", "## 风险提醒"])
    lines.extend([f"- {item}" for item in risk_reminders] or ["- 暂无"])
    if questions_for_next_round:
        lines.extend(["", "## 后续待澄清问题"])
        lines.extend([f"- {item}" for item in questions_for_next_round])
    lines.extend(["", closing])
    return "\n".join(lines)
