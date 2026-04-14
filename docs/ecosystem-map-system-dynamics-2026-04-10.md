# 生态图谱：系统动力学及相关学科的知识版图

> 目标：为项目决策提供完整的学科背景，理解 CLD/FCM/D2D 在更大图景中的位置
> 创建于：2026-04-10 | Related: #15

---

## 一、起源：梅西会议（1941-1953）

整个生态最重要、最少被提及的起源事件。

一批跨领域顶级学者（Wiener、von Neumann、McCulloch、Bateson 等）聚集讨论一个问题：
**机器、大脑、社会有没有共同的运行原理？**

这一系列会议直接催生两个平行学科，奠定了整个生态的基础：

```
梅西会议（1941-1953）
    │
    ├──→ 控制论（Norbert Wiener, 1948）
    │       核心命题："反馈是控制和通信的普遍原理"
    │       影响：工程控制、神经科学、AI、系统动力学
    │
    └──→ 一般系统论（Ludwig von Bertalanffy, 1950s）
            核心命题："系统整体行为不能从各部分推断"
            影响：生物学、社会科学、管理学
```

---

## 二、五个主干学科共同体

### 2.1 系统动力学（System Dynamics）

- **创始人**：Jay Forrester，MIT Sloan，1956
- **起源**：电气工程师转向管理科学，用工程反馈控制思想建模企业/城市/世界系统
- **核心工具**：CLD（因果回路图）+ Stock-Flow 仿真
- **代表著作**：
  - Forrester《Industrial Dynamics》1961
  - Forrester《World Dynamics》1971（启发《增长的极限》）
  - Senge《第五项修炼》1990（将 SD 带入管理大众市场）
  - Sterman《Business Dynamics》2000（标准教材）
  - Meadows《系统之美》2008（最佳入门书）
- **学术社群**：System Dynamics Society
- **核心期刊**：System Dynamics Review
- **年会**：ISDC（2024 挪威卑尔根，2025 波士顿，2026 已计划）
- **最新趋势**：ISDC 2025 专设 "AI in System Dynamics" 分会场

### 2.2 复杂科学（Complexity Science）

- **核心机构**：Santa Fe Institute，1984
- **核心命题**：涌现、自组织、适应性、非线性
- **代表人物**：John Holland（复杂适应系统 CAS）、Murray Gell-Mann、Stuart Kauffman
- **核心工具**：Agent-Based Modeling（ABM）、复杂网络、分形
- **和 SD 的关系**：SD 关注宏观反馈动态，ABM 关注微观个体涌现；两者互补，有 Hybrid SD-ABM 研究
- **最新趋势**：LLM 驱动的 Agent-Based Simulation（用 LLM 扮演社会个体，模拟政策影响）

### 2.3 运筹学（Operations Research）

- **起源**：二战时期军事决策优化，1950s 学科化
- **核心工具**：线性/非线性规划、仿真优化、排队论、马尔可夫决策过程
- **学术社群**：INFORMS
- **和 SD 的关系**：共享"决策支持"目标，但 OR 偏优化，SD 偏理解动态机制

### 2.4 模糊系统 → FCM

- **模糊逻辑**：Lotfi Zadeh，1965，用语言描述不精确性
- **FCM（模糊认知图）**：Bart Kosko，1986，CLD × 模糊逻辑 = 带权重的有向图
- **FCM 的本质**：Kosko 本人称之为"可解释的循环神经网络"
- **学术社群**：IEEE 模糊系统技术委员会
- **实用工具**：FCMpy（Python）
- **和 SD 的关系**：FCM 是 CLD 的数学化扩展，是 SD 和模糊系统的交叉产物

### 2.5 因果推断（Causal Inference）

- **创始人**：Judea Pearl，《Causality》2000，《为什么》2018
- **核心命题**：相关性 ≠ 因果；干预（do-calculus）需要结构因果模型
- **核心工具**：DAG（有向无环图）、do-calculus、反事实推断
- **实用工具**：DoWhy（微软）、CausalNex（QuantumBlack/麦肯锡）、gCastle
- **学术社群**：NeurIPS/ICML/UAI 的因果方向
- **和 SD 的关系**：见下节

---

## 三、核心张力：SD vs 因果推断

两个社群**几十年来几乎互不搭理**，但研究的本质是同一件事：因果。

| 维度 | 系统动力学（SD） | 因果推断（Pearl） |
|------|----------------|----------------|
| 起源背景 | 工程 / 管理科学 | 统计 / 计算机科学 |
| 图结构 | **有向有环图**（反馈回路是核心） | **有向无环图 DAG** |
| 核心问题 | 系统长期动态是什么？ | 干预 X 对 Y 效果多大？ |
| 数据依赖 | 不需要数据（机制驱动） | 需要观测数据 |
| 输出形式 | 时间序列、反馈结构分析 | 干预效果估计量（数值） |
| 局限 | 难以从数据自动学习 | 无法直接处理反馈环 |
| 不确定性 | 定性或 Monte Carlo | 置信区间、贝叶斯后验 |

**2020 年代开始汇合**：
- 因果推断社群开始研究循环系统（Cyclic SCMs）
- SD 社群引入数据驱动方法（Data-driven SD）
- D2D 是一个桥接尝试：CLD 结构 + Monte Carlo 数值探索

---

## 四、最新前沿（2022-2025）

### 4.1 Causal AI 运动（最重要）

Bernhard Schölkopf（Max Planck Institute）2021 年发起，Yoshua Bengio 联署：

> **深度学习只学了相关性，真正的泛化需要因果结构**

推动了：
- 因果发现工具爆发（NOTEARS, PCMCI, DoWhy, CausalNex）
- LLM + 因果推断研究激增
- **世界模型（World Models）**：LeCun 的 JEPA 在尝试让模型学习因果结构

**关键论文**：arXiv 2102.11107 — "Towards Causal Representation Learning"（Schölkopf et al.）

### 4.2 LLM + 系统动力学（最直接相关）

- **arXiv 2503.21798**（2025/03）：LLM + 精心 Prompt 可生成专家级 CLD（简单结构已验证）
- **Agentic Leash arXiv 2601.00097**（2025）：LLM Agent 从文本自动提取 FCM
- **ISDC 2025**：专设 AI 分会场，这个方向正在从边缘走向主流

### 4.3 Data-driven SD

传统 SD 完全依赖专家手工建模。2023-2025 年出现混合路径：
- 用 ML 从时间序列数据中反推 Stock-Flow 结构
- D2D：无需数据，用 CLD 结构 + 参数采样做探索性仿真
- Neural ODE：深度学习直接学出微分方程（黑盒，可解释性差）

### 4.4 LLM 驱动的 ABM

用 LLM 扮演复杂系统中的个体（政策制定者、市民、企业），模拟政策落地后的集体行为涌现。和本项目不同——本项目的 Agent 是**分析**系统，不是**模拟**系统中的角色。

### 4.5 多社区 CLD 融合（NLP）

- **PMC 2025**：用 Sentence Transformer 对 13 个社区的 592 个 CLD 节点做语义相似度归并，F1=0.68
- 直接参照：多 Agent 各自构建 CLD 后的**节点融合**工程方案

---

## 五、学科入门门槛与社群资源

| 学科 | 入门门槛 | 核心入口 |
|------|---------|---------|
| 系统动力学 | 低 | 《系统之美》→ ISDC 年会论文 |
| 复杂科学 | 中 | Santa Fe Institute 夏校（有免费课程）|
| 运筹学 | 高（数学密集）| INFORMS 期刊 |
| 因果推断 | 高（统计+概率图）| Pearl《为什么》→ DoWhy 文档 |
| Causal AI | 中（需要 ML 基础）| arXiv 2102.11107 |

---

## 六、本项目在生态中的位置

```
系统动力学（SD）生态
    │
    ├── 传统 SD 建模（专家手工，Vensim/Stella）
    ├── D2D（CLD → 探索性仿真，2025）
    ├── FCM（多专家定性 → 半定量，1986）
    │
    └── ← 本项目所在的交叉口 →
         LLM Agent × 多视角隔离 × 共享 CLD × FCM 融合 × D2D 杠杆点
         （无现成产品，ISDC 2025 开始关注这个方向）
```

**护城河本质**：SD 社群懂方法论但不懂 LLM 工程；LLM 工程师不了解 SD 方法论。本项目在两者交叉口构建，方法论驱动是差异化来源。

---

## 七、关键论文索引

| # | 论文 | arXiv/来源 | 对项目价值 |
|---|------|-----------|-----------|
| 1 | Agentic Leash: LLM → FCM 提取 | arXiv 2601.00097 | LLM 自动构建 FCM 的直接参照 |
| 2 | D2D: CLD → 探索性仿真 | arXiv 2508.05659 | 杠杆点分析的核心方法 |
| 3 | LLM 自动生成 CLD（最新）| arXiv 2503.21798 | CLD 自动生成可行性实证 |
| 4 | 多社区 CLD NLP 融合 | PMC 2025 | 多 Agent CLD 融合的工程参照 |
| 5 | Towards Causal Representation Learning | arXiv 2102.11107 | Causal AI 运动的奠基论文 |
| 6 | LLMs for Causal Discovery | arXiv 2402.11068 | LLM 因果推断能力的系统评估 |
| 7 | FCMpy | arXiv 2111.12749 | FCM Python 工具的学术文献 |
| 8 | Kosko FCM 原始论文 | Int.J.Man-Machine Studies 1986 | FCM 数学基础 |

---

*Created: 2026-04-10 22:12 | Related: #15 CP-16*
