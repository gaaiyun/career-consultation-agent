# 数据模型与飞书字段映射

## 1. 设计目标

- 支持咨询全流程的结构化存储
- 支持阶段版本化
- 支持后续同步到飞书多维表格

## 2. 核心实体

## 2.1 Case

表示一个完整职业咨询案例。

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `case_id` | string | 案例唯一 ID |
| `client_alias` | string | 来访者代称 |
| `source_text` | text | 原始倾诉文本 |
| `current_stage` | string | 当前阶段 |
| `tags` | json | 案例标签 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

## 2.2 StageResult

表示某案例在某阶段的一次输出版本。

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 自增主键 |
| `case_id` | string | 所属案例 |
| `stage_name` | string | 阶段名称 |
| `version_no` | integer | 阶段内版本号 |
| `input_payload` | json | 输入快照 |
| `output_payload` | json | 输出快照 |
| `created_at` | datetime | 生成时间 |

## 2.3 PromptRun

表示一次模型调用记录。

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 自增主键 |
| `case_id` | string | 所属案例 |
| `stage_name` | string | 阶段名称 |
| `prompt_name` | string | Prompt 名称 |
| `model` | string | 模型名称 |
| `temperature` | real | 温度参数 |
| `input_summary` | text | 输入摘要 |
| `raw_response` | text | 原始响应 |
| `success` | integer | 是否成功 |
| `latency_ms` | integer | 耗时 |
| `created_at` | datetime | 调用时间 |

## 2.4 ExportRecord

表示导出记录。

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 自增主键 |
| `case_id` | string | 所属案例 |
| `export_type` | string | 导出类型 |
| `content` | text | 导出内容 |
| `created_at` | datetime | 导出时间 |

## 3. 结构化输出对象

## 3.1 StructuredProfile

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

## 3.2 FollowUpQuestionSet

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
      "expected_signal": "string",
      "answer": "string"
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

## 3.3 RoutePlan

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

## 3.4 FinalReport

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

## 4. SQLite 表结构建议

## 4.1 `cases`

```sql
CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  client_alias TEXT NOT NULL,
  source_text TEXT NOT NULL,
  current_stage TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 4.2 `case_versions`

```sql
CREATE TABLE IF NOT EXISTS case_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL,
  stage_name TEXT NOT NULL,
  version_no INTEGER NOT NULL,
  input_payload TEXT NOT NULL,
  output_payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 4.3 `prompt_runs`

```sql
CREATE TABLE IF NOT EXISTS prompt_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL,
  stage_name TEXT NOT NULL,
  prompt_name TEXT NOT NULL,
  model TEXT NOT NULL,
  temperature REAL NOT NULL,
  input_summary TEXT NOT NULL,
  raw_response TEXT NOT NULL,
  success INTEGER NOT NULL,
  latency_ms INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

## 4.4 `exports`

```sql
CREATE TABLE IF NOT EXISTS exports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL,
  export_type TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 5. 飞书多维表格映射设计

首版建议采用“一主多子”结构，避免一个表塞入过多长文本和数组字段。

## 5.1 表一：案例主表

表名建议：`Cases`

| 飞书字段 | 来源字段 | 类型 |
|---|---|---|
| 案例ID | `case_id` | 单行文本 |
| 来访者代称 | `client_alias` | 单行文本 |
| 当前阶段 | `current_stage` | 单选 |
| 标签 | `tags` | 多选 |
| 原始文本摘要 | `source_text` 截断 | 多行文本 |
| 创建时间 | `created_at` | 日期时间 |
| 更新时间 | `updated_at` | 日期时间 |

## 5.2 表二：结构化拆解表

表名建议：`StructuredAnalysis`

| 飞书字段 | 来源字段 | 类型 |
|---|---|---|
| 案例ID | `case_id` | 关联/文本 |
| 版本号 | `version_no` | 数字 |
| 核心总结 | `summary` | 多行文本 |
| 标签 | `tags` | 多选 |
| 教育背景 | `profile.education` | 多行文本 |
| 经验背景 | `profile.experience` | 多行文本 |
| 当前状态 | `profile.current_status` | 单行文本 |
| 兴趣 | `motivation.interests` | 多行文本 |
| 优势 | `motivation.strengths` | 多行文本 |
| 价值观 | `motivation.values` | 多行文本 |
| 外部约束 | `constraints.external` | 多行文本 |
| 内在约束 | `constraints.internal` | 多行文本 |
| 洞察 | `insights` | 多行文本 |
| 待澄清问题 | `open_questions` | 多行文本 |

## 5.3 表三：追问记录表

表名建议：`FollowUpQuestions`

| 飞书字段 | 来源字段 | 类型 |
|---|---|---|
| 案例ID | `case_id` | 关联/文本 |
| 版本号 | `version_no` | 数字 |
| 问题文本 | `question_text` | 多行文本 |
| 提问原因 | `reason` | 多行文本 |
| 优先级 | `priority` | 单选 |
| 回答 | `answer` | 多行文本 |

## 5.4 表四：路线规划表

表名建议：`RoutePlans`

| 飞书字段 | 来源字段 | 类型 |
|---|---|---|
| 案例ID | `case_id` | 关联/文本 |
| 版本号 | `version_no` | 数字 |
| 推荐路线 | `recommended_route` | 单行文本 |
| 路线名称 | `route_name` | 单行文本 |
| 适配度 | `fit_score` | 数字 |
| 优势 | `advantages` | 多行文本 |
| 风险 | `risks` | 多行文本 |
| 准备动作 | `prep_actions` | 多行文本 |
| 决策逻辑 | `decision_logic` | 多行文本 |
| 下一步 | `next_steps` | 多行文本 |

## 5.5 表五：终版报告表

表名建议：`FinalReports`

| 飞书字段 | 来源字段 | 类型 |
|---|---|---|
| 案例ID | `case_id` | 关联/文本 |
| 版本号 | `version_no` | 数字 |
| 标题 | `title` | 单行文本 |
| 开场回应 | `opening` | 多行文本 |
| 核心判断 | `core_findings` | 多行文本 |
| 推荐路线 | `recommended_route` | 单行文本 |
| 行动计划 | `action_plan` | 多行文本 |
| 风险提醒 | `risk_reminders` | 多行文本 |
| 结尾 | `closing` | 多行文本 |

## 6. 同步策略建议

### 首版

- 不自动同步
- 只保留映射规则

### 后续版本

- 手动点击同步单案例
- 失败可重试
- 同步成功记录飞书记录 ID

## 7. 关键注意事项

- 飞书字段应尽量扁平化
- 数组字段写入前需要做换行或分隔符转换
- 长文本字段应避免超过单字段可读极限
- 案例 ID 应作为所有表的统一主关联键
