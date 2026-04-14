# 模板/角色评估业内实践调研

> 目标：调研业内如何评估 AI Agent 模板/角色的可靠性和有效性
> 调研日期：2026-04-12
> 核心发现：语义式评估不足，需要基于任务完成和下游效果的实证方法

---

## 一、为什么语义式评估不够

### 1.1 语义评估的问题

| 评估方式 | 问题 | 举例 |
|---------|------|------|
| 角色描述"看起来对" | 无法验证实际效果 | "资深经济学家"角色可能生成低质量因果链 |
| 一致性检查 | 只测形式，不测功能 | 结构相同但内容空洞 |
| 专家主观打分 | 成本高、难复现 | 不同专家评分差异大 |

**业内共识**：评估 Agent/角色必须基于**实际任务表现**，而非仅语义描述（Galileo, 2024; Anthropic, 2024）

---

## 二、业内核心评估方法

### 2.1 Counterfactual Evaluation（反事实评估）

**来源**：Galileo, Stanford AI Lab (2024)

**核心思想**：
```
系统性能（有该角色）- 系统性能（无该角色）= 角色真实贡献
```

**实施方法**：
```python
def evaluate_role_contribution(role_template, test_tasks):
    """
    评估角色模板的真实贡献
    """
    results_with = []
    results_without = []
    
    for task in test_tasks:
        # 有该角色的系统性能
        system_with = build_system(roles=[role_template, *other_roles])
        result_with = system_with.run(task)
        results_with.append(result_with)
        
        # 无该角色的系统性能（替换为通用角色）
        system_without = build_system(roles=[generic_role, *other_roles])
        result_without = system_without.run(task)
        results_without.append(result_without)
    
    # 计算贡献度
    contribution = calculate_performance_delta(
        results_with, results_without
    )
    return contribution
```

**对 CLDFlow 的应用**：
```
测试场景：Prop 13 分析

1. 完整系统：[经济视角, 政策视角, 社会视角] → CLD 结果 A
2. 移除经济视角：[通用角色, 政策视角, 社会视角] → CLD 结果 B
3. 性能差异 = 经济视角的真实贡献

性能指标：
- CLD 节点覆盖率（该视角独有的节点数）
- 因果链准确性（人工审核）
- FCM 收敛质量（矩阵合理性）
```

---

### 2.2 Action Advancement Metrics（行动推进指标）

**来源**：Galileo (2024)

**核心思想**：Agent 是否有效推进了任务完成

**评估维度**：
```
Action Advancement = 成功推进任务的交互比例

评判标准（二元）：
1. 事实准确性（Factual Accuracy）
2. 目标相关性（Goal Relevance）
3. 工具输出一致性（Tool Output Consistency）
```

**对 CLDFlow 的应用**：
```python
def evaluate_action_advancement(role_template, test_queries):
    """
    评估角色在检索任务中的推进效果
    """
    advances = 0
    total = len(test_queries)
    
    for query in test_queries:
        agent = create_agent(role_template)
        result = agent.retrieve_and_extract(query)
        
        # 检查是否推进了任务
        is_advance = check_advancement_criteria(result)
        # 1. 是否找到新变量？
        # 2. 是否建立有效因果链？
        # 3. 检索结果是否与角色专业匹配？
        
        if is_advance:
            advances += 1
    
    return advances / total  # 推进率
```

---

### 2.3 Downstream Task Performance（下游任务性能）

**来源**：Anthropic, AWS (2024)

**核心思想**：不评估角色本身，评估它对最终系统输出的影响

**评估链路**：
```
角色模板 → Agent 行为 → 检索结果 → CLD 融合 → 最终输出质量

评估点：
1. 检索质量（Coverage / Novelty / Authority）
2. CLD 提取完整性（节点数、边数、循环数）
3. 最终报告质量（人工评分 / 专家审核）
```

**对 CLDFlow 的实施**：
```python
def evaluate_downstream_impact(role_template, test_problems):
    """
    评估角色对最终系统输出的影响
    """
    scores = []
    
    for problem in test_problems:
        # 运行完整 pipeline
        system = CLDFlowSystem()
        system.set_roles([role_template, *base_roles])
        result = system.analyze(problem)
        
        # 评估最终输出质量
        quality_score = evaluate_cld_quality(result.cld)
        # - 节点覆盖率（vs 人工标注 gold standard）
        # - 因果链准确性
        # - 杠杆点识别准确性
        
        scores.append(quality_score)
    
    return mean(scores)
```

---

### 2.4 黄金数据集（Golden Dataset）对比

**来源**：AWS, Confident AI (2024)

**核心思想**：建立基准测试集，对比角色输出与标准答案

**对 CLDFlow 的应用**：
```python
# 建立黄金数据集
GOLDEN_DATASET = [
    {
        "problem": "Prop 13 对加州住房市场的影响",
        "expected_nodes": [
            "房产税", "房价", "政府收入", "公共服务", 
            "房主流动性", "区域不平等"
        ],
        "expected_edges": [
            ("房产税↓", "房价↑", "+"),
            ("房产税↓", "政府收入↓", "-"),
            # ...
        ],
        "expected_leverage_points": ["房产税改革机制"]
    },
    # ... 更多测试用例
]

def evaluate_against_golden(role_template, test_case):
    """
    对比角色生成的 CLD 与黄金标准
    """
    agent = create_agent(role_template)
    result = agent.analyze(test_case["problem"])
    
    # 计算匹配度
    node_recall = len(result.nodes & test_case["expected_nodes"]) / len(test_case["expected_nodes"])
    edge_precision = len(result.edges & test_case["expected_edges"]) / len(result.edges)
    
    return {
        "node_recall": node_recall,
        "edge_precision": edge_precision,
        "overall_f1": calculate_f1(node_recall, edge_precision)
    }
```

---

## 三、可靠性评估的量化指标

### 3.1 来自 Galileo 的指标体系

| 指标类别 | 具体指标 | 适用场景 |
|---------|---------|---------|
| **效率** | Token 使用、API 调用次数、延迟 | 成本控制 |
| **可靠性** | 失败率、异常检测、方差分析 | 稳定性监控 |
| **一致性** | 相似输入的相似输出（embedding 相似度） | 可预测性 |
| **质量** | 幻觉检测、指令遵循度、事实一致性 | 输出质量 |

### 3.2 针对 CLDFlow 的调整

```python
class TemplateReliabilityMetrics:
    """模板可靠性评估指标"""
    
    def measure_efficiency(self, role_template, n_runs=10):
        """
        效率指标：
        - 平均检索轮数
        - 平均 token 消耗
        - 平均完成时间
        """
        pass
    
    def measure_reliability(self, role_template, test_set):
        """
        可靠性指标：
        - 任务完成率（是否成功生成 CLD）
        - 失败模式分类（检索失败？提取失败？融合失败？）
        - 方差分析（不同问题的性能波动）
        """
        pass
    
    def measure_consistency(self, role_template, similar_questions):
        """
        一致性指标：
        - 相似问题的角色行为一致性
        - 输出结构稳定性
        - embedding 相似度聚类
        """
        pass
    
    def measure_quality(self, role_template, ground_truth_cases):
        """
        质量指标：
        - 与黄金数据集对比的 F1 分数
        - 专家人工审核评分
        - 下游任务（FCM/D2D）成功率
        """
        pass
```

---

## 四、A/B 测试实践

### 4.1 来自 Anthropic 和业内的做法

**核心流程**：
```
1. 定义成功指标（Success Metrics）
   - 任务完成率
   - 输出质量分数
   - 用户满意度

2. 分流测试（A/B Test）
   - A 组：原模板
   - B 组：新模板

3. 统计显著性检验
   - 计算 p-value
   - 确定样本量

4. 渐进式 rollout
   - 1% → 10% → 50% → 100%
```

**对 CLDFlow 的应用**：
```python
def ab_test_templates(template_a, template_b, test_cases):
    """
    A/B 测试两个角色模板
    """
    results_a = []
    results_b = []
    
    for case in test_cases:
        # 随机分配
        if random.choice([True, False]):
            score = evaluate_template(template_a, case)
            results_a.append(score)
        else:
            score = evaluate_template(template_b, case)
            results_b.append(score)
    
    # 统计检验
    t_stat, p_value = ttest_ind(results_a, results_b)
    
    return {
        "template_a_mean": mean(results_a),
        "template_b_mean": mean(results_b),
        "improvement": (mean(results_b) - mean(results_a)) / mean(results_a),
        "significant": p_value < 0.05
    }
```

---

## 五、混合评估策略（业内最佳实践）

### 5.1 InfoQ / AWS 推荐的框架

| 层级 | 方法 | 频率 | 成本 |
|------|------|------|------|
| **自动评估** | Counterfactual + Action Advancement | 每次构建 | 低 |
| **基准测试** | Golden Dataset 对比 | 每周 | 中 |
| **A/B 测试** | 生产环境分流 | 每月 | 高 |
| **人工审核** | 专家评分 | 季度 | 很高 |

### 5.2 CLDFlow 建议的评估流水线

```
模板开发阶段：
├── 单元测试（YAML 有效性、语法检查）
├── 反事实评估（vs 通用角色）
└── 小规模黄金数据集测试（3-5 个案例）
        ↓
集成测试阶段：
├── 完整 pipeline 集成测试
├── Action Advancement 评估（10 个查询）
└── 下游质量评估（CLD 完整性）
        ↓
生产验证阶段：
├── A/B 测试（新模板 vs 旧模板）
├── 真实用户反馈收集
└── 季度人工审核（专家评估）
```

---

## 六、关键结论

### 6.1 放弃纯语义评估

| ❌ 不做 | ✅ 改做 |
|--------|--------|
| 角色描述"看起来专业" | 实测下游任务完成率 |
| 一致性检查（结构相同） | 反事实评估（真实贡献） |
| 专家主观打分 | 黄金数据集 F1 分数 |
| 抽象的质量维度 | 可量化的任务指标 |

### 6.2 核心评估原则

1. **基于效果**：评估角色对系统最终输出的贡献
2. **实证测试**：用真实任务/黄金数据集验证
3. **量化指标**：任务完成率、F1 分数、贡献度 Δ
4. **统计严谨**：A/B 测试、显著性检验、置信区间
5. **持续监控**：生产环境性能追踪，及时发现退化

### 6.3 CLDFlow 模板评估 Checklist

```
□ 反事实贡献测试（vs 通用角色）
□ 黄金数据集召回率（节点/边/杠杆点）
□ Action Advancement 推进率
□ 下游任务完成率（CLD → FCM → D2D）
□ A/B 测试显著性（vs 现有模板）
□ 生产环境监控（失败率、token 成本）
```

---

## 七、参考资源

- **Galileo**: Agent Roles in Dynamic Multi-Agent Workflows (2024)
- **Anthropic**: Demystifying evals for AI agents (2024)
- **AWS**: Evaluating AI agents: Real-world lessons (2024)
- **ACM**: Evaluation and Benchmarking of LLM Agents: A Survey (2024)
- **InfoQ**: Evaluating AI Agents in Practice (2024)

---

*Related: CLDFlow 模板实施计划 | 下一步: 更新计划中的评估框架*
