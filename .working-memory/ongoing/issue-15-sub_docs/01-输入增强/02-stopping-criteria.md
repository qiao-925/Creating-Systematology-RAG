# 检索停止条件与评估策略调研

> 目标：为 CLDFlow 定义"资料搜到什么程度算完成"的评估策略
> 调研日期：2026-04-12

---

## 一、核心问题：为什么需要明确的停止条件

**不定义停止条件的后果**（来自生产系统教训）：
- **检索循环（Retrieval Thrash）**：无限检索，成本爆炸
- **工具风暴（Tool Storms）**：反复调用搜索工具但无实质进展
- **上下文膨胀（Context Bloat）**：检索结果累积，淹没有效信息

> LangGraph 官方 Agentic RAG 教程曾因缺少停止条件导致无限循环，最终用 `rewrite_count` 硬限制修复。

---

## 二、主流停止条件策略

### 2.1 硬限制（Hard Limits）—— 底线

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **Max Iterations** | 最多检索 N 轮 | 简单场景，易实现 |
| **Max Cost/Time** | 成本或时间上限 | 生产系统必备 |
| **Max Documents** | 最多处理 M 篇文档 | 防止上下文溢出 |

**缺点**：粗暴，可能过早停止或浪费资源。

---

### 2.2 价值判断（Value-Based）—— 智能停止

来自 **Stop-RAG (arXiv 2510.14337, 2025)** —— 目前最先进的检索停止策略。

**核心思想**：
- 把迭代检索建模为 **Markov 决策过程**
- 训练一个价值估计器，判断"再检索一轮是否能提升答案质量"
- 如果边际价值低于阈值，停止检索

**关键公式**：
```
V(stop) = 当前答案质量
V(continue) = 预期检索后的答案质量 - 检索成本

如果 V(continue) ≤ V(stop): 停止检索
```

**CLDFlow 适用性**：⭐⭐⭐⭐⭐
- 我们的场景天然适合：判断"当前 CLD 是否已覆盖关键变量"
- Phase 2 可考虑训练专用价值估计器

---

### 2.3 信息饱和度（Information Saturation）

**判断标准**：
- **新增检索结果与已有结果重复率 > 80%**
- **连续 N 轮未识别出新变量/新因果链**
- **覆盖度检查**：预设的关键主题是否都已涉及

**实现方式**：
```python
def is_saturated(new_results, accumulated_results, threshold=0.8):
    """判断新检索结果是否带来增量信息"""
    new_entities = extract_entities(new_results)
    existing_entities = extract_entities(accumulated_results)
    
    overlap = len(new_entities & existing_entities) / len(new_entities)
    return overlap > threshold
```

---

### 2.4 任务完成度检查（Task-Based）

来自 Anthropic Research Agent 评估框架：

| 检查项 | 说明 |
|--------|------|
| **Groundedness** | 每条因果链是否有来源支持 |
| **Coverage** | 是否覆盖了问题涉及的所有关键主题 |
| **Source Quality** | 来源是否权威，而非随意抓取 |

---

## 三、CLDFlow 的检索停止策略建议

### 3.1 三层停止机制

```
硬限制层（Hard Guardrails）
├── 最多 10 轮检索
├── 每轮最多 5 个查询
├── 总成本上限 $X
└── 总时间上限 Y 分钟

评估层（Value-Based）
├── 变量覆盖度：是否已识别关键变量类型
│   （政策/经济/社会/法律/历史）
├── 信息饱和度：连续 2 轮无新变量则停止
└── 来源质量检查：是否引用权威来源

任务完成层（Task-Based）
├── 问题分解后的子问题是否都已有答案
└── Conductor 审核通过
```

### 3.2 具体评估指标

| 指标 | 阈值 | 说明 |
|------|------|------|
| **变量覆盖率** | ≥ 80% | 预设视角的变量是否都出现 |
| **因果链密度** | 每变量平均 2-3 条入边/出边 | 避免孤立变量 |
| **来源多样性** | ≥ 3 种类型 | 政府/学术/媒体/数据 |
| **饱和度** | 连续 2 轮重复率 > 70% | 停止检索信号 |

### 3.3 人 in the loop 点

```
自动检索 ──→ 预停止检查 ──→ Conductor 审核 ──→ [人工确认] ──→ 进入 CLD 提取
                ↓                              ↓
            未达标继续检索                  人工补充检索方向
```

---

## 四、Phase 1 vs Phase 2 策略

| 策略 | Phase 1 (MVP) | Phase 2 (优化) |
|------|---------------|----------------|
| **硬限制** | ✅ 简单阈值 | ✅ 更细粒度 |
| **饱和度检测** | ✅ 基于变量重复 | 基于语义向量相似度 |
| **价值估计** | ❌ 用启发式规则 | 训练专用价值网络 |
| **覆盖率检查** | ✅ 预设清单 | LLM 动态评估 |

---

## 五、实现要点

### 5.1 饱和度检测代码框架

```python
class RetrievalSaturationChecker:
    """检索饱和度检查器"""
    
    def __init__(self, entity_extractor):
        self.entity_extractor = entity_extractor
        self.history = []
    
    def check(self, new_documents: List[Document]) -> SaturationResult:
        """检查新增文档是否带来增量信息"""
        new_entities = self._extract_entities(new_documents)
        
        # 计算与历史的重叠
        if not self.history:
            overlap_ratio = 0.0
        else:
            all_historical = set().union(*self.history)
            overlap = new_entities & all_historical
            overlap_ratio = len(overlap) / len(new_entities) if new_entities else 1.0
        
        self.history.append(new_entities)
        
        return SaturationResult(
            new_entities=new_entities,
            overlap_ratio=overlap_ratio,
            is_saturated=overlap_ratio > 0.7 and len(self.history) >= 2,
            total_unique_entities=len(set().union(*self.history))
        )
    
    def _extract_entities(self, documents: List[Document]) -> Set[str]:
        """从文档中提取关键实体（变量名、概念）"""
        # 使用 LLM 或规则提取
        entities = set()
        for doc in documents:
            extracted = self.entity_extractor.extract(doc.content)
            entities.update(extracted)
        return entities
```

### 5.2 Conductor 停止决策 Prompt

```python
STOP_DECISION_PROMPT = """
You are the Conductor agent deciding whether to continue retrieving or stop.

Current research state:
- Question: {question}
- Variables identified: {variables}
- Causal chains found: {chains}
- Sources consulted: {sources}
- Retrieval rounds: {round_count}

Recent retrieval round results:
- New variables found: {new_variables}
- Overlap with existing: {overlap_ratio}%
- New sources: {new_sources}

Decision criteria:
1. Have all key perspectives been covered? (policy, economic, social, legal)
2. Is the information gain diminishing? (overlap > 70%)
3. Are there authoritative sources for each major claim?
4. Is the causal structure sufficiently dense?

Make a decision: [CONTINUE] or [STOP]
If CONTINUE, specify what gaps need to be filled.
If STOP, confirm what has been achieved.
"""
```

---

## 六、参考资源

- **Stop-RAG** (arXiv 2510.14337): Value-Based Retrieval Control
- **Anthropic Agent Evals**: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- **BrowseComp**: Needle-in-haystack research agent benchmark (arXiv 2504.12516)
- **Agentic RAG Failure Modes**: Retrieval thrash, tool storms, context bloat

---

*Related: CLDFlow 输入层设计 | 下一步: 动态视角 Agent 生成机制*
