# Issue #10 Phase 1 现状摸底报告

## 先说结论

- 当前仓库已经具备一条可运行的 `Agentic RAG` 单次查询链路：用户问题可以进入 `AgenticQueryEngine`，由规划 Agent 触发检索、整理答案、返回引用来源，并通过 `RAGResponse` 和 `ChatSession` 挂到现有对话流程中。
- 但这条链路的系统中心仍然是“单轮问答”，不是“研究过程”。现有实现缺少独立的研究内核，无法把问题定焦、证据计划、阶段性判断、下一步决策和停止原因作为一等状态持续推进。
- 因此，本次 MVP 不应该重做检索、会话或前端入口，而应该在业务层新增一个最小的 `research_kernel`，复用已有 `rag_service_query` / `AgenticQueryEngine` 作为取证执行层，先证明“问题 -> 取证 -> 判断 -> 收束”能跑通。

## 资料来源

- `docs/research/harness-engineering/MVP Version/研究型Agent-MVP定义与执行计划.md`
- `backend/business/rag_engine/agentic/engine.py`
- `backend/business/rag_engine/agentic/ISSUES.md`
- `backend/business/chat/session.py`
- `backend/business/rag_api/rag_service_query.py`
- 补充核对：`backend/business/rag_engine/agentic/research_trace.py`
- 补充核对：`backend/business/rag_engine/agentic/research_decision.py`
- 补充核对：`backend/business/rag_engine/agentic/CHECK_REPORT.md`
- 架构边界参考：`docs/architecture.md`

## 1. 现有系统能做什么、不能做什么

### 1.1 已有能力

1. 系统已经有一个可复用的 Agentic 查询执行器。`AgenticQueryEngine.query()` 会创建规划 Agent，执行一次受 `max_iterations`、`timeout_seconds` 约束的查询，并返回 `(answer, sources, reasoning_content, trace_info)`。
2. 查询入口已经统一。`rag_service_query.execute_query()` 负责调用查询引擎、把来源转换成 `SourceModel`、补充 `metadata`，因此后续研究内核不需要自己重写来源格式化或响应包装逻辑。
3. 现有 agentic 链路已经开始暴露“研究味”的内部痕迹。`research_trace.py` 会从答案和来源里整理出 `current_judgment`、`supporting_evidence`、`open_tensions`、`next_question`、`stop_reason` 等字段，说明仓库里已经有把“回答”往“阶段性判断”收敛的尝试。
4. 会话层已经能保存单轮问答及其来源。`ChatSession` / `ChatTurn` 支持记录 `question`、`answer`、`sources`、`reasoning_content` 和时间戳，并可序列化到 JSON 文件。
5. 架构分层是清楚的。`docs/architecture.md` 明确要求 `frontend -> business -> infrastructure` 单向依赖，这意味着研究内核可以作为新的业务层模块接入，而不必绕过现有服务边界。

### 1.2 当前不能做什么

1. 不能把用户问题转成一个持续推进的研究任务。现有 `execute_query()` 只负责“接收一个问题，调用一次 query_engine，返回一次响应”，没有研究任务对象，也没有多轮研究循环。
2. 不能把“判断”作为公开、一等的结果契约返回。当前公开返回的是 `answer + sources + metadata`；`research_trace.py` 里的 `current_judgment` 等字段只是内部 trace 扩展，不是稳定的业务输出。
3. 不能显式管理研究状态。`ChatSession` 保存的是对话历史，而不是研究历史；它没有证据账本、未解决张力、预算消耗、停止原因、候选下一步动作等研究态字段。
4. 不能可靠地回溯研究证据。`ISSUES.md` 已明确指出 sources / reasoning 的提取仍是简化实现，依赖 ReActAgent 返回结构和工具调用历史，运行时可靠性还需要验证。
5. 不能把“何时继续、何时收束、何时停止”变成可审计决策。当前最多只有 `max_iterations` 和超时这类执行约束，还没有研究内核层面的继续/停止准则，更没有 HITL 交还点。

### 1.3 现状判断

当前仓库最接近研究型 Agent 的部分，不是一个完整研究闭环，而是“带规划能力的单次查询引擎 + 对研究决策的启发式 trace 提取”。这说明项目已经有可复用的下层能力，但系统本体仍缺席：缺的不是再加一个工具，而是把这些工具组织成研究闭环的业务内核。

## 2. 研究内核缺失的具体能力清单

以下缺口控制在 5 条内，并只保留本次 MVP 真正需要补的能力：

1. **问题定焦能力**
   当前没有一个步骤把用户原问题收敛成“本轮具体要判断什么、范围到哪里、什么情况下应停止”的研究目标。
2. **预算内的研究循环编排能力**
   当前链路只有单次查询，没有“分解子查询 -> 调用取证 -> 形成阶段判断 -> 决定继续或收束”的循环控制器。
3. **研究结果合约能力**
   当前没有 `ResearchResult` 这类最小业务契约来稳定承载 `judgment`、`evidence_refs`、`confidence`、`next_questions`、`turns_used`。
4. **研究状态承载能力**
   当前没有研究态内存来记录已经用过哪些子查询、收集了哪些关键证据、还剩哪些张力、预算已消耗多少。
5. **可解释的停止/继续决策能力**
   当前没有业务层决策器来说明“为什么现在继续补证据”“为什么现在可以收束”“为什么因为证据不足而停止”。

## 3. 本次 MVP 的 scope 边界决定

### 3.1 纳入本次 MVP 的范围

1. **新增一个业务层内的最小 `research_kernel`**
   理由：当前真正缺的是研究内核，而不是检索能力或 UI 入口。把最小新增限定在业务层，最符合现有分层约束，也最容易验证主命题是否成立。
2. **复用现有 `rag_service_query` / `AgenticQueryEngine` 作为取证执行层**
   理由：仓库已经有查询入口、来源格式化、trace 组装和现成的 agentic 引擎；MVP 应验证研究闭环，而不是重写检索链路。
3. **把输出收敛到最小研究结果**
   理由：`judgment`、`evidence_refs`、`confidence`、`next_questions`、`turns_used` 已足以验证“这不是摘要，而是阶段性判断”，同时不会预支复杂报告协议。
4. **只做单 Agent、有限轮次、固定预算的研究循环**
   理由：MVP 目标是证明受控自主判断成立，不是证明系统能无限扩张。单 Agent + `budget_turns` 已经足够承载第一版实验。

### 3.2 明确排除在本次 MVP 之外的内容

1. **不改现有公开 API、前端入口和会话协议**
   理由：Issue 计划已明确禁止修改现有 API；当前阶段也只需要证明研究内核最小闭环可运行，不需要立刻把它接进用户主路径。
2. **不重写检索、重排序、来源提取基础设施**
   理由：这些能力已经存在，且当前 Phase 1 结论是“组织方式缺失”而非“取证能力完全缺失”。
3. **不引入多 Agent、长期记忆、数据库持久化**
   理由：这些会显著扩大复杂度预算，而且并不直接服务于验证第一版研究闭环。
4. **不把输出协议扩展成完整研究报告系统**
   理由：MVP 只需要证明能形成判断和下一步问题，不需要提前设计完整产品化交付格式。
5. **不处理超出当前执行约束的人类协同流程**
   理由：本轮先用预算和停止条件证明“有限自主”即可，复杂 HITL 流程可以放到后续阶段再显式建模。

### 3.3 对后续阶段的直接含义

- Phase 2 应只定义研究内核契约，不要触碰现有查询路径和公开接口。
- Phase 3 应把最小循环实现为“研究编排层”，而不是另起一套检索实现。
- 如果后续实现需要修改数据库 schema、公开 API 或认证逻辑，应视为超出本次 MVP 边界，必须升级给人。
