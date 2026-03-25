from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_questioning(case, workflow_service) -> None:
    st.markdown("## 矛盾追问工作台")

    st.markdown(
        """
        **工作流**：AI 生成追问草案（可选参考）→ 咨询师自行发出追问并记录回答 → 
        保存追问记录 → 进入路线规划。第3步路线规划会优先使用你的追问记录，而不只是 AI 草案。
        """,
        help="第2步是整个工作流中最重要的人工介入环节。AI 草案仅供参考，核心是你对来访者的追问和你的判断修正。",
    )

    # ------------------------------------------------------------------ #
    # AI draft
    # ------------------------------------------------------------------ #
    latest = workflow_service.get_latest_stage_output(case.case_id, "questioning")

    with st.expander("AI 追问草案（可选，点击展开）", expanded=latest is None):
        if st.button("生成 AI 追问草案", use_container_width=True, key="gen_questioning"):
            with st.spinner("正在生成…"):
                try:
                    latest = workflow_service.run_question_generation(case.case_id)
                    st.success("AI 追问草案已生成。")
                except Exception as exc:
                    st.error(f"生成失败，请重试。\n\n{exc}")

        if latest:
            questions = latest.get("questions", [])
            if questions:
                st.markdown("**AI 建议的追问问题**")
                for i, q in enumerate(questions, 1):
                    text = q.get("question_text", "")
                    reason = q.get("reason", "")
                    signal = q.get("expected_signal", "")
                    with st.container():
                        st.markdown(f"**{i}. {text}**")
                        cols = st.columns(2)
                        with cols[0]:
                            st.caption(f"追问原因：{reason}")
                        with cols[1]:
                            st.caption(f"预期信号：{signal}")
                        st.divider()

            with st.expander("查看 / 编辑完整 AI 输出 JSON", expanded=False):
                edited = st.text_area(
                    "追问结果 JSON",
                    value=to_pretty_json(latest),
                    height=260,
                    key=f"edit_q_{case.case_id}",
                )
                if st.button("保存修订版 JSON", key="save_questions_json"):
                    try:
                        workflow_service.save_question_answers(case.case_id, json.loads(edited))
                        st.success("JSON 修订版已保存。")
                    except json.JSONDecodeError:
                        st.error("JSON 格式不正确，请修正后再保存。")
        else:
            st.info("点击上方按钮生成草案，也可以直接跳过，在下方填写追问记录。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Human notes — primary input
    # ------------------------------------------------------------------ #
    st.markdown("**咨询师追问记录**（核心输入，直接影响路线规划质量）")
    st.caption(
        "记录你实际发给来访者的追问、对方的回答，以及你的判断修正。"
        "生成路线规划时，这段文字的优先级高于 AI 追问草案。"
    )
    existing_notes = workflow_service.get_human_notes(case.case_id, "questioning")
    human_notes = st.text_area(
        "咨询师追问记录",
        value=existing_notes,
        height=260,
        placeholder=(
            "问：你说的「能养活自己就好」是北京生活标准还是老家标准？\n"
            "答：老家安徽小城，父母没压力，主要是自己想独立，没有硬性收入底线。\n\n"
            "判断：财务约束没有原文描述的那么紧，核心驱动是独立感而非收入底线。\n"
            "矛盾三修正：转专业不是为了就业面，而是为了降低考公难度，但这个逻辑本身有问题，因为……"
        ),
        key=f"notes_q_{case.case_id}",
        label_visibility="collapsed",
    )
    if st.button("保存追问记录", key="save_q_notes", type="primary"):
        workflow_service.save_human_notes(case.case_id, "questioning", human_notes)
        st.success("追问记录已保存，路线规划时会自动带入。")
