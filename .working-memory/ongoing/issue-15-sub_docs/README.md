# Issue #15: 综合集成法架构洞察

> 目标：从综合集成法案例推导出 Agent 的工程架构，找到可落地的实现路径
> 状态：🟡 进行中（CP-18）
> GitHub: [Issue #15](https://github.com/qiao-925/Creating-Systematology-RAG/issues/15)

---

## 快速导航

| 文档 | 内容 | 日期 |
|------|------|------|
| [01-input-enhancement](01-input-enhancement.md) | 输入增强技术（HyDE + 多查询检索） | 04-12 |
| [02-stopping-criteria](02-stopping-criteria.md) | 检索停止条件（三层机制） | 04-12 |
| [03-evaluation-strategy](03-evaluation-strategy.md) | 检索评估策略（Anthropic Harness 模式） | 04-12 |
| [04-academic-sources](04-academic-sources.md) | 可靠学术数据源（Tier 分级） | 04-12 |
| [05-human-in-loop](05-human-in-loop.md) | 多模型评估与人类介入机制 | 04-12 |
| [06-dynamic-agent](06-dynamic-agent.md) | 动态视角 Agent 生成 | 04-12 |
| [07-template-evaluation](07-template-evaluation.md) | 模板评估业内实践调研 | 04-12 |
| [08-implementation-report](08-implementation-report.md) | 模板系统实施报告 | 04-12 |

---

## 核心决策（倒序）

### 2026-04-12 | CP-18 模板系统 Phase 1 完成
- **决策**：完成 `backend/perspectives/` 基础架构 + 4 个 DDC 模板
- **评估框架**：反事实对比 + Action Advancement（占位实现，待真实测试）
- **下一动作**：工程架构设计 + 真实环境集成测试
- **来源**: [Issue #15 CP-18](https://github.com/qiao-925/Creating-Systematology-RAG/issues/15#issuecomment-4231162350)

### 2026-04-12 | CP-18 输入增强层决策
- **检索策略**：HyDE + 多查询检索（3-5 个角度）
- **数据源**：T1（政府/顶级期刊）/ T2（学术预印本）/ T3（媒体）/ T4（过滤）
- **Phase 1 数据源**：arXiv API + Semantic Scholar + FRED + World Bank + OECD

### 2026-04-12 | CP-18 检索停止与评估决策
- **停止条件**：硬限制（10 轮/5 查询）+ 饱和度检测（连续 2 轮 Novelty < 30%）+ Coverage ≥ 80%
- **评估策略**：Generator-Evaluator 分离（Anthropic Harness 模式）

### 2026-04-12 | CP-18 多模型与人类介入决策
- **架构**：Specialist(DeepSeek-V3) + Evaluator(GPT-4o-mini) 双模型对照
- **介入模式**：HOTL（Human-on-the-Loop），自动执行 + 关键节点通知
- **必须介入点**：方向确认、节点归并争议、硬限制到达

---

## 当前阻塞

| 阻塞项 | 依赖 | 预计解除 |
|--------|------|---------|
| 模板真实环境测试 | Conductor 集成完成 | 工程架构设计后 |

---

## 相关资源

- **Working Memory**: [ongoing/2026-04-10-02_【research】综合集成法架构洞察.md](../../.working-memory/ongoing/2026-04-10-02_【research】综合集成法架构洞察.md)
- **Board**: [.working-memory/board.md](../../.working-memory/board.md)
- **历史文档**: [docs/metasynthesis-architecture-insight-2026-04-10.md](../../metasynthesis-architecture-insight-2026-04-10.md)

---

*最后更新：2026-04-12*
