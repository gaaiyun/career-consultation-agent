# Prompt 设计文档

## 1. 目标

将职业咨询流程拆为四个独立阶段，每个阶段使用单独 Prompt，保证：

- 输出结构稳定
- 便于单独调优
- 支持 JSON 解析

## 2. 统一约束

所有阶段均使用以下统一约束：

- 以职业咨询师助手身份工作
- 不虚构缺失事实
- 明确区分“已知事实”和“推断”
- 优先输出 JSON
- 列表字段使用数组
- 不输出额外解释性前后缀

统一系统提示词思路：

```text
你是一个职业咨询师助手。你的职责是把来访者的碎片化叙述转化为结构化信息、矛盾追问、路线规划和正式回复稿。你要遵守 GPS+锚点 的咨询思路：先做定位系统、动力系统、约束系统拆解，再做逻辑校准和路线反推。不要虚构事实，不要越权做心理诊断，结论必须基于已知信息。
```

## 3. 阶段一：结构化拆解

### Prompt 文件

- `src/prompts/structured_analysis.md`

### 输入

- 来访者原始文本
- 可选标签

### 输出目标

- 产出 `GPS+锚点` 结构化画像
- 提炼核心矛盾
- 输出初步方向和待澄清点

### JSON Schema

```json
{
  "core_profile": {
    "one_sentence_summary": "string",
    "tags": ["string"]
  },
  "gps_analysis": {
    "positioning_system": {
      "static_coordinates": {
        "education_background": ["string"],
        "professional_assets": ["string"],
        "current_status": "string"
      },
      "dynamic_path": {
        "work_timeline": ["string"],
        "achievement_events": ["string"],
        "transition_logic": ["string"]
      }
    },
    "motivation_system": {
      "interest_circle": ["string"],
      "ability_circle": ["string"],
      "value_circle": ["string"],
      "anchor_summary": "string"
    },
    "constraint_system": {
      "external_reality": ["string"],
      "internal_obstacles": ["string"]
    }
  },
  "contradictions": [
    {
      "label": "string",
      "description": "string",
      "why_it_matters": "string"
    }
  ],
  "preliminary_insights": ["string"],
  "possible_directions": ["string"],
  "clarification_questions": ["string"],
  "consultant_notes": {
    "confidence_level": "high|medium|low",
    "missing_information": ["string"],
    "bias_risks": ["string"]
  }
}
```

### 质量要求

- 不用空泛形容词替代事实
- 尽量提炼“矛盾”
- 未提及的信息不能编造

## 4. 阶段二：矛盾追问

### Prompt 文件

- `src/prompts/question_generation.md`

### 输入

- 原始文本
- 结构化拆解结果

### 输出目标

- 识别逻辑漏洞、模糊点、隐含假设
- 生成优先级明确的追问清单
- 给出咨询师继续深挖的提问策略

### JSON Schema

```json
{
  "question_strategy": {
    "goal": "string",
    "priority_rule": "string"
  },
  "questions": [
    {
      "question_text": "string",
      "reason": "string",
      "linked_contradiction": "string",
      "priority": "high|medium|low",
      "expected_signal": "string"
    }
  ],
  "logic_checks": [
    {
      "assumption": "string",
      "risk": "string"
    }
  ],
  "consultant_prompting_notes": ["string"]
}
```

### 质量要求

- 问题必须服务于后续路线判断
- 避免重复提问
- 优先问 1 到 2 个最关键的问题

## 5. 阶段三：路线规划

### Prompt 文件

- `src/prompts/route_planning.md`

### 输入

- 原始文本
- 结构化拆解结果
- 追问与补充回答

### 输出目标

- 识别 2 到 4 条可行路线
- 输出推荐路线与行动反推
- 明确“为什么推荐、为什么不推荐其他路径”

### JSON Schema

```json
{
  "planning_summary": {
    "decision_frame": "string",
    "core_tradeoff": "string"
  },
  "route_options": [
    {
      "route_name": "string",
      "route_positioning": "string",
      "fit_score": 0,
      "fit_reasons": ["string"],
      "advantages": ["string"],
      "risks": ["string"],
      "required_conditions": ["string"],
      "prep_actions": ["string"],
      "time_horizon": "string"
    }
  ],
  "recommended_route": {
    "route_name": "string",
    "why_recommended": ["string"],
    "why_not_others": ["string"],
    "reverse_action_plan": {
      "now": ["string"],
      "next_1_to_3_months": ["string"],
      "next_3_to_12_months": ["string"]
    }
  },
  "consultant_conclusion": {
    "bottom_line_advice": "string",
    "watch_points": ["string"]
  }
}
```

### 质量要求

- 路线命名要具体
- 明确说明推荐依据
- 不给只有概念没有动作的建议

## 6. 阶段四：终版回复报告

### Prompt 文件

- `src/prompts/final_report.md`

### 输入

- 原始文本
- 结构化拆解结果
- 路线规划结果

### 输出目标

- 形成可直接回复来访者的正式文本
- 风格接近成熟咨询师的回复结构

### JSON Schema

```json
{
  "title": "string",
  "opening": "string",
  "summary_of_case": "string",
  "core_findings": [
    {
      "theme": "string",
      "detail": "string"
    }
  ],
  "route_recommendation": {
    "recommended_route": "string",
    "recommendation_detail": "string",
    "alternative_routes": ["string"]
  },
  "action_plan": {
    "immediate_actions": ["string"],
    "near_term_actions": ["string"],
    "mid_term_actions": ["string"]
  },
  "risk_reminders": ["string"],
  "questions_for_next_round": ["string"],
  "closing": "string"
}
```

### 质量要求

- 语气克制、专业
- 避免制造焦虑
- 强调“建议”而非“宣判”

## 7. Prompt 变量规范

建议统一使用下列变量：

- `{{ source_text }}`
- `{{ case_tags }}`
- `{{ structured_analysis_json }}`
- `{{ follow_up_questions_json }}`
- `{{ route_plan_json }}`

## 8. 调用规范

### 8.1 generate_json

默认所有阶段调用 `generate_json()`。

当模型输出非 JSON 时：

1. 先尝试提取 JSON 片段
2. 提取失败则抛错
3. UI 提示人工重试

### 8.2 温度建议

- 结构化拆解：`0.2`
- 矛盾追问：`0.3`
- 路线规划：`0.4`
- 终版报告：`0.5`

## 9. 评估建议

每次优化 Prompt 时，建议从以下维度评估：

- 结构完整性
- 与原文一致性
- 是否提出关键矛盾
- 是否有空泛建议
- 是否便于咨询师直接接管编辑
