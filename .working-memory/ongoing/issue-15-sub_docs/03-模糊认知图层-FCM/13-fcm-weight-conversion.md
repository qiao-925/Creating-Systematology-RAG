# 模糊层 - 语言权重到数值转换调研

## 核心问题

多 Agent 用自然语言描述的权重（如"Very High"）如何转换为数值（-1 到 +1），用于 FCM 计算，并量化不确定区间。

---

## 备选方案对比

### 方案 A：固定映射表（推荐 Phase 1）

| 语言标签 | 数值 | 区间（不确定性） |
|----------|------|------------------|
| +VH (Very High) | +0.9 | [0.8, 1.0] |
| +H (High) | +0.7 | [0.6, 0.8] |
| +M (Medium) | +0.5 | [0.4, 0.6] |
| +L (Low) | +0.3 | [0.2, 0.4] |
| +VL (Very Low) | +0.1 | [0.0, 0.2] |
| 0 (No effect) | 0.0 | [0.0, 0.0] |
| -VL | -0.1 | [-0.2, 0.0] |
| -L | -0.3 | [-0.4, -0.2] |
| -M | -0.5 | [-0.6, -0.4] |
| -H | -0.7 | [-0.8, -0.6] |
| -VH | -0.9 | [-1.0, -0.8] |

**优点**：简单，一致性好，易解释
**缺点**：粒度有限，无法表达细微差别

### 方案 B：LLM 直接输出数值

Prompt：
```
评估因果关系强度，输出 -1.0 到 +1.0 之间的数值。
-1.0 = 极强抑制, 0 = 无影响, +1.0 = 极强促进
```

**优点**：连续值，表达力强
**缺点**：LLM 校准差，不同运行偏差大

### 方案 C：混合方案（推荐 Phase 2）

1. LLM 先给语言标签（降低决策负担）
2. 映射为点估计值
3. Phase 2 引入贝叶斯，语言标签转为概率分布

---

## 学术/工业界实践

### 1. FCM 经典方法（Kosko, 1986）

**传统 FCM**：
- 权重 ∈ [-1, +1]
- 专家直接给出数值
- 无显式不确定性

**问题**：
- 专家难以直接给精确数值
- 不同专家数值标准不一致

### 2. 语言权重 + 模糊数（Papageorgiou, 2013）

**方法**：
- 专家用语言描述（Low, Medium, High）
- 映射为三角模糊数（Triangular Fuzzy Numbers）

**三角模糊数定义**：
```
Low = (0.0, 0.25, 0.5)      # 最小值, 最可能值, 最大值
Medium = (0.25, 0.5, 0.75)
High = (0.5, 0.75, 1.0)
```

**FCM 计算**：
- 使用模糊算术（扩展原理）
- 结果也是模糊数，表达不确定性

### 3. 贝叶斯 FCM（Recent Work, 2023-2024）

**核心思想**：
- 权重不是点估计，是概率分布
- 多专家权重聚合用贝叶斯推断
- 输出：后验分布 `N(μ, σ²)`

**Phase 1 简化**：
- 用语言标签作为离散先验
- 映射为区间而非完整分布

### 4. ExpertFcm 库实践

**实现方式**：
```python
from expert_fcm import FuzzyCognitiveMap

# 语言权重映射
linguistic_map = {
    'VH': 0.9, 'H': 0.7, 'M': 0.5, 'L': 0.3, 'VL': 0.1,
    'N': 0.0,
    '-VL': -0.1, '-L': -0.3, '-M': -0.5, '-H': -0.7, '-VH': -0.9
}

# 专家权重聚合
fcm = FuzzyCognitiveMap()
for expert_opinion in expert_opinions:
    fcm.add_edge(
        source, target,
        weight=linguistic_map[expert_opinion['label']],
        confidence=expert_opinion.get('confidence', 1.0)
    )
```

---

## 推荐方案

### Phase 1 MVP：固定映射表 + 简单区间

**映射表**：
```python
LINGUISTIC_WEIGHT_MAP = {
    '+VH': (0.9, 0.10),  # (点估计, 不确定半径)
    '+H':  (0.7, 0.10),
    '+M':  (0.5, 0.10),
    '+L':  (0.3, 0.10),
    '+VL': (0.1, 0.10),
    '0':   (0.0, 0.00),
    '-VL': (-0.1, 0.10),
    '-L':  (-0.3, 0.10),
    '-M':  (-0.5, 0.10),
    '-H':  (-0.7, 0.10),
    '-VH': (-0.9, 0.10),
}

def convert_to_weight(label: str) -> tuple[float, float]:
    """返回 (点估计, 不确定半径)"""
    return LINGUISTIC_WEIGHT_MAP.get(label, (0.0, 0.0))
```

**输出格式**：
```json
{
  "weight_matrix": {
    "政府住房补贴 → 房价": {
      "point_estimate": 0.7,
      "uncertainty_range": [0.6, 0.8],
      "source_opinions": [
        {"agent": "policy", "label": "+H", "confidence": 0.8},
        {"agent": "economic", "label": "+M", "confidence": 0.7}
      ]
    }
  }
}
```

### Phase 2 升级：贝叶斯聚合

**贝叶斯推断简化版**：
```python
# 多专家意见聚合为后验分布
# 假设每个专家意见是带噪声的观测
# 先验：Uniform(-1, 1)
# 似然：N(label_value, expert_confidence)

# 后验均值（加权平均）
weights = [opinion['confidence'] for opinion in opinions]
values = [linguistic_map[opinion['label']][0] for opinion in opinions]
posterior_mean = np.average(values, weights=weights)

# 后验方差（不确定性）
posterior_var = 1 / sum(w for w in weights)  # 简化计算
```

---

## Prompt 模板

### Agent 评级指令

```
你是 {perspective} 专家。请评估以下因果关系的强度：

{source} → {target}

证据：{evidence}

请从以下标签中选择：
+VH (极强促进), +H (强促进), +M (中等促进), +L (弱促进), +VL (极弱促进)
0 (无影响)
-VL, -L, -M, -H, -VH (抑制)

选择标准：
- +VH: 几乎必然导致显著增加
- +H: 很可能导致明显增加
- +M: 有一定概率导致增加
- +L: 轻微或间接的促进
- +VL: 极微弱的影响

只输出标签，不要有其他解释。
输出格式：+H
```

---

## 待决策事项

1. **语言标签粒度**
   - 选项 A：11 级（+VH 到 -VH，含 0）
   - 选项 B：7 级（去掉 VL）
   - **建议**：A，保留粒度，不增加复杂度

2. **不确定半径值**
   - 选项 A：固定 ±0.1（推荐，简单）
   - 选项 B：按级别变化（VH±0.1, M±0.15, VL±0.05）
   - **建议**：A，Phase 1 统一处理

3. **是否收集 Agent 置信度**
   - 选项 A：收集（增加 Prompt："同时给出置信度 0-1"）
   - 选项 B：不收集（所有意见等权重）
   - **建议**：B，Phase 1 简化，冲突检测阶段处理分歧

4. **区间表示方式**
   - 选项 A：[min, max]
   - 选项 B：点估计 ± 半径
   - **建议**：A，清晰直观

---

## 代码模板

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

class LinguisticLabel(Enum):
    PLUS_VH = "+VH"
    PLUS_H = "+H"
    PLUS_M = "+M"
    PLUS_L = "+L"
    PLUS_VL = "+VL"
    ZERO = "0"
    MINUS_VL = "-VL"
    MINUS_L = "-L"
    MINUS_M = "-M"
    MINUS_H = "-H"
    MINUS_VH = "-VH"

@dataclass
class WeightWithUncertainty:
    point_estimate: float
    lower_bound: float
    upper_bound: float
    source_opinions: List[dict]

class LinguisticWeightConverter:
    """语言权重转换器"""
    
    MAP = {
        LinguisticLabel.PLUS_VH: (0.9, 0.10),
        LinguisticLabel.PLUS_H: (0.7, 0.10),
        LinguisticLabel.PLUS_M: (0.5, 0.10),
        LinguisticLabel.PLUS_L: (0.3, 0.10),
        LinguisticLabel.PLUS_VL: (0.1, 0.10),
        LinguisticLabel.ZERO: (0.0, 0.00),
        LinguisticLabel.MINUS_VL: (-0.1, 0.10),
        LinguisticLabel.MINUS_L: (-0.3, 0.10),
        LinguisticLabel.MINUS_M: (-0.5, 0.10),
        LinguisticLabel.MINUS_H: (-0.7, 0.10),
        LinguisticLabel.MINUS_VH: (-0.9, 0.10),
    }
    
    @classmethod
    def convert(cls, label: LinguisticLabel) -> Tuple[float, float]:
        """转换为 (点估计, 不确定半径)"""
        return cls.MAP[label]
    
    @classmethod
    def aggregate(
        cls,
        opinions: List[Tuple[LinguisticLabel, float]]  # (label, confidence)
    ) -> WeightWithUncertainty:
        """聚合多专家意见"""
        # 简单加权平均（Phase 1）
        weights = []
        uncertainties = []
        
        for label, conf in opinions:
            point, radius = cls.convert(label)
            weights.append(point * conf)
            uncertainties.append(radius * conf)
        
        total_conf = sum(conf for _, conf in opinions)
        
        return WeightWithUncertainty(
            point_estimate=sum(weights) / total_conf,
            lower_bound=(sum(weights) - sum(uncertainties)) / total_conf,
            upper_bound=(sum(weights) + sum(uncertainties)) / total_conf,
            source_opinions=[{"label": l.value, "confidence": c} for l, c in opinions]
        )
```

---

## 下一步

等待用户阅读后决策 4 个事项。
