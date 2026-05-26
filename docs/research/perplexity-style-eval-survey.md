# Perplexity 风格「检索 → 建图 → 评估」调研

> 2026-05-20 · 结合项目内规格（docs/design/thinking-observability-spec.md）与 Perplexity 公开资料

## 1. 概念对齐：两层含义

| 层次 | Perplexity 实际做法 | Systematology 映射 |
|------|---------------------|--------------|
| UX / 可观测 | 流式 reasoning_steps：web_search → fetch_url → 综合撰写 | Thinking 三步：retrieve → build_cld → evaluate |
| 质量评估 | 开源 search_evals + 产品内 live signal | RAGAS（检索）、CLD Judge、FCM/D2D 数值、轻量 ResearchEvaluator |

竞品调研已指出：几乎没有产品对「研究过程本身」做系统化质量评估；Perplexity 强在检索 API 与过程可见，弱在领域方法论与因果图质量度量。Systematology 的差异化正在第三步「评估杠杆」——若只抄 Perplexity 的 UI 而不建评估闭环，优势会被稀释。

## 2. Perplexity 模式拆解

### 2.1 过程可见（Pro Search）

- 内置工具：web_search、fetch_url_content，模型自选组合。
- 流式响应中的 reasoning_steps 暴露每次工具调用（关键词、命中 URL、snippet）。
- 用户感知阶段近似：检索 → 深读 → 撰写（与 Systematology 的「检索 → 建图 → 评估」同构，领域词不同）。

### 2.2 检索基础设施（AI-first Search API）

- 子文档粒度：section/span 作为一等检索单元，而非整页文档。
- 混合检索：lexical + semantic 合并，多阶段 ranking（启发式 → embedding → cross-encoder）。
- 闭环信号：每日约 2 亿查询 + 答案生成构成 live agentic 评测数据，驱动索引与排序迭代。

### 2.3 分级路径

- 快速路径：单次检索 + 综合（≈ 传统 RAG）。
- Deep Research：多轮 agentic，分钟级。

### 2.4 官方评估框架 search_evals

| 维度 | 设计 |
|------|------|
| 原则 | 复杂度谱系、中立、可复现、可扩展 |
| Harness | 单步搜索 + Deep Research 两套 agent |
| Benchmark | SimpleQA、FRAMES（单步）；BrowseComp、HLE（深度） |
| 评分 | 与原文一致的 prompted classifier |
| 对比 API | Perplexity、Exa、Brave、SERP 类 |

公开结果（2025-09）：Perplexity 在质量与 p50 延迟（约 358ms）上领先。SimpleQA 约 0.93，说明检索+综合端到端强，但不覆盖因果图结构正确性。

仓库：perplexityai/search_evals

## 3. 「检索 → 建图 → 评估」各步可评什么

### 3.1 检索（retrieve）

| 指标类型 | 代表指标 | 来源/工具 |
|----------|----------|-----------|
| 经典 IR | Recall@k、MRR、nDCG | 需 gold chunk/doc |
| RAG 专用 | context precision/recall、faithfulness | RAGAS / DeepEval |
| Agentic | IA@k、信息紧凑度 IC | InfoDeepSeek 等 |
| 过程 | 来源 tier、召回数、重试次数 | Systematology source_tiered_retrieve 已有 tier |
| 产品 | citation 可点击、引用与 claim 对齐 | Perplexity 强项；学术工具普遍弱 |

Perplexity 启示：评测应放在「被 AI 调用的检索 API」上，而非仅静态 corpus QA。

### 3.2 建图（build_cld）

Perplexity 没有等价步骤；学界/工业近似评测方向：

| 指标类型 | 内容 | 备注 |
|----------|------|------|
| 结构有效性 | 节点/边数、环检测、孤立节点 | 规则即可 |
| 语义对齐 | 边与证据句对齐率 | LLM-as-Judge 或人工 |
| 与 gold CLD 对比 | 边 F1、节点匹配 | 需标注集（成本高） |
| GraphRAG 向 | 多跳推理、层次检索 | GraphRAG-Bench、RAGSearch |
| 过程 | Judge 冲突检测、归并、超时 | 架构里已有 Judge + 重试（180s） |

### 3.3 评估（evaluate）

Systematology 第三步是 FCM / D2D / 杠杆排序：

| 指标类型 | 内容 |
|----------|------|
| 数值 | 稳定态收敛、干预敏感性、杠杆排序一致性 |
| 不确定性 | 置信区间（D2D uncertainty.py 已有分档） |
| 可解释 | 杠杆点 ↔ CLD 路径可追溯 |
| 降级 | CLD/FCM/D2D 失败时的确定性降级路径 |

### 3.4 过程可观测（横跨三步）

与 Perplexity 对齐的最小契约（见 thinking-observability-spec.md）：

```typescript
interface ThinkingStep {
  id: "retrieve" | "build_cld" | "evaluate";
  status: "pending" | "active" | "done" | "error";
  detail?: string;  // "找到 24 篇相关论文"
}
```

评估维度：
- 步骤是否按 pipeline 顺序完成
- 每步 startedAt/endedAt → 延迟分解
- detail 是否结构化（计数、变量数、路径数）

## 4. 行业评估框架对照（2025–2026）

| 框架 | 侧重 | 对 Systematology 的适用性 |
|------|------|---------------------|
| search_evals | Search API + agent harness | 若自建/换检索后端，可借鉴；不覆盖 CLD |
| RAGAS | RAG 端到端与检索质量 | 已集成（可选）；补 retrieve 步 |
| RAGCap-Bench | Planning / Evidence / Grounded reasoning / Noise | 适合 Lead Agent 分组件评测 |
| InfoDeepSeek | 动态网页、多轮、紧凑度 | 偏开放域；学术库需改编 |
| GraphRAG-Bench / RAGSearch | GraphRAG vs RAG、agentic search | 建图与检索联合场景可参考 |
| ResearchEvaluator（项目内） | 判断句、证据追溯、张力、收束效率 | 偏「研究叙述」；与 FCM 杠杆评估互补 |

结论：没有现成 benchmark 直接评「检索→CLD→FCM/D2D」全链；需要分层评测 + 少量领域 gold set。

## 5. Systematology 现状与差距

**已有：**
- Pipeline：RAG → CLD → FCM/D2D，SharedCLD 契约清晰
- UI 规格：Perplexity 式三步 Thinking（thinking-observability-spec.md）
- 评估碎片：RAGAS、ResearchEvaluator、CLD Judge、单元测试

**缺口：**

| 缺口 | 影响 |
|------|------|
| Thinking API 未结构化流式 | 无法自动评「过程完整性」 |
| 检索评测未与 search_evals 式 harness 对齐 | 换检索策略缺回归基线 |
| 建图无公开图结构 benchmark | CLD 质量主要靠 Judge，缺可复现数据集 |
| 第三步「评估」无独立 benchmark | 杠杆排序难做版本对比 |
| UX 与评测脱节 | 用户看到三步，系统未必逐步打点 |

## 6. 建议的评估体系

### Tier A — 立即可做（MVP+）

- 结构化 Thinking 事件：每步 emit ThinkingStep，日志进 LangSmith/自建 trace
- 检索回归：固定 20–50 个领域 query + 期望来源 tier/最小召回数；RAGAS 子集每周跑
- 建图规则门禁：环、空图、边无 evidence 引用 → 自动 fail 或降级
- FCM/D2D 快照测试：同一 SharedCLD 输入，杠杆 Top-K 排序稳定

### Tier B — 对标 Perplexity 深度

- 引入双 harness：fast（单轮）vs deep（多轮 CLD 迭代）
- 自建 CLD-mini：10–30 题 + 专家简图 gold，报边级 F1 + 关键节点召回
- 过程分：convergence_efficiency + 每步 token/耗时 → ROI 面板

### Tier C — 产品差异化

- 方法论一致性分：CLD 是否满足系统科学约束（库存、延迟、平衡回路等）
- 杠杆可行动性：干预建议是否对应图中路径（可追溯率）
- 人机评测：过程可见 + 专家打分

## 7. 与 Perplexity 的取舍总结

| 学 Perplexity | 不学 / 要超越 |
|---------------|---------------|
| 分步可见、reasoning_steps 级透明 | 仅 spinner 或折叠长推理 |
| Search API 级 benchmark + 延迟 SLA | 只评最终报告文采 |
| 快速/深度两档 | 所有问题都走重 pipeline |
| 子文档级检索粒度 | 整篇 PDF chunk 粗糙召回 |
| — | 因果图 + FCM/D2D 的过程与结果双评估（赛道空白） |

## 8. 参考资料

- Perplexity：Pro Search Tools、Search API 架构与评估、search_evals
- 项目：docs/design/thinking-observability-spec.md、ARCHITECTURE.md、backend/infrastructure/evaluation/research_evaluator.py
- 学术 benchmark：SimpleQA、FRAMES、BrowseComp、HLE；GraphRAG-Bench、RAGCap-Bench、InfoDeepSeek
