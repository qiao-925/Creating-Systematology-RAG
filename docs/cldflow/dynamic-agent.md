# 动态视角Agent生成机制

> 架构概览见：`docs/CLDFlow-architecture.md` CLD层

---

## 核心思路

固定视角（政策/经济/社会）无法覆盖所有问题类型。Conductor根据问题特征动态生成3-5个Specialist Agent。

---

## Phase 1：预定义模板 + LLM优化

```python
TEMPLATES = {
    "policy": {"role": "政策分析师", "focus": ["法规", "政策工具", "政府行为"]},
    "economic": {"role": "经济分析师", "focus": ["市场机制", "价格", "供需"]},
    "social": {"role": "社会分析师", "focus": ["居民行为", "社会效应", "公平性"]},
    "legal": {"role": "法律分析师", "focus": ["法规约束", "合规性", "权利义务"]},
    "technical": {"role": "技术分析师", "focus": ["技术可行性", "基础设施", "创新"]},
}
```

Conductor：
1. 用LLM识别问题需要的领域
2. 加载对应模板
3. 用LLM细化每个模板（关注焦点、检索策略）

---

## Phase 2：完全动态生成

Conductor直接让LLM生成视角清单，无需模板。

---

## 视角数量

| 问题复杂度 | 视角数量 | 硬上限 |
|-----------|---------|--------|
| 简单 | 2-3 | 5 |
| 中等 | 3-4 | 5 |
| 复杂 | 4-5 | 5 |

---

## Specialist Agent Prompt 模板

```python
def generate_specialist_prompt(perspective, question):
    return f"""你是{perspective['role']}，专精于{perspective['domain']}。

任务：从研究材料中提取与以下问题相关的因果关系：
"{question}"

关注领域：{', '.join(perspective['focus_areas'])}

输出格式：CausalLink JSON数组
- source: 原因变量
- target: 结果变量
- polarity: "+" 或 "-"
- evidence: 原文引用

你不需要考虑专业领域外的视角，其他专家会覆盖那些方面。"""
```

---

## 学术参考

| 来源 | 核心发现 | 对CLDFlow的启示 |
|------|---------|-----------------|
| PersonaFlow (arXiv 2409.12538) | 用户自定义专家画像提升自主感 | 让Conductor可定义专家类型 |
| PRISM (arXiv 2603.18507) | 生成型任务适合专家角色，判别型不适合 | CLD提取=生成型，用专家角色；融合=判别型，减少角色干扰 |
| Agentic Leash (arXiv 2601.00097) | 单Agent即可提取FCM | 验证可行性，但缺多视角架构 |

---

*整合自 issue-15-sub_docs: 06-dynamic-agent.md*
