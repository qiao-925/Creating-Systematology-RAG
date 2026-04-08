# 创建系统学知识库RAG应用 (Creating Systematology RAG Application)

> 基于多策略检索增强生成的智能问答系统，通过并行融合向量、BM25、Grep 检索策略和智能路由，从知识库精准检索并生成带引用来源的答案。

---

## 1. 快速开始

**1. 克隆并配置**
```bash
git clone <repository-url>
cd Creating-Systematology-RAG
cp env.template .env
# 编辑 .env，配置 DEEPSEEK_API_KEY 和 Chroma Cloud 凭证
```

**2. 安装并启动**
```bash
make              # 安装依赖 + 运行测试
make run          # 启动 Web 应用
```

> 📖 GPU 配置、Windows 特殊处理 → [高级配置指南](docs/quick-start-advanced.md)

---

## 2. 核心特性

| 特性 | 说明 |
|------|------|
| **双模式 RAG** | 传统 RAG（固定策略）+ Agentic RAG（Agent 自主决策），可通过 UI 切换 |
| **多策略检索** | 向量语义、BM25 关键词、Grep 正则、混合检索，自动路由选择最优策略 |
| **三级降级** | Agent 失败 → ModularEngine → 纯 LLM → 友好错误，确保服务可用 |
| **可插拔设计** | Embedding、Retriever、Reranker、Observer 均支持替换 |
| **可观测性** | 集成 LlamaDebugHandler + RAGAS，行为透明可追踪 |

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

**四层架构**：用户层 → 服务层 → Agent Core → 基础设施层。核心是 LlamaIndex AgentWorkflow 驱动的研究型 Agent，LLM 自主决策研究节奏，代码层只设硬护栏。

> 📖 详细架构、工作流程、模块职责 → [架构设计文档](docs/architecture.md)

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

## 6. 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 三层架构、工作流程、模块交互、决策记录 |
| [高级配置](docs/quick-start-advanced.md) | GPU 配置、Windows 处理、Chroma Cloud、配置系统 |
| [Prompt 模板](prompts/README.md) | Prompt 模板集中管理与使用指南 |
| [Aha Moments](aha-moments/README.md) | 项目开发中的顿悟瞬间与深度思考 |
| [任务日志](agent-task-log/README.md) | AI Agent 执行任务的完整记录 |

---

## 7. 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**最后更新**: 2026-03-25  
**License**: MIT
