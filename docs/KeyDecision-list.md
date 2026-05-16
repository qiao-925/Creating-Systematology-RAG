# CLDFlow 关键决策记录

> 来源：`docs/CLDFlow-MVP-plan.md` §1.3，全部已闭合。

| # | 问题 | 决策结果 | 来源 |
|---|------|----------|------|
| D1 | 编排框架 | **LlamaIndex AgentWorkflow** | 用户确认 + `research_kernel/agent.py` 样板 |
| D2 | CLDNode 字段 | `id, label, description`（以 `models.py` 为准） | D24(UUID) + D23(删除置信度) + D25(删除 strength) |
| D3 | CausalLink.relation | `Literal["influences", "causes", "enables", "inhibits", "supports", "requires"]` | 用户确认 |
| D4 | FCM 仿真引擎 | NumPy 直接实现（FCMpy 因 tqdm 冲突移除） | D21 技术栈锁定 |
| D5 | ParsedQuery.documents 类型 | LlamaIndex `Document` 组件 | 用户确认 |
| D6 | PerspectiveSpec 类型 | Pydantic model，复用 `perspectives/generator.py` 的 Perspective 结构 | 现有代码 |
| D7 | D2D 解释 Agent | MVP 不做，纯计算输出 | 架构文档"可选" |
| D8 | 输入增强数据源 | arXiv + Semantic Scholar + FRED + World Bank + OECD（全部 5 个） | D16 |
| D9 | HyDE 实现模型 | DeepSeek-V3 | D17 模型分工 |
| D10 | 节点归并 Embedding | MiniLM-L6-v2 | D21 技术栈锁定 |
| D11 | 测试 mock 方案 | mock `llama_index.core.llms.LLM.complete()` 方法 | 用户确认 |
| D12 | 黄金样例场景 | 财政补贴 + Prop 13（1978加州房产税） | 研究文档验证案例锁定 |
