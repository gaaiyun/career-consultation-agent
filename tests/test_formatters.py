"""Tests for report formatting (structured payload -> Markdown)."""
from __future__ import annotations

from src.services.formatters import to_markdown_report, to_pretty_json


def test_markdown_passthrough_when_present() -> None:
    assert to_markdown_report({"report_markdown": "# Hi\nbody"}) == "# Hi\nbody"


def test_pretty_json_keeps_chinese() -> None:
    out = to_pretty_json({"k": "中文"})
    assert "中文" in out
    assert "\\u" not in out


def test_structured_report_renders_all_sections() -> None:
    payload = {
        "title": "测试报告",
        "opening": "你目前卡在定位问题上。",
        "summary_of_case": "5 年 B 端内容运营。",
        "core_findings": [
            {"theme": "定位", "detail": "问题大于能力问题"},
            "市场没有识别你的能力",
        ],
        "route_recommendation": {
            "recommended_route": "具身智能内容运营",
            "recommendation_detail": "复用 B 端经验。",
            "alternative_routes": ["回到甲方", "大模型企业内容"],
        },
        "action_plan": {
            "immediate_actions": ["改简历定位段"],
            "near_term_actions": ["投 3 家垂直公司"],
            "mid_term_actions": ["搭个人作品集"],
        },
        "risk_reminders": ["不要盲投"],
        "questions_for_next_round": ["目标薪资区间？"],
        "closing": "先从定位改起。",
    }
    md = to_markdown_report(payload)
    assert md.startswith("# 测试报告")
    assert "## 核心画像" in md
    assert "## 核心判断" in md
    assert "- 定位：问题大于能力问题" in md
    assert "- 市场没有识别你的能力" in md
    assert "## 推荐路线" in md
    assert "具身智能内容运营" in md
    assert "## 备选路线" in md
    assert "- 回到甲方" in md
    assert "### 立刻开始" in md
    assert "- 改简历定位段" in md
    assert "## 风险提醒" in md
    assert "## 后续待澄清问题" in md
    assert md.rstrip().endswith("先从定位改起。")


def test_structured_report_handles_empty_sections() -> None:
    md = to_markdown_report({"title": "空报告"})
    assert "# 空报告" in md
    assert "- 暂无" in md  # empty action lists fall back to 暂无
