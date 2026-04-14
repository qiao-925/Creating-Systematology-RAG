# 多模型评估与人类介入机制调研

> 目标：为 CLDFlow 设计"分离检索器与评估器"的多模型架构，以及人类介入策略
> 调研日期：2026-04-12
> 核心诉求：可靠性、避免死亡循环、合理的用户介入点

---

## 一、核心问题：为什么需要分离评估器

### 1.1 单模型自我评估的失效

来自 Anthropic 的实证发现（2025）：

```
问题：让同一个 Agent 生成并评估自己的工作
     → 倾向于过度乐观（leniency bias）
     → 即使质量平庸也会"自信地称赞"
     → 在主观任务上尤为严重

解决方案：分离 Generator 和 Evaluator
     → Evaluator 可以独立调优为"怀疑者"
     → Generator 有具体反馈可以迭代改进
```

**对 CLDFlow 的启示**：
- ✅ Conductor 作为独立评估者，非 Specialist Agent 自我评估
- ✅ 更进一步：Evaluator 本身可以用不同模型，避免系统性偏见

---

## 二、多模型评估架构

### 2.1 基础模式：单模型双角色

```
[Specialist Agent - GPT-4o]  →  检索 + 生成 CLD 片段
                ↓
[Conductor - GPT-4o]  →  评估（同一模型，不同 prompt）
                ↓
[决策]
```

**问题**：同一模型可能有系统性偏见

---

### 2.2 进阶模式：多模型对照

```
[Specialist Agent - DeepSeek/Claude]  →  检索 + 生成
                ↓
[Conductor Evaluator - GPT-4o]  →  评估 ①
[Conductor Evaluator - Claude]    →  评估 ②
                ↓
[投票/共识机制]
                ↓
[决策]
```

**优势**：
- 避免单一模型的系统性偏见
- 不同模型的分歧本身就是不确定性的信号
- 共识结果更可靠

**成本**：2-3x API 调用成本

---

### 2.3 建议的 CLDFlow 多模型架构

**Phase 1（MVP）**：
```
Specialist Agent: DeepSeek-V3（成本低，中文好）
Conductor Evaluator: GPT-4o-mini（快速、可靠）
Final Review: Claude Sonnet（质量把关，关键节点）
```

**Phase 2（增强）**：
```
Specialist Agent: 多实例（不同模型并行）
Evaluator: 模型投票（GPT-4o + Claude + Gemini）
Arbitrator: 人类或最强模型（Claude Opus）
```

---

## 三、人类介入机制（HITL）设计

### 3.1 三种介入模式对比

来自行业实践的分类：

| 模式 | 人类角色 | 适用场景 | 例子 |
|------|---------|---------|------|
| **Human-in-the-Loop** (HITL) | 执行前审批/修正 | 高风险、不可逆操作 | 医疗诊断、金融交易 |
| **Human-on-the-Loop** (HOTL) | 监督、事后审查 | 中等风险、可撤销 | 内容审核、数据分析 |
| **Human-out-of-the-Loop** | 完全自主 | 低风险、重复性任务 | 日志清理、数据格式化 |

---

### 3.2 Manus AI 的做法：完全自主

**Manus 的设计理念**：
- **最小人类干预**：用户只给高阶目标，Manus 端到端自动执行
- **24/7 虚拟执行环境**：在云端持续运行
- **代码作为行动机制**：用 Python 代码执行复杂操作

**优势**：
- 流畅的用户体验
- 适合标准化任务

**风险**：
- 方向偏移难以及时发现
- 对于研究类任务，可靠性存疑

**对 CLDFlow 的启示**：
- ❌ 不适合完全照搬 Manus——研究任务需要可审计性
- ✅ 可以借鉴其"Sprint 合约"模式——检索前约定标准

---

### 3.3 Anthropic 的做法：工具化介入

**Anthropic 的理念**（来自 "Building effective agents"）：

```
Agents are just workflows with feedback loops.

关键是：
1. 清晰的成功标准
2. 透明的执行过程
3. 可介入的检查点
```

**Ralph Loop 模式**（长任务编排）：
```
Agent 声称完成 → 系统询问"真的完成了吗？" → 
  - 如果是：进入下一阶段
  - 如果否：Agent 承认不足，继续改进
```

**对 CLDFlow 的启示**：
- ✅ 在关键节点设置"检查点"（checkpoint）
- ✅ 让用户可以选择介入或自动继续
- ✅ 不是强制介入，而是提供透明度和选择权

---

### 3.4 监管趋势：HITL 成为合规要求

**NIST AI Risk Management Framework (2024)**：
- 关键决策场景要求人类监督
- 需要文档化审查记录
- 强调可解释性和可追溯性

**对 CLDFlow 的启示**：
- ✅ 政策分析属于"高影响决策支持"
- ✅ 人类介入不是可选，是合规要求
- ✅ 所有介入点需要审计日志

---

## 四、CLDFlow 人类介入策略设计

### 4.1 介入点设计（渐进式）

```
[用户输入问题]
        ↓
[Conductor 问题分析] ──→ 🔔 介入点 1：确认分析方向
        ↓
[动态视角生成] ──→ 🔔 介入点 2：调整/增删专家视角
        ↓
[Specialist Agent 并行检索]
        ↓
[检索结果评估] ──→ 🔔 介入点 3：确认覆盖度/补充检索
        ↓
[CLD 融合] ──→ 🔔 介入点 4：审核节点归并（关键！）
        ↓
[FCM 权重赋值] ──→ 🔔 介入点 5：审核权重合理性
        ↓
[D2D 杠杆点分析] ──→ 🔔 介入点 6：最终审核输出
        ↓
[生成报告]
```

### 4.2 介入触发条件（自动 → 人工）

| 触发条件 | 自动处理 | 建议人工介入 |
|---------|---------|-------------|
| **检索覆盖率 < 80%** | 自动继续检索 | 如果 3 轮后仍不足 |
| **评估器分歧大**（模型投票分歧） | 标记高不确定性 | 建议人工确认 |
| **来源质量低**（T3/T4 占比高） | 自动过滤并提示 | 如果无法找到 T1/T2 来源 |
| **节点归并争议**（相似度 0.65-0.85） | 自动决策 | 建议人工确认 |
| **权重分歧大**（Agent 间分歧 > 0.5） | 标记并继续 | 建议人工审核 |
| **硬限制到达**（10 轮检索） | 强制停止并报告 | 必须人工决定是否继续 |

### 4.3 介入界面设计

**模式 A：异步通知（推荐）**
```
[System 消息]
检索阶段已完成，检测到以下情况：
- 经济视角覆盖率：75%（略低于 80% 阈值）
- 建议补充：房地产市场微观机制相关文献

[用户选项]
[继续] [补充检索] [查看详情]
```

**模式 B：实时阻断（关键节点）**
```
[System 消息]
CLD 融合阶段需要您的确认：

节点归并建议：
- "政府补贴力度" vs "财政补贴规模" → 建议合并为"补贴力度"
置信度：0.78（中等）

[确认合并] [保留分离] [修改名称]
```

---

## 五、死亡循环防护机制

### 5.1 多层防护

```
第一层：硬限制（Hard Limits）
├── 最多 10 轮检索
├── 每轮最多 5 个查询
├── 总成本上限
└── 总时间上限（如 30 分钟）

第二层：智能检测（Smart Detection）
├── 连续 N 轮无新发现
├── 检索结果重复率 > 70%
└── 评估器置信度持续下降

第三层：人工兜底（Human Override）
├── 硬限制到达时强制人工确认
├── 评估器分歧大时建议人工介入
└── 用户可随时暂停/干预
```

### 5.2 关键设计：不可逆检查点

来自 Anthropic Harness 的启示：

```
每个 Sprint（检索轮次）结束时的检查清单：

□ 本轮是否发现新变量/新关系？
□ 来源质量是否达标？
□ 覆盖率是否提升？
□ 是否出现重复/循环检索？

如果 4 项都是"否"：触发"饱和预警"
  → 建议停止或调整策略
  → 需人工确认是否继续
```

---

## 六、多模型评估实现草案

### 6.1 模型分工建议

| 角色 | 模型 | 理由 |
|------|------|------|
| **Specialist Agent** | DeepSeek-V3 | 成本低，中文强，推理能力好 |
| **Conductor Evaluator** | GPT-4o-mini | 快、可靠、成本低 |
| **争议仲裁** | Claude Sonnet | 质量把关，复杂判断 |
| **Final Review** | Claude Opus（可选） | 最终输出审核 |

### 6.2 评估投票机制

```python
class MultiModelEvaluator:
    """多模型评估器"""
    
    def __init__(self):
        self.models = {
            'gpt4o': OpenAIClient(),
            'claude': AnthropicClient(),
            # 'gemini': GoogleClient(),  # Phase 2
        }
    
    def evaluate(self, retrieval_result: dict) -> EvaluationConsensus:
        """多模型投票评估"""
        
        votes = []
        for model_name, client in self.models.items():
            vote = client.evaluate(retrieval_result)
            votes.append(vote)
        
        # 计算共识度
        consensus = self._calculate_consensus(votes)
        
        return EvaluationConsensus(
            should_stop=all(v.should_stop for v in votes),
            coverage=median([v.coverage for v in votes]),
            confidence=consensus.agreement_rate,
            dissenting_opinions=consensus.dissenters,
            recommendation=self._generate_recommendation(votes)
        )
    
    def _calculate_consensus(self, votes: List[Vote]) -> Consensus:
        """计算模型间共识度"""
        
        # 简单多数投票
        stop_votes = sum(1 for v in votes if v.should_stop)
        agreement_rate = stop_votes / len(votes)
        
        # 分歧分析
        if agreement_rate == 1.0:
            return Consensus(agreement_rate=1.0, dissenters=[])
        
        # 有分歧时，记录不同意见
        dissenters = [v.model for v in votes if v.should_stop != (stop_votes > len(votes)/2)]
        
        return Consensus(
            agreement_rate=agreement_rate,
            dissenters=dissenters
        )
```

### 6.3 分歧处理策略

```
评估器分歧场景：

场景 A：2:0 或 3:0 一致
  → 直接采纳多数意见

场景 B：1:1 分歧（2 模型时）
  → 引入第三模型仲裁
  → 或标记为"高不确定性"，建议人工介入

场景 C：2:1 分歧（3 模型时）
  → 采纳多数意见
  → 但标记"存在不同意见"
  → 输出时附加不确定性说明
```

---

## 七、决策建议

### 7.1 人类介入策略（渐进式）

| 阶段 | 介入模式 | 说明 |
|------|---------|------|
| **MVP (Phase 1)** | Human-on-the-Loop | 自动运行，关键节点通知用户 |
| **增强 (Phase 2)** | 可选 HITL | 用户可设置"严格模式"，增加介入点 |
| **专家模式** | Human-in-the-Loop | 每个检查点强制确认 |

**默认推荐：HOTL（Human-on-the-Loop）**
- 系统自主执行
- 关键决策点异步通知用户
- 用户可选择介入或继续
- 所有操作可审计、可追溯

### 7.2 多模型策略（成本效益平衡）

| 阶段 | 策略 | 成本 | 可靠性 |
|------|------|------|--------|
| **MVP** | 单模型双角色 | 低 | 中 |
| **MVP+** | 双模型对照（Generator-Evaluator 分离） | 中 | 中高 |
| **Phase 2** | 三模型投票 | 高 | 高 |

**推荐 Phase 1：双模型对照**
- Specialist: DeepSeek-V3
- Evaluator: GPT-4o-mini
- 成本低（DeepSeek 便宜），可靠性提升明显

### 7.3 关键检查点（必须人工可介入）

```
🔴 必须介入点（可配置为自动）：
1. 问题分析方向确认
2. 节点归并争议（相似度中等）
3. 硬限制到达时的继续/停止决策

🟡 建议介入点（默认自动，可通知）：
4. 检索覆盖率不达标
5. 评估器分歧大
6. 来源质量整体偏低

🟢 自动执行点（无需介入）：
7. 常规检索轮次
8. 无争议的节点归并
9. FCM 仿真计算
```

---

## 八、参考资源

- **Anthropic Building Effective Agents**: https://www.anthropic.com/research/building-effective-agents
- **Anthropic Harness Design**: https://www.anthropic.com/engineering/harness-design-long-running-apps
- **Manus AI 分析**: https://www.baytechconsulting.com/blog/manus-ai-an-analytical-guide-to-the-autonomous-ai-agent-2025
- **Human-in-the-Loop Best Practices**: https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo
- **NIST AI RMF**: NIST AI Risk Management Framework (2024)

---

*Related: CLDFlow 架构设计 | 下一步: 工程架构图（模块接口定义）*
