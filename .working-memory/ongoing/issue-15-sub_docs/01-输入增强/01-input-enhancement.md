# RAG 查询改写与输入增强调研

> 目标：为 CLDFlow 的自动检索增强层提供技术选型参考
> 调研日期：2026-04-12

---

## 一、核心问题：为什么需要查询改写

用户原始查询通常存在以下问题，导致检索质量差：

| 问题类型 | 说明 | 示例 |
|---------|------|------|
| **缺少上下文** | 代词、省略导致语义不完整 | "它有什么影响？" |
| **对话式语言** | 口语化表达，非检索友好 | "给我讲讲那个政策" |
| **查询过短** | 信息密度不足 | "Prop 13" |
| **关键词缺失** | 缺乏专业术语 | "房价为什么涨了"（缺少"因果关系"） |

**解决方案**：在检索前增加 Query Rewrite 层，将用户查询转换为检索友好的形式。

---

## 二、主流查询改写技术

### 2.1 HyDE (Hypothetical Document Embeddings)

**原理**：
- 先用 LLM 生成一个"假设的理想答案"
- 用这个假设答案做向量检索，而不是用原始查询

**优势**：
- 绕过查询-文档的语义鸿沟
- 假设答案包含更多相关关键词

**劣势**：
- 多一次 LLM 调用，增加延迟和成本
- 假设答案可能偏离用户真实意图

**LlamaIndex 实现**：
```python
from llama_index.core.indices.query.query_transform.base import HyDEQueryTransform

hyde = HyDEQueryTransform(include_original=True)
# include_original=True: 同时保留原始查询和假设文档检索
```

**CLDFlow 适用性**：⭐⭐⭐⭐
- 适合我们的场景：用户问题（如"分析 Prop 13 影响"）可以生成一个假设的分析框架，帮助检索相关文献

---

### 2.2 多查询检索 (Multi-Query Retrieval)

**原理**：
- 从一个用户问题生成多个不同角度的检索查询
- 并行检索，结果合并去重

**示例**：
```
用户查询: "What is the difference between LangGraph and AutoGPT?"

改写后:
- "LangGraph vs AutoGPT architecture comparison"
- "differences between LangGraph and AutoGPT agent framework"
- "LangGraph workflow design vs AutoGPT autonomous agent"
```

**优势**：
- 提高召回率（Recall）
- 覆盖不同表达方式的相关文档

**劣势**：
- 检索成本增加 3-5 倍
- 需要有效的结果合并策略

**LangChain 实现**：`MultiQueryRetriever`

**CLDFlow 适用性**：⭐⭐⭐⭐⭐
- 我们的场景天然需要多视角：政策/经济/社会角度分别检索，正好对应不同查询

---

### 2.3 查询分解 (Query Decomposition)

**原理**：
- 将复杂问题拆分为多个子问题
- 每个子问题独立检索，逐步构建答案

**示例**：
```
用户查询: "Why is LangGraph more stable than AutoGPT?"

分解后:
1. "LangGraph architecture design principles"
2. "AutoGPT architecture and implementation"
3. "AutoGPT stability issues and failure modes"
```

**优势**：
- 适合复杂推理任务
- 每个子问题更简单，检索更准确

**劣势**：
- 增加系统复杂度
- 需要处理子问题间的依赖关系

**LlamaIndex 实现**：`StepDecomposeQueryTransform` + `MultiStepQueryEngine`

**CLDFlow 适用性**：⭐⭐⭐
- 我们的问题通常是单一宏观问题（"分析某政策影响"），分解价值不如多查询高
- 但在 CLD 提取阶段，可以将大问题分解为"识别变量"、"提取因果链"等子任务

---

### 2.4 查询路由 (Query Routing)

**原理**：
- 先识别查询意图
- 根据意图路由到不同的检索策略

**路由表示例**：
| 意图 | 路由策略 |
|------|---------|
| 事实查询 | 向量检索 |
| 比较查询 | 多源对比检索 |
| 最新信息 | Web 搜索（非本地文档） |

**CLDFlow 适用性**：⭐⭐⭐⭐
- 我们的场景需要混合检索：本地知识库 + Web 搜索 + 学术文献

---

## 三、CLDFlow 的输入增强策略建议

### 3.1 分层检索架构

```
用户输入（问题 + 可选本地材料）
        ↓
[查询改写层]
  • 意图识别（政策分析 / 经济分析 / 综合研究）
  • HyDE 生成假设答案框架
  • 多查询生成（3-5 个不同角度）
        ↓
[并行检索层]
  ├── 本地知识库（向量检索）
  ├── Web 搜索（实时信息）
  ├── 学术文献（arXiv/Google Scholar）
  └── 历史数据（特定领域数据库）
        ↓
[结果融合层]
  • 去重
  • 重排序（Reranker）
  • 按视角分类（供 Specialist Agent 使用）
        ↓
多视角 Agent 各取所需
```

### 3.2 技术选型

| 组件 | 建议方案 | 理由 |
|------|---------|------|
| 查询改写 | HyDE + 多查询 | 两者结合，提高召回 |
| 本地检索 | Chroma（已有） | 无需更换 |
| Web 搜索 | Tavily / DuckDuckGo API | 实时信息补充 |
| 学术文献 | arXiv API + Semantic Scholar | 论文检索 |
| 结果融合 | LlamaIndex 的 Reranker | 已有生态兼容 |

### 3.3 关键决策点

**Q: 是否需要实时 Web 搜索？**
- **是**。政策分析需要最新数据（如"2024年加州房价数据"），本地知识库必然滞后。

**Q: 是否保留用户提供的本地材料？**
- **是**。作为检索增强的锚点，但系统应主动验证和补充，而非完全依赖。

**Q: 如何处理检索结果过载？**
- 按 Specialist Agent 的视角需求预过滤
- 例如：政策视角 Agent 优先看政府文档，经济视角 Agent 优先看数据报告

---

## 四、实现要点

### 4.1 Prompt 设计模板

```python
# 查询改写 Prompt
QUERY_REWRITE_PROMPT = """
You are a research query optimizer for policy analysis.

User question: {query}

Generate:
1. Intent classification: [policy | economic | social | comprehensive]
2. Hypothetical answer outline (for HyDE)
3. 3-5 search queries from different angles:
   - Policy/legal angle
   - Economic/data angle  
   - Social/public opinion angle
   - Historical/case study angle
   - Academic/theoretical angle

Return in JSON format.
"""
```

### 4.2 与 CLDFlow 架构的集成点

```
[输入层增强]  ← 本次调研结论
        ↓
[CLD 层]      ← 已有设计
        ↓
[FCM 层]
        ↓
[D2D 层]
```

**集成方式**：作为独立模块 `QueryEnhancer`，在 Conductor 问题分析前调用。

---

## 五、参考资源

- LlamaIndex Query Transformations: https://developers.llamaindex.ai/python/framework/optimizing/advanced_retrieval/query_transformations/
- HyDE Paper: https://arxiv.org/abs/2212.10496
- Multi-Query Retrieval Pattern: LangChain MultiQueryRetriever
- Agentic RAG Survey (2025): https://arxiv.org/abs/2501.09136

---

*Related: CLDFlow 业务架构设计 | 下一步: 动态视角 Agent 生成机制调研*
