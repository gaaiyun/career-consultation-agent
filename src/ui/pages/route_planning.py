from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_route_planning(case, workflow_service) -> None:
    st.header("路线规划")
    latest = workflow_service.get_latest_stage_output(case.case_id, "route_planning")
    if st.button("生成路线规划", use_container_width=True):
        latest = workflow_service.run_route_planning(
            case.case_id,
            model_name=st.session_state.get("active_model"),
        )
        st.success("已生成路线规划。")

    if not latest:
        st.info("请先完成前序阶段。")
        return

    edited = st.text_area(
        "路线规划 JSON",
        value=to_pretty_json(latest),
        height=340,
    )
    if st.button("保存路线规划修订版", key="save_route_plan"):
        try:
            workflow_service.save_manual_stage_output(
                case.case_id,
                "route_planning",
                json.loads(edited),
            )
            st.success("路线规划修订版已保存。")
        except json.JSONDecodeError:
            st.error("JSON 格式不正确，请修正后再保存。")
