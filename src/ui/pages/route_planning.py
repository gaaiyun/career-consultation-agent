from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


_REACHABILITY_LABELS = {
    "open_market": "✅ 正常招聘可进",
    "restricted": "⚠️ 需要内部资源/特殊背景",
    "theoretical": "❌ 理论存在，公开岗位极少",
}


def render_route_planning(case, workflow_service) -> None:
    st.header("第3步：路线规划")

    # ------------------------------------------------------------------ #
    # Feasibility check — best filled BEFORE generating routes
    # ------------------------------------------------------------------ #
    with st.expander("路线可达性标注（建议先填）", expanded=True):
        st.caption(
            "如果你已经知道哪些路线「理论存在但现实不好进」，在这里提前标注。"
            "**点击生成路线规划时，这段内容会直接注入 Prompt，让 AI 在规划时避开你标注的不成立路线。**"
        )
        existing_feasibility = workflow_service.get_human_notes(case.case_id, "route_feasibility")
        feasibility_notes = st.text_area(
            "路线可达性标注",
            value=existing_feasibility,
            height=120,
            placeholder=(
                "例如：\n"
                "- 「高校辅导员」现在普遍要求硕士以上，本科应届生不要排这条。\n"
                "- 「国央企管培生」要求 985/211，双非本科不适合作为主推路线。\n"
                "- 「音乐版权专员」岗位极少，不建议 AI 列为可行路线。"
            ),
            key=f"feasibility_{case.case_id}",
            label_visibility="collapsed",
        )
        if st.button("保存路线标注", key="save_feasibility"):
            workflow_service.save_human_notes(case.case_id, "route_feasibility", feasibility_notes)
            st.success("路线标注已保存，下次生成路线规划时会自动带入。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Generate route planning
    # ------------------------------------------------------------------ #
    latest = workflow_service.get_latest_stage_output(case.case_id, "route_planning")
    if st.button("生成路线规划", use_container_width=True, type="primary", key="gen_routes"):
        with st.spinner("正在生成路线规划…"):
            try:
                latest = workflow_service.run_route_planning(case.case_id)
                st.success("已生成路线规划。")
            except Exception as exc:
                st.error(f"路线规划生成失败，请重试。\n\n错误信息：{exc}")

    if not latest:
        st.info("请先完成前序阶段（结构化拆解 + 追问记录），然后点击上方按钮生成路线规划。")
        return

    # ------------------------------------------------------------------ #
    # Structured route display
    # ------------------------------------------------------------------ #
    route_options = latest.get("route_options", [])
    if route_options:
        st.subheader("路线选项")
        for route in route_options:
            reachability = route.get("reachability", "open_market")
            label = _REACHABILITY_LABELS.get(reachability, reachability)
            score = route.get("fit_score", 0)
            route_name = route.get("route_name", "未命名")
            with st.expander(f"{route_name}  |  适配度 {score}  |  {label}", expanded=False):
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
        st.subheader(f"主推路线：{recommended['route_name']}")
        conclusion = latest.get("consultant_conclusion", {})
        if conclusion.get("bottom_line_advice"):
            st.success(conclusion["bottom_line_advice"])
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

    # Advanced JSON editor
    with st.expander("高级：编辑路线规划 JSON", expanded=False):
        edited = st.text_area(
            "路线规划 JSON",
            value=to_pretty_json(latest),
            height=340,
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
    # Consultant notes on route planning — fed into final report
    # ------------------------------------------------------------------ #
    st.subheader("咨询师对路线的补充判断（可选）")
    st.caption(
        "在这里写你对 AI 路线规划的补充、修正或最终判断。"
        "**生成第4步终版报告时会直接纳入这段判断，让报告更贴近你的真实结论。**"
    )
    existing_rp_notes = workflow_service.get_human_notes(case.case_id, "route_planning")
    rp_notes = st.text_area(
        "咨询师对路线的补充判断",
        value=existing_rp_notes,
        height=160,
        placeholder=(
            "例如：\n"
            "主推路线调整为「具身智能公司内容运营」，因为 TA 有 B 端内容经验，"
            "且具身智能是当前热门赛道，入职门槛相对宽松。\n"
            "「直接服务甲方」这条路线实际上适合投递之前合作过的客户，"
            "而不是通过简历盲投，需要在行动计划里说清楚这一点。"
        ),
        key=f"notes_rp_{case.case_id}",
        label_visibility="collapsed",
    )
    if st.button("保存咨询师补充判断", key="save_rp_notes"):
        workflow_service.save_human_notes(case.case_id, "route_planning", rp_notes)
        st.success("咨询师补充判断已保存，生成终版报告时会自动带入。")
