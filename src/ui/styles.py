"""Shared Streamlit CSS injection for a professional consulting-tool aesthetic."""
from __future__ import annotations

import streamlit as st


_CSS = """
<style>
/* ── Layout & baseline ─────────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

section.main > div { padding-top: 1.5rem; }

/* ── Typography ────────────────────────────────────────────────────────── */
h1 { font-size: 1.55rem !important; font-weight: 700 !important; letter-spacing: -0.3px; }
h2 { font-size: 1.15rem !important; font-weight: 600 !important; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 0.35rem; margin-top: 1.2rem !important; }
h3 { font-size: 1.0rem !important; font-weight: 600 !important; }

/* ── Sidebar ───────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.06);
    background-color: #111520;
}
[data-testid="stSidebar"] h2 {
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6B7A99;
    border-bottom: none;
}

/* ── Tabs ──────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] button {
    font-size: 0.82rem;
    font-weight: 500;
    padding: 0.4rem 0.8rem;
    color: #8A95A8;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #C9D1E0;
    border-bottom: 2px solid #4B8BF4;
}

/* ── Buttons ───────────────────────────────────────────────────────────── */
[data-testid="stButton"] button {
    border-radius: 4px;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    transition: all 0.15s ease;
}
[data-testid="stButton"] button[kind="primary"] {
    background: #4B8BF4;
    border: none;
    color: #fff;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: #3A76E0;
}
[data-testid="stButton"] button[kind="secondary"] {
    border: 1px solid rgba(255,255,255,0.1);
}

/* ── Text areas & inputs ───────────────────────────────────────────────── */
textarea, input[type="text"] {
    border-radius: 4px !important;
    font-size: 0.85rem !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background-color: #111520 !important;
}
label { font-size: 0.82rem; font-weight: 500; color: #8A95A8; }

/* ── Info / success / error boxes ─────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 4px;
    font-size: 0.84rem;
    border: none;
}

/* ── Progress bar ──────────────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {
    background: #4B8BF4;
}

/* ── Expander ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.84rem;
    font-weight: 500;
}

/* ── Divider ───────────────────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.07) !important; margin: 1rem 0 !important; }

/* ── Metric labels ─────────────────────────────────────────────────────── */
[data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

/* ── Status widget ─────────────────────────────────────────────────────── */
[data-testid="stStatusWidget"] {
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px;
}

/* ── Caption ───────────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.78rem;
    color: #6B7A99;
}

/* ── Download button ───────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    font-size: 0.82rem;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
</style>
"""


def inject_styles() -> None:
    """Inject shared CSS into the current Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
