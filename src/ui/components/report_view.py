from __future__ import annotations

import streamlit as st


def render_json_section(title: str, payload: dict) -> None:
    st.subheader(title)
    st.json(payload)


def render_markdown_section(title: str, content: str) -> None:
    st.subheader(title)
    st.markdown(content)
