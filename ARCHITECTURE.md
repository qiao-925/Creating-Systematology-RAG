# ARCHITECTURE Flow Map


> 统一运行流程图版本。只保留一张图，作为系统主架构表达。

```text
用户输入问题 / 来源材料
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  1. 输入与增强                                                │
│  业务：把原始问题变成可分析任务                                 │
│  工程：Input Pipeline / 检索 / 解析 / 过滤                    │
│                                                              │
│  - HyDE + 多查询                                               │
│  - 来源分级 T1-T4                                              │
│  - 文档解析、质量过滤、饱和度检测                              │
│  输出：ParsedQuery                                             │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  2. Lead Agent 编排                                            │
│  业务：决定先做什么、后做什么、哪些分析需要调用                 │
│  工程：LlamaIndex AgentWorkflow + Guardrails                   │
│                                                              │
│  - 持有完整研究上下文                                           │
│  - 先调用 CLD                                                  │
│  - 判断是否需要 FCM / D2D                                      │
│  - 控制预算、超时、重试、终止                                   │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  3. 前置分析：CLD                                              │
│  业务：提取因果结构，形成共同根                                 │
│  工程：CLD Module（真多 Agent 子系统）                         │
│                                                              │
│  - 视角生成                                                    │
│  - Specialist × N 并行提取                                     │
│  - 节点归并 / 冲突检测                                         │
│  - 裁判 Agent / 自审                                           │
│  输出：SharedCLD                                               │
└──────────────────────────────────────────────────────────────┘
        │
        ├──────────────────────────────────────────────────────┐
        │                                                      │
        ▼                                                      ▼
┌──────────────────────────────┐                 ┌──────────────────────────────┐
│  4A. 衍生分析：FCM            │                 │  4B. 衍生分析：D2D            │
│  业务：半定量场景仿真         │                 │  业务：全定量杠杆点分析       │
│  工程：FCM Module             │                 │  工程：D2D Module             │
│                              │                 │                              │
│  - 单 Agent 批量评级          │                 │  - 扰动分析                   │
│  - 权重映射                   │                 │  - 不确定性计算               │
│  - Kosko 仿真                 │                 │  - 杠杆点排序                 │
│  输出：WeightedFCM            │                 │  输出：LeverageAnalysis       │
└──────────────────────────────┘                 └──────────────────────────────┘
        │                                                      │
        └──────────────────────────────┬───────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────┐
│  5. 结果融合与报告                                              │
│  业务：把多个分析结果整理成可读决策报告                         │
│  工程：Report Assembler / StructuredReport                    │
│                                                              │
│  - 汇总 CLD / FCM / D2D                                        │
│  - 语义融合，不做硬编码数据转换                                 │
│  - 引用来源、输出洞察、给出结论                                 │
│  - 输出内容包括：                                              │
│    1. 因果结构图（CLD 可视化）                                  │
│    2. 场景对比表（FCM 仿真结果，如调用）                       │
│    3. 杠杆点排序（D2D 结果，如调用）                           │
│    4. 综合洞察（Lead Agent 基于完整上下文生成）                │
│    5. 证据追溯（来源 Agent + 原文引用 + 来源层级）             │
│  输出：StructuredReport / StructuredFailureReport             │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
最终结果展示给用户
```




### 3.1 技术栈

#### 系统级技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.12 | 类型提示、match statement |
| 包管理 | uv | 快速依赖管理 |
| 前端 | Streamlit | 单页应用，原生组件优先 |
| Web框架 | FastAPI | API 路由 |
| 配置 | Pydantic + YAML + .env | 类型安全配置 |

#### RAG 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| RAG 框架 | LlamaIndex | Document/Node/Index/QueryEngine 抽象 |
| 向量存储 | Chroma Cloud | 云端托管，无需本地部署 |
| Embedding | HuggingFace Local / API | 可插拔 |
| LLM | DeepSeek API | 推理链输出，成本合理 |
| 重排序 | SentenceTransformer / BGE | 可插拔 |

#### CLDFlow 技术栈

| 类别 | 技术 | 用途 | 决策来源 |
|------|------|------|----------|
| 图操作 | NetworkX | CLD 构建、环检测、入度分析 | D21 |
| FCM 仿真 | FCMpy | Kosko 迭代、收敛判断 | D21 |
| 节点归并 | Sentence Transformer (MiniLM-L6-v2) | 余弦相似度归并 | D21 |
| LLM 结构化输出 | Instructor | JSON Schema 强制输出 | D21 |
| 生成模型 | DeepSeek-V3 | Specialist Agent | D17 |
| 评估模型 | GPT-4o-mini | Evaluator / Judge | D17 |
| 数据验证 | Pydantic strict mode | 层间边界校验 | D27 |
| 类型检查 | mypy | 强制 | D30 |





 
## 6. 目录结构 & Code Map

```
Creating-Systematology-RAG/
│
├── app.py                          # 🖥️ Streamlit Web应用入口（单页应用）
│
├── .streamlit/                     # ⚙️ Streamlit 配置文件
│   └── config.toml                # 主题配置（Light/Dark 模式）
│
├── frontend/                       # 🎨 前端层（Presentation Layer）
│   ├── main.py                    # 主入口（单页应用）
│   ├── components/               # UI组件（优先使用 Streamlit 原生组件）
│   │   ├── chat_display.py       # 聊天显示（含可观测性信息）
│   │   ├── config_panel/         # 配置面板模块（统一配置管理）
│   │   │   ├── models.py         # AppConfig 数据模型 + LLM 预设
│   │   │   ├── panel.py          # 主配置面板
│   │   │   ├── llm_presets.py    # LLM 预设面板（精确/平衡/创意）
│   │   │   └── rag_params.py     # RAG 参数面板（Top-K、相似度阈值等）
│   │   ├── file_viewer.py        # 文件查看（弹窗）
│   │   ├── observability_summary.py # 可观测性摘要展示
│   │   ├── sources_panel.py      # 引用来源面板
│   │   └── settings_dialog.py   # 设置弹窗（使用 st.dialog()）
│   ├── settings/                  # 设置模块
│   │   └── data_source.py        # 数据源管理
│   ├── utils/                     # 工具函数
│   │   ├── services.py           # 服务封装
│   │   ├── state.py              # 状态管理
│   │   └── sources.py            # 来源处理
│   └── tests/                     # 前端测试
│
├── backend/                        # 💻 后端代码（核心业务逻辑）
│   │
│   ├── business/                   # 业务层（Business Layer）
│   │   ├── rag_engine/            # RAG引擎
│   │   │   ├── agentic/          # Agentic RAG 模块
│   │   │   │   ├── agent/        # Agent 实现（规划 Agent、工具）
│   │   │   │   └── prompts/      # Agent Prompt 模板
│   │   │   └── core/             # 传统 RAG 模块
│   │   │       ├── engine.py     # ModularQueryEngine
│   │   │       ├── retrievers/   # 检索器实现
│   │   │       ├── reranking/   # 重排序器
│   │   │       └── processing/   # 查询处理
│   │   ├── rag_api/               # RAG Service
│   │   │   ├── models.py         # 数据模型（Pydantic）
│   │   │   └── rag_service.py   # 统一服务接口
│   │   ├── chat/                  # 对话管理
│   │   │   └── manager.py         # ChatManager
│   │   ├── perspectives/          # 视角模板系统（已实现）
│   │   │   ├── classifier.py
│   │   │   ├── generator.py
│   │   │   ├── registry.py
│   │   │   ├── evaluator.py
│   │   │   ├── templates/
│   │   │   └── generated/
│   │   └── cldflow/               # CLDFlow 业务模块（建议新增）
│   │       ├── service.py
│   │       ├── conductor.py
│   │       ├── state.py
│   │       ├── models.py
│   │       ├── input/
│   │       ├── cld/
│   │       ├── fcm/
│   │       ├── d2d/
│   │       └── reporting.py
│   │
│   └── infrastructure/             # 基础设施层（Infrastructure Layer）
│       ├── data_loader/            # 数据加载
│       │   ├── source_loader.py
│       │   ├── source/
│       │   │   ├── github.py
│       │   │   └── local_file.py
│       │   └── parser.py
│       ├── indexer/                # 索引构建
│       │   ├── index_manager.py
│       │   └── tools/
│       ├── embeddings/            # 向量化（可插拔）
│       │   ├── factory.py
│       │   ├── local.py
│       │   └── api.py
│       ├── llms/                  # 大语言模型
│       │   └── factory.py
│       ├── observers/             # 可观测性（可插拔）
│       │   ├── factory.py
│       │   └── llama_debug.py
│       ├── config/                # 配置管理
│       │   └── settings.py
│       ├── git/                   # Git 操作
│       │   └── manager.py
│       └── logger.py              # 结构化日志系统
│
├── docs/                           # 📚 文档中心
│   ├── ARCHITECTURE.md            # 架构设计文档（本文档）
│   ├── core-beliefs.md            # 15 命题（信念来源）
│   ├── CLDFlow-invariants.md      # 7 个不变量
│   ├── CLDFlow-defaults.md        # 实现默认值
│   ├── CLDFlow-architecture.md    # CLDFlow 业务架构
│   ├── CLDFlow-engineering.md     # CLDFlow 工程架构
│   ├── architecture.md            # 系统级三层架构（原有）
│   ├── cldflow/                   # CLDFlow 各层详细设计
│   │   ├── input-enhancement.md
│   │   ├── cld-layer.md
│   │   ├── fcm-layer.md
│   │   ├── d2d-layer.md
│   │   └── cross-cutting.md
│   ├── research/                  # 调研与探索
│   │   ├── insights/
│   │   └── harness-engineering/
│   └── engineering/               # 工程参考
│
├── data/                           # 📁 数据目录
│   ├── raw/                       # 原始数据
│   ├── vector_store/              # 向量存储
│   └── github_repos/              # GitHub仓库（本地克隆）
│
├── logs/                           # 📋 日志目录
│
├── .working-memory/                # 💡 工作记忆
│   ├── board.md                   # 看板
│   ├── aha-moments/               # 洞察沉淀
│   ├── ongoing/                   # 进行中任务
│   └── archive/                   # 已归档
│
├── skills/                         # 🔧 Agent Skills
│   └── cs-rag-architecture-guideline/
│
├── tests/                          # 🧪 测试
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── pyproject.toml                  # Python 项目配置
├── uv.lock                        # uv 锁定文件
├── .env                            # 环境变量（本地）
├── .env.remote                     # 环境变量（远程）
├── Dockerfile                      # Docker 配置
└── Makefile                        # 构建脚本
```


# 数据统计文档

> 本文档沉淀 `ARCHITECTURE.md` 中的数据规模、模块统计、测试覆盖和 CLDFlow 实现状态。

## 1. 总体规模

- 后端代码：143 个 Python 文件
- 前端代码：26 个 Python 文件
- 测试代码：99 个 Python 文件
- 总计：268 个文件

## 2. 按层级统计

| 层级 | 模块数 | 主要职责 |
|------|--------|----------|
| 前端层 | 26 | 用户交互与展示 |
| 业务层 | 43 | 核心业务逻辑 |
| 基础设施层 | 78 | 技术基础设施 |
| 测试层 | 99 | 测试覆盖 |

## 3. 核心功能模块

| 功能领域 | 模块数 | 说明 |
|----------|--------|------|
| RAG 引擎 | 35 | 传统 RAG + Agentic RAG |
| 数据加载 | 18 | GitHub + 本地文件导入 |
| 索引构建 | 20 | 向量索引管理 |
| 向量化 | 9 | Embedding 模型管理 |
| 检索策略 | 6 | vector / bm25 / hybrid / grep / multi |
| 重排序 | 4 | 结果重排序 |
| 可观测性 | 5 | 日志、调试、评估 |
| 前端 UI | 26 | Streamlit 界面组件 |
| 配置管理 | 5 | LLM 预设、RAG 参数、应用配置 |

## 4. 测试覆盖情况

- 单元测试：46 个文件
- 集成测试：15 个文件
- 性能测试：6 个文件
- E2E 测试：1 个文件
- 测试工具：12 个文件

## 5. CLDFlow 实现状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 视角模板系统 | ✅ 已实现 | `backend/perspectives/` 5 模板 + 22 测试 |
| ResearchAgent 样板 | ✅ 已实现 | `backend/business/research_kernel/agent.py` |
| Lead Agent 编排 | 📋 待实现 | 建议落位 `backend/business/cldflow/orchestration/` |
| CLD Module | 📋 待实现 | 建议落位 `backend/business/cldflow/modules/cld/` |
| FCM Module | 📋 待实现 | 建议落位 `backend/business/cldflow/modules/fcm/` |
| D2D Module | 📋 待实现 | 建议落位 `backend/business/cldflow/modules/d2d/` |

## 6. 与主文档的关系

- 主架构：`ARCHITECTURE.md`
- 实现计划：`docs/implementation-plan.md`
- 版本规划：`docs/version-plan.md`

