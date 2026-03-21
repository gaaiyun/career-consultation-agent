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
    "deepseek-ai/DeepSeek-V3.2",
    "zai-org/GLM-4.6",
]


def main() -> None:
    settings = get_settings()
    client = SiliconFlowClient(settings)
    prompt_registry = PromptRegistry(settings)

    source_text = Path("examples/case_01_ruc_han_language.txt").read_text(encoding="utf-8")
    prompt = prompt_registry.render_prompt("structured_analysis", {"source_text": source_text})
    system_prompt = (
        "你是一个职业咨询师助手。你的职责是把来访者的碎片化叙述转化为结构化信息、"
        "矛盾追问、路线规划和正式回复稿。你要遵守 GPS+锚点 的咨询思路。"
    )

    results: dict[str, dict] = {}
    for model in MODELS:
        start = time.time()
        try:
            output = client.generate_json(
                system_prompt,
                prompt,
                model=model,
                temperature=0.2,
                timeout=30,
                max_tokens=1200,
            )
            results[model] = {
                "success": True,
                "elapsed_seconds": round(time.time() - start, 2),
                "output": output,
            }
            print(f"[OK] {model} -> {results[model]['elapsed_seconds']}s", flush=True)
        except Exception as exc:
            raw_text = ""
            try:
                raw_text = client.generate(
                    system_prompt,
                    prompt,
                    model=model,
                    temperature=0.2,
                    timeout=20,
                    max_tokens=1200,
                )
            except Exception as raw_exc:
                raw_text = f"<raw generation failed: {raw_exc}>"
            results[model] = {
                "success": False,
                "elapsed_seconds": round(time.time() - start, 2),
                "error": str(exc),
                "raw_text_preview": raw_text[:2000],
            }
            print(f"[ERR] {model} -> {exc}", flush=True)

    Path("tmp").mkdir(exist_ok=True)
    Path("tmp/compare_models_case01.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
