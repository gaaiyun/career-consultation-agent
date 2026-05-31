# Career Consultation Agent

面向职业咨询师的 Streamlit 工作台。把来访者一大段口语化倾诉，拆成四个阶段处理，每个阶段都留人工修改的口子，最后产出一份可直接发出的回复稿。

四个阶段对应真实咨询里的四步动作：

1. GPS+锚点结构化拆解：把碎片信息整理成定位、动力、约束三个系统，并标出矛盾点。
2. 矛盾追问与逻辑校准：生成追问草案，咨询师据此发问、记录回答，回答的优先级高于 AI 草案。
3. 路线规划与行动反推：按"条件 + 需求"筛出 2 到 3 条可行路线，区分可达性，反推每条路线现在要补什么。
4. 正式回复报告：把前三步沉淀成一份给来访者的 Markdown 回复。

每个阶段的输出都按版本存进本地 SQLite，可回看、可手改、可重跑。模型调用走 OpenAI 兼容接口，换服务商只改配置、不改代码。

## 这套流程为什么这么设计

- 咨询师主导：系统是助手不是替身，四个阶段都能改、都能回退重跑。
- 分阶段而非一次性出稿：单个 Prompt 一把梭容易跳步、结构散；拆开后哪一步质量差一目了然。
- 结构先于文风：先把结构化字段稳住，报告语言风格再优化。
- 人工判断进 Prompt：咨询师的追问记录、可达性标注、路线修正都会注入下游 Prompt，而不是摆设。

## 模型路由

- 单模型模式：四个阶段都用侧边栏手动选的那个模型。
- GLM 全阶段模式：四个阶段都走 GLM-4.6。结构化输出在实测里更稳，默认用这个。
- 混合分流模式：拆解、追问、规划走 GLM-4.6，终版报告走 DeepSeek。属于实验选项。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置模型接口

接任意 OpenAI 兼容接口，三个变量：API Key、Base URL、模型名。PowerShell：

```powershell
# 例：硅基流动
$env:LLM_API_KEY = "你的_key"
$env:LLM_BASE_URL = "https://api.siliconflow.cn/v1"
$env:LLM_MODEL = "deepseek-ai/DeepSeek-V3.2"

# 例：直连 DeepSeek
$env:LLM_API_KEY = "你的_key"
$env:LLM_BASE_URL = "https://api.deepseek.com"
$env:LLM_MODEL = "deepseek-v4-flash"
```

cmd 用 `set`，bash 用 `export`。

旧的 `SILICONFLOW_API_KEY` / `SILICONFLOW_BASE_URL` / `SILICONFLOW_MODEL` 仍然可用，作为 `LLM_*` 的回退；`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` 也会被读取。三组优先级：`LLM_*` > `OPENAI_*` > `SILICONFLOW_*`。

可选变量：`LLM_TIMEOUT`（秒，默认 90）、`LLM_NATIVE_JSON`（设 `false` 可关掉 `response_format=json_object`，给不支持该参数的端点用）。

### 3. 运行应用

```bash
streamlit run app.py
```

没配 Key 时应用照常打开，能新建和浏览案例，只是点生成会提示缺 Key。

## Streamlit Secrets

本地环境变量和 Streamlit 的 `secrets.toml` 都支持，变量名一致。示例见 `.streamlit/secrets.toml.example`。

## 部署到 Streamlit Community Cloud

### 1. 推送到 GitHub

先把本项目推到你的 GitHub 仓库。

### 2. 在 Streamlit Community Cloud 新建应用

- 选择你的 GitHub 仓库
- 主文件填写 `app.py`
- Python 依赖自动读取 `requirements.txt`

### 3. 在 Streamlit Secrets 中填入配置

```toml
LLM_API_KEY = "你的_key"
LLM_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_MODEL = "deepseek-ai/DeepSeek-V3.2"
LLM_TIMEOUT = "60"
```

### 4. 部署后验证

- 能打开案例录入页
- 能新建案例
- 配好 Secrets 后能正常调用模型

## 测试

测试套件不打网络、不需要 Key：用一个假的 LLM 客户端和临时 SQLite 库，覆盖 JSON 抽取与修复、四个阶段的 normalizer、报告渲染、Prompt 模板、模型路由、仓储读写，以及四阶段编排（含人工笔记注入下游 Prompt、版本递增、人工修订）。

```bash
pip install -r requirements.txt pytest
pytest
```

GitHub Actions 在 push 和 PR 时跑同一套测试（Python 3.11 / 3.12 / 3.13），见 `.github/workflows/ci.yml`。

要对真实接口做一次端到端验证，配好上面的 `LLM_*` 环境变量后跑 `scripts/run_example_tests.py`，它会把四个示例案例各跑一遍四阶段并把结果写到 `tmp/test_outputs/`。

## 文档

- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/PROMPT_SPEC.md`
- `docs/DATA_MODEL_AND_FEISHU_MAPPING.md`
- `docs/FEISHU_SYNC_NEXT_STEPS.md`
- `docs/IMPLEMENTATION_ROADMAP.md`

## 示例测试案例

- `examples/README.md`
- `examples/case_01_ruc_han_language.txt`
- `examples/case_02_music_major_transition.txt`
- `examples/case_03_b2b_content_operator.txt`
- `examples/case_04_ruc_labor_econ_gap.txt`

## 项目结构

```text
app.py
src/
  config/        # 配置读取（LLM_* / OPENAI_* / SILICONFLOW_* 回退）
  domain/        # 领域模型
  integrations/  # 飞书多维表格映射（预留，未启用）
  llm/           # OpenAI 兼容客户端 + 模型路由
  prompts/       # 四阶段 Prompt 模板（Markdown）
  services/      # normalizer 与报告 formatter
  storage/       # SQLite 建表与仓储
  ui/            # Streamlit 页面与组件
  workflow/      # 四阶段编排
tests/           # pytest，离线可跑
docs/
data/            # 运行时生成的本地数据库
```
