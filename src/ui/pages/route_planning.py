from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


_REACHABILITY_LABELS = {
    "open_market": "正常招聘可进",
    "restricted": "需要特殊背景或内部资源",
    "theoretical": "理论存在，公开岗位极少",
}

_REACHABILITY_COLORS = {
    "open_market": "normal",
    "restricted": "off",
    "theoretical": "off",
}


def render_route_planning(case, workflow_service) -> None:
    st.markdown("## 路线规划")

    # ------------------------------------------------------------------ #
    # Feasibility pre-annotation
    # ------------------------------------------------------------------ #
    with st.expander("路线可达性标注（建议在生成前填写）", expanded=True):
        st.caption(
            "标注你认为不成立的路线或限制条件。点击生成路线规划时，这段内容会直接注入 Prompt，"
            "让模型在规划时排除你标注的不可达路线。"
        )
        existing_feasibility = workflow_service.get_human_notes(case.case_id, "route_feasibility")
        feasibility_notes = st.text_area(
            "路线可达性标注",
            value=existing_feasibility,
            height=110,
            placeholder=(
                "例如：\n"
                "- 高校辅导员现在普遍要求硕士以上，本科应届不要排这条。\n"
                "- 国央企管培生要求 985/211，双非本科不适合作为主推路线。\n"
                "- 音乐版权专员岗位极少，不建议作为可行路线列出。"
            ),
            key=f"feasibility_{case.case_id}",
            label_visibility="collapsed",
        )
        if st.button("保存标注", key="save_feasibility"):
            workflow_service.save_human_notes(case.case_id, "route_feasibility", feasibility_notes)
            st.success("已保存，下次生成路线规划时会自动带入。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Generate
    # ------------------------------------------------------------------ #
    latest = workflow_service.get_latest_stage_output(case.case_id, "route_planning")
    if st.button("生成路线规划", use_container_width=True, type="primary", key="gen_routes"):
        with st.spinner("正在生成…"):
            try:
                latest = workflow_service.run_route_planning(case.case_id)
                st.success("路线规划已生成。")
            except Exception as exc:
                st.error(f"生成失败，请重试。\n\n{exc}")

    if not latest:
        st.info("请先完成前序阶段（结构化拆解 + 追问记录），然后点击上方按钮生成路线规划。")
        return

    # ------------------------------------------------------------------ #
    # Structured display
    # ------------------------------------------------------------------ #
    route_options = latest.get("route_options", [])
    if route_options:
        st.markdown("**路线选项**")
        for route in route_options:
            reachability = route.get("reachability", "open_market")
            label = _REACHABILITY_LABELS.get(reachability, reachability)
            score = route.get("fit_score", 0)
            route_name = route.get("route_name", "未命名")
            header = f"{route_name}  ·  适配度 {score}  ·  {label}"
            with st.expander(header, expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**定位**")
                    st.write(route.get("route_positioning", ""))
                    st.markdown("**优势**")
                    for adv in route.get("advantages", []):
                        st.markdown(f"- {adv}")
                    st.markdown("**风险**")
                    for risk in route.get("risks", []):
                        st.markdown(f"- {risk}")
                with col_b:
                    st.markdown("**适配原因**")
                    for reason in route.get("fit_reasons", []):
                        st.markdown(f"- {reason}")
                    st.markdown("**入场门槛**")
                    for cond in route.get("required_conditions", []):
                        st.markdown(f"- {cond}")
                    st.markdown("**行动步骤**")
                    for action in route.get("prep_actions", []):
                        st.markdown(f"- {action}")

    recommended = latest.get("recommended_route", {})
    if recommended.get("route_name"):
        st.markdown(f"**主推路线：{recommended['route_name']}**")
        conclusion = latest.get("consultant_conclusion", {})
        if conclusion.get("bottom_line_advice"):
            st.info(conclusion["bottom_line_advice"])
        action_plan = recommended.get("reverse_action_plan", {})
        if any(action_plan.values()):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**立刻要做**")
                for a in action_plan.get("now", []):
                    st.markdown(f"- {a}")
            with col2:
                st.markdown("**1-3 个月**")
                for a in action_plan.get("next_1_to_3_months", []):
                    st.markdown(f"- {a}")
            with col3:
                st.markdown("**3-12 个月**")
                for a in action_plan.get("next_3_to_12_months", []):
                    st.markdown(f"- {a}")

    with st.expander("高级：编辑路线规划 JSON", expanded=False):
        edited = st.text_area(
            "路线规划 JSON",
            value=to_pretty_json(latest),
            height=320,
            key=f"edit_rp_{case.case_id}",
        )
        if st.button("保存人工修订版 JSON", key="save_route_plan"):
            try:
                workflow_service.save_manual_stage_output(
                    case.case_id,
                    "route_planning",
                    json.loads(edited),
                )
                st.success("路线规划修订版已保存。")
            except json.JSONDecodeError:
                st.error("JSON 格式不正确，请修正后再保存。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Consultant notes on route — fed into final report
    # ------------------------------------------------------------------ #
    st.markdown("**咨询师对路线的补充判断**（选填，生成终版报告时自动带入）")
    st.caption(
        "写你对 AI 路线规划的补充、修正或最终结论。"
        "生成第4步终版报告时，这段判断会直接注入 Prompt。"
    )
    existing_rp_notes = workflow_service.get_human_notes(case.case_id, "route_planning")
    rp_notes = st.text_area(
        "咨询师对路线的补充判断",
        value=existing_rp_notes,
        height=160,
        placeholder=(
            "例如：\n"
            "主推路线调整为「具身智能公司内容运营」，TA 有 B 端内容经验，且具身智能是当前热门赛道。\n"
            "「直接服务甲方」这条路线适合投递之前合作过的客户，不适合简历盲投，\n"
            "行动计划里需要说清楚这一点。"
        ),
        key=f"notes_rp_{case.case_id}",
        label_visibility="collapsed",
    )
    if st.button("保存补充判断", key="save_rp_notes"):
        workflow_service.save_human_notes(case.case_id, "route_planning", rp_notes)
        st.success("已保存，生成终版报告时会自动带入。")
