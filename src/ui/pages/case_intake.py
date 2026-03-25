from __future__ import annotations

import streamlit as st

from src.domain.models import Case, new_case_id


def render_case_intake(case_repo) -> str | None:
    st.markdown("## 新建案例")
    st.caption("输入来访者原始信息，创建一个新的咨询案例。")

    with st.form("new_case_form"):
        client_alias = st.text_input(
            "来访者代称",
            placeholder="例如：26届专升本同学A",
        )
        tags_text = st.text_input(
            "标签（逗号分隔，可选）",
            placeholder="例如：转行, 应届, 双非",
        )
        source_text = st.text_area(
            "原始文本",
            height=260,
            placeholder="粘贴来访者发来的原始咨询文字……",
        )
        submitted = st.form_submit_button("创建案例", type="primary", use_container_width=True)

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
