from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_structured_analysis(case, workflow_service) -> None:
    st.markdown("## 结构化拆解")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**原始文本**")
        st.text_area(
            "source_text_preview",
            value=case.source_text,
            height=340,
            disabled=True,
            label_visibility="collapsed",
        )
    with col2:
        latest = workflow_service.get_latest_stage_output(case.case_id, "structured_analysis")
        if st.button("生成结构化拆解", use_container_width=True, type="primary"):
            with st.spinner("正在生成…"):
                try:
                    latest = workflow_service.run_structured_analysis(case.case_id)
                    st.success("结构化拆解已生成。")
                except Exception as exc:
                    st.error(f"生成失败，请重试。\n\n{exc}")
        if latest:
            edited = st.text_area(
                "结构化结果 JSON（可直接编辑后保存）",
                value=to_pretty_json(latest),
                height=280,
                key=f"edit_sa_{case.case_id}",
            )
            if st.button("保存人工修订版", key="save_structured_analysis"):
                try:
                    workflow_service.save_manual_stage_output(
                        case.case_id,
                        "structured_analysis",
                        json.loads(edited),
                    )
                    st.success("人工修订版已保存。")
                except json.JSONDecodeError:
                    st.error("JSON 格式不正确，请修正后再保存。")
        else:
            st.info("还没有拆解结果，点击上方按钮生成。")

    st.divider()

    st.markdown("**咨询师补充判断**（选填，内容会在生成第2步追问草案时注入）")
    existing_notes = workflow_service.get_human_notes(case.case_id, "structured_analysis")
    human_notes = st.text_area(
        "咨询师补充判断",
        value=existing_notes,
        height=160,
        placeholder=(
            "写你对 AI 拆解结果的补充、修正或自己的判断。\n"
            "例如：矛盾三里对转专业的判断需要修正，该来访者真正的问题是就业竞争力不足，而不是专业本身。"
        ),
        key=f"notes_sa_{case.case_id}",
        label_visibility="collapsed",
    )
    if st.button("保存补充判断", key="save_sa_notes"):
        workflow_service.save_human_notes(case.case_id, "structured_analysis", human_notes)
        st.success("已保存，下一步生成时会自动带入。")
