# Systematology 方向锚定与论文调研

> 调研日期：2026-07-17
>
> 决策用途：校正 Systematology 的产品目标、研究边界和 MVP 验证顺序。本文是对现有 `issue-15-Systematology架构设计与实现-v2.md` 与 `paper-research/` 材料的增量结论，不改写历史记录。
>
> 结论强度：下文把同行评审论文、预印本和软件/网页资料明确区分；不把 LLM 生成的因果边或 D2D 情景结果表述为已被证实的因果结论。

---

## 1. 结论先行

### 建议保留，但重新锚定目标

**Systematology 应定位为：面向一个明确研究问题和一个可追溯论文语料库的“证据约束因果建模研究助手”。**

它自动完成文献检索、证据片段抽取、候选因果图构建、冲突呈现与探索性情景分析；研究者在关键边、变量类型和最终解释上复核。产物是一个有版本、有出处、可反驳的系统假设模型，而不是“自动发现真实因果”或“替用户给出政策决策”。

### 需要立即调整的五项原假设

| 原假设 | 调整后的判断 | 原因 |
|---|---|---|
| `CLD -> FCM -> D2D` 三层不可拆分 | 改为“证据图/CLD 为主干，FCM 和 D2D 是两条可选分析支路”；MVP 先做 D2D 支路 | D2D 正式论文直接从带变量类型标注的 CLD 生成探索性 SD 模型；FCM 不是其必需输入。 |
| 全程自动、无人工介入；高分歧交给裁判 Agent | 改为“自动草拟 + 证据门控 + 人工复核”；Agent 只能标记/解释分歧，不能把分歧消除为事实 | 近期 CLD 研究将可追溯性、参与式审查和可复现性视为模型质量条件；LLM 裁判没有独立外部证据。 |
| 多 Agent 视角隔离是主要护城河 | 降为实现手段；真正资产是“边级证据、语境、冲突和版本历史” | 多个同质 LLM 的投票不等于多源证据。可审计的证据图才可复核、可累积、可用于比较。 |
| FCM 的语言权重可直接承载定量结论 | FCM 仅作为专家假设/情景实验的半定量表示；权重必须带来源、范围和敏感性结果 | 没有校准数据时，权重不是效应量，不能作为政策效果预测。 |
| 面向宽泛“宏观政策/法律”直接通用化 | MVP 先锚定一个证据密集、边界清晰、可获得全文的政策问题；通过后再扩展 | 目前最可靠的实证工作集中在明确领域语料和明确任务，尚不支持宽泛自治分析。 |

### 一句话的 MVP 定义

> 给定一个问题和经过筛选的论文集合，生成带逐边引用与冲突说明的候选 CLD；在用户确认变量类型和关键假设后，使用 D2D 输出带不确定性范围的**探索性**杠杆点候选与下一步数据需求。

---

## 2. 对现有材料的复核

已细读 `issue-15-Systematology架构设计与实现-v2.md`、`paper-research/论文阅读路线图.md`、`LLM-CLD-阅读记录.md`、`FCMpy-阅读记录.md` 和 `改进清单-论文赋能.md`。其中以下判断仍然成立：

- CLD 是共享模型，且“先变量、后因果边”的两阶段抽取优于一次性出图。
- 变量的方向性命名、严格 Schema、图级评估、错误类型学和迭代修订都是正确的工程方向。
- D2D 的核心价值是用不确定性表达探索性结构推演，而不是制造确定的预测。

但有三项信息已经过时或需要更精确地表述：

1. `D2D 无开源实现` 已不成立。D2D 已作为同行评审论文发表于 *BMC Medicine*（2026-06-18），论文明确说明同时提供 Python 包与 Web 应用。应先复现或对照其协议，而不是从零定义一套同名但不可比较的算法。
2. D2D 不是 FCM 的下游。D2D 的最小额外输入是将 CLD 变量标为 stock、flow、auxiliary 或 constant；它使用边存在性和极性并在参数不确定性下进行探索。将 FCM 点权重强行输给 D2D，会混淆两个模型的假设来源。
3. `全自动裁判 Agent` 没有被现有论文验证。最接近的 LLM-CLD 正式论文仍需要资深系统动力学专家重写和修订；其作者也明确把量化验证留作未来工作。

---

## 3. 近期研究的关键证据

### 3.1 D2D 已成为最直接的动力学依据

**Uleman et al. (2026), “Diagrams-to-Dynamics (D2D): Exploring causal loop diagram leverage points under uncertainty”, *BMC Medicine*.**  
DOI: https://doi.org/10.1186/s12916-026-04971-0

- 这是已发表论文，不再只是原路线图中的预印本候选。
- 它从 CLD 的边和极性出发，要求用户按协议标注变量类型，再生成探索性系统动力学模型；目标是比较杠杆点的相对潜力，并显式呈现不确定性。
- 作者将 D2D 与由同一 CLD 建立的校准 SD 模型比较；相较静态网络中心性，D2D 的杠杆点结果更一致。
- 该结果只支持“高/低杠杆点候选的探索性排序”，不支持无数据的真实效应大小、时间预测或跨领域泛化。

**对项目的含义**：D2D 应是 MVP 的主要分析支路，但必须沿用其变量标注协议、参数采样和不确定性报告方式，并把官方实现/论文结果作为基线。

### 3.2 证据三角测量比 Agent 投票更接近可靠性

**“Evidence triangulator: using large language models to extract and synthesize causal evidence across study designs” (2025), *Nature Communications*.**  
DOI: https://doi.org/10.1038/s41467-025-62783-x

- 论文采用两阶段抽取：先抽取暴露-结果概念，再抽取关系；这与现有 CLD 两阶段设计相互印证。
- 在其健康研究案例中，关系方向识别 F1 为 0.86，统计显著性识别 F1 为 0.96；它还按研究设计汇总证据的一致性。
- 这不是一般因果发现的证明，且实验领域是饮食/健康文献；但它证明“论文级证据 + 关系级抽取 + 跨设计汇总”可以构成可评测的产品核心。

**对项目的含义**：增加 `EvidenceClaim` 层，优先于 CLD/FCM。每一条候选边必须可回溯到原文片段、研究设计、语境和方向；不一致是输出，不是由裁判静默抹平。

### 3.3 自动 text-to-map 已有数据集和评测资源，但还不是免审查能力

**“Benchmarking and Assessing Transformations Between Text and Causal Maps via Large Language Models” (2025), *Applied Ontology*.**  
DOI: https://doi.org/10.1177/15705838241304102

- 提供五个开放数据集、标准格式、评测程序和 notebook，覆盖 sentence/paragraph 级的 text-to-map 与 map-to-text，包含公共卫生和生态管理等领域。
- 这为项目建立黄金集、节点/边 F1、图编辑距离、map-to-text 可读性评测提供了立即可用的外部基线。

**对项目的含义**：在自建宏观政策案例之前，先将该资源作为回归测试集；不能只依赖模型自评或“看图感觉正确”。

### 3.4 可追溯性是 CLD 的质量底线

**“Strengthening a weak link: transparency of causal loop diagrams — current state and recommendations” (2023), *System Dynamics Review*.**  
DOI: https://doi.org/10.1002/sdr.1753

- 作者审查 72 篇文章；完全满足“平实方法说明、方法可辨识、因果边来源明确”三项的比例分别仅为 44%、38% 与 25%。
- 该问题不是排版细节，而是模型能否被他人解释、修订与扩展的问题。

**对项目的含义**：来源不是附注，而是数据模型的必填字段。没有可定位来源的边不可进入“已支持 CLD”。

### 3.5 新的结构分析框架也强调参与者复核

**QSEM (2025), “The Qualitative Systems Exploration Model”, *System Dynamics Review*.**  
DOI: https://doi.org/10.1002/sdr.70015

- QSEM 分为 System Factor Classification、Loops of Interest、Archetype Identification and Analysis 三阶段。
- 它在参与式系统动力学中强调结构选择应透明、可复现、可追溯，并与 Group Model Building 脚本结合。

**对项目的含义**：将“变量分类、回路选择、系统原型”做成显式、可审查的三个工作台，而不是让 Conductor 的内部 prompt 一次性完成。

### 3.6 LLM 自动 CLD 的最新证据支持“草稿”，不支持“自治定论”

**“LLM-Powered, Expert-Refined Causal Loop Diagramming via Pipeline Algebra” (2025), *Systems*.**  
DOI: https://doi.org/10.3390/systems13090784

- 论文将流水线步骤建模为有类型、幂等的运算，以复用中间结果并实现 bit-level 可复现。
- 在案例中，资深系统动力学实践者发现初始 CLD 缺少最佳实践模式且过度依赖问题陈述；加入规则和迭代 prompt 后才改进。
- 作者明确说量化验证仍是未来工作。

**对项目的含义**：应继承“幂等、缓存、版本化中间产物”的工程思想，但不能把此论文当成“全自动 CLD 已可靠”的验证。

### 3.7 人机交互是当前高质量工具的共同模式

**CausalChat (2025), “Interactive Causal Model Development and Refinement Using Large Language Models”, *IEEE TVCG*.**  
DOI: https://doi.org/10.1109/TVCG.2025.3602448

- 工具让用户递归审查变量对、潜变量、混杂因素和中介，并将文字解释与可视图连接；作者开展了专家与非专家用户研究。
- 它与项目并不相同，但直接反驳了“用户无需参与”是唯一正确产品形态的假设。

---

## 4. 论文阅读优先级

### P0：在继续扩展流水线前必须精读

| 论文 | 为什么必须读 | 读完应形成的资产 |
|---|---|---|
| D2D, *BMC Medicine*, 2026 | 直接定义 D2D 的输入协议、探索边界、比较基线和不确定性表达 | D2D 输入标注规范、复现计划、与官方实现的对照测试 |
| Evidence triangulator, *Nature Communications*, 2025 | 直接证明论文证据抽取和跨设计因果证据汇总可量化评测 | `EvidenceClaim` Schema、两阶段提取 prompt、证据汇总规则 |
| Text/Causal Map Benchmark, *Applied Ontology*, 2025 | 外部数据集和评测方案，避免自说自话 | 外部基准接入、节点/边/图级评估脚本 |
| CLD transparency, *System Dynamics Review*, 2023 | 定义来源、方法和报告的最低质量线 | 边级出处与方法报告的发布检查表 |
| QSEM, *System Dynamics Review*, 2025 | 将 CLD 从“图”拆为可复核的结构分析流程 | 因子分类、回路与原型的 review UI/状态机 |

### P1：架构与交互设计的重要补充

| 论文 | 用途 | 限制 |
|---|---|---|
| Pipeline Algebra, *Systems*, 2025 | 幂等流水线、缓存、中间产物复用、专家修订 | 单案例，量化验证尚未完成 |
| CausalChat, *IEEE TVCG*, 2025 | 变量对探索、混杂/中介提示、文本-图联动交互 | 不是 CLD/D2D 评估论文 |
| “Leveraging Large Language Models for Automated Causal Loop Diagram Generation” (ISDC 2024 / arXiv:2503.21798) | 两阶段变量/边提取、方向性变量命名 | 44 个小型教学 CLD，非真实复杂问题验证 |
| “From Text to Map: A System Dynamics Bot for Constructing Causal Loop Diagrams” (arXiv:2402.11400) | 对照早期 text-to-CLD 工具的失败模式 | 预印本；不应作为可靠性依据 |

### P2：保留为背景，不作为 MVP 的设计依据

| 材料 | 处理建议 |
|---|---|
| FCMpy (2021) | 保留其 FCM 表达、聚合与仿真知识；不把停更风险较高的库或其论文当成核心工程方案。 |
| “Causal Autoencoder-like Generation of Feedback FCMs” (arXiv:2509.25593) | 仅借鉴可解释中间文本；它是预印本且重构误差/无反馈机制不适合作为关键路径。 |
| 一般“LLM causal discovery/reasoning”论文 | 只用于写清边界：语言模型可提出假设和检索知识，不能凭文本自身识别真实世界的因果效应。 |

---

## 5. 建议的产品与数据模型

### 5.1 最小可信流水线

```text
研究问题 + 纳入标准
        |
        v
可复现论文语料库（DOI、版本、检索式、筛选原因）
        |
        v
EvidenceClaim：原文片段 -> 变量对、方向、研究设计、语境、不确定性
        |
        v
候选 CLD：每条边保留支持/反对/不确定证据，不强迫合并
        |
        +---- 人工复核：变量词表、关键边、冲突、stock/flow/auxiliary/constant 标签
        |
        +---- FCM（可选）：专家假设下的半定量 what-if
        |
        +---- D2D（优先）：探索性杠杆点、参数不确定性、数据缺口
        |
        v
可导出的模型版本、审查记录和研究报告
```

### 5.2 `EvidenceClaim` 的最低字段

- `claim_id`、`model_version`、`source_doi`、`source_version`、`retrieval_date`
- `verbatim_excerpt`、`location`（页码/章节/字符定位）、`extractor_version`
- `cause_variable`、`effect_variable`、`polarity`、`relation_type`
- `study_design`、`population_or_context`、`intervention_or_exposure`、`outcome`
- `effect_estimate`、`uncertainty`、`statistical_significance`（若原文提供）
- `support_status`（support/contradict/ambiguous/not-causal）、`review_status`、`review_note`

CLD 的一条边应引用零到多个 `EvidenceClaim`；边本身不存“模型感觉到的置信度”来替代来源。无法提供引用的边可保留为 `hypothesis`，但不得伪装成文献支持。

### 5.3 必须写入 UI 和报告的边界语句

- “此图表示从指定语料库抽取并经审查的因果假设，不等同于已识别的因果效应。”
- “D2D 输出为在明确结构和参数假设下的探索性杠杆点排序，不是政策效果预测或行动建议。”
- “冲突证据按研究设计、语境和来源展示；未收敛不被自动解释为无效。”

---

## 6. MVP 验证门槛

不要先以“能否跑通 CLD -> FCM -> D2D”为验收。以下四道门全部通过，才有理由扩展到宏观政策/法律的通用工具。

### Gate 1：语料与出处

- 为一个窄问题冻结检索式、纳入/排除标准、论文版本和语料快照。
- 所有展示为“文献支持”的边必须能回到可定位原文；抽样人工检查其引用是否真的支持方向和关系类型。
- 记录缺失全文、矛盾结果和不可判定片段，而不是静默丢弃。

### Gate 2：抽取和 CLD 的外部评测

- 用 *Applied Ontology* 的开放资源和一个人工标注的领域小集同时测试。
- 报告变量 F1、带方向边 F1、图编辑距离、来源定位准确率、错误类型分布与模型/提示版本。
- 基线至少包括：单次 LLM 抽取、现有两阶段抽取、人工/专家标注。不得只用 LLM-as-a-judge。

### Gate 3：模型审查与结构稳定性

- 研究者逐条接受、拒绝或标记关键边；报告接受率和拒绝原因。
- 对同一冻结语料的重跑，比较节点、边、回路和证据引用的稳定性；随机性不能被“多 Agent 一致”掩盖。
- 对变量分类、回路和原型按 QSEM 式的显式步骤保留审查日志。

### Gate 4：D2D 的正确比较方式

- 先使用 D2D 论文的变量类型标注协议，而不是把 FCM 离散语言权重直接灌入。
- 与官方 D2D 实现或一个具有已知校准 SD 模型的案例比较：报告杠杆点排序的一致性、敏感性和不确定性覆盖。
- 如果没有外部基准，只能显示“待验证的结构假设”，不能宣称“找到了最优杠杆点”。

---

## 7. 接下来的实施顺序

1. **冻结方向和边界**：将项目描述改为“evidence-grounded causal modelling copilot”；删除或标注所有“自动决策/预测真实走向”的表述。
2. **先建证据层**：实现语料快照、`EvidenceClaim`、逐边引用、支持/反对并存和模型版本化；这是后续多 Agent、FCM、D2D 共用的基础。
3. **建立外部基准**：接入 text-to-map 数据集和 D2D 对照案例；再决定现有 Specialist、Judge、合并器的具体改造。
4. **实现可复核 CLD 工作台**：采用两阶段变量/边抽取，明确变量词表、边证据和冲突；将“裁判”改成“证据汇总/分歧解释”。
5. **把 D2D 作为第一个动力学 MVP**：在审查后的 CLD 上运行，输出假设、区间、敏感性与数据缺口。FCM 延后为可插拔的专家情景模块。
6. **只做一个垂直案例**：选择有足够同行评审文献、可获得全文、结果可对照的单一政策议题；不要同时做财政补贴、Prop 13 和泛法律分析。

---

## 8. 调研方法与范围

- 本轮重点复核了仓库内 `Research & Brainstorm` 的架构、阅读记录和改进清单。
- 外部检索于 2026-07-17 通过 OpenAlex 进行，检索主题包括 `causal loop diagram`、`large language model causal`、`text causal map`、`evidence triangulation` 和 `participatory system dynamics`；对关键论文回到 DOI/期刊页面核对出版状态与摘要。
- 优先级：同行评审期刊 > 正式会议论文 > 预印本 > 软件/网页资料。D2D、Evidence Triangulator、QSEM 等近期论文发布不久，引用次数仍低，本文按研究设计、发表渠道和与问题的直接性判断，不以早期引文量排序。
- 这不是系统综述或 meta-analysis；它的用途是为当前产品范围建立可执行、可证伪的研究锚点。后续进入具体垂直领域时，需要针对该领域另做协议化系统检索。

---

## 9. 最终决策

**建议采纳：保留“CLD + 探索性动力学 + 杠杆点”的研究雄心，但把产品从“全自动多 Agent 决策器”改为“有证据出处、可复核、可版本化的因果建模协作工具”。**

这不是缩小价值，而是将可验证性置于生成能力之前。若 Gate 1-4 能在一个垂直案例中成立，项目才拥有向宏观政策和法律问题扩展的可靠基础。
