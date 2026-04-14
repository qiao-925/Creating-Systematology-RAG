# CLD层 - 冲突检测与消解设计

> 架构概览见：`docs/CLDFlow-architecture.md` CLD层
> 默认参数见：`docs/CLDFlow-defaults.md` CLD层

---

## 冲突类型

| 类型 | 定义 | 示例 |
|------|------|------|
| 极性冲突 | 同一因果对，不同极性 | A说"补贴→房价(+)"，B说"补贴→房价(-)" |
| 方向冲突 | 因果关系方向相反 | A说"税收→房价"，B说"房价→税收" |
| 遗漏冲突 | 仅一个Agent识别某因果对 | 仅政策Agent提到 |

---

## 分歧度计算

```python
def calculate_disagreement(links):
    """
    返回 0-1 的分歧度
    0 = 完全一致，1 = 完全对立
    """
    total = len(links)
    if total <= 1:
        return 0
    plus_count = sum(1 for l in links if l['polarity'] == '+')
    minus_count = total - plus_count
    disagreement = 1 - abs(plus_count - minus_count) / total
    return disagreement
```

| Agent分布 | 分歧度 | 含义 |
|-----------|--------|------|
| 3:0 | 0 | 无分歧 |
| 3:1 | 0.5 | 中等分歧 |
| 2:2 | 1.0 | 完全分歧 |

---

## 消解策略

| 分歧度 | 处理方式 | 置信度标记 |
|--------|----------|-----------|
| 0 | 直接采纳 | high |
| <0.3 | 多数投票 | high |
| 0.3-0.5 | 加权平均+标记 | medium |
| >0.5 | 裁判Agent评审 | low |

### 裁判Agent

- 触发条件：分歧度 > 0.5
- 机制：元投票评审（阅读所有Agent的证据，选择最合理结论）
- 成本：+$0.01-0.05/次
- 不变量I-4：无人工介入，裁判Agent自动消解

### 方向冲突

标记为**反馈环**（双向关系），这是系统动力学常见模式，不强制选单向。

---

## 代码骨架

```python
class ConflictDetector:
    def __init__(self, thresholds=(0.3, 0.5)):
        self.low_threshold, self.high_threshold = thresholds

    def detect(self, merged_links):
        grouped = self._group_by_node_pair(merged_links)
        conflicts, resolved = [], []
        for pair, links in grouped.items():
            disagreement = self._calculate_disagreement(links)
            if disagreement == 0:
                resolved.append(self._adopt(links))
            elif disagreement < self.low_threshold:
                resolved.append(self._majority_vote(links))
            elif disagreement < self.high_threshold:
                resolved.append(self._weighted_average(links))
            else:
                conflicts.append(self._refer_to_judge(links, disagreement))
        return {"conflicts": conflicts, "resolved": resolved}
```

---

## 已决策事项

| 决策 | 结论 | 来源 |
|------|------|------|
| 消解策略 | 多数投票为主，平局送裁判 | D6 |
| 分歧度阈值 | 低<0.3 / 中0.3-0.5 / 高>0.5 | D6 |
| Agent可信度 | Phase 1不考虑（所有Agent平等） | D6 |
| 方向冲突 | 标记为反馈环 | D6 |

---

*整合自 issue-15-sub_docs: 11-cld-conflict-resolution.md*
