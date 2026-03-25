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
from src.ui.styles import inject_styles
from src.workflow.orchestrator import ConsultationWorkflowService
from src.workflow.stages import FINAL_REPORT, QUESTIONING, ROUTE_PLANNING, STRUCTURED_ANALYSIS


settings = get_settings()
init_db(settings)
case_repo = CaseRepository(settings)
workflow_service = ConsultationWorkflowService(settings)

_STAGE_LABELS = {
    STRUCTURED_ANALYSIS.name: "结构化拆解",
    QUESTIONING.name: "矛盾追问",
    ROUTE_PLANNING.name: "路线规划",
    FINAL_REPORT.name: "终版报告",
}
_ALL_STAGES = list(_STAGE_LABELS.keys())


def _case_label(case) -> str:
    return f"{case.client_alias}  ·  {case.case_id[-8:]}"


def _render_progress_and_run_all(case) -> None:
    completed = workflow_service.completed_stages(case.case_id)
    n_done = len(completed)
    n_total = len(_ALL_STAGES)

    stage_display = "  /  ".join(
        _STAGE_LABELS[s] if s in completed else f"[ {_STAGE_LABELS[s]} ]"
        for s in _ALL_STAGES
    )
    st.progress(
        n_done / n_total,
        text=f"{n_done} / {n_total}  —  {stage_display}",
    )

    if n_done < n_total:
        col_btn, col_hint = st.columns([2, 5])
        with col_btn:
            run_all = st.button(
                "运行后续所有步骤",
                key="run_all_pipeline",
                type="primary",
                use_container_width=True,
                help="从当前进度开始，依次自动运行剩余所有步骤（不会覆盖已有结果）",
            )
        with col_hint:
            st.caption("如果某一步失败，前序结果会保留，可单独在对应页签重新生成。")

        if run_all:
            with st.status("正在运行后续步骤…", expanded=True) as status:
                try:
                    def on_start(stage_name: str) -> None:
                        st.write(f"运行中：{_STAGE_LABELS.get(stage_name, stage_name)}")

                    def on_done(stage_name: str) -> None:
                        st.write(f"完成：{_STAGE_LABELS.get(stage_name, stage_name)}")

                    executed = workflow_service.run_pipeline_remaining(
                        case.case_id,
                        on_stage_start=on_start,
                        on_stage_done=on_done,
                    )
                    if executed:
                        status.update(
                            label=f"完成。共执行 {len(executed)} 个步骤。",
                            state="complete",
                        )
                    else:
                        status.update(label="所有步骤已完成，无需重新运行。", state="complete")
                except Exception as exc:
                    status.update(label=f"运行中断：{exc}", state="error")
                    st.error(f"运行失败，请查看对应步骤页签。\n\n{exc}")
            st.rerun()
    else:
        st.caption("所有步骤已完成。可在各页签查看或修改，然后下载终版报告。")


def main() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    if "selected_case_id" not in st.session_state:
        st.session_state.selected_case_id = None
    if "active_model" not in st.session_state:
        st.session_state.active_model = settings.siliconflow_model
    if "routing_key" not in st.session_state:
        st.session_state.routing_key = ROUTING_GLM_ONLY

    # ------------------------------------------------------------------ #
    # Sidebar
    # ------------------------------------------------------------------ #
    with st.sidebar:
        st.markdown("## 职业咨询工作台")
        st.divider()

        st.markdown("**模型路由**")
        routing_key = st.selectbox(
            "路由策略",
            options=list(ROUTING_PROFILES.keys()),
            format_func=lambda v: ROUTING_PROFILES[v].label,
            index=list(ROUTING_PROFILES.keys()).index(st.session_state.routing_key)
            if st.session_state.routing_key in ROUTING_PROFILES
            else 0,
            label_visibility="collapsed",
        )
        st.session_state.routing_key = routing_key
        workflow_service.set_routing_key(routing_key)
        st.caption(ROUTING_PROFILES[routing_key].description)

        active_model = st.selectbox(
            "手动模型（仅在「单模型」策略下生效）",
            options=list(settings.supported_models),
            index=list(settings.supported_models).index(st.session_state.active_model)
            if st.session_state.active_model in settings.supported_models
            else 0,
            disabled=routing_key != ROUTING_SINGLE,
            label_visibility="visible",
        )
        st.session_state.active_model = active_model
        workflow_service.set_active_model(active_model)

        if routing_key != ROUTING_SINGLE:
            with st.expander("阶段模型映射"):
                for sn, mn in ROUTING_PROFILES[routing_key].stage_models.items():
                    st.caption(f"{sn}  →  {mn}")

        st.divider()

        st.markdown("**案例**")
        cases = case_repo.list_cases()
        options = ["__new__"] + [c.case_id for c in cases]
        labels = {"__new__": "新建案例"}
        labels.update({c.case_id: _case_label(c) for c in cases})
        selected = st.selectbox(
            "选择案例",
            options=options,
            format_func=lambda v: labels[v],
            index=0
            if st.session_state.selected_case_id not in options
            else options.index(st.session_state.selected_case_id),
            label_visibility="collapsed",
        )
        st.session_state.selected_case_id = None if selected == "__new__" else selected

        if not workflow_service.llm_client.is_configured():
            st.warning("未检测到 API Key，无法调用模型生成内容。")

    # ------------------------------------------------------------------ #
    # Main area — new case intake
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # Case header
    # ------------------------------------------------------------------ #
    st.markdown(f"### {case.client_alias}")
    st.caption(
        f"案例 ID：{case.case_id}  ·  "
        f"当前阶段：{case.current_stage}  ·  "
        f"路由：{ROUTING_PROFILES[st.session_state.routing_key].label}"
    )

    _render_progress_and_run_all(case)
    st.divider()

    # ------------------------------------------------------------------ #
    # Stage tabs
    # ------------------------------------------------------------------ #
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["结构化拆解", "矛盾追问", "路线规划", "终版报告", "历史版本"]
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
        _render_history(case)


def _render_history(case) -> None:
    st.markdown("## 历史版本")
    versions = workflow_service.list_stage_versions(case.case_id)
    if not versions:
        st.info("还没有历史版本。")
        return
    for version in versions:
        if version["stage_name"].endswith("_notes"):
            continue
        with st.expander(
            f"{version['stage_name']}  ·  v{version['version_no']}  ·  {version['created_at'][:19]}"
        ):
            st.json(version["output_payload"])


def _safe_render(renderer, case, workflow_service) -> None:
    try:
        renderer(case, workflow_service)
    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
