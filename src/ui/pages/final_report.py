from __future__ import annotations

import streamlit as st

from src.services.formatters import to_markdown_report


def render_final_report(case, workflow_service) -> None:
    st.header("第4步：终版回复报告")

    # ------------------------------------------------------------------ #
    # Show consultant notes from route planning that will be fed in
    # ------------------------------------------------------------------ #
    rp_notes = workflow_service.get_human_notes(case.case_id, "route_planning")
    if rp_notes:
        with st.expander("咨询师对路线的补充判断（来自第3步，已自动带入报告）", expanded=False):
            st.markdown(rp_notes)
    else:
        st.caption(
            "💡 如果你在第3步写了「咨询师对路线的补充判断」，生成时会自动带入报告。"
            "目前该字段为空，你可以回到第3步补充后再生成。"
        )

    # ------------------------------------------------------------------ #
    # Generate / download
    # ------------------------------------------------------------------ #
    latest = workflow_service.get_latest_stage_output(case.case_id, "final_report")
    markdown = to_markdown_report(latest) if latest else ""

    col1, col2 = st.columns(2)
    with col1:
        if st.button("生成终版报告", use_container_width=True, type="primary"):
            with st.spinner("正在生成终版报告…"):
                try:
                    latest = workflow_service.run_final_report(case.case_id)
                    st.success("已生成终版报告。")
                    markdown = to_markdown_report(latest)
                except Exception as exc:
                    st.error(f"终版报告生成失败，请重试。\n\n错误信息：{exc}")
    with col2:
        if latest and markdown:
            st.download_button(
                "下载 Markdown",
                data=markdown.encode("utf-8"),
                file_name=f"{case.case_id}_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

    if not latest:
        st.info("请先完成路线规划（第3步），然后点击上方按钮生成终版报告。")
        return

    st.divider()

    # ------------------------------------------------------------------ #
    # Report editor
    # ------------------------------------------------------------------ #
    if "report_markdown" in latest:
        st.subheader("报告内容（可直接编辑）")
        edited_markdown = st.text_area(
            "终版报告 Markdown",
            value=latest.get("report_markdown", ""),
            height=400,
            key=f"edit_fr_{case.case_id}",
            label_visibility="collapsed",
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
        edited_markdown = st.text_area(
            "终版报告内容",
            value=to_markdown_report(latest),
            height=400,
            key=f"edit_fr_fallback_{case.case_id}",
            label_visibility="collapsed",
        )
        if st.button("保存终版报告修订版", key="save_final_report_fallback"):
            workflow_service.save_manual_stage_output(
                case.case_id,
                "final_report",
                {"report_markdown": edited_markdown},
            )
            markdown = edited_markdown
            st.success("终版报告修订版已保存。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Markdown preview
    # ------------------------------------------------------------------ #
    st.subheader("Markdown 预览")
    if markdown:
        st.markdown(markdown)
    else:
        st.info("报告内容为空。")
