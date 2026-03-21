from __future__ import annotations

import streamlit as st

from src.config.settings import get_settings
from src.llm.model_router import ROUTING_GLM_ONLY, ROUTING_PROFILES, ROUTING_SINGLE
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
    if "active_model" not in st.session_state:
        st.session_state.active_model = settings.siliconflow_model
    if "routing_key" not in st.session_state:
        st.session_state.routing_key = ROUTING_GLM_ONLY

    with st.sidebar:
        st.header("案例列表")
        routing_key = st.selectbox(
            "模型路由策略",
            options=list(ROUTING_PROFILES.keys()),
            format_func=lambda value: ROUTING_PROFILES[value].label,
            index=list(ROUTING_PROFILES.keys()).index(st.session_state.routing_key)
            if st.session_state.routing_key in ROUTING_PROFILES
            else 0,
        )
        st.session_state.routing_key = routing_key
        workflow_service.set_routing_key(routing_key)
        st.caption(ROUTING_PROFILES[routing_key].description)

        active_model = st.selectbox(
            "手动模型",
            options=list(settings.supported_models),
            index=list(settings.supported_models).index(st.session_state.active_model)
            if st.session_state.active_model in settings.supported_models
            else 0,
            disabled=routing_key != ROUTING_SINGLE,
        )
        st.session_state.active_model = active_model
        workflow_service.set_active_model(active_model)

        if routing_key != ROUTING_SINGLE:
            with st.expander("查看阶段模型映射"):
                for stage_name, model_name in ROUTING_PROFILES[routing_key].stage_models.items():
                    st.write(f"`{stage_name}` -> `{model_name}`")

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

    st.info(
        f"当前案例：`{case.client_alias}` | 当前阶段：`{case.current_stage}` | 路由策略：`{ROUTING_PROFILES[st.session_state.routing_key].label}` | 手动模型：`{st.session_state.active_model}`"
    )

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
