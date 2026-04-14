# 动力层 - 不确定区间计算调研

## 核心问题

如何将多 Agent 权重分歧（如政策 Agent 说 +H，经济 Agent 说 +M）量化为置信度区间，并在杠杆点排序中体现不确定性的影响。

---

## 不确定性来源

| 来源 | 描述 | 量化方式 |
|------|------|----------|
| **Agent 分歧** | 不同视角给出不同权重 | 权重分布范围 |
| **语言标签粒度** | +H 转换为 0.7±0.1 | 映射表自带区间 |
| **证据质量** | 原文引用强弱 | 证据置信度 |
| **模型简化** | Phase 1 简化假设 | 保守估计区间 |

---

## 备选方案对比

### 方案 A：极值区间（推荐 Phase 1）

**方法**：
- 取所有 Agent 意见的最小值和最大值
- 输出区间：[min, max]

**示例**：
```
政策 Agent: +H (0.7)
经济 Agent: +M (0.5)
社会 Agent: +H (0.7)

→ 区间: [0.5, 0.7]
→ 点估计: 0.6 (均值)
→ 不确定半径: 0.1
```

**优点**：简单直观，覆盖所有可能
**缺点**：对异常值敏感

### 方案 B：标准差区间

**方法**：
- 计算 Agent 权重的均值和标准差
- 区间：均值 ± 1.96×标准差（95% 置信）

**示例**：
```
意见: [0.9, 0.7, 0.5, 0.7]
均值: 0.7
标准差: 0.158
→ 区间: [0.39, 1.01] → 截断到 [0.39, 1.0]
```

**优点**：统计严谨
**缺点**：假设正态分布，小样本不准确

### 方案 C：分位数区间

**方法**：
- 取 5% 和 95% 分位数
- 不受异常值影响

**示例**：
```
意见排序: [0.5, 0.7, 0.7, 0.9]
5% 分位: 0.5 (或插值)
95% 分位: 0.9
→ 区间: [0.5, 0.9]
```

### 方案 D：贝叶斯可信区间（推荐 Phase 2）

**方法**：
- 贝叶斯推断得到后验分布
- 输出 95% 可信区间

**优点**：最严谨的区间估计
**缺点**：计算复杂，需要选择先验

---

## 学术/工业界实践

### 1. 模糊数方法（FCM 传统）

**三角模糊数**：
```
每个权重 = (下界, 最可能值, 上界)

聚合：模糊数平均
结果 = (平均下界, 平均最可能, 平均上界)
```

**应用**：
- Papageorgiou 等人的 FCM 工作
- 保留语言描述的直觉性

### 2. 概率区间方法

**置信区间**：
- 基于样本统计量
- 假设某种分布（正态、Beta 等）

**Bootstrap 方法**：
- 重采样估计区间
- 不依赖分布假设

### 3. 专家系统不确定性

**Dempster-Shafer 证据理论**：
- 信度函数 Bel(A)：下限
- 似真函数 Pl(A)：上限
- 区间 [Bel, Pl] 表示不确定性

### 4. 敏感性分析中的不确定性传播

**方法**：
```python
def uncertainty_propagation(weight_intervals, n_samples=1000):
    """
    蒙特卡洛传播权重不确定性
    """
    results = []
    
    for _ in range(n_samples):
        # 从每个区间均匀采样
        sampled_weights = [
            np.random.uniform(low, high)
            for low, high in weight_intervals
        ]
        
        # 运行 D2D 分析
        leverage_points = analyze(sampled_weights)
        results.append(leverage_points)
    
    # 统计每个杠杆点的稳定性
    return aggregate_statistics(results)
```

---

## 推荐方案

### Phase 1 MVP：极值区间 + 稳定性标记

```python
class UncertaintyCalculator:
    """不确定性计算器"""
    
    def calculate_interval(self, opinions: List[Dict]) -> Dict:
        """
        计算权重不确定区间
        
        opinions: [{agent, weight, label}, ...]
        """
        weights = [op['weight'] for op in opinions]
        
        # 极值区间
        lower = min(weights)
        upper = max(weights)
        point = np.mean(weights)
        
        # 分歧度
        span = upper - lower
        
        # 一致性判断
        if span < 0.2:
            consistency = "high"
            recommendation = "reliable"
        elif span < 0.5:
            consistency = "medium"
            recommendation = "use_with_caution"
        else:
            consistency = "low"
            recommendation = "needs_review"
        
        return {
            "interval": [lower, upper],
            "point_estimate": point,
            "span": span,
            "consistency": consistency,
            "recommendation": recommendation,
            "source_opinions": [
                {"agent": op['agent'], "weight": op['weight']}
                for op in opinions
            ]
        }
```

### 杠杆点不确定性传播（简化）

**不传播到排序**，而是事后标记：
```python
def analyze_leverage_with_uncertainty(
    leverage_points,
    weight_uncertainties
):
    """
    杠杆点排序 + 不确定性标记
    """
    results = []
    
    for lp in leverage_points:
        node = lp['node']
        
        # 检查该节点相关边的权重不确定性
        related_edges = get_edges_incident_to(node)
        
        avg_uncertainty = np.mean([
            weight_uncertainties[edge]['span']
            for edge in related_edges
        ])
        
        # 综合得分 = 影响力 / (1 + 不确定性)
        # 不确定性高的杠杆点降级
        adjusted_score = lp['impact_score'] / (1 + avg_uncertainty)
        
        results.append({
            **lp,
            "uncertainty_penalty": avg_uncertainty,
            "adjusted_score": adjusted_score,
            "reliability": "high" if avg_uncertainty < 0.2 else "low"
        })
    
    # 按调整后得分重排序
    results.sort(key=lambda x: x['adjusted_score'], reverse=True)
    
    return results
```

### 输出格式

```json
{
  "leverage_points_with_uncertainty": [
    {
      "rank": 1,
      "node": "房贷利率",
      "impact_score": 2.34,
      "adjusted_score": 2.11,
      "uncertainty_analysis": {
        "related_edges": 3,
        "avg_weight_uncertainty": 0.11,
        "reliability": "high",
        "note": "各 Agent 对利率影响意见一致，置信度高"
      },
      "recommendation": "优先干预候选"
    },
    {
      "rank": 2,
      "node": "土地供应政策",
      "impact_score": 2.10,
      "adjusted_score": 1.40,
      "uncertainty_analysis": {
        "related_edges": 2,
        "avg_weight_uncertainty": 0.50,
        "reliability": "low",
        "note": "政策效果分歧大，经济 Agent 认为影响中等，社会 Agent 认为影响微弱"
      },
      "recommendation": "需谨慎，建议补充研究"
    }
  ]
}
```

---

## 可视化建议

### 杠杆点图表

```
影响力
   │
3.0├───── ◆ (利率)              ← 高影响+高置信
   │
2.5├───── ◇ (土地供应)          ← 高影响+低置信
   │
2.0├─────────── ▲ (补贴)
   │
1.5├──────────────── ■ (税收)
   │
   └──────┬──────┬──────┬──────┬→ 置信度
          0.0    0.2    0.4    0.6
          
图例: ◆ 高置信  ◇ 低置信
```

### 建议矩阵

| 影响力 | 高置信度 | 低置信度 |
|--------|----------|----------|
| **高** | ◆ 优先干预 | ◇ 需更多研究 |
| **中** | 可考虑 | 暂不推荐 |
| **低** | 忽略 | 忽略 |

---

## 待决策事项

1. **区间计算方法**
   - 选项 A：极值区间（简单）**推荐**
   - 选项 B：标准差区间
   - 选项 C：分位数区间
   - **建议**：A，Phase 1 简单直观

2. **不确定性是否影响排序**
   - 选项 A：调整得分（高不确定降级）**推荐**
   - 选项 B：仅标记，不调整排序
   - **建议**：A，避免高不确定杠杆点误导决策

3. **是否显示原始区间给用户**
   - 选项 A：显示（透明）**推荐**
   - 选项 B：仅显示可靠性等级
   - **建议**：A，可审计性要求

4. **低置信度阈值**
   - 区间跨度 > 0.5 视为低置信？
   - **建议**：0.5，经验值

---

## 代码模板

```python
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

@dataclass
class UncertainWeight:
    point_estimate: float
    interval: Tuple[float, float]
    span: float
    consistency: str  # high/medium/low

class UncertaintyManager:
    """不确定性管理器"""
    
    def __init__(self, low_threshold=0.2, high_threshold=0.5):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
    
    def calculate_weight_uncertainty(
        self,
        opinions: List[Tuple[str, float]]  # (agent, weight)
    ) -> UncertainWeight:
        """计算单个权重的不确定性"""
        
        weights = [w for _, w in opinions]
        
        lower = min(weights)
        upper = max(weights)
        point = np.mean(weights)
        span = upper - lower
        
        if span < self.low_threshold:
            consistency = "high"
        elif span < self.high_threshold:
            consistency = "medium"
        else:
            consistency = "low"
        
        return UncertainWeight(
            point_estimate=point,
            interval=(lower, upper),
            span=span,
            consistency=consistency
        )
    
    def adjust_leverage_for_uncertainty(
        self,
        leverage_score: float,
        related_uncertainties: List[float]
    ) -> Tuple[float, str]:
        """
        根据不确定性调整杠杆点得分
        
        Returns: (adjusted_score, reliability_label)
        """
        avg_uncertainty = np.mean(related_uncertainties)
        
        # 调整公式：原始得分 / (1 + 不确定性惩罚)
        adjusted = leverage_score / (1 + avg_uncertainty)
        
        if avg_uncertainty < 0.2:
            reliability = "high"
        elif avg_uncertainty < 0.5:
            reliability = "medium"
        else:
            reliability = "low"
        
        return adjusted, reliability
```

---

## 下一步

等待用户阅读后决策 4 个事项。
