# 动力层 - 敏感性分析算法调研

## 核心问题

Phase 1 简化的 D2D 层（无完整 ODE+Monte Carlo），如何用敏感性分析识别杠杆点（高影响力节点），作为政策干预的优先候选。

---

## D2D 论文回顾

**Differential Dynamic Logic (D2D)** 核心思想：
- 通过差分方程描述系统演化
- 蒙特卡洛采样探索参数空间
- 识别"杠杆点"（Leverage Points）— 小投入大回报的干预位置

**问题**：论文无开源实现，ODE+Monte Carlo 计算成本高。

---

## Phase 1 简化方案

### 核心思路

用**敏感性分析**替代完整 ODE：
1. 对每个节点施加扰动（+10%）
2. 观察系统响应（稳态变化幅度）
3. 按影响力排序 → 杠杆点候选

### 算法流程

```
输入：FCM 权重矩阵 W，稳态初始值 S_0

对于每个节点 i:
    1. 施加扰动: S_0[i] *= 1.1  (+10%)
    2. 运行 FCM 仿真 → 新稳态 S_new
    3. 计算响应幅度: ||S_new - S_0||
    4. 记录节点 i 的影响力分数

按影响力分数排序 → 杠杆点列表
```

---

## 备选方案对比

### 方案 A：单节点扰动（推荐 Phase 1）

**方法**：
- 逐个节点施加固定幅度扰动
- 其他节点保持基线值
- 观察系统整体响应

**优点**：简单，可解释，计算快
**缺点**：未考虑组合效应（多个节点同时扰动）

### 方案 B：全局扰动 + 归因

**方法**：
- 同时扰动所有节点（随机或系统）
- 用统计方法归因各节点贡献
- 如：Shapley Value、偏相关系数

**优点**：考虑交互效应
**缺点**：复杂，计算成本高

### 方案 C：基于拓扑的重要性

**方法**：
- 不运行仿真，直接分析图结构
- 指标：度中心性、PageRank、中介中心性

**优点**：极快，无需数值计算
**缺点**：不考虑因果权重，可能误导

### 方案 D：梯度近似（Phase 2）

**方法**：
- 计算稳态对节点初值的梯度
- ∂S/∂S_0[i] 作为影响力度量

**优点**：数学严谨
**缺点**：需要可微分，FCM 有激活函数非线性

---

## 学术/工业界实践

### 1. 系统动力学敏感性分析

**方法**：
- **一阶敏感性**：单个参数变化的影响
- **二阶敏感性**：参数交互效应
- **全局敏感性**：参数分布整体影响（Sobol 指数）

**工具**：
- Vensim（系统动力学软件）
- Python SALib 库

### 2. FCM 敏感性分析

**典型方法**：
```python
def fcm_sensitivity_analysis(fcm, baseline_state):
    """
    基于 FCM 的敏感性分析
    """
    sensitivities = {}
    
    for node in fcm.nodes:
        # 施加 10% 扰动
        perturbed_init = baseline_state.copy()
        perturbed_init[node] *= 1.1
        
        # 重新仿真
        result = fcm.simulate(perturbed_init)
        
        # 计算影响
        impact = np.linalg.norm(result - baseline_state)
        sensitivities[node] = impact
    
    return sensitivities
```

### 3. 杠杆点识别框架（Meadows, 1999）

**12 类杠杆点**（从弱到强）：
1. 常数/参数
2. 缓冲区大小
3. 物质流/信息流
4. 反馈延迟
5. 负反馈回路
6. 正反馈回路
7. 信息流结构
8. 系统规则
9. 自组织能力
10. 系统目标
11. 心智模式
12. 范式超越

**对 CLDFlow 的启示**：
- 我们的 FCM 主要涉及 1-6 层（参数到反馈回路）
- 更高层杠杆点（规则、目标）需人工介入

---

## 推荐方案

### Phase 1 MVP：单节点扰动 + 影响力排序

```python
class LeveragePointAnalyzer:
    """杠杆点分析器（简化版）"""
    
    def __init__(self, fcm_simulator):
        self.sim = fcm_simulator
    
    def analyze(
        self,
        baseline_interventions: Dict[str, float] = None,
        perturbation_factor: float = 1.1,
        metric: str = "euclidean"
    ) -> List[Dict]:
        """
        识别杠杆点
        
        Returns: 按影响力排序的节点列表
        """
        # 1. 计算基准稳态
        baseline = self.sim.simulate(
            initial_state=np.zeros(self.sim.n),
            fixed_nodes=baseline_interventions
        )
        baseline_state = baseline['final_state']
        
        # 2. 对每个节点施加扰动
        leverage_scores = []
        
        for i, node in enumerate(self.sim.concepts):
            # 施加扰动
            perturbed_init = np.zeros(self.sim.n)
            perturbed_init[i] = perturbation_factor
            
            # 运行仿真
            result = self.sim.simulate(
                initial_state=perturbed_init,
                fixed_nodes=baseline_interventions
            )
            
            # 计算影响力
            if metric == "euclidean":
                impact = np.linalg.norm(result['final_state'] - baseline_state)
            elif metric == "max_change":
                impact = np.max(np.abs(result['final_state'] - baseline_state))
            elif metric == "average_change":
                impact = np.mean(np.abs(result['final_state'] - baseline_state))
            
            leverage_scores.append({
                "node": node,
                "node_idx": i,
                "impact_score": impact,
                "affected_nodes": self._get_top_affected(
                    result['final_state'] - baseline_state, n=3
                )
            })
        
        # 3. 排序
        leverage_scores.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return leverage_scores
    
    def _get_top_affected(self, diff, n=3):
        """获取受影响最大的 n 个节点"""
        abs_diff = np.abs(diff)
        top_indices = np.argsort(abs_diff)[-n:][::-1]
        return [
            {"node": self.sim.concepts[i], "change": diff[i]}
            for i in top_indices
        ]
```

### 输出格式

```json
{
  "leverage_points": [
    {
      "rank": 1,
      "node": "房贷利率",
      "impact_score": 2.34,
      "interpretation": "对利率施加 +10% 扰动，系统整体状态变化 2.34 个单位",
      "top_affected_nodes": [
        {"node": "购房需求", "change": -0.8},
        {"node": "房价", "change": -0.6},
        {"node": "建筑许可", "change": -0.4}
      ],
      "intervention_suggestion": "调整利率政策可能对住房市场产生广泛影响"
    },
    {
      "rank": 2,
      "node": "政府住房补贴",
      "impact_score": 1.89,
      ...
    }
  ],
  "analysis_parameters": {
    "perturbation_factor": 1.1,
    "metric": "euclidean",
    "baseline_interventions": null
  }
}
```

---

## 不确定区间传播

### 问题

FCM 权重有不确定区间（如 0.7±0.1），如何传播到杠杆点分析？

### 简化方案（Phase 1）

**不传播**，杠杆点分析基于点估计权重：
- 理由：敏感性分析本身是近似方法
- 不确定性在 FCM 层聚合时处理

### Phase 2 升级

**多次采样**：
```python
def robust_leverage_analysis(fcm, n_samples=100):
    """
    考虑权重不确定性的鲁棒杠杆点分析
    """
    all_results = []
    
    for _ in range(n_samples):
        # 从权重区间采样
        sampled_weights = sample_weights_from_intervals(fcm.weight_intervals)
        fcm.set_weights(sampled_weights)
        
        # 运行杠杆点分析
        result = analyze_leverage_points(fcm)
        all_results.append(result)
    
    # 统计：哪些节点在多次采样中都是高杠杆点
    consistency = calculate_consistency(all_results)
    
    return {
        "robust_leverage_points": [
            node for node, score in consistency.items()
            if score > 0.8  # 80% 采样中都是高杠杆点
        ]
    }
```

---

## 与 Meadows 杠杆点框架的结合

### 分类输出

```python
def classify_leverage_type(node, fcm_graph):
    """
    根据图结构分类杠杆点类型
    """
    in_degree = fcm_graph.in_degree(node)
    out_degree = fcm_graph.out_degree(node)
    
    if out_degree > 5 and in_degree < 2:
        return "high_out_degree", "Type 6: 正反馈回路驱动者"
    elif in_degree > 5:
        return "high_in_degree", "Type 5: 负反馈回路核心"
    elif nx.betweenness_centrality(fcm_graph)[node] > 0.3:
        return "high_betweenness", "Type 7: 信息流枢纽"
    else:
        return "parameter", "Type 1-2: 参数/缓冲区"
```

---

## 待决策事项

1. **扰动幅度**
   - 选项 A：固定 +10%（推荐）
   - 选项 B：按比例（大值小扰动，小值大扰动）
   - 选项 C：多幅度测试（10%, 20%, 50%）
   - **建议**：A，简单可预期

2. **影响力度量方式**
   - 选项 A：欧几里得范数（整体变化）**推荐**
   - 选项 B：最大单节点变化
   - 选项 C：平均变化
   - **建议**：A，综合反映系统影响

3. **是否考虑组合扰动**
   - 选项 A：不考虑（Phase 1）**推荐**
   - 选项 B：考虑两两组合（复杂度高）
   - **建议**：A，留给 Phase 2

4. **不确定性是否传播**
   - 选项 A：不传播（点估计）**推荐**
   - 选项 B：多次采样统计
   - **建议**：A，简化

5. **是否结合拓扑分析**
   - 选项 A：纯数值敏感性（推荐）
   - 选项 B：数值 + 拓扑中心性混合
   - **建议**：A，拓扑分析单独做可选补充

---

## 代码模板

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

@dataclass
class LeveragePoint:
    rank: int
    node: str
    impact_score: float
    affected_nodes: List[Dict]
    leverage_type: str

class LeverageAnalyzer:
    """杠杆点分析器"""
    
    def __init__(
        self,
        fcm_simulator,
        perturbation_factor: float = 1.1,
        metric: str = "euclidean"
    ):
        self.sim = fcm_simulator
        self.perturbation = perturbation_factor
        self.metric = metric
    
    def find_leverage_points(
        self,
        baseline_interventions: Optional[Dict] = None,
        top_n: int = 10
    ) -> List[LeveragePoint]:
        """识别前 N 个杠杆点"""
        
        # 基准稳态
        baseline = self._get_baseline(baseline_interventions)
        
        # 逐个扰动
        scores = []
        for i, node in enumerate(self.sim.concepts):
            score = self._calculate_impact(i, baseline, baseline_interventions)
            scores.append((node, i, score))
        
        # 排序
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # 构造结果
        results = []
        for rank, (node, idx, score) in enumerate(scores[:top_n], 1):
            affected = self._get_affected_nodes(idx, baseline, baseline_interventions)
            lever_type = self._classify_type(node)
            
            results.append(LeveragePoint(
                rank=rank,
                node=node,
                impact_score=score,
                affected_nodes=affected,
                leverage_type=lever_type
            ))
        
        return results
    
    def _get_baseline(self, interventions):
        result = self.sim.simulate(
            initial_state=np.zeros(self.sim.n),
            fixed_nodes=interventions
        )
        return result['final_state']
    
    def _calculate_impact(self, node_idx, baseline, interventions):
        perturbed = np.zeros(self.sim.n)
        perturbed[node_idx] = self.perturbation
        
        result = self.sim.simulate(
            initial_state=perturbed,
            fixed_nodes=interventions
        )
        
        diff = result['final_state'] - baseline
        
        if self.metric == "euclidean":
            return np.linalg.norm(diff)
        elif self.metric == "max":
            return np.max(np.abs(diff))
        else:
            return np.mean(np.abs(diff))
```

---

## 下一步

等待用户阅读后决策 5 个事项。
