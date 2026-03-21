from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_questioning(case, workflow_service) -> None:
    st.header("矛盾追问工作台")
    latest = workflow_service.get_latest_stage_output(case.case_id, "questioning")
    if st.button("生成追问问题集", use_container_width=True):
        latest = workflow_service.run_question_generation(
            case.case_id,
            model_name=st.session_state.get("active_model"),
        )
        st.success("已生成追问问题集。")

    if not latest:
        st.info("请先生成追问问题集。")
        return

    edited = st.text_area(
        "追问结果 JSON",
        value=to_pretty_json(latest),
        height=320,
    )
    if st.button("保存追问与回答", key="save_questions"):
        try:
            workflow_service.save_question_answers(case.case_id, json.loads(edited))
            st.success("追问与回答已保存。")
        except json.JSONDecodeError:
            st.error("JSON 格式不正确，请修正后再保存。")
