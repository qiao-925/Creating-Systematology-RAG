# FCM层 - 仿真算法设计

> 架构概览见：`docs/CLDFlow-architecture.md` FCM层
> 默认参数见：`docs/CLDFlow-defaults.md` FCM层

---

## FCM 基础

- **节点**：概念变量（如"房价"、"利率"）
- **边**：带权重的因果关系（-1 到 +1）
- **状态向量**：各节点的激活值
- **更新公式**：`A_i(t+1) = f( A_i(t) + Σ_j A_j(t) * W_ji )`

---

## Phase 1：Kosko迭代法

```python
def kosko_simulation(adj_matrix, initial_state, max_iter=100, epsilon=1e-4, activation='tanh'):
    """
    adj_matrix: 权重矩阵 (n x n)
    initial_state: 初始状态向量 (n,)
    max_iter: 最大迭代次数
    epsilon: 收敛阈值
    activation: 激活函数
    """
    state = initial_state.copy()
    for t in range(max_iter):
        new_state = activation_fn(state @ adj_matrix, activation)
        if np.linalg.norm(new_state - state) < epsilon:
            return new_state, t, True  # 收敛
        state = new_state
    return state, max_iter, False  # 未收敛
```

### 激活函数选择

| 函数 | 输出范围 | 适用场景 | 推荐 |
|------|---------|---------|------|
| **Tanh** | [-1, +1] | 正负权重对称 | **Phase 1** |
| Sigmoid | [0, 1] | 仅正权重 | 不适合 |
| Bivalent | {0, 1} | 离散决策 | 不适合 |
| Trivalent | {-1, 0, 1} | 简化分析 | Phase 2 |

### 收敛判断

- 阈值：`epsilon = 1e-4`
- 最大迭代：100步
- 未收敛处理：取最后状态+标记"未收敛"（不变量I-7：自审不通过需标记）

---

## 场景仿真

| 场景 | 初始状态 | 说明 |
|------|---------|------|
| 基准 | 当前状态 | 无干预 |
| 干预 | 修改特定节点值 | 政策干预 |

**对比**：`差异 = 干预稳态 - 基准稳态`

---

*整合自 issue-15-sub_docs: 14-fcm-simulation.md*
