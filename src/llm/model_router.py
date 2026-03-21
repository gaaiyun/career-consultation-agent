from __future__ import annotations

from dataclasses import dataclass


ROUTING_SINGLE = "single_model"
ROUTING_GLM_ONLY = "glm_all_stages"
ROUTING_HYBRID = "glm_analysis_deepseek_report"


@dataclass(frozen=True)
class RoutingProfile:
    key: str
    label: str
    description: str
    stage_models: dict[str, str]


ROUTING_PROFILES: dict[str, RoutingProfile] = {
    ROUTING_SINGLE: RoutingProfile(
        key=ROUTING_SINGLE,
        label="单模型模式",
        description="所有阶段都使用当前手动选中的模型。",
        stage_models={},
    ),
    ROUTING_GLM_ONLY: RoutingProfile(
        key=ROUTING_GLM_ONLY,
        label="GLM 全阶段模式（推荐）",
        description="结构化、追问、规划、报告全部使用 GLM-4.6。基于当前实测，这是职业咨询复杂结构输出下最稳妥的默认方案。",
        stage_models={
            "structured_analysis": "zai-org/GLM-4.6",
            "questioning": "zai-org/GLM-4.6",
            "route_planning": "zai-org/GLM-4.6",
            "final_report": "zai-org/GLM-4.6",
        },
    ),
    ROUTING_HYBRID: RoutingProfile(
        key=ROUTING_HYBRID,
        label="混合分流模式（实验）",
        description="结构化拆解、追问、路线规划使用 GLM-4.6，终版报告使用 DeepSeek-V3.2。当前保留为实验模式，不作为默认推荐。",
        stage_models={
            "structured_analysis": "zai-org/GLM-4.6",
            "questioning": "zai-org/GLM-4.6",
            "route_planning": "zai-org/GLM-4.6",
            "final_report": "deepseek-ai/DeepSeek-V3.2",
        },
    ),
}


def resolve_model_for_stage(
    stage_name: str,
    *,
    routing_key: str,
    fallback_model: str,
) -> str:
    profile = ROUTING_PROFILES.get(routing_key)
    if not profile or not profile.stage_models:
        return fallback_model
    return profile.stage_models.get(stage_name, fallback_model)
