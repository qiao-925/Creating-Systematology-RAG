# Issue #11 执行上下文

## 任务摘要

- **Issue**: #11 - 将当前 RAG 应用改造为研究型 Agent
- **URL**: https://github.com/qiao-925/Creating-Systematology-RAG/issues/11
- **Status**: 框架选型已定 → 进入架构骨架设计
- **Stage**: 冻结研究内核 / 冻结支撑边界 / 冻结有限自主边界
- **Next**: 确认 LangGraph 选型 / 开始研究内核状态机设计

## 关键进展

### 2025-04-07 框架选型调研完成

对比 7 个 Agent 框架后，最终推荐排序：

| 排名 | 框架 | 理由 |
|------|------|------|
| 1 | **LangGraph** | 研究循环需要精确状态控制，Graph + 条件边最匹配 |
| 2 | PydanticAI | 类型安全 + Graph + 持久执行，但生态成长期 |
| 3 | LlamaIndex AgentWorkflow | 迁移成本最低，但控制力不足风险 |

**关键结论**：LangGraph 在研究循环 FSM、Agent 控制力、状态管理方面有压倒性优势。

## 改造目标

把当前系统改造为：**以受控自主判断为核心、以高密度知识场为证据支撑、以启发用户为目标的研究型 Agent。**

成功信号：
- 输出里有明确**判断**，不只是摘要和资料罗列
- 判断可以回溯到证据
- 输出能揭示关键张力、隐藏关系、新的追问方向
- 系统能在预算内决定何时补证据、何时收束

## 关键路径

```
问题 → 定焦 → 证据计划 → 取证与校验 → 综合与判断 → 收束决策 → 启发式交付
```

## 当前阶段：架构骨架设计

### 冻结项（按顺序）

1. **冻结研究内核** ← 当前
2. 冻结支撑边界（研究内核 vs 证据执行层 vs 模型层）
3. 冻结有限自主边界与治理
4. 冻结 MVP 交付形式
5. 再进入实现与旧系统承接

## 下一步选项

### A. 确认 LangGraph 选型
- 若确认：标记选型完成，进入研究内核设计
- 若需重新评估：对比 PydanticAI 的深度集成成本

### B. 设计研究内核状态机
- 定义六个阶段的状态转换（定焦 → 证据计划 → 取证 → 综合 → 决策 → 交付）
- 确定每个状态的输入/输出/停止条件
- 设计状态持久化方案（checkpoint）

### C. 创建子 Issue 追踪
- 研究内核设计
- LangGraph 与现有检索层集成
- 旧系统承接策略（ModularQueryEngine / AgenticQueryEngine）

## 参考资料

- `docs/research/harness-engineering/MVP Version/研究型Agent-MVP定义与执行计划.md` — 核心定义
- `docs/architecture.md` — 当前系统架构
- `backend/business/rag_engine/agentic/ISSUES.md` — 当前 agentic 层已知问题
