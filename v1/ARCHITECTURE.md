# Architecture

本文档描述 Systematology 系统的高层架构。如果你想理解代码库的整体设计和各模块职责，这是正确的起点。

> 参考了 [rust-analyzer architecture.md](https://github.com/rust-lang/rust-analyzer/blob/d7c99931d05e3723d878bea5dc26766791fa4e69/docs/dev/architecture.md) 的组织方式：Bird's Eye View → Code Map → Cross-Cutting Concerns，每个模块附带 Architecture Invariant。

---

## 目录

- [Bird's Eye View](#birds-eye-view)
- [技术选型](#技术选型)
- [目录结构 & Code Map](#目录结构--code-map)
  - [`backend/core/models.py` — 核心数据模型](#backendcoremodelspy--核心数据模型)
  - [`backend/core/orchestration/` — Lead Agent 编排](#backendcoreorchestration--lead-agent-编排)
  - [`backend/core/modules/cld/` — CLD 因果环路图提取](#backendcoremodulescld--cld-因果环路图提取)
  - [`backend/core/modules/fcm/` — FCM 模糊认知图仿真](#backendcoremodulesfcm--fcm-模糊认知图仿真)
  - [`backend/core/modules/d2d/` — D2D 动态杠杆点分析](#backendcoremodulesd2d--d2d-动态杠杆点分析)
  - [`backend/core/input/` — 输入与增强](#backendcoreinput--输入与增强)
  - [`backend/core/reporting/` — 结果融合与报告](#backendcorereporting--结果融合与报告)
  - [`backend/core/service.py` — 确定性脚手架](#backendcoreservicepy--确定性脚手架)
  - [`backend/core/api.py` — Systematology API 路由](#backendcoreapipy--systematology-api-路由)
  - [`backend/infrastructure/agent/` — Research Agent 内核](#backendinfrastructureagent--research-agent-内核)
  - [`backend/infrastructure/retrieval/` — 可插拔检索系统](#backendinfrastructureretrieval--可插拔检索系统)
  - [`backend/infrastructure/llms/` — LLM 工厂](#backendinfrastructurellms--llm-工厂)
  - [`backend/infrastructure/config/` — 配置管理](#backendinfrastructureconfig--配置管理)
  - [`backend/infrastructure/embeddings/` — 向量化系统](#backendinfrastructureembeddings--向量化系统)
  - [`backend/infrastructure/initialization/` — 初始化系统](#backendinfrastructureinitialization--初始化系统)
- [Workflow（流水线总览）](#workflow流水线总览)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
  - [分层与依赖方向](#分层与依赖方向)
  - [错误处理](#错误处理)
  - [可观测性](#可观测性)
  - [测试策略](#测试策略)
  - [配置管理](#配置管理)
  - [工程约束](#工程约束)
  - [数据流与中心契约](#数据流与中心契约)
- [数据统计](#数据统计)

---

## Bird's Eye View

Systematology 是一个围绕**动态假设（Dynamic Hypothesis）研究**的因果推理分析流水线。核心任务是将描述系统行为的文本转化为因果环路图（CLD），进而执行仿真与杠杆分析，输出结构化的决策报告。

**为什么是"动态假设"？** 在系统动力学中，将动态假设转化为 CLD 是建模的关键一步——从文本中提取关键变量和因果关系，构建系统的反馈结构。这正是本项目的起点：一切分析都围绕动态假设的提取、形式化、仿真与验证展开。

核心机制：系统接受一个动态假设（研究问题 + 可选来源材料），经查询增强后，由 Lead Agent（ReAct 模式）自主编排三个分析阶段——CLD（因果环路图提取）、FCM（模糊认知图仿真）、D2D（动态杠杆点分析）——最终将结果融合为报告。每个阶段是一个独立模块，通过 `SharedCLD` 这一中心数据契约串联。

输入：动态假设（研究问题） + LlamaIndex `Document` 列表。
输出：`StructuredReport`（含因果结构图、场景对比、杠杆点排序、综合洞察、证据追溯）或 `StructuredFailureReport`（含失败阶段、原因、详情）。

底层引擎保证：分析过程受预算控制（轮次 + token），模块之间通过 Pydantic 模型严格校验边界，pipeline 失败时降级而非崩溃。

## 技术选型

核心选型定义系统身份，支撑组件可按需替换。各技术的使用细节见 Code Map 对应模块。

**核心选型**

| 角色 | 技术 | 选型理由 |
|------|------|----------|
| Agent 框架 | LlamaIndex (ReActAgent + AgentWorkflow) | 多 Agent 编排，工具注册，内置 ReAct 循环 |
| LLM 网关 | LiteLLM | 统一多模型接口，屏蔽提供商差异，支持 DeepSeek / MiMO / Kimi |
| Web 框架 | FastAPI | REST API + SSE 流式响应，Pydantic 原生集成 |
| 数据契约 | Pydantic v2 (strict mode) | 层间边界校验，类型安全，`extra="forbid"` |
| 因果图操作 | NetworkX | CLD 构建、环检测、入度分析，Python 图算法事实标准 |

**支撑组件**

| 职责 | 技术 | 状态 |
|------|------|------|
| 结构化输出 | Instructor | 已启用，JSON Schema 强制输出 |
| 向量存储 | Chroma Cloud | 已启用，云端托管 |
| FCM 数值计算 | NumPy | 已启用，Kosko 矩阵迭代 |
| 节点归并 | sentence-transformers (MiniLM-L6-v2) | 已启用，余弦相似度归并 |
| 日志 | structlog | 已启用，结构化追踪 |
| 前端 | Next.js / React | 已启用 |
| Embedding | HuggingFace (local / API) | 待确定方案 |
| 重排序 | SentenceTransformer / BGE | 待确定方案 |
| 评估 | RAGAS | 可选 |

---

## 目录结构 & Code Map

本节按目录逐个说明各模块的职责、关键数据结构和设计约束。注意 **Architecture Invariant** 小节——它们描述的是刻意不存在的东西，和刻意做出的设计选择。

标记为 **API Boundary** 的模块是对外暴露接口的位置，边界内外的规则不同。

```
Systematology/
│
├── backend/                        # 后端核心
│   ├── fastapi/                   #   FastAPI API 层（前端唯一入口）
│   │   ├── main.py                #     应用入口（uvicorn backend.fastapi.main:app）
│   │   ├── deps.py                #     依赖注入（AppState 单例）
│   │   ├── schemas.py             #     请求/响应模型
│   │   └── routes/                #     路由（config, health）
│   │
│   ├── core/                      #   核心层（业务逻辑，按架构图组织）
│   │   ├── input/                 #     ① 输入与增强
│   │   ├── orchestration/         #     ② Lead Agent 编排
│   │   ├── modules/               #     ③ 分析模块
│   │   │   ├── cld/              #       CLD 因果环路图提取
│   │   │   ├── fcm/              #       FCM 模糊认知图仿真
│   │   │   └── d2d/              #       D2D 动态杠杆点分析
│   │   ├── reporting/             #     ④ 结果融合与报告
│   │   ├── models.py              #     核心数据模型（全系统共享）
│   │   ├── service.py             #     确定性脚手架（MVP 测试用）
│   │   └── api.py                 #     Systematology API 路由
│   │
│   ├── infrastructure/             #   基础设施层
│   │   ├── agent/                 #     通用 Agent 原语（Research Agent 内核）
│   │   ├── retrieval/             #     通用检索（多策略 + 结果融合）
│   │   ├── reranking/             #     通用重排序
│   │   ├── formatting/            #     输出格式化（Markdown 校验/修复/引用）
│   │   ├── config/                #     配置管理（YAML + 环境变量）
│   │   ├── llms/                  #     LLM 工厂（LiteLLM 统一接口）
│   │   ├── embeddings/            #     向量化（本地 + HF Inference API）
│   │   ├── indexer/               #     索引构建（Chroma 向量数据库）
│   │   ├── data_loader/           #     数据加载（GitHub + 本地文件）
│   │   ├── observers/             #     可观测性（structlog + LlamaIndex 观测）
│   │   └── initialization/        #     初始化系统（拓扑排序 + 依赖管理）
│   │
│   └── prompts/                   #   Prompt 模板
│
├── tests/                          # 测试
├── scripts/                        # 运维脚本
├── web/                            # Next.js / React 前端
├── docs/                           # 文档
│   ├── constraint-system.md        #   约束体系（rules/hooks/yaml 三层防线）
│   ├── decision-log.md             #   决策日志（只增不改）
│   └── design/                     #   设计文档（Figma 工作流 + token 矩阵）
│       ├── design-anchoring-summary.md  # 设计锚定摘要（核心概念/信息架构/组件映射）
│       └── report page/                 # Report Page 定稿（设计规范/tokens/组件映射）
├── data/                           # 数据目录
│
├── application.yml                 # 应用配置
├── pyproject.toml                  # Python 项目配置
├── Makefile                        # 构建脚本
├── ARCHITECTURE.md                 # 架构设计文档（本文档）
└── README.md                       # 项目说明
```

---

### `backend/core/models.py` — 核心数据模型

全系统共享的数据契约。所有模型使用 Pydantic v2 + `ConfigDict(extra="forbid")`，在每个边界严格校验，不允许额外字段。

**领域类型（因果分析域）：**
- `CLDNode` — 因果图节点：id, label, description
- `CausalLink` — 因果边：source, target, relation（6 种关系：influences, causes, enables, inhibits, supports, requires）
- `SharedCLD` — **中心数据契约**：节点列表 + 边列表 + 元数据。CLD 模块产出，FCM 和 D2D 消费
- `WeightedFCM` — NxN 权重矩阵 + 置信度矩阵 + 基线状态 + 干预状态
- `NodeImpact` / `LeverageAnalysis` — D2D 输出：按影响力排序的杠杆点 + 不确定性区间

**流水线结果类型：**
- `StructuredReport` — 最终输出：CLD 可视化、场景对比、杠杆点排序、综合洞察、证据追溯
- `StructuredFailureReport` — 失败输出：run_id, stage, reason, details
- `RunContext` — 可变编排状态：预算轮次/token、工具调用记录、失败记录

**Architecture Invariant:** `models.py` 只依赖 `pydantic` 和 `llama_index.core.Document`，不依赖任何基础设施模块。它是核心层中最纯净的文件，其他所有模块都可以安全地导入它而不会引入传递依赖。

---

### `backend/core/orchestration/` — Lead Agent 编排

Lead Agent 决定先做什么、后做什么、哪些分析需要调用。它使用 LlamaIndex 的 `AgentWorkflow` + `ReActAgent`，**不实现任何分析逻辑**——所有分析委托给模块层的 FunctionTool。

**关键文件：**
- `lead_agent.py` — `LeadAgent` 类：接受 LLM + 配置，`run()` 方法创建工具、实例化 ReAct Agent、运行 workflow
- `tools.py` — 5 个 FunctionTool：`run_cld_analysis`, `run_fcm_analysis`, `run_d2d_analysis`, `generate_report`, `generate_failure_report`
- `guardrails.py` — 5 个守卫函数（详见下文）
- `prompts.py` — 系统提示词，指导 ReAct Agent 的调用顺序

**Architecture Invariant:** Lead Agent 是自主的。ReAct Agent 根据系统提示词自行决定工具调用顺序，guardrails 只强制前置条件（CLD 必须先于 FCM/D2D）。这意味着调整 pipeline 顺序只需修改提示词，不需要改代码。

**Architecture Invariant:** 工具文件使用惰性导入（在函数体内 `from backend.core.modules.cld.module import CLDModule`）。Lead Agent 本身不直接导入模块内部实现，编排层与模块层在 import 时解耦。

**Architecture Invariant:** `RunContext` 是可变的编排状态，随工具调用累积。它不是领域模型——它是运行时簿记。领域模型（`SharedCLD`, `WeightedFCM` 等）是不可变的数据传递载体。

**守卫函数（Guardrails）：**
- `check_pipeline_rail` — 确保前置阶段已完成
- `check_budget` — 强制 token 和轮次预算
- `check_schema` — 校验原始数据是否符合 Pydantic 模型
- `check_isolation` — 确保 Specialist 输出不跨引用彼此的 ID 命名空间
- `check_self_review` — 校验 SharedCLD 结构完整性（>=2 节点、>=1 边、无孤立节点）

---

### `backend/core/modules/cld/` — CLD 因果环路图提取

这是 pipeline 中最复杂的模块。它是一个**真正的多 Agent 子系统**：视角生成 → Specialist 并行提取 → 节点归并 → 冲突检测 → 裁判门控。

**Pipeline（`CLDModule.run()`）：**
1. `PerspectiveGenerator` 将问题分类到 DDC（杜威十进制分类），从 YAML 模板库选择视角
2. N 个 Specialist 通过 `asyncio.gather` 并行提取因果关系，每个 Specialist 是独立的 LLM 调用
3. 节点归并：使用 sentence-transformers（MiniLM-L6-v2）计算余弦相似度（阈值 0.8），不可用时降级到字符三元组 Jaccard
4. 冲突检测：按 (source, target) 分组，不同视角给出不同关系时标记冲突（low/medium/high）
5. 冲突解决：多数投票
6. 裁判门控：结构检查 + Judge LLM 审查（G6 降级策略：有 OpenAI key 用 GPT-4o-mini，否则用 DeepSeek）

**关键数据结构：**
- `CLDAnalysisInput` — 研究问题 + 文档 + 视角提示 + 最大视角数
- `CLDAnalysisOutput` — SharedCLD + 使用的视角 + 置信度 + 诊断信息
- `Perspective` — DDC 类别 + 模板 + 约束条件

**Architecture Invariant:** CLD 模块是自包含的。它只从 `backend.core.models` 和 `backend.infrastructure.*` 导入。编排层只通过 `CLDModule.run()` 访问它。这意味着可以独立测试 CLD 模块，不需要启动整个 pipeline。

**Architecture Invariant:** Specialist 使用 instructor 保证结构化输出，降级到手动 JSON 解析 + Pydantic 校验。这是为了在 instructor 不可用时保持功能完整。

---

### `backend/core/modules/fcm/` — FCM 模糊认知图仿真

将定性 CLD 关系转换为数值权重，运行 Kosko FCM 仿真。

**关键文件：**
- `mapper.py` — 关系→权重映射表（causes=0.7, enables/influences/supports=0.5, requires=0.7, inhibits=-0.7）
- `simulator.py` — Kosko 迭代：`state(t+1) = sigmoid(W^T @ state(t))`，收敛阈值 1e-6，最大 100 次迭代
- `rater.py` — LLM 边权重评级（7 级量表），失败时降级到 mapper 默认值

**Architecture Invariant:** FCM 依赖 `SharedCLD`，不导入 CLD 内部实现。它只使用共享模型，不知道 CLD 是怎么生成的。这保证了模块间的松耦合。

**Architecture Invariant:** FCM 仿真直接使用 NumPy 而非 fcmpy 库，原因是 tqdm 版本冲突。这是一个务实的工程决策，不是架构选择。

---

### `backend/core/modules/d2d/` — D2D 动态杠杆点分析

通过单节点扰动分析识别系统杠杆点。

**关键文件：**
- `sensitivity.py` — 对每个节点施加扰动（默认 10%），计算一步传播效应 `effect = W^T @ perturbed_state`
- `ranking.py` — 将敏感度结果转为 `LeverageAnalysis`，按影响力排序，置信度分级（high>0.7, medium>0.3, low）
- `uncertainty.py` — 基于 FCM 置信度矩阵估算上下界（高置信 ±10%，中 ±30%，低 ±50%）

**Architecture Invariant:** D2D 从 `fcm.mapper` 导入 `map_relation_to_weight`。这是**核心层内唯一的跨模块依赖**。D2D 和 FCM 共享权重映射函数，因为它们需要一致的关系→权重语义。这是一个有意的设计权衡，不是意外耦合。

---

### `backend/core/input/` — 输入与增强

将原始研究问题转为增强后的 `ParsedQuery`。

**Pipeline（`pipeline.py`）：**
1. HyDE（假设性文档嵌入）+ 多查询生成，并行执行
2. 构建查询列表：原始 + HyDE 答案 + 替代表述
3. 迭代检索 + 饱和度检测（最多 3 轮）

**关键组件：**
- `enhance.py` — `hyde_expand()` 生成假设性学术答案；`multi_query_generate()` 生成 N 个替代表述
- `retrieve.py` — `source_tiered_retrieve()` 按来源分级（academic=1, government=2, report=3, news=4, blog=5）排序
- `stop_rules.py` — `check_saturation()` 使用字符三元组 Jaccard 相似度检测边际收益递减（阈值 0.9）

**Architecture Invariant:** 输入管道是无状态的。每次调用都是独立的，不持有跨请求的状态。这使得它可以安全地并发使用。

---

### `backend/core/reporting/` — 结果融合与报告

将多个分析结果组装为 `StructuredReport`。

**关键函数：** `synthesize_report()` 接受 RunContext、SharedCLD、可选的 WeightedFCM、可选的 LeverageAnalysis、可选的综合洞察文本。

**Architecture Invariant:** 报告层使用 Lead Agent 做语义融合，不做硬编码数据转换。`_generate_default_insights()` 是降级方案——当 Lead Agent 未提供洞察时生成基础文本。这意味着报告质量取决于 Lead Agent 的能力，报告层本身是"薄"的。

---

### `backend/core/service.py` — 确定性脚手架

`SystematologyAppService` 是 MVP 阶段的确定性占位实现：`parse_query()`, `build_shared_cld()`, `build_weighted_fcm()`, `build_leverage_analysis()`, `synthesize_report()`。

**Architecture Invariant:** 这个服务是测试脚手架，不是生产路径。真正的分析由编排层（Lead Agent + 模块）完成。它保留是为了在没有 LLM 的环境下做集成测试。

---

### `backend/core/api.py` — Systematology API 路由

FastAPI 路由，prefix `/api/systematology`：
- `POST /analyze` — 接受 `AnalyzeRequest`，创建 LeadAgent，运行 pipeline，返回 `AnalyzeResponse`
- `GET /health` — 健康检查

**Architecture Invariant:** API 层是**唯一的 HTTP 边界**。它知道 FastAPI 和 JSON 序列化，核心层不知道。如果你想从核心层暴露数据结构 X，不要让它可序列化——在 API 层创建对应的序列化副本并手动转换。这与 rust-analyzer 的 `ide` vs `rust-analyzer` crate 的边界设计一致。

---

### `backend/infrastructure/agent/` — Research Agent 内核

一个**完全独立于 Systematology 的 Agent 系统**，用于证据驱动研究。

**关键组件：**
- `ResearchAgent` — 包装 LlamaIndex AgentWorkflow + ReActAgent，注册 5 个工具：vector_search, hybrid_search, record_evidence, synthesize, reflect, evaluate_judgment
- `ResearchState` — 可变状态：evidence_ledger, current_judgment, confidence, budget tracking
- `ResearchOutput` — 不可变输出：judgment, evidence, confidence, tensions, next_questions

**Architecture Invariant:** Research Agent 和 Systematology Lead Agent 是**完全独立的系统**。它们共享基础设施（LLM 工厂、配置、日志），但有独立的状态、工具和编排。Research Agent 不被 Systematology pipeline 调用。这是刻意的——它们解决不同的问题，强制分离避免了不必要的耦合。

---

### `backend/infrastructure/retrieval/` — 可插拔检索系统

多策略检索 + 结果融合。

**策略：** `vector`, `bm25`, `hybrid`（vector+BM25 via QueryFusionRetriever）, `multi`（自定义 MultiStrategyRetriever）, `grep`

**融合：** `ResultMerger` 支持 3 种策略：倒数排名融合（RRF, k=60）、加权分数融合、简单拼接。含基于内容的去重。

**Architecture Invariant:** 检索系统通过 Adapter 模式与 LlamaIndex 解耦。`LlamaIndexRetrieverAdapter` 将 LlamaIndex retriever 适配到内部 `BaseRetriever` 接口，`MultiStrategyRetrieverAdapter` 反向适配。这使得可以独立替换检索策略而不影响上层。

---

### `backend/infrastructure/llms/` — LLM 工厂

通过 LiteLLM 统一 LLM 接口。

**关键行为：**
- `create_llm(model_id, temperature, max_tokens, enable_retry)` — 主入口
- 惰性导入 LiteLLM（导入耗时 6+ 秒）
- 指数退避重试（默认 3 次）
- `build_chat_messages()` 按模型类型适配消息格式：reasoning 模型收到单条 user message，标准模型收到 system+user 拆分

**Architecture Invariant:** LLM 工厂不持有全局 LLM 实例。每次 `create_llm()` 返回新实例。全局缓存在 embedding 和 reranker 层，不在 LLM 层。这是因为不同调用点可能需要不同的 temperature 或 max_tokens 配置。

---

### `backend/infrastructure/config/` — 配置管理

集中式配置：YAML + 环境变量。

**关键设计：**
- `Config` 类加载 `application.yml`，通过 Pydantic `ConfigModel` 校验
- 敏感信息（API keys）来自 `.env`，静态配置来自 YAML
- `__getattr__` 提供大写属性访问（`config.DEEPSEEK_API_KEY`），通过属性映射表实现向后兼容
- 支持多模型配置（reasoning vs standard）

**Architecture Invariant:** 配置是**模块级单例**（`config = Config()`）。所有模块导入同一个实例。配置在应用启动时加载一次，运行时不变。如果你想在运行时修改配置，需要重启应用。

---

### `backend/infrastructure/embeddings/` — 向量化系统

**实现：** `LocalEmbedding`（本地 sentence-transformers）和 `HFInferenceEmbedding`（HF Inference API，批量处理，每批 100 条）。

**Architecture Invariant:** embedding 实例是**全局单例缓存**（`_global_embedding_instance`）。`create_embedding()` 首次调用时创建，后续调用返回缓存。这是因为加载模型代价高昂，且 embedding 维度在运行时固定。

---

### `backend/infrastructure/initialization/` — 初始化系统

结构化、基于类别的模块初始化框架。

**类别（按顺序执行）：**
1. `FOUNDATION` — encoding, config, logger
2. `CORE` — embedding, chroma, index_manager, llm_factory, session_state, rag_service, chat_manager
3. `OPTIONAL` — query_engine, llama_debug, ragas

**关键行为：** 大多数 CORE 模块标记为 `is_required=False`（惰性加载）。`InitializationManager` 执行拓扑排序，跟踪状态（PENDING/SUCCESS/FAILED/SKIPPED），生成带计时的格式化报告。

**Architecture Invariant:** 初始化系统使用依赖图而非固定顺序。模块声明自己的依赖，系统自动排序。添加新模块只需注册依赖关系，不需要修改初始化顺序。

---

## Workflow（流水线总览）

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

---

## Cross-Cutting Concerns

本节讨论跨越多个模块的横切关注点。

### 分层与依赖方向

系统采用两层架构：

```
┌─────────────────────────────────────────────┐
│  core/（业务逻辑）                            │
│  orchestration / modules / input / reporting │
│  models.py（纯领域模型，零基础设施依赖）       │
├─────────────────────────────────────────────┤
│  infrastructure/（基础设施）                   │
│  llms / retrieval / config / embeddings /    │
│  indexer / observers / agent primitives       │
├─────────────────────────────────────────────┤
│  fastapi/（API 边界）                         │
│  HTTP 路由 / 序列化 / 依赖注入                │
└─────────────────────────────────────────────┘
```

**依赖规则：**
- core 可以导入 infrastructure（通过工厂函数获取 LLM、embedding 等）
- infrastructure **不**导入 core（基础设施不知道业务逻辑）
- fastapi 可以导入 core 和 infrastructure
- `models.py` 不依赖任何基础设施模块——它是依赖图的叶子节点

**已知偏差：** core 层对 infrastructure 的依赖限于日志、配置访问和 LLM 工厂。`models.py` 本身只有 `pydantic` 和 `llama_index.core.Document` 两个外部依赖。

### 错误处理

系统在不同层采用不同的错误策略：

**核心层：** guardrails 抛出 `RuntimeError`；工具调用失败时累积 `FailureRecord` 到 `RunContext`；pipeline 失败返回 `StructuredFailureReport` 而非崩溃。核心层的哲学是**降级而非崩溃**——有确定性降级路径（placeholder CLD、mapper 默认权重、judge 默认通过）。

**基础设施层：** 自定义异常层次（`DataImportError` → `NetworkError` 可重试 / `AuthenticationError` 不可重试 / `NotFoundError` / `ParseError`）。关键词分类错误类型。指数退避重试。

**API 层：** 捕获所有异常为 HTTP 500。API 层不暴露内部错误细节。

### 可观测性

两套系统并存：

**Legacy Observer 模式（`BaseObserver` ABC）：** 生命周期钩子（`on_query_start`, `on_query_end`, `on_retrieval`, `on_rerank`, `on_generation`）。`ObserverManager` 管理多个 observer，错误隔离。包含 `LlamaDebugObserver` 和 `RAGASEvaluator`。

**现代 Instrumentation（LlamaIndex API）：** `ObservabilityEventHandler` 路由 LLM/retrieval/synthesis/query 事件到结构化日志。`ObservabilitySpanHandler` 跟踪 span 计时。通过 `enable_instrumentation()` 一次性注册（幂等）。

**日志：** structlog，双输出——开发环境控制台，生产环境 JSON。文件日志：`TimedRotatingFileHandler`，每日轮转，30 天保留。激进抑制噪声日志器（urllib3, httpx, chromadb telemetry 等）。

### 测试策略

**三个测试边界：**

1. **API 边界（最外层）：** 通过 HTTP 测试 FastAPI 端点。数量少，因为类型系统已经覆盖了协议正确性。
2. **编排边界（中间层）：** 测试 Lead Agent 的工具调用和 guardrails。guardrails 是纯函数，可独立测试。
3. **模块边界（最内层）：** 测试 CLD/FCM/D2D 的输入→输出转换。使用确定性输入和快照比较。

**Architecture Invariant:** 测试不依赖外部资源。LLM 调用在测试中被 mock 或使用确定性 placeholder。这保证了测试的可重复性。

### 工程约束

三层防线确保文件放置和文档规范：rules 软引导 → hooks 硬拦截 → yaml 单一真相源。详见 [docs/constraint-system.md](docs/constraint-system.md)。

### 配置管理

**分离原则：** `.env` 存密钥，`application.yml` 存一切其他配置。Pydantic 在加载时校验。

**惰性加载：** 所有重型模块（embedding、LLM、index、Chroma）使用延迟初始化。初始化系统标记大多数 CORE 模块为 `is_required=False`。

**Architecture Invariant:** 配置在启动时加载一次，运行时不变。`Config` 是模块级单例。如果你想在运行时修改配置，需要重启应用。这是刻意的简化——避免了配置变更传播的复杂性。

### 数据流与中心契约

`SharedCLD` 是系统的**中心数据契约**：

```
CLD Module ──产出──> SharedCLD ──消费──> FCM Module
                       │
                       └────消费──> D2D Module
```

FCM 和 D2D 只依赖 `SharedCLD`（来自 `models.py`），不依赖 CLD 模块内部实现。唯一例外：D2D 从 `fcm.mapper` 导入 `map_relation_to_weight`，因为两者需要一致的关系→权重语义。

**Architecture Invariant:** 模块间通过 Pydantic 模型传递数据，不通过共享可变状态。每个模块的输出是不可变的数据结构，下一个模块的输入。这使得模块可以独立测试、独立替换。

---

## 数据统计

> 截至 2026-05-16，含 Systematology MVP 全部代码，Streamlit 前端已删除。

| 维度 | 数量 |
|------|------|
| Git 跟踪文件 | 1117 |
| 后端 Python 文件 | 203（~27,282 行） |
| Next.js/React 前端文件 | 40（~2,941 行） |
| 测试 Python 文件 | 118（~22,675 行） |
| 文档 Markdown 文件 | 105 |

| 功能领域 | 说明 |
|----------|------|
| Systematology | CLD → FCM → D2D 因果分析流水线（34 个 Python 文件） |
| Research Kernel | 证据驱动研究 Agent（独立于 Systematology） |
| RAG 引擎 | 传统 RAG + Agentic RAG |
| 数据加载 | GitHub 同步 + 本地文件导入 |
| 向量化 | HuggingFace Embedding（local + API） |
| 索引构建 | Chroma 向量索引管理 |
| 可观测性 | structlog + LlamaIndex Observers + RAGAS 评估 |

| 测试类型 | 文件数 |
|----------|--------|
| 单元测试 | 58 |
| 集成测试 | 15 |
| 性能测试 | 7 |
| E2E 测试 | 4 |
| 回归测试 | 2 |
| Systematology 专用 | 3 |
| 测试夹具 | 9 |
| 测试工具 | 12 |
