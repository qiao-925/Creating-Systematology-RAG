# 检索停止条件与收敛判断调研

## 核心问题

CLD/FCM/D2D 各层何时停止检索/提取/分析？防止无限循环和资源浪费。

---

## 问题场景

| 场景 | 风险 | 例子 |
|------|------|------|
| **无限检索** | Agent 不断发现新文档，无法收敛 | "再搜一篇，还有更多信息" |
| **循环提取** | CLD 节点不断增加，无法完成 | 每次提取都发现新变量 |
| **过度仿真** | FCM 场景组合爆炸 | 想测试所有可能的干预组合 |
| **资源耗尽** | API 费用过高，时间过长 | 单个查询花费 $10+ |

---

## 备选方案对比

### 方案 A：硬限制（必须）

| 维度 | 限制 | 理由 |
|------|------|------|
| 总轮次 | 最多 10 轮 | 防止无限循环 |
| 每轮查询 | 最多 5 次 | 控制单次搜索量 |
| 总成本 | 上限 $5/查询 | 成本控制 |
| 总时间 | 上限 5 分钟 | 用户体验 |

**优点**：简单，可靠，保底
**缺点**：可能过早停止，错过重要信息

### 方案 B：智能检测（推荐）

**新信息检测**：
```python
def has_new_information(current_round, previous_rounds):
    """
    检测当前轮是否发现新信息
    """
    current_concepts = set(extract_concepts(current_round))
    previous_concepts = set()
    
    for r in previous_rounds:
        previous_concepts.update(extract_concepts(r))
    
    new_concepts = current_concepts - previous_concepts
    
    # 新发现概念数 < 阈值 → 可能收敛
    return len(new_concepts) > 2  # 阈值可调
```

**重复率检测**：
```python
def calculate_redundancy(current, history):
    """
    计算当前轮与历史的重复率
    """
    # 基于 embedding 相似度
    current_emb = embed(current)
    history_embs = [embed(h) for h in history]
    
    similarities = [cosine_sim(current_emb, h) for h in history_embs]
    max_sim = max(similarities)
    
    # 最大相似度 > 0.9 → 高度重复
    return max_sim > 0.9
```

### 方案 C：收敛判断（CLD 层）

**节点增长曲线**：
```
轮次 1: 10 个节点
轮次 2: 15 个节点 (+5)
轮次 3: 17 个节点 (+2)
轮次 4: 18 个节点 (+1)
轮次 5: 18 个节点 (+0) → 收敛，可停止
```

**实现**：
```python
def check_convergence(node_counts, window=3, threshold=1):
    """
    检查节点增长是否收敛
    
    node_counts: [10, 15, 17, 18, 18]
    """
    if len(node_counts) < window:
        return False
    
    # 最近 window 轮的增长量
    recent_growth = [
        node_counts[i] - node_counts[i-1]
        for i in range(-window, 0)
    ]
    
    # 平均增长 < 阈值 → 收敛
    return np.mean(recent_growth) < threshold
```

### 方案 D：任务完成度评估

**Checklist 方法**：
```python
COMPLETION_CRITERIA = {
    'cld_extraction': {
        'min_concepts': 10,
        'min_edges': 15,
        'perspectives_covered': ['policy', 'economic', 'social']
    },
    'fcm_rating': {
        'all_edges_rated': True,
        'divergence_acceptable': 0.5
    }
}

def assess_completion(stage, results):
    criteria = COMPLETION_CRITERIA[stage]
    
    checks = []
    for key, threshold in criteria.items():
        actual = results.get(key)
        checks.append({
            'criterion': key,
            'required': threshold,
            'actual': actual,
            'passed': _check_passed(actual, threshold)
        })
    
    all_passed = all(c['passed'] for c in checks)
    
    return {
        'stage_complete': all_passed,
        'checks': checks,
        'can_proceed': all_passed
    }
```

---

## 学术/工业界实践

### 1. 信息检索停止策略

**经典方法**：
- **Precision@K**：找到 K 个相关文档后停止
- **Recall-oriented**：估计剩余相关文档数，低于阈值停止
- **Cost-benefit**：边际收益 < 边际成本时停止

### 2. LLM Agent 的停止条件

**ReAct 模式**：
- 思考 → 行动 → 观察 → 循环
- 停止条件：
  1. 得出答案
  2. 达到最大步数
  3. 无法继续（无可用工具）

**对 CLDFlow 的启示**：
- 我们的 Agent 是"提取者"而非"推理者"
- 停止条件应基于"信息量"而非"答案正确性"

### 3. 复杂系统建模收敛

**系统动力学实践**：
- 模型复杂度与洞察力的权衡
- 80/20 法则：20% 的核心变量产生 80% 的系统行为
- **启示**：不需要穷尽所有因果链

---

## 推荐方案

### Phase 1 MVP：三层防护

```python
class StoppingCriteria:
    """停止条件管理器"""
    
    def __init__(self):
        self.hard_limits = {
            'max_rounds': 10,
            'max_queries_per_round': 5,
            'max_cost_usd': 5.0,
            'max_time_seconds': 300
        }
        
        self.smart_thresholds = {
            'new_concepts_min': 2,
            'redundancy_max': 0.9,
            'convergence_window': 3,
            'convergence_growth_threshold': 1
        }
    
    def should_stop(
        self,
        current_round: int,
        round_results: List[Dict],
        cost_so_far: float,
        time_so_far: float
    ) -> Tuple[bool, str]:
        """
        判断是否应该停止检索
        
        Returns: (should_stop, reason)
        """
        
        # 1. 硬限制检查（最高优先级）
        if current_round >= self.hard_limits['max_rounds']:
            return True, f"达到最大轮次限制 ({self.hard_limits['max_rounds']})"
        
        if cost_so_far >= self.hard_limits['max_cost_usd']:
            return True, f"达到成本上限 (${cost_so_far:.2f})"
        
        if time_so_far >= self.hard_limits['max_time_seconds']:
            return True, f"达到时间上限 ({time_so_far:.0f}s)"
        
        # 2. 智能检测（如果数据足够）
        if len(round_results) >= 2:
            # 新信息检查
            latest = round_results[-1]
            previous = round_results[:-1]
            
            new_concepts = self._count_new_concepts(latest, previous)
            if new_concepts < self.smart_thresholds['new_concepts_min']:
                return True, f"新发现概念数 ({new_concepts}) 低于阈值"
            
            # 重复率检查
            redundancy = self._calculate_redundancy(latest, previous)
            if redundancy > self.smart_thresholds['redundancy_max']:
                return True, f"重复率过高 ({redundancy:.2f})"
            
            # 收敛检查（需要至少 4 轮）
            if len(round_results) >= 4:
                node_counts = [r['concept_count'] for r in round_results]
                if self._check_convergence(node_counts):
                    return True, "节点增长已收敛"
        
        return False, "继续检索"
```

### 各层具体策略

| 层级 | 停止条件 | 硬限制 | 智能检测 |
|------|----------|--------|----------|
| **输入层** | 文档解析完成 | 单文档 < 100 页 | 无 |
| **CLD 提取** | 节点增长收敛 | 10 轮/5 查询 | 新概念 < 2 |
| **节点归并** | 归并完成 | 单次完成 | 无 |
| **FCM 评级** | 所有边已评级 | 同 CLD | 分歧度稳定 |
| **D2D 分析** | 所有节点已分析 | 单次完成 | 无 |

---

## 人工兜底机制

### 强制确认场景

```python
FORCED_REVIEW_TRIGGERS = [
    'hard_limit_reached',      # 硬限制到达
    'high_divergence_detected', # 高分歧度
    'unresolved_conflicts',     # 未消解冲突
    'unexpected_cost_spike',    # 成本异常
    'timeout_approaching'       # 即将超时
]

def request_human_decision(context, options):
    """
    请求人工决策
    
    context: 当前状态和问题描述
    options: ["继续", "停止", "调整参数"]
    """
    # 向用户展示当前状态
    # 等待用户输入
    pass
```

### 降级策略

| 触发条件 | 降级策略 |
|----------|----------|
| 成本接近上限 | 切换到 cheaper model (GPT-4 → GPT-3.5) |
| 时间接近上限 | 减少 Agent 数量（3→2 视角） |
| 复杂度过高 | 简化分析范围（聚焦核心变量） |

---

## 待决策事项

1. **硬限制数值**
   - 最大轮次：10 vs 15 vs 20
   - 成本上限：$5 vs $10
   - **建议**：10 轮 / $5，可调整

2. **新信息阈值**
   - 每轮至少发现 N 个新概念：2 vs 3
   - **建议**：2，宽松避免过早停止

3. **重复率阈值**
   - 相似度 > 0.9 视为重复？
   - **建议**：0.9，保守

4. **是否强制人工确认**
   - 选项 A：硬限制到达自动停止（推荐）
   - 选项 B：硬限制到达请求人工确认
   - **建议**：A，减少打断

5. **是否支持动态调整**
   - 选项 A：固定限制（推荐）
   - 选项 B：根据任务复杂度动态调整
   - **建议**：A，简单可预期

---

## 代码模板

```python
from dataclasses import dataclass
from typing import List, Dict, Tuple
import time

@dataclass
class RoundResult:
    round_id: int
    concept_count: int
    new_concepts: List[str]
    redundant_with_previous: bool
    cost_usd: float

class StoppingManager:
    """停止条件管理器"""
    
    def __init__(
        self,
        max_rounds: int = 10,
        max_cost: float = 5.0,
        max_time: float = 300,
        new_concept_threshold: int = 2,
        redundancy_threshold: float = 0.9
    ):
        self.limits = {
            'rounds': max_rounds,
            'cost': max_cost,
            'time': max_time
        }
        self.thresholds = {
            'new_concepts': new_concept_threshold,
            'redundancy': redundancy_threshold
        }
        
        self.start_time = time.time()
        self.total_cost = 0.0
        self.round_history = []
    
    def record_round(self, result: RoundResult):
        """记录本轮结果"""
        self.round_history.append(result)
        self.total_cost += result.cost_usd
    
    def check_stop(self) -> Tuple[bool, str]:
        """检查是否应该停止"""
        elapsed = time.time() - self.start_time
        
        # 硬限制
        if len(self.round_history) >= self.limits['rounds']:
            return True, "max_rounds"
        
        if self.total_cost >= self.limits['cost']:
            return True, "max_cost"
        
        if elapsed >= self.limits['time']:
            return True, "max_time"
        
        # 智能检测
        if len(self.round_history) >= 2:
            latest = self.round_history[-1]
            
            if len(latest.new_concepts) < self.thresholds['new_concepts']:
                return True, "low_new_information"
            
            if latest.redundant_with_previous:
                return True, "high_redundancy"
        
        return False, "continue"
```

---

## 下一步

等待用户阅读后决策 5 个事项。
