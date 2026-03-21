from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import get_settings
from src.prompts.registry import PromptRegistry
from src.llm.siliconflow_client import SiliconFlowClient


MODELS = [
    "zai-org/GLM-4.6",
    "deepseek-ai/DeepSeek-V3.2",
]


def main() -> None:
    settings = get_settings()
    client = SiliconFlowClient(settings)
    prompt_registry = PromptRegistry(settings)

    source_text = Path("examples/case_01_ruc_han_language.txt").read_text(encoding="utf-8")

    structured_analysis_json = json.dumps(
        {
            "core_profile": {
                "one_sentence_summary": "一位人大汉语言大一学生，家庭无托底、视力受限，极度追求就业安全感，正在纠结是否通过转专业换取更大的职业退路。",
                "tags": ["人大", "汉语言", "家境一般", "病理性高度近视", "求稳"],
            },
            "contradictions": [
                {
                    "label": "求稳与转专业",
                    "description": "一方面追求稳定和低风险，另一方面希望通过转专业扩大市场化就业退路。",
                    "why_it_matters": "这会直接影响未来是保体制筹码还是换市场化选择权。",
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )

    route_plan_json = json.dumps(
        {
            "recommended_route": {
                "route_name": "专业不动、技能外扩",
                "why_recommended": [
                    "能同时保留班长、入党、绩点等体制内筹码",
                    "也能通过跨院选课和实习积累市场化能力",
                ],
                "why_not_others": [
                    "直接转专业会带来补课压力和已有筹码损失"
                ],
                "reverse_action_plan": {
                    "now": ["稳住绩点", "尽快推进入党流程"],
                    "next_1_to_3_months": ["跨院选新闻或传播实务课", "开始关注校媒和助管机会"],
                    "next_3_to_12_months": ["尝试市场化实习", "同步关注高校行政和国央企路径"],
                },
            }
        },
        ensure_ascii=False,
        indent=2,
    )

    prompt = prompt_registry.render_prompt(
        "final_report",
        {
            "source_text": source_text,
            "structured_analysis_json": structured_analysis_json,
            "route_plan_json": route_plan_json,
        },
    )
    system_prompt = (
        "你是一个职业咨询师助手。你的职责是把来访者的碎片化叙述转化为结构化信息、"
        "矛盾追问、路线规划和正式回复稿。你要遵守 GPS+锚点 的咨询思路。"
    )

    results: dict[str, dict] = {}
    for model in MODELS:
        start = time.time()
        try:
            output = client.generate(
                system_prompt,
                prompt,
                model=model,
                temperature=0.5,
                timeout=35,
                max_tokens=1400,
            )
            results[model] = {
                "success": True,
                "elapsed_seconds": round(time.time() - start, 2),
                "preview": output[:800],
            }
            print(f"[OK] {model} -> {results[model]['elapsed_seconds']}s", flush=True)
        except Exception as exc:
            results[model] = {
                "success": False,
                "elapsed_seconds": round(time.time() - start, 2),
                "error": str(exc),
            }
            print(f"[ERR] {model} -> {exc}", flush=True)

    Path("tmp").mkdir(exist_ok=True)
    Path("tmp/compare_final_report_models.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
