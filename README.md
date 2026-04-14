# Creating Systematology — 系统学深度研究 Agent

> 以系统科学为方法论内核的深度研究 Agent，输出可审计、可评估、可复现的结构化研究。

---

## 1. 快速开始

**1. 克隆并配置**
```bash
git clone <repository-url>
cd Creating-Systematology-RAG
```

**2. 配置 API Keys（二选一）**

- **已有 passphrase**（团队成员 / 新设备）：
  ```bash
  python scripts/env_sync.py setup <passphrase>
  # 之后项目启动时自动从 Gist 拉取 .env，无需手动操作
  ```
- **首次配置**：
  ```bash
  cp env.template .env
  # 编辑 .env，填入 DEEPSEEK_API_KEY、Chroma Cloud 凭证、HF_TOKEN
  make env-init        # 加密上传到私有 Gist，生成 passphrase
  ```

**3. 安装并启动**
```bash
make              # 安装依赖 + 运行测试
make run          # 启动 Web 应用
```

> 📖 GPU 配置、Windows 特殊处理 → [高级配置指南](docs/quick-start-advanced.md)

---

## 2. 三支柱：领域定制 · 可审计 · 评估反馈

| 支柱 | 说明 | 确定性保证 |
|------|------|----------|
| **领域定制** | 系统科学方法论编码在工具、状态模型和流程中，不只是 prompt 指令 | 方法论步骤和状态模型由架构 enforce |
| **可审计** | 每一步推理过程可追溯：工具调用、状态变更、决策理由均有结构化日志 | 审计记录不依赖 LLM 概率输出 |
| **评估反馈** | 内建质量度量（证据可追溯性、张力识别、收束效率）+ 运行时回流 | 评估分数是确定性计算，非 LLM 自评 |

> **设计哲学**：LLM 是概率机器——Skill 层（prompt）引导推理方向提供创造力，架构层（工具/状态/评估）enforce 关键约束提供可靠性。两层叠加，概率负责探索，确定性负责底线。

### 工程特性

| 特性 | 说明 |
|------|------|
| **双模式 RAG** | 传统 RAG（固定策略）+ Agentic RAG（Agent 自主决策），可通过 UI 切换 |
| **多策略检索** | 向量语义、BM25 关键词、Grep 正则、混合检索，自动路由选择最优策略 |
| **三级降级** | Agent 失败 → ModularEngine → 纯 LLM → 友好错误，确保服务可用 |
| **可插拔设计** | Embedding、Retriever、Reranker、Observer 均支持替换 |
| **可观测性** | LlamaIndex Instrumentation + structlog 结构化追踪，行为透明可追溯 |
| **自动密钥管理** | `.env` 加密存储于私有 Gist，项目启动时无感自动拉取 |

---

## 3. 技术栈

- **Python 3.12+** / **uv** - 语言与依赖管理
- **LlamaIndex** - RAG 核心框架（含 ReActAgent）
- **DeepSeek API** - 大语言模型（支持推理链）
- **Chroma Cloud** - 向量数据库（云端托管）
- **Streamlit** - Web 界面（支持 Dark 模式）
- **HuggingFace Embeddings** - 本地向量模型
- **structlog** / **Pydantic** - 结构化日志与类型安全

---

## 4. 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│  用户层   Streamlit UI / Chat Interface                       │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  服务层   Agent Service / Session Manager                     │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│   Research Agent Core  (LlamaIndex AgentWorkflow)             │
│                                                               │
│   ┌─────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │   LLM   │◀──▶│  Agent Loop  │◀──▶│     工具集        │   │
│   │DeepSeek │    │  推理 ─ 执行  │    │ vector_search    │   │
│   │OpenAI   │    │  ─ 观察 循环  │    │ hybrid_search    │   │
│   │LiteLLM  │    │              │    │ record_evidence  │   │
│   └─────────┘    └──────┬───────┘    │ synthesize       │   │
│                         │            │ reflect          │   │
│                         │            │ evaluate_judgment│   │
│                    ┌────▼─────┐      └─────────┬────────┘   │
│                    │  State   │                 │            │
│                    │ 证据账本  │◀────── 工具读写 ─┘            │
│                    │ 研究进度  │                              │
│                    └──────────┘                              │
│                                                               │
│   护栏: timeout / max_iterations / prompt约束 / 输出schema    │
│   可观测: structlog + Observers (每步可追溯)                   │
│                                                               │
└──────────────────────────┬───────────────────────────────────┘
                           │ 工具访问外部资源
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  基础设施层                                                    │
│  Chroma VectorDB / HuggingFace Embeddings / Reranker         │
│  State Persistence (Context 序列化)                            │
└──────────────────────────────────────────────────────────────┘
```

**输出**: `ResearchOutput { judgment, evidence, confidence, tensions, next_questions }`

**四层架构**：用户层 → 服务层 → Agent Core → 基础设施层。核心是 LlamaIndex AgentWorkflow 驱动的研究型 Agent，LLM 自主决策研究节奏（概率层），代码层 enforce 状态、评估和审计（确定性层）。

> 📖 详细架构、工作流程、模块职责 → [架构设计文档](docs/architecture.md)

### 研究运行流程

架构图描述系统**由什么组成**，运行流程描述**实际发生什么**。以下是 Research Agent 处理一个研究问题的完整运行时路径：

```
用户提问
  │
  ▼
定焦 ─────────── LLM 理解问题，聚焦到可研究的子问题
  │
  ▼
取证计划 ──────── 制定 2-3 个关键子问题 + 检索策略
  │
  │         ┌──────────────────────────────────────────────┐
  │         │          取证 ─ 判断 ─ 评估 闭环              │
  ▼         │                                              │
┌───────────┴──┐                                           │
│  取证执行     │                                           │
│  search →    │                                           │
│  阅读 →      │                                           │
│  record      │  每次 record_evidence 消耗 1 轮预算        │
└──────┬───────┘                                           │
       │                                                   │
       ▼                                                   │
┌──────────────┐                                           │
│  综合判断     │                                           │
│  synthesize: │  判断 + 置信度 + 张力 + 追问方向           │
└──────┬───────┘                                           │
       │                                                   │
       ▼                                                   │
┌──────────────┐    质量不达标                               │
│  评估回流     │    且有预算     ┌────────────────┐        │
│  evaluate_   ├──────────────▶│ 改进建议:       │        │
│  judgment    │               │ · 补充证据      ├────────┘
│              │               │ · 修正判断      │
│ 证据可追溯性  │               │ · 具化张力      │
│ 张力识别      │               └────────────────┘
│ 收束效率      │
└──────┬───────┘
       │ 质量达标 或 预算耗尽
       ▼
┌──────────────┐
│  反思收束     │  reflect → 确认完成
└──────┬───────┘
       │
       ▼

  ResearchOutput { judgment, evidence, confidence, tensions, next_questions }
```

**核心机制**：Agent 自主控制节奏，代码层只设硬护栏（timeout / max_iterations / budget）。评估回流让 Agent 在研究过程中自我校正，而不是等研究结束才发现质量问题。

---

## 5. 项目规模评估

截至 `2026-03-25`，按 `git ls-files` 统计，本项目共包含 `646` 个 Git 跟踪文件。该口径仅统计仓库受版本控制的文件，排除 `.venv`、缓存目录和其他生成物，更适合用于正式规模评估。

| 维度 | 当前规模 |
|------|----------|
| 仓库整体 | `646` 个 Git 跟踪文件 |
| 核心代码 | `275` 个 Python 文件，约 `46,985` 行 |
| 后端代码 | `148` 个 Python 文件，约 `21,636` 行 |
| 前端代码 | `28` 个 Python 文件，约 `4,898` 行 |
| 测试体系 | `97` 个 Python 文件，约 `20,128` 行 |
| 文档沉淀 | `328` 个 Markdown 文件 |

综合判断：从核心代码体量看，本项目属于`中型偏大`的 Python 工程；若将测试体系和文档沉淀一并计入，仓库整体已呈现`中大型工程仓库`特征，说明项目在功能实现之外，也投入了较完整的验证与文档化建设。

---

## 6. 常用命令

### 开发与测试

| 命令 | 说明 |
|------|------|
| `make` | 安装依赖 + 运行完整测试 |
| `make run` | 启动 Streamlit Web 应用 |
| `make start` | 一键启动（安装 + 测试 + 运行） |
| `make dev` | 开发模式（安装 + 快速测试） |
| `make test-unit` | 仅运行单元测试 |
| `make test-fast` | 跳过慢速测试 |

### 密钥管理

| 命令 | 说明 |
|------|------|
| `make env-init` | 首次配置：加密 `.env` 并上传到私有 Gist |
| `make env-push` | 更新 `.env` 后推送到 Gist（如更换 API Key） |
| `make env-pull` | 从 Gist 拉取并解密 `.env` |
| `python scripts/env_sync.py setup <passphrase>` | 新设备初始化（一次性） |

> `.env` 丢失无需担心——项目启动时会自动从 Gist 恢复（需本机已配置 passphrase）。

### 验证与评估

| 命令 | 说明 |
|------|------|
| `make verify-observability` | 验证可观测性 + 评估体系（真实 API 调用） |
| `make e2e-smoke` | E2E 冒烟测试（1 题快速验证） |
| `make e2e-regression` | E2E 回归测试（多题质量验证） |

---

## 7. 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 三层架构、工作流程、模块交互、决策记录 |
| [高级配置](docs/quick-start-advanced.md) | GPU 配置、Windows 处理、Chroma Cloud、配置系统 |
| [Prompt 模板](prompts/README.md) | Prompt 模板集中管理与使用指南 |
| [Aha Moments](aha-moments/README.md) | 项目开发中的顿悟瞬间与深度思考 |
| [任务日志](agent-task-log/README.md) | AI Agent 执行任务的完整记录 |

---

## 8. 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**最后更新**: 2026-04-10  
**License**: MIT
