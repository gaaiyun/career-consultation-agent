from __future__ import annotations

import streamlit as st

from src.config.settings import get_settings
from src.storage.db import init_db
from src.storage.repositories import CaseRepository
from src.ui.pages.case_intake import render_case_intake
from src.ui.pages.final_report import render_final_report
from src.ui.pages.questioning import render_questioning
from src.ui.pages.route_planning import render_route_planning
from src.ui.pages.structured_analysis import render_structured_analysis
from src.workflow.orchestrator import ConsultationWorkflowService


settings = get_settings()
init_db(settings)
case_repo = CaseRepository(settings)
workflow_service = ConsultationWorkflowService(settings)


def _case_label(case) -> str:
    return f"{case.client_alias} | {case.current_stage} | {case.case_id}"


def main() -> None:
    st.set_page_config(page_title=settings.app_name, layout="wide")
    st.title("职业咨询 Agent")
    st.caption("面向职业咨询师的 Streamlit 咨询助手 MVP")

    if not workflow_service.llm_client.is_configured():
        st.warning("未检测到 `SILICONFLOW_API_KEY`，当前只能查看和编辑案例，无法调用模型生成内容。")

    if "selected_case_id" not in st.session_state:
        st.session_state.selected_case_id = None

    with st.sidebar:
        st.header("案例列表")
        cases = case_repo.list_cases()
        options = ["__new__"] + [case.case_id for case in cases]
        labels = {"__new__": "新建案例"}
        labels.update({case.case_id: _case_label(case) for case in cases})
        selected = st.selectbox(
            "选择案例",
            options=options,
            format_func=lambda value: labels[value],
            index=0 if st.session_state.selected_case_id not in options else options.index(st.session_state.selected_case_id),
        )
        st.session_state.selected_case_id = None if selected == "__new__" else selected

    if st.session_state.selected_case_id is None:
        created_case_id = render_case_intake(case_repo)
        if created_case_id:
            st.session_state.selected_case_id = created_case_id
            st.rerun()
        return

    case = case_repo.get(st.session_state.selected_case_id)
    if not case:
        st.error("案例不存在，请重新选择。")
        st.session_state.selected_case_id = None
        return

    st.info(f"当前案例：`{case.client_alias}` | 当前阶段：`{case.current_stage}`")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["1. 结构化拆解", "2. 矛盾追问", "3. 路线规划", "4. 终版报告", "5. 历史版本"]
    )

    with tab1:
        _safe_render(render_structured_analysis, case, workflow_service)
    with tab2:
        _safe_render(render_questioning, case, workflow_service)
    with tab3:
        _safe_render(render_route_planning, case, workflow_service)
    with tab4:
        _safe_render(render_final_report, case, workflow_service)
    with tab5:
        st.header("历史版本")
        versions = workflow_service.list_stage_versions(case.case_id)
        if not versions:
            st.info("还没有历史版本。")
        for version in versions:
            with st.expander(
                f"{version['stage_name']} | v{version['version_no']} | {version['created_at']}"
            ):
                st.json(version["output_payload"])


def _safe_render(renderer, case, workflow_service) -> None:
    try:
        renderer(case, workflow_service)
    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
