# 模糊层 - 多专家权重聚合算法调研

## 核心问题

多 Agent（专家）对同一因果关系给出不同权重，如何聚合成单一权重矩阵供 FCM 仿真使用。

---

## 备选方案对比

### 方案 A：简单平均（推荐 Phase 1）

```python
weights = [w1, w2, w3]
final_weight = np.mean(weights)
```

**优点**：简单，公平，易于解释
**缺点**：不考虑专家可信度差异，异常值影响大

### 方案 B：加权平均（需可信度）

```python
# 每个专家有可信度 c_i
final_weight = sum(c_i * w_i) / sum(c_i)
```

**可信度来源**：
- 历史准确率（需要积累数据）
- 领域匹配度（Prompt 中自评）
- 证据质量（证据长度、来源权威性）

**缺点**：Phase 1 无历史数据，可信度难以客观估计

### 方案 C：中位数聚合（稳健）

```python
final_weight = np.median(weights)
```

**优点**：对异常值不敏感
**缺点**：丢失分布信息，极端意见被忽略

### 方案 D：贝叶斯聚合（推荐 Phase 2）

**原理**：
- 每个专家意见是带噪声的观测
- 先验：Uniform(-1, 1)
- 后验：基于观测更新

**输出**：权重分布而非点估计

**复杂度**：高，需要采样或解析解

### 方案 E：模糊数聚合（保留不确定性）

**方法**：
- 每个权重是三角模糊数 (a, b, c)
- 聚合：模糊数平均
- 输出：模糊权重，表达不确定性

---

## 学术/工业界实践

### 1. ExpertFcm 库中的聚合

**实现**：
```python
from expert_fcm import ExpertFcmAggregator

aggregator = ExpertFcmAggregator(method='mean')
# 或 'weighted_mean', 'median', 'fuzzy'

result = aggregator.aggregate(expert_opinions)
```

**方法对比**：
| 方法 | 适用场景 | 优点 |
|------|----------|------|
| mean | 专家水平相近 | 简单公平 |
| weighted_mean | 专家可信度不同 | 重视高可信专家 |
| median | 有极端值 | 稳健 |
| fuzzy | 需要不确定性 | 保留完整信息 |

### 2. 德尔菲法（Delphi Method）

**经典共识构建方法**：
1. 多轮匿名问卷
2. 每轮后分享统计结果（中位数、四分位数）
3. 专家根据群体意见调整
4. 收敛至共识

**对 CLDFlow 的启示**：
- 我们是一次性提取，无多轮反馈
- 但可借鉴"统计摘要+人工介入"模式

### 3. 证据推理（Dempster-Shafer）

**处理不确定性**：
- 每个证据有基本概率分配（BPA）
- Dempster 组合规则合并证据
- 输出：信度函数（Belief）和似真函数（Plausibility）

**优点**：数学严谨，处理"不知道"
**缺点**：计算复杂，解释难度大

---

## 分歧度量化

### 指标定义

```python
def calculate_divergence(weights: List[float]) -> Dict:
    """
    计算专家意见分歧度
    """
    n = len(weights)
    if n <= 1:
        return {"divergence": 0, "recommendation": "adopt"}
    
    mean_w = np.mean(weights)
    std_w = np.std(weights)
    range_w = max(weights) - min(weights)
    
    # 变异系数（相对分歧）
    cv = std_w / (abs(mean_w) + 1e-6)
    
    # 极性分歧（正负相反）
    signs = [np.sign(w) for w in weights]
    polarity_agreement = max(signs.count(1), signs.count(-1), signs.count(0)) / n
    
    return {
        "mean": mean_w,
        "std": std_w,
        "range": range_w,
        "cv": cv,  # 变异系数
        "polarity_agreement": polarity_agreement,  # 极性一致度
        "divergence_score": (1 - polarity_agreement) * 0.7 + min(cv, 1.0) * 0.3,
        "recommendation": _recommend_by_divergence((1 - polarity_agreement) * 0.7 + min(cv, 1.0) * 0.3)
    }

def _recommend_by_divergence(score):
    if score < 0.3:
        return "low_divergence_auto_adopt"
    elif score < 0.6:
        return "medium_divergence_aggregate"
    else:
        return "high_divergence_review"
```

### 分歧度分级

| 分值 | 级别 | 处理建议 |
|------|------|----------|
| 0-0.3 | 低分歧 | 自动聚合采纳 |
| 0.3-0.6 | 中等分歧 | 聚合但标记 |
| 0.6-1.0 | 高分歧 | 强制人工介入 |

---

## 推荐方案

### Phase 1 MVP：简单平均 + 分歧度标记

```python
class WeightAggregator:
    def __init__(self, divergence_threshold=0.5):
        self.threshold = divergence_threshold
    
    def aggregate(
        self,
        opinions: List[Dict]  # [{agent, label, weight}, ...]
    ) -> Dict:
        """
        聚合多专家权重
        """
        weights = [op['weight'] for op in opinions]
        
        # 1. 计算分歧度
        divergence = self._calculate_divergence(weights)
        
        # 2. 聚合
        final_weight = np.mean(weights)
        
        # 3. 决策
        if divergence['divergence_score'] < 0.3:
            status = 'confirmed'
            action = 'auto_adopt'
        elif divergence['divergence_score'] < self.threshold:
            status = 'confirmed_with_note'
            action = 'aggregate_with_warning'
        else:
            status = 'conflicted'
            action = 'needs_review'
            final_weight = None  # 不确定
        
        return {
            "final_weight": final_weight,
            "aggregation_method": "mean",
            "divergence": divergence,
            "source_opinions": opinions,
            "status": status,
            "action": action
        }
```

### Phase 2 升级：可信度加权

**可信度来源（逐步积累）**：
```python
@dataclass
class AgentCredibility:
    agent_id: str
    overall_score: float  # 0-1，综合可信度
    
    # 分解维度
    domain_match: float      # 领域匹配度
    historical_accuracy: float  # 历史准确率（需积累）
    evidence_quality: float     # 证据质量
    consistency: float          # 内部一致性

class CredibilityWeightedAggregator:
    def aggregate(self, opinions: List[Dict], credibilities: Dict[str, float]):
        """按可信度加权聚合"""
        
        total_credibility = 0
        weighted_sum = 0
        
        for op in opinions:
            agent = op['agent']
            credibility = credibilities.get(agent, 0.5)  # 默认 0.5
            
            weighted_sum += op['weight'] * credibility
            total_credibility += credibility
        
        return weighted_sum / total_credibility
```

---

## 输出格式

```json
{
  "aggregation": {
    "edge": "政府住房补贴 → 房价",
    "final_weight": 0.6,
    "uncertainty_range": [0.3, 0.9],
    "aggregation_method": "mean",
    "divergence": {
      "mean": 0.6,
      "std": 0.28,
      "cv": 0.47,
      "polarity_agreement": 1.0,
      "divergence_score": 0.14,
      "recommendation": "low_divergence_auto_adopt"
    },
    "source_opinions": [
      {"agent": "policy", "label": "+H", "weight": 0.7, "evidence": "..."},
      {"agent": "economic", "label": "+M", "weight": 0.5, "evidence": "..."},
      {"agent": "social", "label": "+H", "weight": 0.7, "evidence": "..."}
    ],
    "status": "confirmed",
    "action": "auto_adopt"
  }
}
```

---

## 待决策事项

1. **聚合算法**
   - 选项 A：简单平均 **推荐**
   - 选项 B：中位数
   - 选项 C：加权平均（需可信度）
   - **建议**：A，Phase 2 考虑 C

2. **分歧度阈值**
   - 低/中分界线：0.3 vs 0.4
   - 中/高分界线：0.5 vs 0.6
   - **建议**：0.3 / 0.5

3. **是否强制分歧度高的不聚合**
   - 选项 A：强制人工介入（严格）
   - 选项 B：聚合但高亮警告（宽松）**推荐**
   - **建议**：B，不阻塞流程

4. **是否记录历史可信度**
   - 选项 A：Phase 1 就记录，为 Phase 2 准备
   - 选项 B：Phase 1 不记录，简化
   - **建议**：A，数据结构预留字段即可，不强制要求

---

## 代码模板

```python
from dataclasses import dataclass
from typing import List, Dict, Literal
import numpy as np

@dataclass
class ExpertOpinion:
    agent_id: str
    weight: float  # -1 到 +1
    label: str     # 如 "+H"
    evidence: str
    confidence: float = 0.5  # 自评置信度，可选

class WeightAggregator:
    """专家权重聚合器"""
    
    def __init__(
        self,
        method: Literal["mean", "median", "weighted"] = "mean",
        low_threshold: float = 0.3,
        high_threshold: float = 0.5
    ):
        self.method = method
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
    
    def aggregate(self, opinions: List[ExpertOpinion]) -> Dict:
        weights = [op.weight for op in opinions]
        
        # 聚合
        if self.method == "mean":
            final = np.mean(weights)
        elif self.method == "median":
            final = np.median(weights)
        else:
            raise NotImplementedError("weighted method requires credibility")
        
        # 分歧度
        divergence = self._calculate_divergence(weights)
        
        # 决策
        if divergence['divergence_score'] < self.low_threshold:
            status = 'confirmed'
        elif divergence['divergence_score'] < self.high_threshold:
            status = 'confirmed_with_warning'
        else:
            status = 'high_divergence'
        
        return {
            "final_weight": final,
            "method": self.method,
            "divergence": divergence,
            "opinions": [
                {
                    "agent": op.agent_id,
                    "label": op.label,
                    "weight": op.weight,
                    "evidence_preview": op.evidence[:100]
                }
                for op in opinions
            ],
            "status": status
        }
    
    def _calculate_divergence(self, weights: List[float]) -> Dict:
        if len(weights) <= 1:
            return {"divergence_score": 0}
        
        mean_w = np.mean(weights)
        std_w = np.std(weights)
        cv = std_w / (abs(mean_w) + 1e-6)
        
        signs = [np.sign(w) for w in weights]
        polarity_agreement = max(
            signs.count(1), signs.count(-1), signs.count(0)
        ) / len(weights)
        
        score = (1 - polarity_agreement) * 0.7 + min(cv, 1.0) * 0.3
        
        return {
            "mean": mean_w,
            "std": std_w,
            "cv": cv,
            "polarity_agreement": polarity_agreement,
            "divergence_score": score
        }
```

---

## 下一步

等待用户阅读后决策 4 个事项。
