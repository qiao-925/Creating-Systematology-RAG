# 输入增强评估策略调研（综合版）

> 目标：为 CLDFlow 定义"检索到什么程度算完成"的评估机制
> 调研日期：2026-04-12
> 核心参考：Anthropic "Harness design for long-running apps"

---

## 一、核心问题：为什么评估策略如此关键

### 1.1 没有评估策略的后果

来自生产系统的教训（Anthropic, 2025）：

| 问题 | 表现 | 后果 |
|------|------|------|
| **检索循环（Retrieval Thrash）** | 无限检索，不知道何时停止 | 成本爆炸 |
| **自我评估失效** | Agent 对自己工作过于乐观 | 质量平庸不自知 |
| **上下文膨胀** | 累积的检索结果淹没有效信息 | 性能下降 |

> "LangGraph 官方 Agentic RAG 教程曾因缺少停止条件导致无限循环，最终用 `rewrite_count` 硬限制修复。"

### 1.2 传统方法的局限

**硬阈值的问题**：
- 固定轮数：可能过早停止或浪费资源
- 固定成本：无法适应问题复杂度差异

**LLM 自我评估的问题**（Anthropic 发现）：
- Agent 倾向于**过度自信**地评价自己的工作
- 即使质量很差，也会"自信地称赞"
- 在主观任务上尤为严重（没有二值检查的任务）

---

## 二、前沿方案：Anthropic Harness Design

### 2.1 核心洞察：分离生成器与评估器

**关键发现**：
```
问题：让同一个 Agent 生成并评估自己的工作
     → 倾向于过度乐观（leniency bias）

解决方案：分离 Generator 和 Evaluator
     → Evaluator 可以独立调优为"怀疑者"
     → Generator 有具体反馈可以迭代改进
```

**对 CLDFlow 的启示**：
- ✅ Conductor 作为独立评估者，而非 Specialist Agent 自我评估
- ✅ 评估标准需要明确、可量化
- ✅ 评估结果需要具体反馈，而非简单 pass/fail

---

### 2.2 主观质量的可量化方法

即使是设计美学这种主观领域，Anthropic 也建立了可量化的评分体系：

**四维评分标准**：

| 维度 | 评估内容 | 权重 |
|------|---------|------|
| **Design Quality** | 整体设计是否协调一致，有独特氛围和识别度 | ⭐⭐⭐⭐⭐ |
| **Originality** | 是否有定制决策，而非模板/默认值/AI 套路 | ⭐⭐⭐⭐⭐ |
| **Craft** | 技术执行：排版、间距、色彩、对比度 | ⭐⭐⭐ |
| **Functionality** | 可用性：用户能否理解界面、找到操作 | ⭐⭐⭐ |

**关键原则**：
- 评分标准要明确、具体，避免模糊
- "设计是否好看" → "是否遵循了我们的设计原则"
- 通过 few-shot 示例校准评估者的判断

---

### 2.3 Sprint 合约模式

**生成前约定完成标准**：

```
Generator（生成器）  →  提出 Sprint 合约  →  Evaluator（评估器）
                        （要做什么 + 如何验证）      （审核合约合理性）
                              ↓ 双方同意
                           开始实现
                              ↓
                        Evaluator 根据合约验收
```

**对 CLDFlow 的应用**：
- Conductor 为每个 Specialist Agent 定义"检索完成标准"
- 在开始检索前，Agent 和 Conductor 就"什么算搜够了"达成一致

---

## 三、CLDFlow 输入增强评估策略设计

### 3.1 评估架构：三层分离

```
[Specialist Agent 检索]
        ↓
[Conductor 评估]  ← 独立评估者，非自我评估
   ├── 定量指标检查
   ├── 质量评分
   └── 具体反馈
        ↓
[决策]
   ├── 达标 → 进入 CLD 提取
   └── 未达标 → 继续检索（有具体改进方向）
```

### 3.2 四维评估标准

参考 Anthropic 模式，为信息检索设计评估维度：

| 维度 | 评估内容 | 权重 | 评估方式 |
|------|---------|------|---------|
| **Coverage** | 是否覆盖了问题涉及的关键主题 | ⭐⭐⭐⭐⭐ | 检查清单 |
| **Novelty** | 是否发现了新的变量/关系（非重复信息） | ⭐⭐⭐⭐ | 实体重叠率 |
| **Authority** | 来源质量：政府/学术/主流媒体/数据 | ⭐⭐⭐⭐ | 来源分类统计 |
| **Depth** | 信息的深度：是否触及因果机制 | ⭐⭐⭐ | 抽样检查 |

### 3.3 评估检查清单（Coverage）

针对"Prop 13 分析"示例：

```python
COVERAGE_CHECKLIST = {
    "政策维度": {
        "tax_policy": "房产税政策细节",
        "legal_framework": "法律框架和条款",
        "implementation": "执行机制和流程",
    },
    "经济维度": {
        "housing_market": "住房市场影响",
        "tax_revenue": "财政收入变化",
        "property_values": "房产价值波动",
    },
    "社会维度": {
        "resident_behavior": "居民行为变化",
        "equity_issues": "公平性问题",
        "demographic_impact": "人口结构影响",
    },
    "历史维度": {
        "historical_context": "历史背景",
        "comparison_cases": "对比案例（其他州/时期）",
    }
}
```

**覆盖率计算**：
```
coverage_score = (已覆盖检查项) / (总检查项)
阈值：≥ 80% 视为达标
```

### 3.4 Novelty 检测：信息饱和度

**实体重叠率计算**：

```python
def calculate_novelty(new_documents, accumulated_entities):
    """
    计算新文档带来的增量实体
    
    Args:
        new_documents: 本轮检索的新文档
        accumulated_entities: 已累积的实体集合
    
    Returns:
        novelty_score: 新实体占比（0-1）
    """
    new_entities = extract_entities(new_documents)
    
    if not new_entities:
        return 0.0
    
    novel_entities = new_entities - accumulated_entities
    novelty_score = len(novel_entities) / len(new_entities)
    
    return novelty_score

# 停止条件：连续 2 轮 novelty_score < 0.3（即 70% 是重复的）
```

### 3.5 评估 Prompt 模板

```python
RETRIEVAL_EVALUATION_PROMPT = """
You are the Conductor evaluating a Specialist Agent's retrieval results.

Research question: {question}
Agent perspective: {perspective}

Retrieved documents summary:
- Total documents: {doc_count}
- Sources: {source_list}
- Key entities found: {entity_list}

Evaluate against these criteria:

1. **Coverage** (0-100)
   Checklist items covered: {covered_items}/{total_items}
   Score: ___

2. **Novelty** (0-100)
   New entities this round: {new_entities}
   Overlap with accumulated: {overlap_ratio}%
   Score: ___

3. **Authority** (0-100)
   Source breakdown:
   - Government/Academic: {gov_acad_count}
   - News/Media: {news_count}
   - Blogs/Opinion: {blog_count}
   Score: ___

4. **Depth** (0-100)
   Sample document analysis:
   - Contains causal mechanisms? Yes/No
   - Contains quantitative data? Yes/No
   - Contains historical context? Yes/No
   Score: ___

Overall assessment:
- [ ] Ready to proceed to CLD extraction
- [ ] Needs more retrieval (specify gaps)

If needs more, specify:
- Missing topics: ___
- Suggested search directions: ___
- Recommended sources: ___
"""
```

---

## 四、停止条件决策矩阵

### 4.1 三层停止机制

| 层级 | 条件 | 动作 |
|------|------|------|
| **硬限制** | 最多 10 轮检索 / 每轮最多 5 查询 / 总成本上限 | 强制停止 |
| **评估层** | Coverage ≥ 80% AND 连续 2 轮 Novelty < 30% | 建议停止 |
| **人工层** | Conductor 评估通过 | 确认停止 |

### 4.2 决策流程

```
[第 N 轮检索完成]
        ↓
[自动检查硬限制]
   ├── 超限 → 强制停止，记录原因
   └── 未超限 → 继续
        ↓
[Conductor 评估]
   ├── Coverage < 80% → 继续，指定补充方向
   ├── Novelty 仍高 → 继续
   ├── Novelty 低但 Coverage 不足 → 调整策略继续
   └── Coverage ≥ 80% AND Novelty 低 → 建议停止
        ↓
[人工确认]（可选，初期建议保留）
   ├── 确认 → 进入 CLD 提取
   └── 否 → 继续检索
```

---

## 五、与 Anthropic 模式的对比

| 维度 | Anthropic 前端设计 Harness | CLDFlow 检索评估 |
|------|---------------------------|------------------|
| **生成器** | Frontend Generator | Specialist Agent（检索） |
| **评估器** | Frontend Evaluator | Conductor |
| **迭代次数** | 5-15 轮 | 最多 10 轮 |
| **评估维度** | Design, Originality, Craft, Functionality | Coverage, Novelty, Authority, Depth |
| **硬阈值** | 单项低于阈值即失败 | 综合判断 + 硬限制兜底 |
| **反馈方式** | 详细评分 + 文字反馈 | 评分 + 具体改进建议 |

---

## 六、Phase 1 实现建议

### 6.1 简化评估（MVP）

| 评估项 | Phase 1 实现 | Phase 2 增强 |
|--------|-------------|--------------|
| Coverage | 预设检查清单，人工确认 | LLM 自动评估 |
| Novelty | 简单实体重叠统计 | 语义相似度检测 |
| Authority | 来源域名分类 | 内容质量分析 |
| Depth | 抽样人工检查 | LLM 自动评估 |

### 6.2 代码框架

```python
class RetrievalEvaluator:
    """检索结果评估器（Conductor 组件）"""
    
    def __init__(self, checklist: Dict[str, List[str]]):
        self.checklist = checklist
        self.history = []
    
    def evaluate(self, 
                 documents: List[Document],
                 perspective: str) -> EvaluationResult:
        """评估 Specialist Agent 的检索结果"""
        
        # 1. Coverage 评估
        coverage = self._check_coverage(documents)
        
        # 2. Novelty 评估
        novelty = self._calculate_novelty(documents)
        
        # 3. Authority 评估
        authority = self._assess_authority(documents)
        
        # 4. 综合决策
        should_stop = self._should_stop(coverage, novelty)
        
        return EvaluationResult(
            coverage=coverage,
            novelty=novelty,
            authority=authority,
            should_stop=should_stop,
            feedback=self._generate_feedback(coverage, novelty)
        )
    
    def _should_stop(self, coverage: float, novelty: float) -> bool:
        """判断是否应停止检索"""
        return coverage >= 0.8 and novelty < 0.3
```

---

## 七、参考资源

- **Anthropic Harness Design**: https://www.anthropic.com/engineering/harness-design-long-running-apps
- **Anthropic Agent Evals**: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- **Stop-RAG** (arXiv 2510.14337): Value-Based Retrieval Control
- **PersonaFlow** (arXiv 2409.12538): Expert Perspective Simulation

---

*Related: CLDFlow 业务架构 | 下一步: 工程架构设计（模块接口 + 流水线）*
