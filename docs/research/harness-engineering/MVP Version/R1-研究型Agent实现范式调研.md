# R1：研究型 Agent 的主流实现范式调研

> 对应 MVP执行总计划.md → R1。目标：冻结研究内核的状态定义和状态转换规则。

---

## 高密度概括

Lee Han Chung 的四级分类已被业界广泛引用：**DAG → FSM → Trained E2E → RL-trained**。我们已选定 FSM 作为第一版模式。本文档的核心任务是把 FSM 从"概念标签"推进到"可编码的状态机设计"。

关键判断：
1. LangGraph 的 StateGraph 是当前 FSM 模式最成熟的工程载体，Google 官方 Deep Research Agent 即基于此。
2. 研究型 Agent 的 FSM 核心循环是 `生成查询 → 取证 → 反思 → 路由决策（继续/收束）`，不是线性流水线。
3. 状态对象是"共享白板"模式——所有节点读写同一个 TypedDict，用 reducer 控制合并策略。

---

## 1. 业界分类回顾（Lee Han Chung）

来源：[The Differences between Deep Research, Deep Research, and Deep Research](https://leehanchung.github.io/blogs/2025/02/26/deep-research/)

| 级别 | 模式 | 特征 | 代表 |
|------|------|------|------|
| L1 | **DAG** | 多步 LLM 调用串联，单次通过，无回路 | GPT-Researcher（早期） |
| L2 | **FSM** | 加入 reflexion / self-reflection，LLM 部分引导状态转换 | Jina Deep Search, LangGraph agents |
| L3 | **Trained E2E** | 用 DSPy 等端到端优化整个流程 | Stanford STORM |
| L4 | **RL-trained** | 强化学习训练端到端研究能力 | OpenAI Deep Research |

**对我们的意义**：L1 质量不稳定（纯 prompt 工程），L3/L4 门槛过高。L2（FSM）是最务实起点——这与冻结集 #8 一致。

---

## 2. Google Deep Research Agent（LangGraph 参考实现）

来源：[LangGraph 101: Let's Build A Deep Research Agent](https://towardsdatascience.com/langgraph-101-lets-build-a-deep-research-agent/) — 基于 Google 开源仓库

### 2.1 图结构（4 节点 + 条件边）

```
START
  → generate_query（生成搜索查询）
     → [conditional: continue_to_web_research] 并行分发多个查询
        → web_research（执行搜索，回收结果）
           → reflection（评估信息是否充足，识别知识缺口）
              → [conditional: evaluate_research]
                 ├─ is_sufficient=True 或 loop_count >= max → finalize_answer → END
                 └─ is_sufficient=False → 再次并行 web_research（用 follow_up_queries）
```

### 2.2 状态定义（OverallState）

```python
class OverallState(TypedDict):
    messages: Annotated[list, add_messages]          # 对话历史
    search_query: Annotated[list, operator.add]      # 累积搜索查询
    web_research_result: Annotated[list, operator.add]  # 累积搜索结果
    sources_gathered: Annotated[list, operator.add]  # 累积来源
    initial_search_query_count: int                  # 初始查询数
    max_research_loops: int                          # 最大研究循环
    research_loop_count: int                         # 当前循环计数
    reasoning_model: str                             # 使用的推理模型
```

节点专用子状态：
- `ReflectionState`：is_sufficient, knowledge_gap, follow_up_queries, research_loop_count
- `QueryGenerationState`：query_list
- `WebSearchState`：search_query, id

### 2.3 关键设计模式

- **共享白板**：OverallState 是全局状态，每个节点接收当前状态、执行任务、返回增量更新，框架自动合并。
- **Reducer 驱动合并**：`Annotated[list, operator.add]` 表示累积（追加），普通 `int` 表示覆盖。
- **条件路由**：路由函数检查状态后返回下一个节点名称，实现 FSM 状态转换。
- **并行执行**：通过 `Send` 对象触发多个 web_research 节点并行运行。
- **结构化输出**：`llm.with_structured_output()` 保证每步输出都符合预定义 schema。

---

## 3. GPT-Researcher 多 Agent 架构

来源：[GPT Researcher + LangGraph](https://docs.gptr.dev/blog/gptr-langgraph), [DeepWiki](https://deepwiki.com/assafelovic/gpt-researcher)

### 3.1 架构模式

Planner + Execution 模式，7 个专职 Agent：
1. **Chief Editor** — 编排者（LangGraph 主图接口）
2. **GPT Researcher** — 自主研究 Agent（核心）
3. **Editor** — 规划大纲
4. **Reviewer** — 验证正确性
5. **Reviser** — 基于反馈修订
6. **Writer** — 编写终稿
7. **Publisher** — 多格式发布

### 3.2 流程

```
browser（初始调研）→ planner（规划大纲）
  → researcher（并行：每个大纲主题独立研究）
    → reviewer → reviser（循环直到满意）
  → writer（汇编终稿）→ publisher
```

### 3.3 状态定义

```python
class ResearchState(TypedDict):
    task: dict
    initial_research: str
    sections: List[str]
    research_data: List[dict]
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[str]
    report: str
```

### 3.4 对我们的意义

GPT-Researcher 是**多 Agent + 报告生成**导向，我们第一版只做**单 Agent + 判断形成**。但它的 Reviewer → Reviser 循环（自反思模式）值得借鉴。

---

## 4. Stanford STORM

- 使用 DSPy 端到端优化，质量接近 Wikipedia 文章。
- 核心创新：模拟多视角 AI 对话，然后从对话中提取结构化大纲和内容。
- 属于 L3（Trained E2E），不在我们第一版范围内，但其"多视角对话 → 结构化产出"思路可作为后续参考。

---

## 5. 映射到我们的研究内核

### 5.1 我们需要的状态机 vs Google 参考实现

| Google Deep Research | 我们的研究内核 | 差异 |
|---------------------|--------------|------|
| generate_query | **问题定焦** + 证据计划 | 我们不只是生成搜索词，还要收敛研究范围和边界 |
| web_research | **取证与校验** | 我们的取证源是本地知识库（RAG），不是 web 搜索 |
| reflection | **综合与判断** + 下一步决策 | 我们的反思目标是形成判断，不只是识别知识缺口 |
| finalize_answer | **启发式交付** | 我们的交付是判断 + 证据 + 张力 + 下一步问题 |

### 5.2 研究内核状态机草案

```
状态节点：
  S1: 问题定焦（focus_question）
  S2: 证据计划（plan_evidence）
  S3: 取证（gather_evidence）
  S4: 综合判断（synthesize_judgment）
  S5: 收束决策（convergence_decision）
  S6: 启发式交付（deliver_insight）

转换规则：
  START → S1
  S1 → S2
  S2 → S3
  S3 → S4
  S4 → S5
  S5 → S3  [需要补充证据]
  S5 → S6  [判断足以收束]
  S5 → S6  [预算耗尽，强制收束]
  S6 → END
```

### 5.3 研究状态对象草案

```python
class ResearchState(TypedDict):
    # 问题与边界
    original_question: str              # 用户原始问题
    focused_question: str               # 定焦后的可研究问题
    research_boundary: str              # 研究边界说明
    
    # 证据
    evidence_plan: list[str]            # 证据获取计划（优先级排序）
    evidence_ledger: Annotated[list, operator.add]  # 证据账本（累积）
    
    # 判断
    current_judgment: str               # 当前阶段性判断
    confidence: str                     # 判断置信度（high/medium/low）
    unresolved_tensions: list[str]      # 未解决的关键张力
    
    # 控制
    budget_turns: int                   # 预算上限
    current_turn: int                   # 当前轮次
    stop_reason: str                    # 停止原因（空=未停止）
    
    # 交付
    next_questions: list[str]           # 值得继续追问的方向
```

---

## 6. LlamaIndex 生态详细评估

> 当前项目已深度依赖 LlamaIndex（`llama-index>=0.14.3`，含 LLMs、Embeddings、VectorStore、Readers 共 8 个子包）。如果 LlamaIndex 自身的编排能力已经足够，可避免引入新生态。以下是对 LlamaIndex 编排层三个层次的详细评估。

### 6.1 LlamaIndex Workflows（底层编排引擎）

来源：[Workflows 1.0 公告](https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems)、[官方文档](https://developers.llamaindex.ai/python/framework/module_guides/workflow/)

**定位**：事件驱动、async-first 的通用编排框架。2024 年底独立为 `llama-index-workflows` 包，但 `llama-index-core` 已内置（`llama_index.core.workflow`）。

**核心概念**：

| 概念 | 说明 |
|------|------|
| **Event** | Pydantic 对象，步骤之间的数据载体。`StartEvent` / `StopEvent` 是内置特殊事件 |
| **Step** | `@step` 装饰器标注的 async 方法，接收一种 Event、返回另一种 Event。框架从类型签名推断执行图 |
| **Workflow** | 继承 `Workflow` 类，包含多个 step。无需手动 `add_node/add_edge`，图结构从事件类型自动推导 |
| **Context** | `ctx = Context` 对象，步骤之间共享状态的容器。通过 `await ctx.get(key)` / `await ctx.set(key, val)` 读写 |
| **WorkflowCheckpointer** | 为 Workflow 运行做 checkpoint，可从任意 checkpoint 恢复执行 |

**代码示例——带反思循环的 Corrective RAG**：

```python
class RetrieveEvent(Event):
    query: str

class EvaluateEvent(Event):
    documents: list
    query: str

class CorrectiveRAGFlow(Workflow):
    @step
    async def retrieve(self, ev: StartEvent) -> EvaluateEvent:
        docs = await self.retriever.aretrieve(ev.query)
        return EvaluateEvent(documents=docs, query=ev.query)

    @step
    async def evaluate(self, ev: EvaluateEvent) -> RetrieveEvent | StopEvent:
        # LLM 判断文档是否足够回答问题
        if is_sufficient:
            answer = await self.llm.acomplete(...)
            return StopEvent(result=answer)
        else:
            # 改写查询，重新检索（循环）
            new_query = await rewrite(ev.query)
            return RetrieveEvent(query=new_query)
```

**关键能力对照（与 LangGraph）**：

| 能力 | LlamaIndex Workflows | LangGraph |
|------|---------------------|-----------|
| **图定义方式** | 隐式——从 `@step` 的事件类型签名推导 | 显式——`add_node()` + `add_edge()` |
| **状态管理** | `Context` 对象，key-value 存取，无 reducer | `TypedDict` + `Annotated[..., reducer]`，框架自动合并 |
| **条件路由** | step 返回不同 Event 类型即可分支 | `add_conditional_edges()` + 路由函数 |
| **循环** | step 返回自身或上游的 Event 类型即可回路 | 条件边指向已有节点 |
| **并行执行** | `ctx.send_event()` 发送多个事件触发并行步骤 | `Send` 对象列表 |
| **Checkpointing** | `WorkflowCheckpointer`，按 step 粒度存/恢复 | 内置 checkpointer，按节点粒度存/恢复 |
| **HITL** | `ctx.write_event_to_stream()` + `ctx.wait_for_event()` | `interrupt_before/after` + `Command(resume=...)` |
| **结构化输出** | 需自行调用 LLM structured output | `llm.with_structured_output()` 原生集成 |
| **可观测性** | 可选安装 `llama-index-instrumentation`（OpenTelemetry、Arize Phoenix） | LangSmith 原生集成 |
| **Typed State** | v1.0 新增 typed state 支持 | 从一开始就是 TypedDict |

### 6.2 LlamaIndex AgentWorkflow（高层 Agent 抽象）

来源：[AgentWorkflow 公告](https://www.llamaindex.ai/blog/introducing-agentworkflow-a-powerful-system-for-building-ai-agent-systems)

**定位**：基于 Workflows 的上层封装，专门为构建 Agent 系统减少样板代码。

**核心特性**：

- **FunctionAgent**：支持 function calling 的 Agent（需 LLM 支持 tool use）
- **ReActAgent**：基于 ReAct 范式的 Agent（任意 LLM）
- **多 Agent 编排**：通过 `can_handoff_to` 声明 Agent 间的任务转交关系
- **内置状态管理**：`initial_state` + `Context` 在 Agent 间共享
- **事件流**：`stream_events()` 实时监控 Agent 行为
- **HITL**：`InputRequiredEvent` + `HumanResponseEvent`

**多 Agent 示例**：

```python
agent_workflow = AgentWorkflow(
    agents=[research_agent, write_agent, review_agent],
    root_agent="ResearchAgent",
    initial_state={
        "research_notes": {},
        "report_draft": "",
        "review_feedback": "",
    },
)
```

**关键判断**：AgentWorkflow 的编排模型是 **Agent-centric**（Agent 自主决策转交给谁），而不是 **Graph-centric**（开发者显式定义状态转换）。对于研究内核需要的 FSM 模式，Agent-centric 的控制力不够——我们需要开发者显式控制"何时取证、何时反思、何时收束"，而不是让 LLM 自主决定。

### 6.3 LlamaIndex Memory 系统

| 类型 | 说明 |
|------|------|
| **短期记忆** | 聊天历史，内置 SQLite 存储，按 token limit 自动截断 |
| **StaticMemoryBlock** | 不可变事实（用户信息、环境约束） |
| **FactExtractionMemoryBlock** | 从对话中自动抽取关键事实 |
| **VectorMemoryBlock** | 基于 embedding 的长期对话片段存储 |

对研究内核而言，Memory 系统解决的是"对话记忆"，而不是"研究状态"（证据账本、阶段性判断、未决张力）。两者不等价。

### 6.4 LlamaIndex Workflows 用于研究内核的可行性评估

**可以做到的**：
- 用 `@step` + Event 类型实现 S1→S6 状态转换
- 用 `Context` 承载 ResearchState
- 用 Event 返回类型实现条件路由和循环
- 用 `WorkflowCheckpointer` 做状态持久化
- HITL 通过事件流支持
- **不引入新依赖**——`llama_index.core.workflow` 已在项目中

**不够理想的**：
- **状态管理粒度**：Context 是 key-value 存取，没有 LangGraph 的 reducer 自动合并机制。累积型字段（如 evidence_ledger）需要手动 get → append → set
- **图可视化**：隐式图结构不容易可视化和调试，LangGraph 有原生图渲染
- **社区参考实现**：目前没有基于 LlamaIndex Workflows 的 Deep Research Agent 参考实现；LangGraph 有 Google 官方实现
- **Typed State 成熟度**：v1.0 刚引入 typed state，文档和实践较少
- **并行控制**：`ctx.send_event()` 的并行模式不如 LangGraph `Send` 直观

**结论**：LlamaIndex Workflows **技术上可行**，作为 FSM 载体够用。相比 LangGraph，它的优势是**零新依赖**，劣势是**状态管理人体工学差、缺少研究型 Agent 参考实现、社区实践少**。

### 6.5 现有项目依赖现状

```toml
# pyproject.toml 中的 LlamaIndex 依赖
llama-index>=0.14.3
llama-index-llms-openai>=0.2.0
llama-index-llms-deepseek>=0.2.0
llama-index-llms-litellm>=0.6.0
llama-index-embeddings-huggingface>=0.3.0
llama-index-vector-stores-chroma>=0.2.0
llama-index-readers-file>=0.2.0
llama-index-readers-web>=0.2.0
```

`llama-index-core`（含 Workflows）已经随 `llama-index>=0.14.3` 安装。即用 Workflows 方案 **无需新增任何 pip 依赖**。

---

## 7. 技术选型对比总结

| 维度 | LangGraph | LlamaIndex Workflows | 纯手写 FSM |
|------|-----------|---------------------|------------|
| **FSM 表达力** | ⭐⭐⭐ 显式图 + 条件边 + Send 并行 | ⭐⭐ 隐式图 + Event 类型路由 + ctx.send_event | ⭐⭐⭐ 完全自定义 |
| **状态管理** | ⭐⭐⭐ TypedDict + reducer 自动合并 | ⭐⭐ Context key-value，需手动合并 | ⭐ 全部自行实现 |
| **Checkpointing** | ⭐⭐⭐ 内置，按节点粒度 | ⭐⭐ WorkflowCheckpointer，按 step 粒度 | ❌ 需自行实现 |
| **HITL** | ⭐⭐⭐ interrupt + Command 原生 | ⭐⭐ 事件流 + wait_for_event | ❌ 需自行实现 |
| **参考实现** | ⭐⭐⭐ Google Deep Research Agent | ⭐ Corrective RAG（较简单） | ❌ 无 |
| **新增依赖** | `langgraph` + `langchain-core` | ❌ **零新依赖**（已内置） | ❌ 零新依赖 |
| **与现有代码兼容** | 共存（编排层 vs 检索层） | ⭐⭐⭐ **原生兼容**（同一生态） | ⭐⭐ 需自行对接 |
| **学习成本** | 中（新概念：StateGraph, Send, reducer） | 低（已有 LlamaIndex 经验） | 低（纯 Python） |
| **社区活跃度** | ⭐⭐⭐ 大量文章、教程、实践 | ⭐⭐ 文档齐全，但 Workflows 实践尚少 | N/A |

**修正后的判断**：

- 如果 **优先零依赖 + 与现有生态一致**：LlamaIndex Workflows 是务实选择。FSM 核心循环可以实现，只是状态管理需要多写一些胶水代码。
- 如果 **优先最强 FSM 表达力 + 参考实现可直接复刻**：LangGraph 是最成熟选择，但引入 LangChain 生态。
- **纯手写 FSM** 工程量最大，但对于 MVP 的 6 状态 + 2 个条件转换，实际复杂度可能没有想象中高。

---

## 8. 待冻结项

以下问题需人类决策后才能冻结：

1. **技术选型**：LangGraph vs LlamaIndex Workflows vs 手写 FSM？
2. **状态机粒度**：S1-S6 是否需要更细（如 S3 拆分为"查询生成"+"检索执行"+"结果校验"）？
3. **证据源**：第一版只用本地 RAG，还是也接 web 搜索？
4. **反思深度**：reflection 节点只做"信息充足性判断"，还是同时做"证据冲突检测 + 判断质量评估"？
