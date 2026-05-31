# 更新记录

## v2

接口层从绑定单一服务商改为服务商无关，并补上自动化测试和 CI。底层四阶段工作流和提示词没动。

### 接口层服务商无关化

- LLM 客户端从 `SiliconFlowClient` 改名 `OpenAICompatibleClient`，旧名保留为别名，旧的 `from src.llm.siliconflow_client import SiliconFlowClient` 仍能用。
- 配置按 `LLM_*` > `OPENAI_*` > `SILICONFLOW_*` 顺序读取，任意 OpenAI 兼容端点改配置即可接入，旧部署不用动。
- `generate_json` 的原生 `json_object` 模式判定不再写死某个模型名，改成按端点能力配置（`LLM_NATIVE_JSON` 可覆盖）。

### 其他改动

- 删掉 `supported_models` 里一个不存在的模型 ID（`Qwen/Qwen3.5-397B-A17B`），换成 `Qwen/Qwen3-235B-A22B-Instruct-2507`。
- 新增 `tests/`：59 个 pytest 用例，离线可跑（假 LLM 客户端 + 临时 SQLite），覆盖 JSON 抽取与修复、四个 normalizer、报告 formatter、Prompt 模板、模型路由、仓储、四阶段编排。
- 新增 `.github/workflows/ci.yml`，push 和 PR 时在 Python 3.11 / 3.12 / 3.13 上跑测试。
- README 与 PRD、ARCHITECTURE 改为服务商无关表述，去掉宣传腔。

### 验证

接 DeepSeek 直连（`https://api.deepseek.com`，`deepseek-v4-flash`）对一个真实案例跑通四阶段：拆解出 2 条矛盾、3 个方向，生成 4 个追问，3 条带可达性的路线并选出主推路线，最后产出 Markdown 报告。凭证只在本机环境变量，不进仓库。
