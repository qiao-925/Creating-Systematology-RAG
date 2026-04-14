# Issue #15: 综合集成法架构洞察

> 一句话目标：从综合集成法案例推导出 Agent 的工程架构，找到可落地的实现路径

---

## Phase 1: 调研与框架（04-10 ~ 04-12）✅

**阶段目标**：完成技术调研 + 模板系统基础架构

### Checkpoint

| CP | 内容 | 状态 |
|----|------|------|
| 1 | 案例还原（财政补贴、价格、工资） | ✅ |
| 2 | 多 Agent 视角隔离方案 | ✅ |
| 3 | 发现核心缺失：共享模型（CLD） | ✅ |
| 4 | 系统动力学概念映射到架构 | ✅ |
| 5 | 图表达 > 文字表达（思维力启发） | ✅ |
| 6 | 系统科学理论版图梳理 | ✅ |
| 7 | 两个维度澄清：工程实现 × 领域定制 | ✅ |
| 8 | 思维路径元认知分析 | ✅ |
| 9 | 三支柱难度本质分析（领域定制=知识问题） | ✅ |
| 10 | 自动 checkpoint 机制设计（AGENTS.md 3轮触发） | ✅ |
| 11 | 调研工具生态（CLD/FCM/D2D/Agentic Leash）并写入文档 | ✅ |
| 12 | D2D 确认为核心输出目标（杠杆点+走向），不可降级为 Phase 2 | ✅ |
| 13 | 范围决策：CLD→FCM→D2D 完整流水线，Phase 1 含简化版 D2D | ✅ |
| 14 | 入门学习路径锁定，验证案例：财政补贴 + Prop 13 | ✅ |
| 15 | FCM 交互式学习完成，理解到位 | ✅ |
| 16 | D2D 交互式学习完成 + 生态图谱文档创建 | ✅ |

### 关键上下文

- **决策**：多 Agent + 共享 CLD → FCM → D2D 完整流水线（三层不可拆分）
- **关键洞察**：
  - D2D 是核心输出，不是 Phase 2 可选项——研究的本质是找杠杆点和预判走向
  - CLD/FCM/D2D 是递进的三层：地图 → 加权地图 → 可仿真的导航
  - 学科谱系：控制论(1948)→系统动力学(1956)→FCM(1986,模糊逻辑×SD)→D2D(2025)
  - Agentic Leash（arXiv 2601.00097）= 最接近目标的现有研究，单Agent+FCM，无多视角隔离
  - 项目护城河：SD生态 × LLM Agent × 多视角隔离，三者交叉无现成产品
  - D2D 的不成熟是设计上的诚实（Monte Carlo 表达不确定性），不是缺陷
  - 验证案例：财政补贴（已熟悉）→ Prop 13（1978加州房产税，47年可对照数据）
  - FCM 学习笔记：权重有向图+迭代计算+场景对比预测；用户立场：FCM 本质是定性的（权重表达强度，非实际量）
  - 《系统之美》已读，定性反馈理论基础充足
  - **关键定位洞察**：宏观系统是最佳应用场景，政策/法律是天然切入点（垂直方向的护城河）
  - CLD 出发两条平行路径：FCM（加权重+矩阵迭代→稳态）vs D2D（打节点类型+ODE→时间序列+杠杆点）
  - 待调研：Participatory AI Modeling 论文群（最接近目标架构的学术参照）
  - 新论文补录：PMC 2025（多社区 CLD NLP 融合，直接参照多Agent融合工程路径）+ arXiv 2503.21798（LLM自动生成CLD可行性实证，2025/03）
- **技术选型锁定（MVP）**：NetworkX（CLD）+ FCMpy封装层（FCM）+ Sentence Transformer（节点归并）+ Instructor（LLM结构化输出）+ FCM敏感性分析（Phase 1 杠杆点）
- **Phase 2 优化备忘**：FCM 边权重 Phase 1 用点估计，Phase 2 引入贝叶斯聚合升级为分布估计（`0.8±0.15`），让 D2D Monte Carlo 有理论依据

### 新增决策（2026-04-12）

#### 输入增强层决策
- 检索策略：HyDE（假设文档嵌入）+ 多查询检索（3-5 个不同角度）
- 数据源分级：T1（政府/顶级期刊）/ T2（学术预印本/智库）/ T3（主流媒体）/ T4（过滤）
- Phase 1 数据源：arXiv API + Semantic Scholar + FRED + World Bank + OECD

#### 检索停止与评估决策
- 停止条件三层：硬限制（10 轮/每轮 5 查询）+ 饱和度检测（连续 2 轮 Novelty < 30%）+ Coverage ≥ 80%
- 评估策略：分离检索器与评估器（Generator-Evaluator 分离）
- 四维评估：Coverage / Novelty / Authority / Depth

#### 多模型与人类介入决策
- 多模型架构 Phase 1：Specialist(DeepSeek-V3) + Evaluator(GPT-4o-mini) 双模型对照
- 人类介入模式：HOTL（Human-on-the-Loop）——自动执行 + 关键节点通知
- 必须介入点：方向确认、节点归并争议（相似度 0.65-0.85）、硬限制到达

#### 死亡循环防护
- 硬限制：10 轮检索、每轮 5 查询、成本/时间上限
- 智能检测：连续无新发现、重复率 > 70%
- 人工兜底：硬限制到达强制确认

### 调研产出

| 主题 | 文档 |
|------|------|
| CLDFlow 业务流程图 | [00](issue-15-sub_docs/00-业务流程图.md) | 五层流水线可视化（Mermaid）|
| RAG 查询改写与输入增强 | [01](issue-15-sub_docs/01-input-enhancement.md) |
| 检索停止条件与评估策略 | [02](issue-15-sub_docs/02-stopping-criteria.md) |
| 输入增强评估策略（综合版） | [03](issue-15-sub_docs/03-evaluation-strategy.md) |
| 学术与政策研究可靠数据源 | [04](issue-15-sub_docs/04-academic-sources.md) |
| 多模型评估与人类介入机制 | [05](issue-15-sub_docs/05-human-in-loop.md) |
| 动态视角 Agent 生成 | [06-dynamic-agent](issue-15-sub_docs/06-dynamic-agent.md) |
| 模板评估业内实践 | [07-template-evaluation](issue-15-sub_docs/07-template-evaluation.md) |
| 模板实施报告 | [08-implementation-report](issue-15-sub_docs/08-implementation-report.md) |

### 实施产出

- **Phase 1 完成**：`backend/perspectives/` 完整模块体系
  - 核心模块：`classifier.py`, `generator.py`, `registry.py`, `evaluator.py`
  - 初始模板：基础模板 + 4 个 DDC 领域模板（320/330/340/360）
  - 测试覆盖：22 个单元测试全部通过
  - 文档：`README.md` + 实施报告
- **评估框架**：反事实对比 + Action Advancement（占位实现，待真实测试）
- **待办**：真实环境集成测试 + 可视化评估报告（挂起，待集成环境就绪）

### 阶段关联文档

- `docs/metasynthesis-architecture-insight-2026-04-10.md`（完整思维路径）
- `docs/brainstorm-product-direction-2026-04-10.md`（前序讨论）
- `docs/competitive-landscape-2026-04-10.md`（竞品调研）
- `docs/research-cld-engineering-landscape-2026-04-10.md`（工具生态调研）
- `docs/ecosystem-map-system-dynamics-2026-04-10.md`（学科生态图谱）

---

## Phase 2: 工程实现（04-12 ~ ）⏳

**阶段目标**：进入架构设计：模块接口 + 流水线实现

### 当前状态

| CP | 内容 | 状态 |
|----|------|------|
| 17 | 架构设计：模块接口 + 流水线实现 | ⏳ 进行中 |

### 决策

| 日期 | 决策 | 来源 |
|------|------|------|
| 04-12 | 流水线锁定：CLD → FCM → D2D（三层不可拆分） | 方向讨论 |
| 04-12 | 技术栈：NetworkX(CLD) + FCMpy(FCM) + Sentence Transformer | 工具生态调研 |
| 04-12 | 输入增强：HyDE + 多查询检索（3-5 角度） | 输入层调研 |
| 04-12 | 检索停止：10 轮/5 查询 + 饱和度检测 | 停止条件调研 |
| 04-12 | 多模型：Specialist(DeepSeek-V3) + Evaluator(GPT-4o-mini) | 人机协同调研 |
| 04-12 | 模板评估：反事实对比 + Action Advancement（占位实现，待真实环境测试）| 评估策略调研 |

### 节点记录（2026-04-13）—— 测试新规则

| 时间 | 类型 | 内容 | 触发 |
|------|------|------|------|
| 04:30 | 图 | 五层运行架构草图（CLD→FCM→D2D 流水线） | AI自动：ASCII图 detected |
| 04:40 | 洞察 | 上下文容易丢失，需加强记录粒度（work-memory-boost 偏粗） | AI自动："我突然想到"语义 |
| 04:45 | 决策 | 采用「轻量级节点标记」方案（A+B混合），不过度设计 | 用户显式："先去做" |
| 04:52 | 图 | 业务流程图 - 保持原版 ASCII 格式 | 用户要求：原封不动 |
| 05:04 | 洞察 | 代码生成质量控制：采用 OpenAI 计划+任务拆分模式，业务评估器延后、代码评估器优先 | AI自动："想到"语义 |
| 05:09 | 决策 | 先确定业务架构（CLD/FCM/D2D 三层核心），再细化工程架构；代码生成质量控制在工程设计阶段考虑 | 用户显式 |
| 05:10 | 下一步 | 业务架构：输入增强✅、多视角Agent✅，开始思考 CLD 因果结构提取层详细逻辑 | 用户显式 |
| 05:23 | 决策 | CLD 层急需调研：提取指令、节点归并 Embedding 选型、冲突检测算法、数据格式，按主题统一做调研 | 用户显式 |
| 05:29 | 完成 | 批量调研完成：12 个文档（CLD 4 + FCM 3 + D2D 2 + 跨层 3），待集中阅读决策 | 批量产出 |
| 06:21 | 决策确认 | 4个关键决策全部确认：(1)JSON Schema输出格式 (2)全自动协作模式 (3)无人工介入点 (4)高分歧用裁判Agent | 用户确认 |

### 调研（进行中）

| 主题 | 状态 | 文档 |
|------|------|------|
| **因果层 - 因果链提取指令设计** | ✅ 完成待阅读 | issue-15-sub_docs/09-cld-extraction-prompt.md |
| **因果层 - 节点归并向量模型选型** | ✅ 完成待阅读 | issue-15-sub_docs/10-cld-node-merging.md |
| **因果层 - 冲突检测与消解算法** | ✅ 完成待阅读 | issue-15-sub_docs/11-cld-conflict-resolution.md |
| **因果层 - 数据格式与接口标准化** | ✅ 完成待阅读 | issue-15-sub_docs/12-cld-data-format.md |
| **模糊层 - 语言权重到数值转换** | ✅ 完成待阅读 | issue-15-sub_docs/13-fcm-weight-conversion.md |
| **模糊层 - 模糊认知图仿真算法** | ✅ 完成待阅读 | issue-15-sub_docs/14-fcm-simulation.md |
| **模糊层 - 多专家权重聚合算法** | ✅ 完成待阅读 | issue-15-sub_docs/15-fcm-aggregation.md |
| **动力层 - 敏感性分析算法** | ✅ 完成待阅读 | issue-15-sub_docs/16-d2d-sensitivity-analysis.md |
| **动力层 - 不确定区间计算** | ✅ 完成待阅读 | issue-15-sub_docs/17-d2d-uncertainty.md |
| **指挥调度机制** | ✅ 完成待阅读 | issue-15-sub_docs/18-conductor-orchestration.md |
| **检索停止条件与收敛判断** | ✅ 完成待阅读 | issue-15-sub_docs/19-retrieval-stopping.md |
| **代码生成质量评估与测试策略** | ✅ 完成待阅读 | issue-15-sub_docs/20-code-quality-evaluator.md |
| 架构详细设计 | ✅ 完成 | 4个关键决策已确认，进入Phase 1 MVP实现 |
| Participatory AI Modeling 论文群 | 📋 待启动 | - |
| MCP 工具生态调研 | ✅ 完成 | [docs/mcp-tools-landscape.md](../../docs/mcp-tools-landscape.md) |

### 实施（进行中）

| 任务 | 状态 |
|------|------|
| 模块接口定义 | 📋 待启动 |
| 流水线实现 | 📋 待启动 |
| A线: Research Kernel MVP 闭环 | 📋 待启动 | #13 子任务，E2E验证 |

### 回文/Pending

| 项目 | 说明 | 预计处理 |
|------|------|----------|
| 🔴 模板真实环境测试 | 依赖 Conductor 集成完成 | Phase 3 |
| 📝 FCM 贝叶斯聚合 | Phase 2 优化点，从 Phase 1 决策带回 | 架构设计时考虑 |
| 🔴 D2D 论文无开源实现 | 完整 ODE+Monte Carlo 需自己实现 | Phase 2/3 |
| 📝 模板评估框架真实测试 | 反事实+AA 占位实现，需 Conductor 集成后测试 | Phase 3 |
| 📝 阶段性结束标准讨论 | 确定以哪个 Issue/Phase 作为第一里程碑（建议：Issue #13 MVP 闭环） | 待决策 |

---

## Phase 3: 验证优化（待定）⬜

**阶段目标**：模板真实环境测试 + 黄金数据集 + 可视化报告

### 待办

- [ ] 模板真实环境测试（依赖 Conductor 集成）
- [ ] 黄金数据集构建
- [ ] 可视化评估报告

---

## 项目锁定

| 项 | 内容 |
|----|------|
| **项目名称** | CLDFlow — 方法论编码于架构的系统科学研究 Agent |
| **EN Description** | A methodology-driven agent for complex system analysis — tracing causal structure (CLD), weighting relationships (FCM), and identifying leverage points (D2D) — to support better decisions on macro-level policy and system problems. |
| **CN Description** | 面向复杂系统分析的方法论驱动 Agent——追踪因果结构（CLD）、量化关系权重（FCM）、识别杠杆点（D2D），为宏观政策与系统问题的决策提供结构化支撑。 |

---

## 图例

| 图标 | 含义 |
|------|------|
| ✅ | 已完成 |
| ⏳ | 进行中 |
| ⬜ | 待启动 |
| 📋 | 待办/未开始 |
| 🔴 | 阻塞项 |
| 📝 | 回文/后续优化 |

---

---

## 未来考虑：MCP 工具层集成（2026-04-13）

> 背景：调研了 Playwright MCP 的工作原理和当前 MCP 生态，整理了与本项目相关的集成点。

### Playwright MCP 原理摘要

- **不用截图**：通过 `page.accessibility.snapshot()` 读取浏览器 AOM 语义树（角色/名称/状态），LLM 看结构不看像素
- **稳定定位**：自定义序列化器 `snapshotter.ts` 将 AOM 转为 YAML-like 格式，每个元素分配 `ref=eX` 临时 ID，LLM 直接引用
- **协议层**：JSON-RPC over WebSocket/stdio，AI 客户端调用标准工具 → Server 翻译成 Playwright API → 返回结果

### 与 CLDFlow 的潜在集成点

| MCP 工具 | 潜在用途 | 优先级 |
|----------|----------|--------|
| **Exa MCP** | Perspective Agent 的语义搜索工具，结构化 JSON 对 RAG pipeline 友好 | 高（Phase 2/3） |
| **Tavily MCP** | research mode 多步搜索计划，适合 Conductor 调度的深度调研场景 | 中 |
| **Playwright MCP** | 爬取需要登录的数据源（FRED/World Bank 动态页面）、可视化结果截图 | 低（Phase 3） |
| **GitHub MCP** | 已用于当前工作流，Actions 监控 CI 状态 | 已在用 |
| **Filesystem MCP** | 白名单目录访问，可配合 Agent 读写本地 data/ 目录 | 视需要 |

### 决策

- Phase 2 架构设计时在 Perspective Agent 工具层**预留 MCP 接口插槽**（不锁定具体实现）
- Exa/Tavily 作为搜索工具优先候选，视 API 成本决定
- 详细工具清单：[docs/mcp-tools-landscape.md](../../docs/mcp-tools-landscape.md)

---

*Issue: #15 | Updated: 2026-04-13*
