# 实现计划层文档

> 本文档沉淀 `ARCHITECTURE.md` 中与实现路径、模块落位、工程拆分、接口契约、阶段演进相关的内容。

## 1. 目标

将 CLDFlow 从现有 RAG 系统中，以“运行流程 + 模块化落位”的方式逐步实现，保证：

- 主链路清晰
- 各模块可独立测试 / 替换 / 演进
- Lead Agent 与 Module 解耦
- CLD 前置、FCM/D2D 可选并列
- 运行态可观测、可审计、可降级

## 2. 实现原则

1. **CLD 前置 + 衍生可选**：CLD 是共同根，FCM/D2D 只在 CLD 就绪后调用。
2. **Tool-as-SubSystem**：Lead Agent 只通过统一工具接口消费能力，不感知内部实现细节。
3. **模块独立**：CLD / FCM / D2D 各自为独立 Module，互不依赖。
4. **强边界校验**：层间输入输出使用 Pydantic strict mode。
5. **自审通过才传递**：每层产出先自审，再进入下游。
6. **运行隔离**：每次 `run()` 生成新的 `RunContext`，不依赖历史残留。

## 3. 目标实现结构

### 3.1 建议目录落位

```text
backend/business/cldflow/
├── service.py
├── orchestration/
│   ├── lead_agent.py
│   ├── prompts.py
│   ├── tools.py
│   ├── guardrails.py
│   └── run_context.py
├── modules/
│   ├── cld/
│   ├── fcm/
│   └── d2d/
├── models/
└── reporting.py
```

### 3.2 各模块职责

#### 输入层

- 查询增强：HyDE + 多查询
- 文档检索：按数据源分级
- 饱和度检测：重复率 / 查询轮次控制
- 来源验证：T1-T4 标记

输出：`ParsedQuery`

#### Lead Agent 编排层

- 持有完整研究上下文
- 调用 CLD / FCM / D2D 工具
- 控制预算、超时、重试、终止
- 负责最终语义融合

输出：`StructuredReport`

#### CLD Module

- 动态视角生成
- Specialist 并行提取
- 节点归并 / 冲突检测
- 裁判仲裁 / 自审

输出：`SharedCLD`

#### FCM Module

- 单 Agent 批量评级
- 权重映射
- Kosko 仿真
- 场景对比

输出：`WeightedFCM`

#### D2D Module

- 扰动分析
- 不确定性计算
- 杠杆点排序
- 可选解释生成

输出：`LeverageAnalysis`

#### 报告层

- 汇总 CLD / FCM / D2D
- 输出综合洞察
- 输出证据追溯
- 生成结构化报告或失败报告

## 4. 接口契约

### 4.1 输入层 → Lead Agent

- 输入：用户研究问题
- 输出：`ParsedQuery`

### 4.2 Lead Agent → CLD Module

- 输入：`CLDAnalysisInput`
- 输出：`CLDAnalysisOutput`
- 必选产物：`SharedCLD`

### 4.3 Lead Agent → FCM Module

- 输入：`FCMAnalysisInput`
- 输出：`FCMAnalysisOutput`
- 必选产物：`WeightedFCM`

### 4.4 Lead Agent → D2D Module

- 输入：`D2DAnalysisInput`
- 输出：`D2DAnalysisOutput`
- 必选产物：`LeverageAnalysis`

### 4.5 Lead Agent → 输出层

- 输入：`RunContext` + 各模块结构化产物
- 输出：`StructuredReport` 或 `StructuredFailureReport`

## 5. 护栏与不变量

- **I-2**：CLD 输出必须满足 JSON Schema
- **I-3**：CLD 前置，FCM/D2D 受护栏控制
- **I-4**：禁止人类介入类工具
- **I-5**：每层入口必须解析验证
- **I-6**：运行隔离
- **I-7**：自审通过才传递

## 6. Phase 演进路径

### Phase 1

- 固定 FCM 默认路径
- 实现 Lead Agent + CLD + FCM + D2D 的主链路
- 建立可观测与失败终态

### Phase 2a

- 将 FCM 模块化
- 引入统一工具接口
- 开始沉淀模块元数据

### Phase 2b

- 引入 CLD / D2D 的工具层进一步解耦
- 增强运行时选择逻辑
- 支持更细粒度的降级策略

### Phase 3

- 引入 SD / 贝叶斯等候选工具
- 基于元数据自主选择
- 持续强化审计与可替换性

## 7. 与其他文档的关联

- 主入口：`ARCHITECTURE.md`
- 数据统计：`docs/data-statistics.md`
- 版本规划：`docs/version-plan.md`





### 2.2 编排控制面（Lead Agent + 护栏）

> **架构演进**（2026-04-17）：原"Conductor 线性推进状态机"改为"Lead Agent 驱动 + 护栏约束"。自主性由 Agent 持有，不变量由护栏强制。两者不冲突，对应"Agent 持决策权 / 代码持执行权"的 Orchestrator-Worker 范式。

```
Lead Agent（LlamaIndex AgentWorkflow，持研究上下文）
    │
    ├── 权限（自主决策）
    │     ├── 解析研究任务、规划策略
    │     ├── 决定视角规模、调用哪些衍生分析
    │     ├── 跨层语义衔接（CLD → 衍生分析）
    │     ├── 观察失败 → 提议重试 / 降级 / 终止
    │     └── 报告层语义融合
    │
    └── 工具集（白名单，受护栏约束）
          ├── run_cld_analysis(question, documents) → SharedCLD
          ├── run_fcm_analysis(shared_cld, scenarios) → WeightedFCM
          ├── run_d2d_analysis(shared_cld) → LeverageAnalysis
          ├── inspect_intermediate(node_id) → 查看中间结果
          └── estimate_budget_remaining() → 预算查询

护栏（代码强约束，不可被 Agent 绕过）
    ├── Pipeline Rail：CLD 未就绪前禁止调用 FCM/D2D（I-3）
    ├── Automation Rail：禁止"请求人类澄清"类工具（I-4）
    ├── Budget Guard：Token / 时间 / 迭代上限
    ├── Schema Guard：每层输入/输出 Pydantic 校验（I-2, I-5）
    ├── Isolation Guard：RunContext 初始化，无跨运行残留（I-6）
    └── Self-Review Gate：每层产出自审通过才回传 Agent（I-7）
```

**关键职责划分**：

| 职责 | 归属 | 理由 |
|------|------|------|
| 要不要进入下一阶段 | Lead Agent | 跨层语义判断 |
| 实际推进阶段 | 护栏（代码） | 保证顺序不跳层 |
| 视角规模决策 | Lead Agent | 领域判断 |
| 失败后重试或终止 | Lead Agent 提议 + 护栏裁决 | Agent 提策略，护栏防滥用 |
| CLD → 衍生 的语义融合 | Lead Agent | 跨层推理 |
| FCM 仿真 / D2D 扰动计算 | 工具（代码） | 数学计算 |
| Token 预算追踪 | 护栏（代码） | 数值监控 |

**工具实现模式（Tool-as-SubSystem）**：

- Lead Agent 看到的是 `FunctionTool.from_defaults(async_fn=run_cld_analysis)`
- 工具内部可以是任意复杂的子系统：CLD 工具内部是多 Agent 编排，FCM 工具内部是单 Agent + Kosko 工具链，D2D 工具内部是纯 NumPy
- Lead Agent **不感知**子系统细节，只消费 `Pydantic Schema` 定义的输入输出
- 符合 Anthropic Multi-Agent Research 的 Orchestrator-Worker 范式

**架构约束**：

- **I-3 CLD 前置 + 衍生可选**：CLD 未产出前，FCM/D2D 工具调用被 Pipeline Rail 拒绝
- **I-4 全自动协作**：Lead Agent 的工具白名单不含"请求人类"类工具
- **I-6 研究运行隔离**：每次 `run()` 创建新 `RunContext`，不依赖前次运行残留

### 2.3 五层职责边界

**架构约束**：
- **I-7 自审通过才传递**：每层产出必须经过自审才进入下游，`validate_output()` 方法

#### Agent 模式决策准则

> 源自 2026-04-17 行业范式调研（Anthropic Multi-Agent Research、Deep Research Survey 2506.12594、观点"信息依赖结构 > Agent 数量"）。

**核心原则**：不问"需要几个 Agent"，问"任务的信息依赖结构是什么"。

**判断规则**（优先级从上到下）：

1. **子任务纯计算，无 LLM 推理** → **工具**（不用 Agent）
2. **子任务信息独立，可真并行** → **多 Agent 并行**（广度优先）
3. **子任务推理连续，强上下文依赖** → **单 Agent 多轮**（深度优先）
4. **默认选单 Agent**，只在证据充分时升级到多 Agent

**反模式警示**：
- 表面可并行但有全局语义依赖的任务不要用多 Agent（FCM 权重评级是典型案例）
- 多 Agent 投票做仲裁会陷入"局部正确整体错误"
- Token 成本：多 Agent 系统约 15× 单 Agent，必须有对应的性能收益才值得

**项目各层 Agent 模式**：

| 层 | Agent 模式 | 理由 |
|----|-----------|------|
| 输入层 | 单 Agent + 并发工具 | 子任务是工具性的（检索、解析） |
| **CLD 层** | **真多 Agent** | 视角真独立，广度探索有价值 |
| FCM 层 | 单 Agent + 工具 | 权重有全局图语义依赖 |
| D2D 层 | 纯工具 | 数学计算（NumPy 扰动） |
| 输出层 | 单 Agent 多轮 | 需要全局一致叙述 |

**含义**：项目的真正创新和护城河集中在 **CLD 阶段的多视角动态生成与融合**；其他阶段是"单 Agent + 领域工具"的标准组合。`backend/perspectives/` 的价值只在 CLD 阶段发挥，不应跨层复用为"通用多视角机制"。

#### Lead Agent（主链路编排 Agent）

**职责**：持有完整研究上下文，按研究问题组合调用 Module，最终做报告层语义融合

| 要素 | 形态 | 说明 |
|------|------|------|
| 运行上下文 | `RunContext`（Pydantic） | `run_id` / 预算 / 已调用工具 / 失败记录 |
| 决策轮次 | ReAct 循环 | 思考 → 调用工具 → 观察 → 思考 |
| 可用工具 | 白名单 FunctionTool | `run_cld_analysis` / `run_fcm_analysis` / `run_d2d_analysis` / 辅助工具 |
| 护栏 | 代码层强约束 | Pipeline / Automation / Budget / Schema / Isolation / Self-Review |
| 最终输出 | `StructuredReport` | Lead Agent 对 Module 结果做语义融合后产出 |

**边界**：Lead Agent 是编排者，不直接做 CLD 提取、FCM 评级、D2D 扰动等领域计算。领域计算由 Module 内部负责，Lead Agent 只消费其结构化输出。

#### 输入层

**Agent 模式**：单 Agent + 并发工具（子任务工具性，无跨任务推理依赖）

**职责**：接收查询、增强检索、标准化输入

| 子模块 | 职责 | 输出 |
|--------|------|------|
| 查询增强 | HyDE + 多查询(3-5角度) | 增强后查询列表 |
| 文档检索 | 按数据源分级检索 | 文档集合 |
| 饱和度检测 | 重复>70%或10轮/5查询硬限制 | 停止信号 |
| 来源验证 | T1-T4分级 | 来源层级标记 |

**输出契约**：`ParsedQuery`（query_text + documents + context）

#### CLD 层（因果结构提取）

**Agent 模式**：**真多 Agent**（视角真独立、广度探索有价值、符合综合集成法）

**职责**：从文档中提取因果变量和关系，构建共享因果图

| 子模块 | Agent 形态 | 职责 | 输出 |
|--------|-----------|------|------|
| 动态视角生成 | Conductor（单 Agent） | 根据问题生成3-5个 Perspective 角色 | Perspective[] |
| Specialist Agent | **多 Agent 并行** | 各视角独立 context，提取因果链 | CausalLink[] |
| 节点归并器 | 工具 | 余弦相似度>0.8 自动归并 | NodeCluster[] |
| 冲突检测器 | 工具 | 计算分歧度，分级处理 | 低/中/高分歧标记 |
| 裁判 Agent | 单 Agent | 高分歧(>0.5)时基于所有视角输出仲裁（非投票） | 融合后的 CausalLink |
| CLD 构建器 | 工具 | 组装共享因果图 | NetworkX DiGraph |

**输出契约**：`SharedCLD`（nodes + edges + metadata）

**多 Agent 约束**：
- 视角数量 3-5 个（甜蜜点，对标 STORM 与 Anthropic 经验）
- 融合策略是"单 Agent 仲裁"而非"多 Agent 投票"（避免局部正确整体错误）

#### FCM 层（模糊认知图）

**Agent 模式**：单 Agent + 工具（权重判断依赖全局图语义，不可孤立评级）

> **设计修正**（2026-04-17）：原方案"复用 CLD 视角做多 Agent 语言评级"违反 Agent 模式决策准则——边权重不是独立子任务，孤立评级一条边会丢失网络视角。修正为单 Agent 基于完整 CLD 批量评级。

**职责**：将定性因果图转化为定量权重矩阵，进行场景仿真

| 子模块 | Agent 形态 | 职责 | 输出 |
|--------|-----------|------|------|
| 权重评级 Agent | **单 Agent（看完整图）** | 基于整个 CLD 对所有边批量 ±L/M/H/VH 评级 | EdgeRating[] |
| 权重映射器 | 工具 | 7档映射 → 权重矩阵 | W[n×n] |
| 仿真引擎 | 工具 | Kosko 迭代求稳态 | 稳态状态向量 |
| 场景对比器 | 工具 | 基准场景 vs 干预场景 | 差异矩阵 |

**输出契约**：`WeightedFCM`（weight_matrix + confidence_matrix + baseline_state + intervention_states）

**为什么不用多 Agent 并行评级**：
- 边权重不独立：A→B 的强度依赖 A→C→B 是否存在、B 是否有其他因
- 表面可并行但有全局语义依赖 → 反模式（见 §2.3 Agent 模式决策准则）
- 单 Agent 一次性看完整图，能保持网络视角一致性

#### D2D 层（杠杆点分析）

**Agent 模式**：纯工具（数学计算，无 LLM 推理）

> **设计修正**（2026-04-17）：原方案将 D2D 作为 Agent 层违反决策准则——扰动分析是 NumPy 计算，不需 LLM 推理。Agent 只在需要生成解释性文本时介入。

**职责**：识别高影响力节点，排序政策干预优先级

| 子模块 | Agent 形态 | 职责 | 输出 |
|--------|-----------|------|------|
| 敏感性分析器 | 工具（NumPy） | 单节点10%扰动，测系统响应 | 影响力分数 |
| 不确定性计算器 | 工具 | 权重置信度传播 → 区间 | 置信度标记 |
| 杠杆点排序器 | 工具 | 按影响力+置信度综合排序 | 杠杆点列表 |
| 解释生成 Agent（可选） | 单 Agent | 为 Top-N 杠杆点生成文字解释 | 说明文本 |

**输出契约**：`LeverageAnalysis`（leverage_points + uncertainty_ranges）

#### 输出层

**Agent 模式**：单 Agent 多轮（需要全局一致叙述，强上下文依赖）

**职责**：结构化呈现分析结果

1. 因果结构图（CLD 可视化）
2. 场景对比表（FCM 仿真结果）
3. 杠杆点排序（影响力+置信度）
4. 证据追溯（来源 Agent + 原文引用 + 来源层级）

**为什么不用多 Agent 分段撰写**：
- 分段会产生"拼接感"，破坏叙述连贯
- 单 Agent 多轮拿完整前序产出，保证全局一致
- 可选 Reviewer 作为单独单 Agent 做质量检查，但不做并行分段

### 2.4 层间接口契约

**架构约束**：
- **I-2 CLD 输出必须符合 JSON Schema**：`SharedCLD` Pydantic model，strict mode 验证
- **I-5 数据边界解析（Parse, Don't Validate）**：每层入口必须解析验证，Pydantic validator

**接口形态演进**：原"线性层间接口"改为"**Module 工具接口**"，每个 Module 都以 `SharedCLD` 为必选输入（除 CLD Module 本身）。FCM 与 D2D **互不依赖**，无接口关系。

#### 接口 1：输入层 → Lead Agent

```yaml
输入: 用户研究问题
  └── question: str

输出: ParsedQuery
  ├── query_text: str
  ├── documents: List[Document]
  └── context: Dict
```

#### 接口 2：Lead Agent → CLD Module（前置必选）

```yaml
工具: run_cld_analysis

输入: CLDAnalysisInput
  ├── research_question: str
  ├── documents: List[Document]
  ├── perspective_hints: Optional[List[str]]    # Lead Agent 可给建议
  └── max_perspectives: int = 5

输出: CLDAnalysisOutput
  ├── shared_cld: SharedCLD                     # 不变量 I-2 强制
  │   ├── nodes: List[CLDNode]                   # 归并后的变量
  │   └── edges: List[CausalLink]                # 融合后的因果链
  ├── perspectives_used: List[PerspectiveSpec]
  ├── confidence: float
  └── diagnostics: Dict                          # 供 Lead Agent 判断是否重试
```

#### 接口 3：Lead Agent → FCM Module（衍生可选）

```yaml
工具: run_fcm_analysis

输入: FCMAnalysisInput
  ├── shared_cld: SharedCLD                     # 必选，以 CLD 为根
  ├── intervention_scenarios: Optional[List[Scenario]]
  └── simulation_config: Optional[SimConfig]

输出: FCMAnalysisOutput
  ├── weighted_fcm: WeightedFCM
  │   ├── weight_matrix: float[n][n]
  │   ├── confidence_matrix: float[n][n]
  │   ├── baseline_state: float[n]
  │   └── intervention_states: Dict[str, float[n]]
  └── diagnostics: Dict
```

#### 接口 4：Lead Agent → D2D Module（衍生可选，与 FCM 并列）

```yaml
工具: run_d2d_analysis

输入: D2DAnalysisInput
  ├── shared_cld: SharedCLD                     # 必选，以 CLD 为根
  │                                              # 注意：不从 FCM 取输入
  ├── variable_types: Dict[str, Literal["stock","flow","auxiliary","constant"]]
  └── perturbation_pct: float = 0.1

输出: D2DAnalysisOutput
  ├── leverage_analysis: LeverageAnalysis
  │   ├── leverage_points: List[NodeImpact]
  │   │   ├── node: str
  │   │   ├── impact_score: float
  │   │   ├── confidence: Literal["high", "medium", "low"]
  │   │   └── affected_nodes: List[str]
  │   └── uncertainty_ranges: Dict[str, Tuple[float, float]]
  └── diagnostics: Dict
```

#### 接口 5：Lead Agent → 输出层（报告层语义融合）

```yaml
输入: Lead Agent 持有的完整上下文
  ├── shared_cld: SharedCLD                     # 必有
  ├── weighted_fcm: Optional[WeightedFCM]        # 如调用 FCM
  ├── leverage_analysis: Optional[LeverageAnalysis]  # 如调用 D2D
  └── run_context: RunContext                    # 调用轨迹、失败记录

输出: StructuredReport
  ├── cld_visualization: GraphViz
  ├── scenario_comparison: Optional[Table]       # 视是否有 FCM 结果
  ├── leverage_ranking: Optional[List[Recommendation]]  # 视是否有 D2D 结果
  ├── synthesized_insights: Text                 # Lead Agent 语义融合产出
  └── evidence_tracing: Dict[str, Citation]
```

**融合策略明确**：
- **不存在** `FCM → D2D` 的数据变换（学术上无依据）
- **不做** Module 输出之间的硬编码融合
- Lead Agent 基于完整上下文做**语义级综合**：并列呈现 + 提炼共同洞察

### 2.5 异常路径与终态

**控制原则**：

- **硬失败**：停止流水线，不进入下游，输出失败摘要
- **软失败**：允许继续，但必须带低置信度标记进入最终报告

**典型异常路径**：

```
检索为空
    ├── 查询改写重试1次
    └── 仍为空 → 失败终态

Specialist 输出不符合 Schema
    ├── 单视角重试最多3次
    └─ 有效视角少于2个 → 失败终态

FCM 不收敛
    ├── 调整保守参数重试1次
    └─ 仍不收敛 → 失败终态

D2D 不确定区间过宽
    └─ 继续输出，但标记 low confidence
```

**失败与降级矩阵**：

| 场景 | 类型 | 处理 | 输出 |
|------|------|------|------|
| 检索为空 | 硬失败 | 改写重试后终止 | 失败摘要 |
| Schema 校验失败 | 硬失败 | 单视角重试，视角数不足则终止 | 失败摘要 |
| 节点归并 / 冲突自审失败 | 硬失败 | 修复回路，失败则终止 | 失败摘要 |
| FCM 部分边缺失评级 | 软失败 | 降低该边置信度，继续聚合 | 低置信度报告 |
| FCM 不收敛 | 硬失败 | 参数回退后仍失败则终止 | 失败摘要 |
| D2D 区间过宽 | 软失败 | 继续输出，但显式标记 | 低置信度报告 |

失败终态输出为 `StructuredFailureReport`，而不是静默中断。

---



#### 冻结原则

1. 模型能力 API only（DeepSeek/OpenAI/LiteLLM），不部署本地模型/微调
2. Agent 编排用 LlamaIndex AgentWorkflow，不引入 LangGraph
3. 可观测性必须加强
4. E2E 验证要建立可复用闭环模式


### 3.3 实现约束

#### 不变量约束（强制）

见 §1.3 架构不变量 I-1 ~ I-7。

#### 默认值（可调，非强制）

> Agent 在不变量边界内可自主调整。调整后需在运行日志中记录。

**输入层**

| 参数 | 默认值 | 来源 |
|------|--------|------|
| 检索停止硬限制 | 10轮/5查询 | D10 |
| 饱和度检测阈值 | 重复>70% | D10 |
| 输入增强 | HyDE + 多查询(3-5角度) | D12 |
| 数据源分级 | T1-T4 | D15 |
| Phase 1 数据源 | arXiv + Semantic Scholar + FRED + World Bank + OECD | D16 |
| 检索质量评估维度 | Coverage/Novelty/Authority/Depth | D19 |

**CLD 层**

| 参数 | 默认值 | 来源 |
|------|--------|------|
| 节点归并阈值 | 0.8(余弦相似度) | D5 |
| 冲突分级 | 低<0.3 / 中0.3-0.5 / 高>0.5 | D6 |
| 置信度字段 | 删除 | D23 |
| 节点ID策略 | UUID | D24 |
| strength字段 | 删除，FCM层再量化 | D25 |
| GraphML支持 | Phase 2 | D26 |
| 接口校验 | Pydantic严格模式 | D27 |

**FCM 层**

| 参数 | 默认值 | 来源 |
|------|--------|------|
| 激活函数 | Tanh | D7 |
| 权重聚合 | 均值（Phase 2→贝叶斯） | D8 |
| 语言权重映射 | 7档: ±L/M/H/VH → ±0.3/0.5/0.7/0.9 | D13 |
| 不确定区间 | 极值[min,max]（Phase 2→贝叶斯可信区间） | D14 |

**D2D 层**

| 参数 | 默认值 | 来源 |
|------|--------|------|
| 敏感性扰动 | 10% | D9 |

**跨层/全局**

| 参数 | 默认值 | 来源 |
|------|--------|------|
| 编排框架 | 自定义轻量编排器（Phase 2→AgentWorkflow） | D11 |
| 模型分工 | Specialist(DeepSeek-V3) + Evaluator(GPT-4o-mini) | D17 |
| 人类介入 | HOTL：自动执行+关键节点通知 | D18 |
| 评估模板 | 反事实对比 + Action Advancement | D22 |
| 代码评估 | 分级：语法阻塞，风格仅警告 | D28 |
| 自动修复次数 | 最多3次 | D29 |
| 类型检查 | 强制 mypy | D30 |

#### 编码规范

- **类型提示**：所有函数、方法、类声明必须补全类型提示
- **日志规范**：统一通过 `backend.infrastructure.logger.get_logger()` 获取 logger，禁止 `print`
- **异常处理**：捕获具体异常类型，记录日志后合理抛出，严禁裸 `except`
- **文件行数**：单个代码文件必须 ≤ 300 行（硬性限制）
- **验证错误**：必须包含修复指引（品味注入，信念 #10）

#### 设计模式

- **工厂模式**：`create_retriever()`, `create_reranker()`, `create_embedding()`, `create_llm()`
- **依赖注入**：所有组件通过构造函数注入依赖，禁止静态单例
- **可插拔设计**：所有核心组件支持可插拔替换
- **延迟加载**：RAGService 中的引擎按需初始化


## 5. 核心模块，组件

### 5.1 RAG 系统组件索引

| 组件 | 位置 | 功能 |
|------|------|------|
| `RAGService` | `rag_api/rag_service.py` | 统一服务入口，延迟加载引擎 |
| `ModularQueryEngine` | `rag_engine/core/engine.py` | 传统 RAG 引擎 |
| `AgenticQueryEngine` | `rag_engine/agentic/engine.py` | Agentic 引擎（ReActAgent） |
| `QueryProcessor` | `rag_engine/processing/query_processor.py` | 查询意图理解+改写 |
| `create_retriever` | `rag_engine/retrieval/factory.py` | 检索器工厂 |
| `create_reranker` | `rag_engine/reranking/factory.py` | 重排序器工厂 |
| `IndexManager` | `infrastructure/indexer/` | 向量索引管理 |
| `AppConfig` | `frontend/components/config_panel/models.py` | 统一配置模型 |

### 5.2 检索策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `vector` | 向量语义检索 | 通用语义查询 |
| `bm25` | 关键词检索 | 精确术语匹配 |
| `hybrid` | 向量+BM25+RRF融合 | 兼顾语义和关键词 |
| `grep` | 正则/文本检索 | 代码、文件名查询 |
| `multi` | 多策略组合 | 复杂查询 |

### 5.3 CLDFlow 模块映射

#### 现有可复用模块

| 位置 | 作用 | 在 CLDFlow 中的角色 |
|------|------|---------------------|
| `backend/perspectives/` | 视角模板、分类、生成、评估 | CLD 层 Perspective 生成与复用 |
| `backend/infrastructure/llms/` | LLM 创建与配置 | Specialist / Evaluator / Judge 调用入口 |
| `backend/infrastructure/observers/` | 可观测性 | 记录每层状态推进、重试与失败原因 |
| `backend/infrastructure/data_loader/` | 文档读取与解析 | 输入层文档标准化 |
| `backend/business/rag_engine/processing/` | 查询处理 | 输入增强可复用能力 |
| `backend/business/rag_engine/retrieval/` | 检索能力 | 输入层检索执行 |
| `backend/business/research_kernel/agent.py` | AgentWorkflow 实践样板 | Phase 2 编排迁移参考，不直接耦合 |

#### 建议新增模块（目标落位）

> 按 Lead Agent + Module 分层组织，每个 Module 独立自洽（可单独测试 / 替换 / 演进）。

```
backend/business/cldflow/
├── __init__.py
├── service.py                 # CLDFlowAppService 统一业务入口
│
├── orchestration/             # Lead Agent 编排层
│   ├── lead_agent.py          # Lead Agent 构建（AgentWorkflow + 工具注册）
│   ├── prompts.py             # Lead Agent system_prompt
│   ├── tools.py               # L2 薄接口层（Lead Agent 看到的 FunctionTool）
│   ├── guardrails.py          # Pipeline / Budget / Schema / Self-Review
│   └── run_context.py         # RunContext / FailureRecord
│
├── modules/                   # 独立分析 Module（Tool-as-SubSystem）
│   ├── cld/                   # CLD Module（真多 Agent 子系统）
│   │   ├── module.py          # CLDModule 主类（run() 入口）
│   │   ├── perspectives.py    # 视角生成 Agent
│   │   ├── specialist.py      # Specialist Agent（复用 research_kernel 样板）
│   │   ├── merge.py           # 节点归并工具
│   │   ├── conflict.py        # 冲突检测工具
│   │   ├── judge.py           # 裁判 Agent（高分歧时启用）
│   │   └── schema.py          # CLDAnalysisInput / CLDAnalysisOutput
│   │
│   ├── fcm/                   # FCM Module（单 Agent + 工具）
│   │   ├── module.py          # FCMModule 主类
│   │   ├── rater.py           # 单 Agent 批量权重评级
│   │   ├── mapper.py          # 7 档语言权重映射
│   │   ├── simulator.py       # Kosko 仿真工具
│   │   └── schema.py          # FCMAnalysisInput / FCMAnalysisOutput
│   │
│   └── d2d/                   # D2D Module（纯工具）
│       ├── module.py          # D2DModule 主类
│       ├── sensitivity.py     # 扰动分析
│       ├── uncertainty.py     # 不确定性计算
│       ├── ranking.py         # 杠杆点排序
│       ├── explainer.py       # 可选解释 Agent（仅 Top-N 需要文字说明时）
│       └── schema.py          # D2DAnalysisInput / D2DAnalysisOutput
│
├── models/                    # 跨模块共享 Schema
│   ├── parsed_query.py        # ParsedQuery
│   ├── shared_cld.py          # SharedCLD（I-2 不变量载体）
│   ├── weighted_fcm.py        # WeightedFCM
│   ├── leverage_analysis.py   # LeverageAnalysis
│   └── report.py              # StructuredReport / StructuredFailureReport
│
├── input/                     # 输入层（前置增强，非 Module）
│   ├── enhance.py             # HyDE + 多查询
│   ├── retrieve.py            # 数据源检索与标准化
│   └── stop_rules.py          # 饱和度检测
│
└── reporting.py               # 报告层语义融合辅助
```

> 上述目录是 **建议落位**，不是当前已实现状态。

**与现有代码的关系**：

- `backend/business/research_kernel/` 是 Lead Agent 与 Specialist 的 ReActAgent 实践样板
- `backend/perspectives/` 在 `cldflow/modules/cld/perspectives.py` 中复用（仅限 CLD Module 内部，不跨 Module 使用）
- Infrastructure 层（llms / observers / logger）保持不变，各 Module 按需注入

### 5.4 跨层协作模式

#### 工厂模式

- `create_retriever()`：根据策略类型创建对应的检索器
- `create_reranker()`：根据类型创建重排序器
- `create_embedding()`：根据配置创建 Embedding 实例
- `create_llm()`：创建 LLM 实例

#### 依赖注入

- 所有组件通过构造函数注入依赖
- 示例：`RAGService(index_manager: IndexManager)`
- 禁止静态单例或隐式全局变量

#### 延迟加载

- RAGService 中的引擎按需初始化（`@property` 装饰器）
- 避免启动时加载所有组件，提升启动速度

---