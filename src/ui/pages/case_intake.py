from __future__ import annotations

import streamlit as st

from src.domain.models import Case, new_case_id


def render_case_intake(case_repo) -> str | None:
    st.header("案例录入")
    with st.form("new_case_form"):
        client_alias = st.text_input("来访者代称", placeholder="例如：人大大四同学A")
        tags_text = st.text_input("标签", placeholder="用逗号分隔，例如：转行,考研,求稳")
        source_text = st.text_area("原始文本", height=220)
        submitted = st.form_submit_button("创建案例")

    if submitted:
        if not client_alias.strip() or not source_text.strip():
            st.error("请填写来访者代称和原始文本。")
            return None
        case = Case(
            case_id=new_case_id(),
            client_alias=client_alias.strip(),
            source_text=source_text.strip(),
            tags=[item.strip() for item in tags_text.split(",") if item.strip()],
        )
        case_repo.create(case)
        st.success(f"案例已创建：{case.case_id}")
        return case.case_id
    return None
