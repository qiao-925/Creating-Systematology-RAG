# References — 设计参考库

本目录收集对本项目有借鉴价值的外部实现、文档和模式。每个条目标注"借鉴了什么"和"为什么不完全照搬"。

**使用方式：** 重大设计决策前，先查本目录是否有可借鉴的模式。参考是起点，不是终点——理解意图后结合项目上下文做取舍。

---

## 架构文档

### rust-analyzer architecture.md

- **链接：** [rust-analyzer/docs/dev/architecture.md](https://github.com/rust-lang/rust-analyzer/blob/d7c99931d05e3723d878bea5dc26766791fa4e69/docs/dev/architecture.md)
- **解决什么问题：** 如何让新人在 15 分钟内理解一个大型代码库的整体设计
- **借鉴了什么：**
  - **Bird's Eye View**：开头一段话概括系统目的、输入、输出、核心机制
  - **Architecture Invariant**：每个模块标注"刻意不存在的东西"，防止后人"补全"它们
  - **API Boundary 标记**：明确哪些是边界，边界内外规则不同
  - **Cross-Cutting Concerns**：横切关注点单独成节，不散落在各模块中
  - **Code Map 按模块组织**：每个目录/模块有职责、关键数据结构、设计约束
- **哪些不适用：**
  - rust-analyzer 是编译器/IDE，我们是 LLM Agent pipeline——它强调增量计算和取消机制，我们强调预算控制和降级策略
  - 它的测试是纯数据驱动快照比较，我们的测试需要 mock LLM 调用
- **落地位置：** `ARCHITECTURE.md` 已采用其组织方式

---

## Agent 编排

### LlamaIndex AgentWorkflow

- **链接：** [LlamaIndex Workflows 文档](https://docs.llamaindex.ai/en/stable/understanding/workflows/)
- **解决什么问题：** 多步骤 Agent 任务的编排、状态传递、错误处理
- **借鉴了什么：**
  - ReActAgent + FunctionTool 的工具注册模式
  - 工具作为独立 Function 封装，Agent 只负责决策调用顺序
- **当前落地：** `backend/core/orchestration/lead_agent.py`

### ReAct 模式（Reasoning + Acting）

- **链接：** [ReAct Paper](https://arxiv.org/abs/2210.03629)
- **解决什么问题：** LLM 在推理和行动之间交替，逐步解决问题
- **借鉴了什么：**
  - 思考→行动→观察的循环
  - 工具调用结果反馈给下一轮推理
- **当前落地：** Lead Agent 的 ReAct 循环；Research Agent 的证据收集循环

---

## 错误处理

### rust-analyzer 的 `(T, Vec<Error>)` 模式

- **链接：** 同 architecture.md Error Handling 章节
- **解决什么问题：** 分析过程不应因单个错误而整体失败
- **借鉴了什么：**
  - 分析函数返回结果 + 错误列表，而非 `Result<T, Error>`
  - 降级而非崩溃：有结果就输出，附带警告
- **当前落地：** `RunContext.failures` 累积失败记录；`StructuredFailureReport` 作为显式返回类型；CLD/FCM/D2D 各有确定性降级路径

---

## 数据契约与边界校验

### Pydantic strict mode

- **链接：** [Pydantic v2 Config](https://docs.pydantic.dev/latest/concepts/config/)
- **解决什么问题：** 层间传递数据时防止意外字段和类型错误
- **借鉴了什么：**
  - `ConfigDict(extra="forbid")` 在每个边界拒绝未知字段
  - 模型即文档：Pydantic 模型定义了数据形状，不需要额外的 schema 文档
- **当前落地：** `backend/core/models.py` 所有模型

---

## 待补充

以下领域有参考价值，待后续补充：

| 领域 | 候选参考 | 优先级 |
|------|----------|--------|
| 多 Agent 并行 | CrewAI / AutoGen 的并行执行模式 | 中 |
| RAG 评估 | RAGAS / DeepEval 的评估框架设计 | 低 |
| 流式响应 | Vercel AI SDK 的流式协议设计 | 中 |
| 可观测性 | LangSmith / LangFuse 的 tracing 设计 | 中 |
| 配置管理 | 12-Factor App 的配置原则 | 低 |
