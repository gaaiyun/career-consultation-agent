from __future__ import annotations


def map_case_to_feishu_fields(case: dict) -> dict:
    return {
        "案例ID": case.get("case_id", ""),
        "来访者代称": case.get("client_alias", ""),
        "当前阶段": case.get("current_stage", ""),
        "标签": case.get("tags", []),
        "原始文本摘要": case.get("source_text", "")[:200],
        "创建时间": case.get("created_at", ""),
        "更新时间": case.get("updated_at", ""),
    }
