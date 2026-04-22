# 工作记忆看板

> 全局视角：先看这里，再进细节

---

## 当前焦点

**#15 CLDFlow架构完善 → 工程实现**

方向：补完业务架构细节 → 画工程架构图 → 让 Agent 自主跑

---

## 进行中

| 任务 | 阶段 | 下一动作 | 更新 |
|------|------|----------|------|
| [#15] CLDFlow业务架构完善 | 架构 | 收敛剩余决策：Conductor停止条件 / FCM评分边界 / 失败终态口径 | 04-16 |
| [#15] CLDFlow工程架构图 | 架构 | 校验模块落位与现有 backend 复用边界 | 04-16 |
| [#13] Research Kernel MVP | 阻塞 | 需LLM API + E2E验证闭环 | 04-08 |

## 已完成（本轮）

| 任务 | 结果 | 日期 |
|------|------|------|
| 业务图 + 工程图同步完善 | 新增 `docs/CLDFlow-engineering.md`，补 Conductor/异常路径/模块映射 | 04-16 |
| docs 文件合并精简 | cldflow/ 14→5 按层合并；architecture/engineering 去重；导航同步更新 | 04-16 |
| 文档迁移到 docs/ | 14个cldflow文档 + 分类整理 + AGENTS.md重写 | 04-15 |
| Harness Engineering落地 | core-beliefs + invariants + defaults | 04-15 |

---

## 前置条件检查

在让Agent自主跑之前，需要确认：

- [ ] 业务架构图：层内流转细节完备（CLD层Conductor调度、FCM层评级流程）
- [x] 工程架构图：代码模块映射到业务层、LLM调用方式、异常路径
- [ ] 运行流程图：正常路径 + 异常路径（Agent失败/LLM超时/检索为空）
- [ ] 验证案例：Prop 13 端到端可跑通

---

## 冻结原则

1. 模型能力 API only（DeepSeek/OpenAI/LiteLLM）
2. Agent编排用 LlamaIndex AgentWorkflow
3. 可观测性必须加强
4. E2E验证要建立可复用闭环模式

---

## 快速链接

- [CLDFlow业务架构](../docs/CLDFlow-architecture.md)
- [CLDFlow工程架构](../docs/CLDFlow-engineering.md)
- [架构不变量](../docs/CLDFlow-invariants.md)
- [决策时间线](ongoing/issue-15-CLDFlow架构设计与实现-v2.md)
- [Aha Moments](../aha-moments/)
