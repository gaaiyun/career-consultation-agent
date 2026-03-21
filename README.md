# Career Consultation Agent

一个面向职业咨询师的 `Streamlit` 咨询助手 MVP。

当前版本已经强化为更贴近真实咨询流程的四阶段工作流：

- `GPS+锚点` 结构化拆解
- 矛盾追问与逻辑校准
- 路线规划与行动反推
- 正式回复报告生成

## 功能概览

- 个案录入与管理
- 结构化拆解
- 矛盾追问生成
- 路线规划
- 终版回复报告
- 本地 `SQLite` 持久化
- `SiliconFlow` OpenAI 兼容接口接入
- 飞书多维表格字段映射预留

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
set SILICONFLOW_API_KEY=your_api_key
set SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
set SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3.2
```

如果使用 PowerShell：

```powershell
$env:SILICONFLOW_API_KEY="your_api_key"
$env:SILICONFLOW_BASE_URL="https://api.siliconflow.cn/v1"
$env:SILICONFLOW_MODEL="deepseek-ai/DeepSeek-V3.2"
```

### 3. 运行应用

```bash
streamlit run app.py
```

## Streamlit Secrets

本项目同时支持：

- 本地环境变量
- `Streamlit` 的 `secrets.toml`

示例文件见 `.streamlit/secrets.toml.example`。

## 部署到 Streamlit Community Cloud

### 1. 推送到 GitHub

先把本项目推到你的 GitHub 仓库。

### 2. 在 Streamlit Community Cloud 新建应用

- 选择你的 GitHub 仓库
- 主文件填写 `app.py`
- Python 依赖自动读取 `requirements.txt`

### 3. 在 Streamlit Secrets 中填入以下配置

```toml
SILICONFLOW_API_KEY = "your_siliconflow_api_key"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "deepseek-ai/DeepSeek-V3.2"
SILICONFLOW_TIMEOUT = "60"
```

### 4. 部署后验证

- 能打开案例录入页
- 能新建案例
- 配置好 `Secrets` 后能正常调用模型

## GitHub 发布建议

建议仓库根目录至少保留：

- `README.md`
- `requirements.txt`
- `.gitignore`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.example`
- `app.py`
- `src/`
- `docs/`

## 文档

- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/PROMPT_SPEC.md`
- `docs/DATA_MODEL_AND_FEISHU_MAPPING.md`
- `docs/IMPLEMENTATION_ROADMAP.md`

## 项目结构

```text
app.py
src/
  config/
  domain/
  integrations/
  llm/
  prompts/
  services/
  storage/
  ui/
  workflow/
docs/
data/
```
