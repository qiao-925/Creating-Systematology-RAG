# CLD层 - 因果链提取设计

> 架构概览见：`docs/CLDFlow-architecture.md` CLD层
> 默认参数见：`docs/CLDFlow-defaults.md` CLD层

---

## 提取策略

**Phase 1：一步提取**（实体+关系同时提取）

Prompt 核心要素：
- 角色定义："你是{perspective}专家"
- 任务定义：提取因果变量和关系
- 输出格式：JSON Schema（不变量I-2强制）
- Few-shot示例：3个（正例、负例、复杂例）

**Phase 2：两步提取**（先实体后关系，参考GraphRAG）

```
Step 1: 实体识别
  "从文档中识别与{domain}相关的关键变量"
  → 变量列表

Step 2: 因果连接识别
  "基于变量列表，找出因果关系"
  → CausalLink[]
```

---

## Prompt 模板（Phase 1）

```python
CLD_EXTRACTION_PROMPT = """
你是{perspective}专家。从以下文档中提取因果变量和它们之间的因果关系。

对于每个因果关系，输出：
- source: 原因变量（具体名词短语，2-5个词）
- target: 结果变量（具体名词短语，2-5个词）
- polarity: "+"（促进）或 "-"（抑制）
- evidence: 原文引用片段

规则：
1. 变量必须是具体名词短语，排除抽象概念
2. 优先选择可量化或明确可观测的变量
3. evidence 必须包含原文引用
4. 只输出 JSON 数组

示例：
[
  {{"source": "政府住房补贴", "target": "房价", "polarity": "+", "evidence": "政府补贴增加了购房需求，推动房价上涨 (p.12)"}},
  {{"source": "利率上升", "target": "购房需求", "polarity": "-", "evidence": "利率上升抑制了购房意愿 (p.8)"}}
]
"""
```

---

## 变量标准化

- **时机**：提取后统一标准化（Conductor层），不在Agent内部
- **原因**：避免Agent间标准不一致
- **方式**：节点归并器处理（见 `cld-node-merging.md`）

---

## 已决策事项

| 决策 | 结论 | 来源 |
|------|------|------|
| 分步vs一步提取 | Phase 1一步，Phase 2两步 | D9 |
| 置信度字段 | Phase 1不收集 | D23 |
| Few-shot示例数 | 3个 | D9 |
| 变量标准化时机 | 提取后统一标准化 | D9 |

---

*整合自 issue-15-sub_docs: 09-cld-extraction-prompt.md*
