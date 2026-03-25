from __future__ import annotations

import json

import streamlit as st

from src.services.formatters import to_pretty_json


def render_questioning(case, workflow_service) -> None:
    st.header("第2步：矛盾追问工作台")

    st.info(
        "**工作流说明**\n\n"
        "1. 先点「生成AI追问草案」让AI给出追问建议（可选，作为参考）。\n"
        "2. 参考草案后，咨询师自己把要问的问题发给来访者。\n"
        "3. 在下方「咨询师追问记录」里写下你实际发出的追问、对方的回答、以及你的判断。\n"
        "4. 保存记录后，进入第3步路线规划。**第3步会直接使用你的追问记录，而不只是AI草案。**",
        icon="ℹ️",
    )

    # ------------------------------------------------------------------ #
    # AI draft — optional, collapsible
    # ------------------------------------------------------------------ #
    latest = workflow_service.get_latest_stage_output(case.case_id, "questioning")

    with st.expander("AI 追问草案（可选参考）", expanded=latest is None):
        if st.button("生成 AI 追问草案", use_container_width=True, key="gen_questioning"):
            with st.spinner("正在生成 AI 追问草案…"):
                try:
                    latest = workflow_service.run_question_generation(case.case_id)
                    st.success("已生成 AI 追问草案。")
                except Exception as exc:
                    st.error(f"生成失败，请重试。\n\n错误信息：{exc}")

        if latest:
            questions = latest.get("questions", [])
            if questions:
                st.markdown("**AI 建议的追问问题：**")
                for i, q in enumerate(questions, 1):
                    text = q.get("question_text", "")
                    reason = q.get("reason", "")
                    signal = q.get("expected_signal", "")
                    st.markdown(
                        f"**{i}. {text}**\n"
                        f"> 追问原因：{reason}\n\n"
                        f"> 预期信号：{signal}"
                    )
                    st.divider()

            # Advanced: raw JSON editor
            with st.expander("高级：查看/编辑完整 AI 输出 JSON", expanded=False):
                edited = st.text_area(
                    "追问结果 JSON",
                    value=to_pretty_json(latest),
                    height=280,
                    key=f"edit_q_{case.case_id}",
                )
                if st.button("保存修订版 JSON", key="save_questions_json"):
                    try:
                        workflow_service.save_question_answers(case.case_id, json.loads(edited))
                        st.success("追问 JSON 修订版已保存。")
                    except json.JSONDecodeError:
                        st.error("JSON 格式不正确，请修正后再保存。")
        else:
            st.info("还没有 AI 追问草案。点击上方按钮生成，也可以跳过直接填写下方记录。")

    st.divider()

    # ------------------------------------------------------------------ #
    # Human notes — the MAIN input for this stage
    # ------------------------------------------------------------------ #
    st.subheader("咨询师追问记录（重要）")
    st.caption(
        "在这里记录你实际发给来访者的追问、对方的回答，以及你的判断修正。"
        "**这段文字会直接影响路线规划的质量，优先级高于 AI 草案。**"
    )
    existing_notes = workflow_service.get_human_notes(case.case_id, "questioning")
    human_notes = st.text_area(
        "咨询师追问记录",
        value=existing_notes,
        height=240,
        placeholder=(
            "例如：\n"
            "我问：你说的「能养活自己就好」是北京生活标准还是老家标准？\n"
            "对方答：老家在安徽小城市，父母没有太大压力，只是不想依赖家里。\n\n"
            "我的判断：财务约束没有原文描述的那么紧，核心驱动是独立感而非收入底线。\n"
            "矛盾三「转专业意图」修正：转专业不是为了就业面，而是为了降低考公难度，\n"
            "但这个逻辑本身有问题，因为……"
        ),
        key=f"notes_q_{case.case_id}",
        label_visibility="collapsed",
    )
    if st.button("保存追问记录", key="save_q_notes", type="primary"):
        workflow_service.save_human_notes(case.case_id, "questioning", human_notes)
        st.success("追问记录已保存，第3步路线规划时会自动带入。")
