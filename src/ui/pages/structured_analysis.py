from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_structured_analysis(case, workflow_service) -> None:
    st.header("结构化拆解")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("原始文本")
        st.text_area("source_text_preview", value=case.source_text, height=320, disabled=True, label_visibility="collapsed")
    with col2:
        latest = workflow_service.get_latest_stage_output(case.case_id, "structured_analysis")
        if st.button("生成结构化拆解", use_container_width=True):
            latest = workflow_service.run_structured_analysis(
                case.case_id,
                model_name=st.session_state.get("active_model"),
            )
            st.success("已生成结构化拆解。")
        if latest:
            edited = st.text_area(
                "结构化结果 JSON",
                value=to_pretty_json(latest),
                height=320,
            )
            if st.button("保存人工修订版", key="save_structured_analysis"):
                try:
                    workflow_service.save_manual_stage_output(
                        case.case_id,
                        "structured_analysis",
                        json.loads(edited),
                    )
                    st.success("已保存人工修订版。")
                except json.JSONDecodeError:
                    st.error("JSON 格式不正确，请修正后再保存。")
        else:
            st.info("还没有结构化拆解结果。")
