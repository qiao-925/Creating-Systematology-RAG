# 模糊层 - 模糊认知图仿真算法调研

## 核心问题

给定权重矩阵，用什么算法进行场景推演，模拟政策干预后的系统演化，并判断何时达到稳态。

---

## FCM 基础原理

### 什么是 FCM

模糊认知图（Fuzzy Cognitive Map）是因果图的一种数学化表示：
- **节点**：概念变量（如"房价"、"利率"）
- **边**：带权重的因果关系（-1 到 +1）
- **状态向量**：各节点的激活值（通常是 0-1 或 -1 到 +1）

### 经典更新公式

```
A_i(t+1) = f( A_i(t) + Σ_j A_j(t) * W_ji )
```

其中：
- `A_i(t)`：节点 i 在时间 t 的激活值
- `W_ji`：从节点 j 到节点 i 的因果权重
- `f`：激活函数（sigmoid / tanh / threshold）

---

## 备选方案对比

### 方案 A：经典 Kosko 迭代法（推荐 Phase 1）

**算法**：
```python
def kosko_simulation(adj_matrix, initial_state, max_iter=100, epsilon=1e-4):
    """
    adj_matrix: 权重矩阵 (n x n)
    initial_state: 初始状态向量 (n,)
    """
    state = initial_state.copy()
    
    for t in range(max_iter):
        new_state = sigmoid(adj_matrix.T @ state)
        
        # 检查收敛
        if np.all(np.abs(new_state - state) < epsilon):
            return new_state, "converged", t
        
        state = new_state
    
    return state, "max_iter_reached", max_iter
```

**激活函数选择**：
| 函数 | 公式 | 输出范围 | 特点 |
|------|------|----------|------|
| Sigmoid | 1/(1+e^(-x)) | (0,1) | 平滑，常用 |
| Tanh | (e^x - e^(-x))/(e^x + e^(-x)) | (-1,1) | 对称，适合正负权重 |
| Threshold | 1 if x>0 else 0 | {0,1} | 离散，适合分类 |

**推荐**：Tanh，因为 FCM 有抑制关系（负权重），对称输出更合理

### 方案 B：非线性 Hebbian 学习（NHL）

**特点**：
- 在线学习权重
- 需要历史数据训练
- 不适合我们的场景（一次性分析，无训练数据）

**适用场景**：需要权重自适应调整的长期系统

### 方案 C：数据驱动的 FCM（DD-FCM）

**特点**：
- 从时间序列数据学习权重
- 需要真实观测数据
- 不适合（我们无历史数据）

### 方案 D：带不确定性的 FCM（Phase 2）

**方法**：
- 每个权重是区间或分布而非点估计
- 使用蒙特卡洛模拟多次运行
- 输出：稳态分布而非单一值

**复杂度**：高，需大量采样

---

## 学术/工业界实践

### 1. FCMpy 库（Python）

**功能**：
```python
from fcapy import FCM

# 创建 FCM
fcm = FCM()
fcm.add_concept("房价")
fcm.add_concept("利率")
fcm.add_edge("利率", "房价", weight=-0.7)

# 场景仿真
fcm.set_state({"利率": 1.0})  # 干预场景
result = fcm.run_simulation(max_iter=50)
```

**局限性**：
- 不支持多专家权重聚合
- 不支持不确定性传播

### 2. FuzzyLite / jFCM（Java）

- 商业级 FCM 实现
- 支持复杂激活函数
- 过重，不适合我们

### 3. 自定义实现（推荐）

**理由**：
- 我们的需求简单（单次仿真，无需学习）
- 需要灵活集成到 CLDFlow 流水线
- 需要支持不确定性区间（Phase 2）

---

## 场景对比策略

### 基准场景 vs 干预场景

```python
class FCMScenarioSimulator:
    def __init__(self, weight_matrix, concept_names):
        self.W = weight_matrix
        self.concepts = concept_names
        self.n = len(concept_names)
    
    def baseline_scenario(self):
        """基准场景：当前状态"""
        initial = np.zeros(self.n)  # 或从数据推断
        return self.simulate(initial)
    
    def intervention_scenario(self, interventions):
        """
        干预场景：强制某些节点值
        interventions: {node_name: forced_value}
        """
        initial = np.zeros(self.n)
        
        result = self.simulate(initial)
        
        # 干预节点固定值
        for name, value in interventions.items():
            idx = self.concepts.index(name)
            result['final_state'][idx] = value
            # 重新仿真几步让影响扩散
            result = self.simulate_with_clamping(result['final_state'], interventions)
        
        return result
    
    def compare_scenarios(self, baseline, intervention):
        """对比两个场景的稳态差异"""
        diff = intervention['final_state'] - baseline['final_state']
        
        return {
            "absolute_changes": diff,
            "percentage_changes": diff / (baseline['final_state'] + 1e-6),
            "most_affected": self._get_top_changed(diff, n=5)
        }
```

### 常见干预类型

| 干预 | 建模方式 | 示例 |
|------|----------|------|
| 增加节点值 | 初始值设为 1.0 | 大幅加息 |
| 减少节点值 | 初始值设为 -1.0 或 0 | 取消补贴 |
| 固定节点值 | 每轮重置为固定值 | 强制价格管制 |
| 修改权重 | 调整边权重 | 政策效果增强 |

---

## 稳态判断

### 收敛标准

| 标准 | 公式 | 阈值建议 |
|------|------|----------|
| 绝对变化 | \|A(t+1) - A(t)\| < ε | ε = 1e-4 |
| 相对变化 | \|A(t+1) - A(t)\| / \|A(t)\| < ε | ε = 1e-3 |
| 最大迭代 | t > max_iter | max_iter = 100 |

### 非收敛情况处理

**振荡检测**：
```python
def detect_oscillation(history, window=10):
    """检测最近 window 步是否周期性重复"""
    if len(history) < window * 2:
        return False
    
    # 检查是否与 window 步前的状态相似
    recent = history[-window:]
    past = history[-2*window:-window]
    
    return all(np.allclose(r, p, atol=1e-3) for r, p in zip(recent, past))
```

**处理策略**：
- 振荡 → 取多步平均作为稳态
- 发散 → 标记异常，检查权重矩阵（可能有不稳定正反馈环）

---

## 推荐方案

### Phase 1 MVP

**核心算法**：Kosko 迭代 + Tanh 激活

```python
import numpy as np
from typing import Dict, Tuple

class FCMSimulator:
    def __init__(self, weight_matrix: np.ndarray, concept_names: list):
        self.W = weight_matrix  # (n, n)
        self.concepts = concept_names
        self.n = len(concept_names)
    
    def tanh_activation(self, x):
        return np.tanh(x)  # 输出范围 (-1, 1)
    
    def simulate(
        self,
        initial_state: np.ndarray,
        max_iter: int = 100,
        epsilon: float = 1e-4,
        fixed_nodes: Dict[int, float] = None
    ) -> Dict:
        """
        运行 FCM 仿真
        
        fixed_nodes: {node_idx: fixed_value} 干预节点固定值
        """
        state = initial_state.copy()
        history = [state.copy()]
        
        for t in range(max_iter):
            # 计算下一状态
            new_state = self.tanh_activation(self.W.T @ state)
            
            # 应用干预（固定节点值）
            if fixed_nodes:
                for idx, val in fixed_nodes.items():
                    new_state[idx] = val
            
            history.append(new_state.copy())
            
            # 检查收敛
            if np.all(np.abs(new_state - state) < epsilon):
                return {
                    "final_state": new_state,
                    "iterations": t + 1,
                    "converged": True,
                    "history": history
                }
            
            state = new_state
        
        # 未收敛，检测振荡
        if self._detect_oscillation(history):
            avg_state = np.mean(history[-10:], axis=0)
            return {
                "final_state": avg_state,
                "iterations": max_iter,
                "converged": False,
                "oscillation_detected": True,
                "history": history
            }
        
        return {
            "final_state": state,
            "iterations": max_iter,
            "converged": False,
            "oscillation_detected": False,
            "history": history
        }
    
    def _detect_oscillation(self, history, window=10):
        if len(history) < window * 2:
            return False
        
        recent = np.array(history[-window:])
        past = np.array(history[-2*window:-window])
        
        return np.allclose(recent, past, atol=1e-3)
```

### Phase 2 升级：不确定性传播

**蒙特卡洛方法**：
```python
def monte_carlo_simulation(self, n_samples=1000):
    """
    权重有不确定性区间时，采样多次运行
    """
    results = []
    
    for _ in range(n_samples):
        # 从权重区间采样
        sampled_W = self._sample_weights_from_intervals()
        
        # 运行仿真
        result = self.simulate_with_weights(sampled_W)
        results.append(result['final_state'])
    
    # 统计输出
    return {
        "mean_state": np.mean(results, axis=0),
        "std_state": np.std(results, axis=0),
        "percentile_5": np.percentile(results, 5, axis=0),
        "percentile_95": np.percentile(results, 95, axis=0)
    }
```

---

## 待决策事项

1. **激活函数选择**
   - 选项 A：Sigmoid (0,1)
   - 选项 B：Tanh (-1,1) **推荐**
   - **理由**：Tanh 对称，适合正负因果

2. **收敛阈值 ε**
   - 选项 A：1e-4（严格）
   - 选项 B：1e-3（宽松，更快）
   - **建议**：A，宁可多迭代几轮

3. **最大迭代次数**
   - 选项 A：50 步
   - 选项 B：100 步 **推荐**
   - 选项 C：200 步（保守）

4. **干预建模方式**
   - 选项 A：初始值设置（简单）**推荐**
   - 选项 B：固定节点值（每轮重置，复杂但更真实）
   - **Phase 1 建议**：A，B 留给 Phase 2

5. **是否预计算所有干预组合**
   - 选项 A：只计算用户指定的干预
   - 选项 B：预计算常见干预组合（租金管制、税收减免等）
   - **建议**：A，按需计算

---

## 代码模板

### 完整 FCM 场景对比流程

```python
from dataclasses import dataclass

@dataclass
class ScenarioResult:
    name: str
    final_state: np.ndarray
    converged: bool
    iterations: int
    interventions: Dict[str, float]

class ScenarioComparator:
    def __init__(self, fcm_simulator: FCMSimulator):
        self.sim = fcm_simulator
    
    def run_comparison(
        self,
        baseline_interventions: Dict[str, float] = None,
        test_interventions: Dict[str, float]
    ) -> Dict:
        """对比基准场景和干预场景"""
        
        # 基准场景
        baseline = self.sim.simulate(
            initial_state=np.zeros(self.sim.n),
            fixed_nodes=baseline_interventions
        )
        
        # 干预场景
        test = self.sim.simulate(
            initial_state=np.zeros(self.sim.n),
            fixed_nodes={**baseline_interventions, **test_interventions}
        )
        
        # 对比结果
        diff = test['final_state'] - baseline['final_state']
        
        return {
            "baseline": baseline,
            "test": test,
            "differences": {
                "absolute": diff,
                "relative": diff / (np.abs(baseline['final_state']) + 1e-6),
                "top_positive": self._get_top_n(diff, n=3, positive=True),
                "top_negative": self._get_top_n(diff, n=3, positive=False)
            }
        }
```

---

## 下一步

等待用户阅读后决策 5 个事项。
