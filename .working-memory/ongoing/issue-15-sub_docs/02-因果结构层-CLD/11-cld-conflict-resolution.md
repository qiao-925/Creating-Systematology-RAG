# 因果层 - 冲突检测与消解算法调研

## 核心问题

多视角 Agent 提取的因果链可能存在冲突（同一对节点，不同 Agent 给出相反极性，或不同证据），如何检测、量化分歧度，并设计消解策略。

---

## 冲突类型定义

| 类型 | 定义 | 示例 |
|------|------|------|
| **极性冲突** | 同一因果对，不同极性 | A说"补贴→房价(+)"，B说"补贴→房价(-)" |
| **方向冲突** | 因果关系方向相反 | A说"税收→房价"，B说"房价→税收" |
| **证据冲突** | 相同结论，但证据矛盾 | 同一文献，不同解读 |
| **遗漏冲突** | 某 Agent 完全未识别某因果对 | 仅一个 Agent 提到 |

---

## 备选方案对比

### 冲突检测方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **A: 精确匹配** | 节点名完全一致才算同一对 | 简单，无歧义 | 错过表述不同但概念同的冲突 |
| **B: 语义匹配** | 用 Embedding 相似度判断同一对 | 覆盖表述差异 | 需要归并前置，复杂度增加 |
| **C: 图匹配** | 在子图层面检测结构冲突 | 发现复杂模式冲突 | 计算成本高 |

### 冲突消解方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **A: 多数投票** | 取最多 Agent 支持的结论 | 简单民主 | 可能 2:2 平局 |
| **B: 加权投票** | 按 Agent 置信度/专业性加权 | 考虑质量差异 | 需要可信权重 |
| **C: 置信度阈值** | 仅当某方置信度显著高于其他时采用 | 避免勉强决策 | 需要校准置信度 |
| **D: 标记待审核** | 冲突不消解，全部标记人工介入 | 保证准确性 | 人工负担重 |
| **E: 证据质量评分** | 评估原文证据的可靠性 | 基于内容而非数量 | 需要证据解析模型 |

---

## 学术/工业界实践

### 1. 多智能体共识算法

**Borda Count（投票理论）**：
- 每个 Agent 对候选结论排序
- 计算 Borda 分数（排名权重）
- 选最高分的结论

**适用于**：多个可能因果解释竞争时

### 2. 置信度聚合

**Dempster-Shafer 证据理论**：
- 处理不确定性和部分证据
- 合并多源证据的置信度
- 识别"未知"状态（证据不足）

**简单实现（加权平均）**：
```python
def aggregate_polarity(links):
    # links: [{agent, polarity, confidence}, ...]
    weighted_sum = sum(
        (1 if l['polarity'] == '+' else -1) * l['confidence']
        for l in links
    )
    
    if abs(weighted_sum) > threshold:
        return '+' if weighted_sum > 0 else '-'
    else:
        return 'uncertain'  # 标记待审核
```

### 3. 系统动力学领域实践

**Group Model Building (GMB)**：
- 利益相关者共同构建 CLD
- 冲突通过"讨论-澄清-共识"消解
- 关键：可视化共享模型，让分歧显性化

**对 CLDFlow 的启示**：
- 冲突不应自动消解，而应呈现给用户
- 提供"冲突地图"帮助理解分歧

### 4. 众包真理发现（Truth Discovery）

**算法**：
- EM 算法估计源可信度和事实真实性
- 迭代优化：可信度高的源，其观点权重更大

**应用**：
- 多 Agent 可信度随任务历史积累
- 新 Agent 默认中等可信度，随表现调整

---

## 推荐方案

### Phase 1 简化策略

**冲突检测流程**：
```
1. 节点归并（前置步骤）
   └── 将表述不同的同一概念归并

2. 分组（按节点对分组）
   └── 收集所有提到 (A→B) 的因果链

3. 冲突识别
   ├── 极性冲突：组内有 '+' 和 '-'
   ├── 方向冲突：组内同时有 (A→B) 和 (B→A)
   └── 遗漏冲突：仅一个 Agent 提到

4. 分歧度量化
   └── 计算极性分歧度 = |#(+) - #(-)| / 总数

5. 决策
   ├── 无冲突 → 直接采纳
   ├── 轻微分歧（<0.3）→ 多数投票
   └── 严重分歧（≥0.3）→ 标记待审核
```

**分歧度计算公式**：
```python
def calculate_disagreement(links):
    """
    links: [{agent, polarity}, ...]
    返回 0-1 的分歧度，0 表示完全一致，1 表示完全对立
    """
    total = len(links)
    if total <= 1:
        return 0  # 无冲突
    
    plus_count = sum(1 for l in links if l['polarity'] == '+')
    minus_count = total - plus_count
    
    # 分歧度 = 1 - |#(+) - #(-)| / 总数
    # 2:2 → 分歧度 = 1 - 0/4 = 1（完全分歧）
    # 3:1 → 分歧度 = 1 - 2/4 = 0.5（中等分歧）
    # 4:0 → 分歧度 = 1 - 4/4 = 0（无分歧）
    disagreement = 1 - abs(plus_count - minus_count) / total
    
    return disagreement
```

**决策矩阵**：
| 分歧度 | Agent 分布 | 决策 |
|--------|------------|------|
| 0 | 全一致 | 直接采纳 |
| 0.0-0.3 | 3:1, 4:1 | 多数投票 |
| 0.3-0.5 | 2:2, 3:2 | 加权投票（如有置信度）或标记 |
| >0.5 | 严重对立 | 标记待审核，强制人工介入 |

### 输出格式

```json
{
  "conflicts": [
    {
      "node_pair": ["政府补贴", "房价"],
      "conflict_type": "polarity",
      "agent_opinions": [
        {"agent": "policy", "polarity": "+", "evidence": "...", "confidence": 0.9},
        {"agent": "economic", "polarity": "-", "evidence": "...", "confidence": 0.7}
      ],
      "disagreement_score": 1.0,
      "resolution": "pending_review",
      "suggested_action": "人工判断补贴对房价的净效应"
    }
  ],
  "resolved": [
    {
      "node_pair": ["利率", "购房需求"],
      "final_polarity": "-",
      "resolution_method": "majority_vote",
      "supporting_agents": ["economic", "social"],
      "disagreement_score": 0.0
    }
  ]
}
```

---

## 待决策事项

1. **冲突消解策略优先级**
   - 选项 A：多数投票为主，平局标记
   - 选项 B：总是标记人工（最保守）
   - 选项 C：引入置信度加权（需要 Agent 自评）
   - **建议**：Phase 1 选 A，简单可预期

2. **分歧度阈值**
   - 轻微/严重分界线：0.3 vs 0.5 vs 其他
   - **建议**：0.3 为标记阈值，实验验证

3. **是否引入 Agent 可信度**
   - 选项 A：Phase 1 不考虑（所有 Agent 平等）
   - 选项 B：简单历史准确率加权
   - **建议**：Phase 1 选 A，避免过度设计

4. **方向冲突处理**
   - 选项 A：标记为"反馈环"（双向关系）
   - 选项 B：强制选择单向（按多数或置信度）
   - 选项 C：标记人工介入
   - **建议**：反馈环是系统动力学常见模式，选 A

---

## 实现要点

**代码结构草案**：
```python
class ConflictDetector:
    def __init__(self, disagreement_threshold=0.3):
        self.threshold = disagreement_threshold
    
    def detect_conflicts(self, merged_links):
        """
        输入：归并后的因果链列表
        输出：冲突报告 + 消解建议
        """
        conflicts = []
        resolved = []
        
        # 按节点对分组
        grouped = self._group_by_node_pair(merged_links)
        
        for pair, links in grouped.items():
            disagreement = self._calculate_disagreement(links)
            
            if disagreement == 0:
                # 无冲突
                resolved.append(self._create_resolved_record(links))
            elif disagreement < self.threshold:
                # 轻微分歧，多数投票
                resolved.append(self._majority_vote(links))
            else:
                # 严重分歧，标记
                conflicts.append(self._create_conflict_record(links, disagreement))
        
        return {"conflicts": conflicts, "resolved": resolved}
    
    def _calculate_disagreement(self, links):
        # 见上文公式
        pass
    
    def _majority_vote(self, links):
        # 简单多数投票
        pass
```

---

## 下一步

等待用户决策以上 4 个事项，确认后产出完整实现代码。
