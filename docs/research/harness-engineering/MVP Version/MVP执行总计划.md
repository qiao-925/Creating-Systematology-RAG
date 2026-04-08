# MVP 执行总计划

> **定义**：以受控自主判断为核心、以高密度知识场为证据支撑、以启发用户为目标的研究型 Agent MVP。
> **命题**：系统能在证据约束下把 `问题 → 取证 → 综合 → 判断 → 启发` 这条链路跑通。
> **架构**：四层——用户层 → 服务层 → Research Agent Core（LlamaIndex AgentWorkflow）→ 基础设施层。
> **路径**：Phase 0（决策冻结）✅ → Phase 1（研究内核闭环）→ Phase 2（服务层接入）→ Phase 3（前端适配 + MVP 验证）。

唯一主文档。所有推进以本文为准，子文档仅作备查。

---

## 冻结集

以下判断不再讨论，直接作为后续所有决策的前提。

### 产品命题

1. **这是研究型 Agent，不是增强版 RAG。** 核心是判断形成，不是材料拼接。
2. **目标是启发，不是总结。** 用户缺的不是更多材料，而是更强判断、关键张力和更值得追问的问题。
3. **第一版从单 Agent 起步。** 不预支多 Agent 复杂度。
4. **知识库和工具是支撑，不是系统本体。** 研究内核才是系统本体。
5. **治理和边界是系统成立的前提，不是附属件。**

### 架构模式

6. **Agent 为主体，RAG 为工具。** Agent 主动管理信息获取，RAG 是它的取证工具之一。
7. **快速路径 + 深度研究分级处理。** 简单查询走快速路径（≈ 传统 RAG），研究型问题走深度研究路径。
8. **LLM 自主编排 + 最小硬护栏。** LLM 自主决策研究节奏，代码层只设不可绕过的护栏（预算上限、必须有证据才能出判断、结构化输出）。原 FSM 的状态节点降级为 prompt 中的阶段指引，不硬编码到代码流程中。

### 技术选型与迁移（原 R1/R2，已冻结）

9. **技术选型：LlamaIndex AgentWorkflow。** 零新依赖，Agent-centric 编排，与现有 LlamaIndex 生态原生兼容。`llama_index.core.workflow` 已随 `llama-index>=0.14.3` 安装。
10. **迁移策略：并行新建（策略 B）。** 新建 `backend/business/research_kernel/` 模块，独立于现有 agentic 路径。复用现有检索能力（vector/hybrid/multi + rerank），不改动现有代码。
11. **工具集**：`vector_search`、`hybrid_search`、`record_evidence`、`synthesize`、`reflect`——对齐 README 架构图。LLM 自主决定调用顺序和频次。
12. **输出结构**：`ResearchOutput { judgment, evidence, confidence, tensions, next_questions }`。
13. **硬护栏清单**：① timeout 超时 ② max_iterations 迭代上限 ③ prompt 约束（必须有证据才出判断）④ 输出 schema 强制（ResearchOutput）。

### MVP 验证命题

第一版只需证明一件事：**系统能在证据约束下把 `问题 → 取证 → 综合 → 判断 → 启发` 这条链路跑通。**

成功信号：输出有明确判断（非摘要）、判断可回溯到证据、能揭示张力或新追问方向、在预算内能收束。

---

## 目标架构（对齐 README 架构图）

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

---

## 模块布局

```
backend/business/
  ├── rag_engine/              # 现有，不动（快速路径继续服务）
  │   ├── agentic/             # 现有 AgenticQueryEngine，保持不变
  │   └── core/                # 现有 ModularQueryEngine，保持不变
  ├── rag_api/                 # 现有 RAGService，新增 research 路由
  ├── chat/                    # 现有 ChatManager，保持不变
  └── research_kernel/         # ← 新建：Research Agent Core
      ├── __init__.py
      ├── state.py             # ResearchState 定义 + ResearchOutput 模型
      ├── agent.py             # AgentWorkflow 构建（LLM + 工具 + 护栏）
      ├── tools/               # 工具集
      │   ├── __init__.py
      │   ├── search.py        # vector_search, hybrid_search（封装现有检索器）
      │   ├── evidence.py      # record_evidence（写入证据账本）
      │   ├── synthesis.py     # synthesize（综合判断形成）
      │   └── reflection.py    # reflect（评估充足性、识别缺口）
      └── prompts/             # 研究内核专用 prompt
          └── system.py        # system prompt（含阶段指引）
```

---

## 执行路径

严格按顺序推进，当前层没有稳定之前不进入下一层。

### Phase 0：决策冻结 ✅

R1/R2 调研已完成，所有关键决策已进入冻结集（#9-#13）。可直接进入 Phase 1。

### Phase 1：研究内核最小闭环（当前阶段）

**目标**：跑通 `问题 → 取证 → 综合 → 判断 → 启发` 端到端闭环。

#### 1.1 State 与 Output 定义 ✅
- [x] `state.py`：定义 `ResearchState`（original_question, focused_question, evidence_ledger, current_judgment, confidence, budget_turns, current_turn）
- [x] `state.py`：定义 `ResearchOutput` Pydantic 模型（judgment, evidence, confidence, tensions, next_questions）

**完成标准**：数据结构通过类型检查，有单元测试。（24 tests passed）

#### 1.2 工具集实现 ✅
- [x] `tools/search.py`：`vector_search` — 封装现有 `create_retriever(strategy="vector")`，返回格式化证据片段
- [x] `tools/search.py`：`hybrid_search` — 封装现有 `create_retriever(strategy="hybrid")`，返回格式化证据片段
- [x] `tools/evidence.py`：`record_evidence` — 将检索结果写入 State 的证据账本，附带来源标注
- [x] `tools/synthesis.py`：`synthesize` — 基于当前证据账本，调用 LLM 形成阶段性判断，写入 State
- [x] `tools/reflection.py`：`reflect` — 评估证据充足性、识别知识缺口、判断是否继续取证

**完成标准**：每个工具有独立单元测试，能通过 mock 验证输入输出。（22 tests passed）

#### 1.3 Agent Loop 构建 ✅
- [x] `agent.py`：基于 LlamaIndex AgentWorkflow 创建 `ResearchAgent`
- [x] 注册 5 个工具到 AgentWorkflow
- [x] 配置 LLM（通过现有 `infrastructure/llms/factory.py`）
- [x] `prompts/system.py`：设计 system prompt，包含阶段指引（定焦 → 计划 → 取证 → 综合 → 收束），但不硬编码为代码流程

**完成标准**：Agent 能接收问题、自主调用工具、产出 ResearchOutput。（4 tests passed）

#### 1.4 硬护栏集成 ✅
- [x] timeout：AgentWorkflow 的超时配置
- [x] max_iterations：最大工具调用轮次限制
- [x] prompt 约束：强制 "无证据不出判断" 规则
- [x] 输出 schema：强制 ResearchOutput 结构化输出

**完成标准**：超过预算能自动收束并给出部分结果；无证据时拒绝出判断。（8 tests passed）

#### 1.5 端到端验证
- [ ] 集成测试：一个研究问题（如“钱学森系统学的核心方法论是什么？”）走完全链路
- [ ] 验证 ResearchOutput 结构完整性
- [ ] 验证 evidence 字段可回溯到知识库原文
- [ ] 验证 tensions 和 next_questions 非空

**完成标准**：Phase 1 验证通过 = 可进入 Phase 2。

**状态**：待端到端验证（需要真实 LLM API + 索引）

### Phase 2：服务层接入

**目标**：研究内核通过服务层对外暴露，支持快速/深度分级路由。

#### 2.1 Agent Service 路由 ✅
- [x] `rag_api/rag_service.py`：新增 `mode="research"` 路由，调用 `ResearchAgent`
- [x] 三模式共存：standard（ModularQueryEngine）/ agentic（AgenticQueryEngine）/ research（ResearchAgent）

#### 2.2 Session 与状态管理 ✅
- [x] 研究状态生命周期管理（MVP：每次调用新建 state）
- [ ] Context 序列化（延后：MVP 不需要跨 session 持久化）

**完成标准**：`RAGService.query(question, mode="research")` 能正确调用研究内核并返回 ResearchOutput。✅

### Phase 3：前端适配 + MVP 验证

**目标**：用户能从 UI 触发深度研究，看到结构化研究结果；验证 MVP 成功信号。

#### 3.1 前端适配 ✅
- [x] 研究模式切换 UI（设置面板 toggle）
- [x] ResearchOutput 展示组件（判断、证据列表、置信度、张力、下一步问题）
- [ ] 研究进度展示（Agent 正在做什么）— 延后

#### 3.2 可观测性 ✅
- [x] structlog 日志覆盖 research_kernel 所有工具调用
- [ ] Observers 接入（LlamaIndex workflow 事件追踪）— 延后

#### 3.3 MVP 成功信号验证
- [ ] 输出有明确判断（非摘要）
- [ ] 判断可回溯到证据
- [ ] 能揭示张力或新追问方向
- [ ] 在预算内能收束

**状态**：待端到端验证（需要真实 LLM + 索引）
**完成标准**：4 条成功信号全部通过 = MVP 完成。

---

## 文档地图

| 文档 | 用途 | 状态 |
|------|------|------|
| **本文（MVP执行总计划.md）** | 唯一主计划，冻结集 + 推进顺序 + 任务拆分 | 🔴 活跃 |
| [研究型Agent-MVP定义与执行计划.md](./研究型Agent-MVP定义与执行计划.md) | 产品定义 | ✅ 已冻结，备查 |
| [orient-report.md](../orient-report.md) | 现有系统能力摸底 | ✅ 已完成，备查 |
| [通用Agent架构.md](./通用Agent架构.md) | 通用 Agent 分层参考 | 📎 参考 |
| [R1-研究型Agent实现范式调研.md](./R1-研究型Agent实现范式调研.md) | R1 调研，方向已冻结（#8 #9） | ✅ 备查 |
| [R2-现有系统迁移路径调研.md](./R2-现有系统迁移路径调研.md) | R2 调研，策略已冻结（#10） | ✅ 备查 |

---

## 收束

当前推进动作：**Phase 1.5 + 3.3 端到端验证**（需要真实 LLM API + 已构建索引）。

Phase 1.1–1.4、Phase 2、Phase 3.1–3.2 已完成（61 unit tests passed）。
