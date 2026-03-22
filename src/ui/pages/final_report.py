from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_markdown_report, to_pretty_json


def render_final_report(case, workflow_service) -> None:
    st.header("终版回复报告")
    latest = workflow_service.get_latest_stage_output(case.case_id, "final_report")
    markdown = to_markdown_report(latest) if latest else ""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("生成终版报告", use_container_width=True):
            latest = workflow_service.run_final_report(case.case_id)
            st.success("已生成终版报告。")
            markdown = to_markdown_report(latest)
    with col2:
        if latest:
            st.download_button(
                "下载 Markdown",
                data=markdown.encode("utf-8"),
                file_name=f"{case.case_id}_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

    if not latest:
        st.info("请先完成路线规划。")
        return

    if "report_markdown" in latest:
        edited_markdown = st.text_area(
            "终版报告 Markdown",
            value=latest.get("report_markdown", ""),
            height=360,
        )
        if st.button("保存终版报告修订版", key="save_final_report_markdown"):
            workflow_service.save_manual_stage_output(
                case.case_id,
                "final_report",
                {"report_markdown": edited_markdown},
            )
            markdown = edited_markdown
            st.success("终版报告修订版已保存。")
    else:
        edited = st.text_area(
            "终版报告 JSON",
            value=to_pretty_json(latest),
            height=280,
        )
        if st.button("保存终版报告修订版", key="save_final_report_json"):
            try:
                latest = json.loads(edited)
                workflow_service.save_manual_stage_output(
                    case.case_id,
                    "final_report",
                    latest,
                )
                markdown = to_markdown_report(latest)
                st.success("终版报告修订版已保存。")
            except json.JSONDecodeError:
                st.error("JSON 格式不正确，请修正后再保存。")

    st.subheader("Markdown 预览")
    st.markdown(markdown)
