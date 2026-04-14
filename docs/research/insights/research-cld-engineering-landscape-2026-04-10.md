# 调研：CLD 工程化实现路径

> 目标：回答「从概念架构（多 Agent + 共享 CLD 模型）到可运行代码，有哪些已有工具和研究可以直接借用？」

## 一、核心发现摘要

| 维度 | 关键结论 |
|------|----------|
| CLD 数据结构 | **有向带符号图（signed digraph）**，NetworkX 原生支持，已有轻量封装（cldx） |
| CLD → 仿真 | **D2D 方法**（2025 arXiv）可将 CLD 直接转为探索性 SD 模型，无需经验数据 |
| LLM → CLD | 2024-2025 年已有 3+ 篇论文验证 LLM 可生成专家水平的 CLD（简单结构） |
| 半定量推理 | **FCM（模糊认知图）** 是 CLD 的天然量化扩展，有成熟 Python 库 |
| 多专家共建 | Group Model Building 方法论成熟，FCMpy 直接支持多专家输入融合 |
| 定性推理引擎 | QSIM 学术价值高但工程落地困难，不建议直接使用 |

## 二、工具全景图

### 2.1 CLD 数据结构与操作

**cldx** — CLD 的最小可用 Python 封装
- 基于 NetworkX DiGraph
- 数据结构：`(source, target, polarity)` 三元组，polarity ∈ {+1, -1}
- 核心功能：添加因果链接、自动检测反馈回路（reinforcing/balancing）、绘图
- 代码极简（< 500 行），可直接参考或内嵌

```python
from cldx import CausalLoopDiagram
cld = CausalLoopDiagram()
cld.add_causal_links([
    ('补贴力度', '企业利润', +1),
    ('企业利润', '就业岗位', +1),
    ('就业岗位', '工资水平', +1),
    ('工资水平', '物价水平', +1),
    ('物价水平', '补贴力度', +1),  # 增强回路
])
loops = cld.find_loops()  # 自动识别 R/B 回路
```

**工程启示**：我们的共享模型数据结构可以直接用 NetworkX DiGraph + 边属性（polarity, confidence, source_agent）。不需要发明新轮子。

### 2.2 从 CLD 到动态仿真

**PySD** (SDXorg/pysd) — 成熟的 SD 仿真库
- 解析 Vensim (.mdl) 和 XMILE 格式模型
- 转译为 Python 代码运行仿真
- **局限**：需要完整的 stock-flow 方程，不能直接跑 CLD
- **定位**：如果未来需要做数值仿真，这是标准工具

**D2D (Diagrams-to-Dynamics)** — 2025 年最新方法（arXiv 2508.05659）
- **核心创新**：CLD + 变量分类标签 → 自动生成探索性 SD 模型
- 用户只需标注每个变量是 stock/flow/auxiliary/constant
- 自动生成方程，在参数空间做蒙特卡洛采样，**不需要经验数据**
- 输出：杠杆点排序 + 不确定性估计
- 开源 Python 包 + Web 应用
- **工程启示**：这正好解决了"CLD 是定性的，怎么做推演"的问题——D2D 给了一个不需要定量数据就能做定性推演的方法

**XMILE** — SD 模型交换标准（OASIS 开放标准 v1.0）
- XML 格式，Vensim/Stella/isee 系统通用
- **工程启示**：如果需要和传统 SD 工具互操作，用 XMILE 作为导出格式

### 2.3 LLM 自动构建 CLD

**论文 1：LLM for Automated CLD Generation** (arXiv 2503.21798, ISDC 2024)
- 测试 LLM 从动态假设文本自动提取变量和因果关系
- 使用标准 digraph 结构作为输出格式
- 对比了 4 种 prompting 技术组合
- **结论：简单模型结构下，LLM 生成的 CLD 质量接近专家水平**
- **关键限制：复杂模型仍有显著差距**

**论文 2：Pipeline Algebra (PA) for CLD** (MDPI Systems 2025)
- 将 CLD 构建分解为流水线步骤：LLM 提取 → 符号验证 → 人类审核
- 强调 human-in-the-loop 的必要性
- **工程启示**：完美契合我们的 Conductor + Agent 架构——Agent 提出因果链接，Conductor 做结构验证，人类做最终审核

**论文 3：AI vs 43 SE Graduates** (INCOSE 2025)
- AI（LLM + 搜索增强）在创建 Janis Groupthink CLD 时**优于** 43 名系统工程研究生
- 说明：LLM 辅助 CLD 构建不只是可行，在特定场景下已经超越人类初学者

### 2.4 半定量推理：模糊认知图 (FCM)

**FCMpy** — 成熟的 FCM Python 库
- 从定性输入（语言学术语如"强正相关"、"弱负相关"）自动生成因果权重
- 支持多专家输入 → 模糊逻辑聚合 → 统一权重矩阵
- 可在 FCM 上运行仿真和干预实验（what-if 分析）
- **核心流程**：
  1. 多个 Agent（专家）各自给出因果关系的定性评估
  2. 用模糊逻辑将定性评估转为 [-1, 1] 的权重
  3. 在权重矩阵上做迭代仿真
  4. 测试干预方案

**工程启示**：FCM 几乎是我们"多 Agent + 共享模型 + 收敛"架构的现成数学框架：
- Agent 的定性判断 → FCM 的语言学术语输入
- 共享模型 → FCM 权重矩阵
- 收敛 → FCM 仿真的稳态
- 干预分析 → FCM 的 what-if 测试

### 2.5 Group Model Building (GMB)

成熟的参与式建模方法论，专门设计用于多利益相关方共同构建系统动力学模型：
- 有标准化的流程（脚本化的 workshop 步骤）
- 文献 > 100 篇，有系统综述（PLOS ONE 2023）
- **核心原则**：
  - 所有参与者对同一个模型贡献不同视角
  - 模型是讨论的载体，不是最终目标
  - 收敛通过迭代修正模型实现
- **工程启示**：GMB 的流程设计可以直接指导 Agent 交互协议的设计

### 2.6 定性推理引擎 (QSIM)

- 经典算法（Kuipers, 1986），基于约束的定性仿真
- 学术优雅但工程实现复杂
- 现代替代品极少，无活跃维护的 Python 库
- **结论：不建议直接使用**，FCM + D2D 已覆盖其核心需求

## 三、工程实现路径建议

### 推荐技术栈

```
共享模型层
├── 数据结构：NetworkX DiGraph + 边属性 (polarity, weight, confidence, source)
├── 定性层：cldx 风格的 CLD（回路检测、结构分析）
├── 半定量层：FCMpy 风格的权重矩阵（多 Agent 输入聚合）
└── 探索性推演：D2D 方法（杠杆点分析、不确定性估计）

Agent 交互层
├── 每个 Agent 输出：(source, target, polarity, confidence, reasoning)
├── Conductor 做：结构验证 + 回路检测 + 冲突发现
└── 收敛判断：权重矩阵变化 < 阈值 or 所有 Agent 无新链接

LLM 辅助层
├── 从文献/数据自动提取因果关系（已验证可行）
├── 生成 CLD 的自然语言解释
└── 辅助 what-if 推演的场景设计
```

### 最小可行实现（MVP 路径）

1. **Phase 1**：用 NetworkX 实现 CLD 数据结构 + 基本操作（添加/删除链接、回路检测、可视化）
2. **Phase 2**：实现多 Agent → CLD 的输入协议（每个 Agent 提交因果链接 + 理由）
3. **Phase 3**：加入 FCM 式权重聚合（多 Agent 判断融合为统一权重）
4. **Phase 4**：集成 D2D 式推演（从 CLD 做杠杆点分析）

### 关键验证问题

| 问题 | 验证方法 | 预期难度 |
|------|----------|----------|
| LLM 能否从中文文献提取 CLD？ | 用已知案例测试 | 中（英文已验证，中文待测） |
| 多 Agent CLD 能否有效收敛？ | 设计 toy problem 测试 | 中 |
| FCM 权重聚合对 Agent 数量敏感吗？ | 实验对比 3/5/7 Agent | 低 |
| D2D 推演结果是否有指导意义？ | 和已知系统行为对比 | 中高 |

## 四、关键参考文献

1. **LLM + CLD 生成**：arXiv 2503.21798 — "Leveraging LLMs for Automated CLD Generation" (ISDC 2024)
2. **Pipeline Algebra**：MDPI Systems 13(9):784 — "LLM-Powered, Expert-Refined CLD via Pipeline Algebra" (2025)
3. **AI vs SE 学生**：INCOSE 2025 — "AI Outperforms 43 SE Graduates in Creating CLDs"
4. **D2D 方法**：arXiv 2508.05659 — "Diagrams-to-Dynamics: Exploring CLD Leverage Points under Uncertainty" (2025)
5. **ChatPySD**：System Dynamics Review — "Embedding SD Models in ChatGPT-4" (2025)
6. **FCMpy**：arXiv 2111.12749 — "FCMpy: Constructing and Analysing FCMs in Python"
7. **PySD**：JOSS 7(78):4329 — "PySD: System Dynamics Modeling in Python" (2022)
8. **GMB 综述**：PLOS ONE (2023) — "Application of GMB in Implementation Research"
9. **XMILE 标准**：OASIS — "XML Interchange Language for System Dynamics v1.0"
10. **多社区 CLD 融合（NLP）**：PMC 2025 — "Integration of large-scale community-developed CLDs: NLP approach to merging factors based on semantic similarity" → 用 Sentence Transformer 对13个社区的592个节点做语义相似度归并，F1=0.68，直接参照"多 Agent CLD 融合"工程路径
11. **LLM 自动化 CLD 生成（最新）**：arXiv 2503.21798 — "Leveraging LLMs for Automated CLD Generation via Curated Prompting" (2025/03) → 证明 LLM 加精心设计 Prompt 可生成与专家相当的 CLD（简单结构），是 CLD 自动生成可行性的最新实证

## 五、对项目的核心洞察

**最大惊喜**：我们在之前讨论中独立推导出的架构（多 Agent + 共享模型 + 张力驱动收敛）在 FCM 领域已有成熟的数学基础和工具支持。这不是巧合——FCM 的设计哲学本身就源自系统动力学 + 多专家协作。

**最大风险**：LLM 对复杂 CLD 的构建能力仍有限（简单结构可以，复杂结构差距大）。这意味着我们的 Agent 不能完全自动化——必须有 human-in-the-loop 或强约束的结构验证。

**最大机会**：D2D 方法填补了"CLD 只是画图不能推演"的鸿沟。如果我们能将 LLM 辅助构建 + D2D 推演 + FCM 收敛整合，这将是一个完整的从定性到半定量的闭环。

**Phase 2 优化方向（贝叶斯网络）**：当前 FCM 边权重是点估计（如 `0.8`）。引入贝叶斯方法可以将其升级为分布估计（如 `0.8 ± 0.15`），让 D2D 的 Monte Carlo 采样范围有理论依据，而非硬编码。实现路径：多 Agent 的语言评级 → 贝叶斯聚合 → 权重后验分布 → D2D 参数采样。（Phase 1 先用点估计，Phase 2 可替换为分布。）

---
*Created: 2026-04-10 19:50 | Related: #15 CP-11*
