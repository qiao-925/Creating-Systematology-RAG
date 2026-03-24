# Autonomous Experiment 1：当前竖切片收敛

## 这份文档解决什么

上一轮 nightshift 先被仓库红测阻塞。本轮已经先把 baseline 恢复到可验证状态，再回到主问题：

> 基于当前仓库现实，研究型 Agent MVP 最值得继续推进的主链路到底是什么？

这里不给“大而全方案”，只做一件事：

- 明确当前仓库已经具备哪些可复用能力
- 明确它离“研究型 Agent”还差的最小关键层
- 给出下一轮最值得实现的一小步

## 一句话结论

当前仓库已经有一个可运行的 `Agentic RAG 规划执行链路`，但它还不是 `研究型 Agent`。

更准确地说：

- 现状强项是：查询理解、检索策略选择、Agentic 查询入口、结果提取与格式化
- 当前缺口是：研究状态、证据账本、阶段性判断、停止依据、启发式交付

所以接下来的主路径不该是重做入口层、重做检索层，或者直接扩成多 Agent。

最值得推进的一小步，是：

> 在现有 `AgenticQueryEngine` 之上补一个最小“研究内核外壳”，先把 `证据 -> 阶段性判断 -> 下一步建议/停止理由` 这条链补上。

## 当前仓库里已经可复用的竖切片

### 1. 前端和服务入口已经打通

当前 UI 与服务入口已经支持切换 Agentic 模式，不需要为 MVP 另起一套入口。

- `frontend/main.py`
  - 会按 `use_agentic_rag` 创建 `RAGService` 与 `ChatManager`
- `backend/business/rag_api/rag_service.py`
  - 会按 `use_agentic_rag` 延迟初始化 `AgenticQueryEngine`
- `backend/business/chat/manager.py`
  - 会在对话主链里切到 `AgenticQueryEngine`

这意味着：

- MVP 不需要新增新的前端入口
- 也不需要新增新的公共服务接口
- 现有 `use_agentic_rag` 就足以作为实验开关

### 2. Agentic 查询执行链已经存在

`backend/business/rag_engine/agentic/engine.py` 已经提供了一个可运行的 Agentic 查询主入口：

- 懒加载 planning agent
- 调用 Agent 并做超时控制
- 提取来源与 reasoning
- 统一格式化输出
- 与现有查询接口保持兼容

这个组件今天更像：

- “会规划检索的查询引擎”

而不是：

- “会围绕研究问题持续推进的研究内核”

### 3. 查询预处理和策略选择已经具备基础骨架

当前 planning agent 已经具备最小工具集：

- `backend/business/rag_engine/agentic/agent/planning.py`
  - 创建 `ReActAgent`
  - 组装查询处理工具和检索工具
- `backend/business/rag_engine/agentic/agent/tools/query_processing_impl.py`
  - `analyze_intent`
  - `rewrite_query`
  - `decompose_multi_intent`
- `prompts/agentic/planning.txt`
  - 已定义“先分析，再决定是否改写/分解，再选择检索策略”的提示词骨架

这部分已经足够承担：

- 研究问题进入系统后的第一跳收敛
- 对复杂问题做最小预处理
- 在多种检索策略之间做选择

### 4. 证据获取层已经不需要重建

现有仓库已经有足够完整的证据执行底座：

- `IndexManager`
- 多种 retriever
- reranker
- source extraction
- response formatting

因此下一轮不该把时间继续花在：

- 重写检索策略
- 重做索引层
- 再造一套新的 Agentic 工具集

## 当前距离“研究型 Agent MVP”真正差什么

北极星文档要求的不是“更聪明地检索”，而是“在证据约束下推进判断”。

按这个标准看，当前系统至少还缺 5 件最关键的事。

### 1. 缺研究状态

当前链路按“单次 query”运行。

它缺少一份最小研究状态，至少应包含：

- 当前研究问题
- 已采纳证据
- 当前阶段性判断
- 尚未解决的关键张力
- 候选下一步动作
- 当前停止原因

没有这层，系统就很难真正做到“每轮都推进”。

### 2. 缺证据账本

当前能提取 sources，但更像“回答附带来源”。

研究型 Agent 需要的是一份更结构化的证据账本，至少要区分：

- 哪些证据支持当前判断
- 哪些证据只提供背景
- 哪些证据彼此冲突
- 哪些关键断言还没有足够证据

### 3. 缺阶段性判断模块

当前输出仍偏向：

- 检索后回答

而不是：

- 基于证据形成阶段性判断

研究型 MVP 至少要能显式区分：

- 事实
- 推断
- 未知

并能说明：

- 为什么此时可以暂时收束
- 或为什么还需要继续补证据

### 4. 缺停止依据

当前 Agent 有 `max_iterations` 和超时控制，但这更像执行护栏，不是研究收束机制。

研究型 MVP 还需要一个业务语义上的停止理由，例如：

- 证据已足够支撑阶段性判断
- 证据冲突仍大，应该交还给人
- 当前知识库不足，继续搜索收益不高

### 5. 缺启发式交付契约

研究型输出不应只是一段答案。

它至少要稳定交付 4 类内容：

- 当前判断
- 关键依据
- 关键张力或未知点
- 下一步值得继续追问的问题

## 下一轮最值得实现的一小步

### 目标

不改 public API，不新增依赖，不改三层结构，只补一个最小研究内核外壳。

### 恢复后已落地的一小步

当前工作树已经把这一步先以内聚、低风险的方式落下：

- 在 `AgenticQueryEngine.query(..., collect_trace=True)` 的 trace 中新增 `research` 结构
- 结构当前包含：
  - `current_judgment`
  - `supporting_evidence`
  - `open_tensions`
  - `next_question`
  - `stop_reason`
  - `recommended_action`
- `recommended_action` 当前显式区分三类最小研究决策：
  - `continue_gathering_evidence`
  - `synthesize_answer`
  - `stop_due_to_insufficient_evidence`
- 这层能力当前只作为内部 trace 扩展存在，不改变公开返回签名

这意味着：

- 现有 Agentic 查询链已经不只是“给出回答”
- 它开始能把一次查询收敛成“当前判断 + 依据 + 未决点 + 下一步问题”的最小研究单元
- 但它还不是完整研究状态机，也还没有跨轮证据账本

### 推荐落点

优先在业务层的 Agentic 查询主链上补一层轻量结构化结果，而不是改前端或基础设施层。

推荐方向：

1. 保留 `frontend -> RAGService -> ChatManager -> AgenticQueryEngine` 现有入口
2. 保留现有 planning agent 负责“查询预处理 + 检索策略选择 + 证据获取”
3. 在 Agent 返回后新增一次“研究型综合”步骤
4. 让综合结果输出一个最小结构，而不是只返回普通 answer

### 这个最小结构应至少包含

建议下一轮先把内部结构收敛成下面 6 个字段：

- `current_judgment`
- `supporting_evidence`
- `open_tensions`
- `next_question`
- `stop_reason`
- `recommended_action`

注意：

- 这一步可以先作为内部结构或 trace 扩展
- 不必马上升级成新的 public API
- 先证明链路成立，再决定是否把它提升为正式输出契约

## 明确不做什么

为了防止主线再次发散，下一轮明确不做：

- 多 Agent 协作
- 长期记忆
- 新数据库或新持久化层
- 重型工作流状态机
- 新前端页面
- 改造现有公共接口

## 下一轮完成标准

如果下一轮只推进一小步，完成标准可以收敛为：

1. Agentic 查询后，系统能生成一个最小研究型结构化结果
2. 结果里能区分“当前判断 / 依据 / 未决张力 / 下一步问题 / 停止理由”
3. 这层能力不破坏现有三层架构与现有公共接口
4. 有最小单元测试覆盖“有证据时收束”和“证据不足时保留未知”两类场景

## 为什么这是当前最值得做的

因为它同时满足 4 个条件：

- 直接服务“研究型 Agent MVP”主命题
- 复用现有代码最多，新增复杂度最少
- 不触碰高风险边界
- 一旦做成，后续是否继续补多轮研究状态、证据账本、启发式交付都会更有落点

换句话说，当前最稀缺的不是又一个检索技巧，而是把现有 Agentic RAG 推进成“会形成阶段性判断”的最小研究闭环。
