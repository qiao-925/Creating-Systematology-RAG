# Issue #15: CLDFlow 架构设计与实现

> 面向复杂系统分析的方法论驱动 Agent——追踪因果结构（CLD）、量化关系权重（FCM）、识别杠杆点（D2D），为宏观政策与系统问题的决策提供结构化支撑。

## 1. Checkpoint 时间线（倒序）

| 日期 | 内容 |
|------|------|
| 04-16 | 同步完善业务架构图与工程架构图：新增 `docs/CLDFlow-engineering.md` |
| 04-16 | 在业务架构中补全 Conductor 控制面、FCM评分主体、异常路径与失败终态 |
| 04-16 | 明确工程落位：现有可复用模块 vs 建议新增 `backend/business/cldflow/` 目录 |
| 04-15 | 完成文档迁移：28个调研文档精简迁移到 docs/，建立分层文档体系 |
| 04-15 | 落地 Harness Engineering 15命题 → core-beliefs + invariants + defaults |
| 04-15 | 重写 AGENTS.md 为地图模式（≤100行），docs/ 分类为 core/cldflow/research/engineering |
| 04-15 | 全局项目扫描：识别工程架构图缺失、Conductor角色未定义、异常路径缺失 |
| 04-15 | 识别业务架构三大缺口：Conductor全局角色 / 异常路径 / FCM评级主体 |
| 04-13 | 确认4个关键决策：JSON Schema输出 / 全自动协作 / 无人工介入 / 高分歧裁判Agent |
| 04-13 | 画出五层运行架构草图（CLD→FCM→D2D 流水线） |
| 04-13 | 选定「轻量级节点标记」方案（A+B混合），拒绝过度设计 |
| 04-13 | 保留业务流程图原版 ASCII 格式 |
| 04-13 | 决定代码评估器优先、业务评估器延后 |
| 04-13 | 确定先做业务架构再细化工程架构 |
| 04-13 | 完成批量调研：12个文档（CLD 4 + FCM 3 + D2D 2 + 跨层 3） |
| 04-12 | 锁定流水线：CLD→FCM→D2D（三层不可拆分） |
| 04-12 | 选定技术栈：NetworkX + FCMpy + Sentence Transformer + Instructor |
| 04-12 | 选定输入增强：HyDE + 多查询检索（3-5角度） |
| 04-12 | 设定检索停止：10轮/5查询 + 饱和度检测 |
| 04-12 | 设定模型分工：Specialist(DeepSeek-V3) + Evaluator(GPT-4o-mini) |
| 04-12 | 选定模板评估：反事实对比 + Action Advancement（占位实现） |
| 04-12 | 完成 Phase 1：`backend/perspectives/` 5模板+22测试通过 |
| 04-12 | 认清D2D是核心输出，不是Phase 2可选项——研究本质是找杠杆点和预判走向 |
| 04-12 | 理解CLD/FCM/D2D递进关系：地图→加权地图→可仿真的导航 |
| 04-12 | 接受D2D的不成熟是设计上的诚实（Monte Carlo表达不确定性），不是缺陷 |
| 04-12 | 确认宏观系统是最佳应用场景，政策/法律是天然切入点（垂直护城河） |
| 04-12 | 认清FCM本质是定性的（权重表达强度，非实际量） |
| 04-12 | 规划Phase 2优化：FCM边权重从点估计升级为贝叶斯分布估计 |
| 04-10 | 发现综合集成法核心不是多专家讨论，是「共享模型」——CLD作为定性到定量的桥梁 |
| 04-10 | 确认多Agent保证视角纯度：Prompt/Knowledge/Tools 三层隔离 |
| 04-10 | 发现收敛驱动力=模型推演vs专家直觉的张力消解，不是轮次耗尽 |
| 04-10 | 确认CLD定性推理是最小可行的「定量」——不需要数值仿真 |
| 04-10 | 推导出架构：Conductor + Perspective Agents(MCP tools) + 共享模型(CLD) + 推演-反馈环 |
| 04-10 | 梳理学科谱系：控制论(1948)→系统动力学(1956)→FCM(1986)→D2D(2025) |
| 04-10 | 找到最接近竞品 Agentic Leash(arXiv 2601.00097)，单Agent+FCM，无多视角隔离 |
| 04-10 | 确认护城河：SD生态×LLM Agent×多视角隔离，三者交叉无现成产品 |
| 04-10 | 确立概率vs确定性双层：Skill层(软约束→创造力) + 架构层(硬约束→可靠性) |
| 04-10 | 锁定范围：CLD→FCM→D2D完整流水线，Phase 1含简化版D2D |
| 04-10 | 锁定验证案例：财政补贴（已熟悉）+ Prop 13（1978加州房产税，47年可对照数据） |
| 04-10 | 收录新论文：PMC 2025（多社区CLD NLP融合）+ arXiv 2503.21798（LLM自动生成CLD实证） |

---

## 3. 执行视图（决策 + 任务）

> 决策 = 执行指令（低可逆），任务 = 执行步骤（高可逆）。
> 状态：✅已定 / ⏳待定(有建议值) / 🔄可回访

### 📥 输入层

**决策**

| ID | 决策 | 指令 | 状态 | 理由 |
|----|------|------|------|------|
| D10 | 何时停止检索 | 混合停止：硬限制保底 + 饱和度智能收敛 | ✅ | 防止无限循环 |
| D12 | 如何增强输入 | 用 HyDE + 多查询检索(3-5角度) | ✅ | HyDE绕过语义鸿沟，多查询覆盖多视角 |
| D15 | 数据源如何分级 | T1(政府/顶级期刊)/T2(学术预印本/智库)/T3(主流媒体)/T4(过滤) | ✅ | 来源可信度分层，保证证据质量 |
| D16 | Phase 1 用哪些数据源 | arXiv API + Semantic Scholar + FRED + World Bank + OECD | ✅ | 免费、稳定、高质量 |
| D19 | 如何评估检索质量 | 四维: Coverage/Novelty/Authority/Depth | ✅ | 全面评估检索质量 |
| D20 | 如何防止死亡循环 | 硬限制(10轮/5查询) + 智能检测(重复>70%) + 人工兜底 | ✅ | 防止检索循环和工具风暴 |

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T13 | 调研输入增强方案 | ✅ | HyDE/停止条件/学术来源 |
| T20 | 实现输入增强层 | 📋 | HyDE+多查询+来源过滤+停止条件 |

### 🔗 CLD层

**决策**

| ID | 决策 | 指令 | 状态 | 理由 |
|----|------|------|------|------|
| D1 | 提取结果用什么格式 | 输出为 JSON Schema | ✅ | 强制结构化，下游全依赖此格式 |
| D2 | 多Agent如何协作 | 全自动协作：3Agent并行提取 + 自动融合 | ✅ | 多视角并行效率高，自动融合保证一致性 |
| D3 | 是否设人工介入 | 全程自动，不设人工介入点 | ✅ | Phase 1验证可行性，人工介入增加复杂度 |
| D4 | 高分歧如何消解 | 由裁判Agent元投票消解 | ✅ | 高分歧需权威消解，裁判Agent比人工快 |
| D5 | 节点归并阈值 | 设为 0.8(余弦相似度) | ✅ | 平衡精确与召回 |
| D6 | 冲突如何分级 | 低<0.3自动聚合 / 中0.3-0.5自动聚合 / 高>0.5送裁判 | ✅ | 三级分流 |
| D23 | 置信度字段是否保留 | 删除（→B） | ⏳ | 减少Prompt复杂度，冲突检测可推断 |
| D24 | 节点ID用什么策略 | 用 UUID（→A） | ⏳ | 简单可靠，无哈希冲突风险 |
| D25 | strength字段是否保留 | 删除（→B），Phase 1只保留极性 | ⏳ | FCM层再量化 |
| D26 | 何时支持GraphML | Phase 2 再支持（→B） | ⏳ | JSON+NetworkX足够调试 |
| D27 | 接口校验多严格 | 用 Pydantic 严格模式（→A） | ⏳ | 生产环境必需，提前发现错误 |

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T9 | 调研CLD层(4文档) | ✅ | 提取Prompt/节点归并/冲突检测/数据格式 |
| T16 | 实现CLD层核心 | 📋 | 提取Agent+归并器+冲突检测器+裁判Agent |

### 🧮 FCM层

**决策**

| ID | 决策 | 指令 | 状态 | 理由 |
|----|------|------|------|------|
| D7 | FCM用什么激活函数 | 用 Tanh | ✅ | 对称输出，适合正负权重 |
| D8 | 权重如何聚合 | 用均值聚合（Phase 2→贝叶斯） | 🔄 | Phase 1最简公平；Phase 2需历史数据 |
| D13 | 语言权重如何映射 | 7档映射: -VH(-0.9) -H(-0.7) -M(-0.5) -L(-0.3) +L(+0.3) +M(+0.5) +H(+0.7) +VH(+0.9) | ✅ | 论文标准7档，覆盖强弱正负 |
| D14 | 不确定区间怎么算 | 用极值区间[min,max]（Phase 2→贝叶斯可信区间） | 🔄 | Phase 1最简 |

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T10 | 调研FCM层(3文档) | ✅ | 权重转换/仿真算法/聚合算法 |
| T17 | 实现FCM层核心 | 📋 | 权重映射+Kosko仿真+场景对比 |

### 📐 D2D层

**决策**

| ID | 决策 | 指令 | 状态 | 理由 |
|----|------|------|------|------|
| D9 | 敏感性扰动多少 | 扰动 10% | ✅ | 保守，避免过度反应 |

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T11 | 调研D2D层(2文档) | ✅ | 敏感性分析/不确定区间 |
| T18 | 实现D2D层核心 | 📋 | 敏感性分析+不确定区间+杠杆点排序 |

### 🔄 跨层/全局

**决策**

| ID | 决策 | 指令 | 状态 | 理由 |
|----|------|------|------|------|
| D11 | 用什么编排框架 | 自定义轻量编排器（Phase 2→AgentWorkflow） | 🔄 | 流程固定可控 |
| D17 | 模型如何分工 | Specialist(DeepSeek-V3) 生成 + Evaluator(GPT-4o-mini) 评估 | ✅ | 生成用强模型，评估用快模型 |
| D18 | 人类如何介入 | HOTL：自动执行 + 关键节点通知（Phase 2可能需确认） | 🔄 | 平衡效率与安全 |
| D21 | 技术栈选什么 | NetworkX(CLD) + FCMpy(FCM) + Sentence Transformer(归并) + Instructor(LLM) | ✅ | 各层最优工具组合 |
| D22 | 如何评估模板 | 反事实对比 + Action Advancement | ✅ | 双维度验证模板价值 |
| D28 | 代码评估多严格 | 分级：语法必须通过，风格仅警告（→B） | ⏳ | 语法阻塞，风格不阻塞 |
| D29 | 自动修复几次 | 最多3次（→3） | ⏳ | 平衡修复与成本 |
| D30 | 类型检查是否强制 | 强制 mypy（→A） | ⏳ | Python 3.12+mypy能发现很多问题 |

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T7 | 实现模板系统 | ✅ | `backend/perspectives/` 5模板+22测试 |
| T8 | 实现评估框架 | ✅ | 反事实+AA（占位） |
| T12 | 调研跨层机制(3文档) | ✅ | Conductor编排/检索停止/代码质量评估 |
| T14 | 调研MCP工具生态 | ✅ | [docs/mcp-tools-landscape](../../docs/mcp-tools-landscape.md) |
| T15 | 定义数据结构(Pydantic models) | 📋 | Node/CausalLink/SharedCLD/WeightedFCM/LeverageAnalysis |
| T19 | 实现Conductor编排 | 📋 | 流水线串联+错误处理+循环防护 |

### 🧭 方向与定位

**任务**

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| T1 | 还原案例（财政补贴、价格、工资） | ✅ | 洞察：共享模型是核心 |
| T2 | 设计多Agent视角隔离方案 | ✅ | Prompt/Knowledge/Tools三层隔离 |
| T3 | 将系统动力学映射到架构 | ✅ | CLD→FCM→D2D递进三层 |
| T4 | 调研工具生态 | ✅ | [docs/research-cld-engineering-landscape](../../docs/research-cld-engineering-landscape-2026-04-10.md) |
| T5 | 调研竞品 | ✅ | [docs/competitive-landscape](../../docs/competitive-landscape-2026-04-10.md) |
| T6 | 绘制学科生态图谱 | ✅ | [docs/ecosystem-map-system-dynamics](../../docs/ecosystem-map-system-dynamics-2026-04-10.md) |

### 🧪 验证（Phase 3）

| ID | 任务 | 状态 | 前置 |
|----|------|------|------|
| T21 | 执行E2E验证 | 📋 | T15-T20 |
| T22 | 调研Participatory AI Modeling论文 | 📋 | — |
| T23 | 测试模板真实环境 | 🔴 | T19(Conductor集成) |
| T24 | 构建黄金数据集 | 📋 | T21 |
| T25 | 生成可视化评估报告 | 📋 | T21 |
| T26 | 测试评估框架 | 🔴 | T19 |

---

## 4. 阻塞与回文

| 项目 | 类型 | 说明 | 处理时机 |
|------|------|------|----------|
| 🔴 模板真实环境测试 | 阻塞 | 依赖Conductor集成完成 | Phase 3 |
| 🔴 D2D无开源实现 | 阻塞 | 完整ODE+Monte Carlo需自实现 | Phase 2/3 |
| 📝 FCM贝叶斯聚合 | 回文 | Phase 2优化，D8回访 | 架构设计时预留接口 |
| 📝 评估框架真实测试 | 回文 | 反事实+AA占位实现 | Phase 3 |
| 📝 阶段性结束标准 | 回文 | 第一里程碑建议：Issue #13 MVP闭环 | 待决策 |

---

## 5. 文档索引

> 调研文档已迁移到 docs/，原始 sub_docs 可删除。

### 核心架构文档（docs/ 根目录）

| 文档 | 内容 | 关联决策 |
|------|------|----------|
| [core-beliefs](../../docs/core-beliefs.md) | 15命题，三层结构 | 全局 |
| [CLDFlow-invariants](../../docs/CLDFlow-invariants.md) | 7个不可变约束 | I-1~I-7 |
| [CLDFlow-defaults](../../docs/CLDFlow-defaults.md) | 实现默认值 | D5,D9,D13等 |
| [CLDFlow-architecture](../../docs/CLDFlow-architecture.md) | 业务架构全景 | D1-D6 |
| [CLDFlow-engineering](../../docs/CLDFlow-engineering.md) | 工程架构：模块映射+状态机+错误处理 | D11,D17,D21 |
| [architecture](../../docs/architecture.md) | 系统架构设计 | 全局 |

### 各层详细设计（docs/cldflow/，按层合并）

| 文档 | 层 | 关联决策 |
|------|-----|----------|
| [input-enhancement](../../docs/cldflow/input-enhancement.md) | 输入层 | D10,D12,D15,D19,D20 |
| [cld-layer](../../docs/cldflow/cld-layer.md) | CLD | D1,D2,D4-D6,D9,D23-D27 |
| [fcm-layer](../../docs/cldflow/fcm-layer.md) | FCM | D7,D8,D13 |
| [d2d-layer](../../docs/cldflow/d2d-layer.md) | D2D | D9,D14 |
| [cross-cutting](../../docs/cldflow/cross-cutting.md) | 跨层 | D11,D22,D28-D30 |

### 调研与探索（docs/research/）

| 文档 | 内容 |
|------|------|
| [metasynthesis-architecture-insight](../../docs/research/insights/metasynthesis-architecture-insight-2026-04-10.md) | 完整思维路径 |
| [brainstorm-product-direction](../../docs/research/insights/brainstorm-product-direction-2026-04-10.md) | 前序讨论 |
| [competitive-landscape](../../docs/research/insights/competitive-landscape-2026-04-10.md) | 竞品调研 |
| [research-cld-engineering-landscape](../../docs/research/insights/research-cld-engineering-landscape-2026-04-10.md) | 工具生态调研 |
| [ecosystem-map-system-dynamics](../../docs/research/insights/ecosystem-map-system-dynamics-2026-04-10.md) | 学科生态图谱 |
| [mcp-tools-landscape](../../docs/research/insights/mcp-tools-landscape.md) | MCP工具生态 |
| [harness-engineering](../../docs/research/harness-engineering/) | Harness Engineering文章拆解 |
| [orient-report](../../docs/research/orient-report.md) | 研究Agent MVP能力评估 |

---

## 6. MCP 工具层（Phase 2/3 预留）

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

*Issue: #15 | v2 restructured | Updated: 2026-04-16 (checkpoint: 业务图+工程图同步完善)*
