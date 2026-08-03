# Systematology Agent 重构 Phase 0 Master Plan

> **构建语境**：基于 GitHub Issues #17–#26 的设计闭环总结，定义从旧 CLD→FCM→D2D 流水线到"DDC 知识树 × 事件驱动 Workflow"新架构的 Phase 0 执行计划。

> **For agentic workers:** 本计划为 Master Plan（总计划），定义全局目标和子计划拆分。每个子计划在执行时使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 实施。

**全局目标**：交付 DDC 知识树骨架 + 第一个节点（003 系统学）策展 + 5 步事件驱动 Workflow 空管线跑通 + 前端发光树可视化。

## 产品定位（2026-07-24 确认）

**Slogan**：
> **寻址 —— 连接未知与已知**

**定位陈述**：输入一个未知，DDC 树找到它在人类知识中的位置，点亮相关学科节点，每个节点输出一个核心洞察 + 原文指引。

**这是怎样一种"垂直"？**
既不是 CLD→FCM→D2D 的单一学科垂直，也不是"通用 AI 聊天"的泛泛而谈。

它是 **发散与收敛的平衡**：
```
发散（DDC 树的广度）         收敛（每个节点的硬工具）
────────────────────         ────────────────────
问题→点亮多个节点          每个有工具的节点产出结构化分析
看到不同学科的视角          003 系统学 → CLD 因果图 + FCM 仿真
发现"原来这个角度也有"     330 经济学 → 博弈论计算 + 外部性量化
                            146 辩证法 → 矛盾分析
```

**Agent 的角色是启发，不是代劳。**
> "不认为一个 agent 能完成所有事情" — 用户的原文

产品输出不只是"答案"，而是：
- 一张被点亮的学科地图（用户看到什么被覆盖、什么没被覆盖）
- 每个发光节点的一个核心洞察（极简，不废话）
- 原文指引（用户自己去探索）

**与普通 LLM 的本质差异**：
| | 普通 LLM | Systematology |
|---|---------|---------------|
| 视角 | 隐式的、训练数据稀释后的平均水平 | 显式的、策展过的学科核心直觉 |
| 盲区 | 不说自己漏了什么 | 暗节点诚实地展示"我没看什么" |
| 质量 | 软约束（"请简洁"） | 硬编码 4 条防线 |
| 深度 | 一次回答 | 三级深度控制（Quick/Standard/Deep） |

**架构概要**：以 DDC（杜威十进制分类法）为知识骨架，事件驱动 Workflow（5 step）替代旧 AgentWorkflow。三步分析深度控制节点数量。旧 CLD→FCM→D2D 降级为 DDC 003 节点下的可选工具。

**技术栈**：
- 后端：Python 3.12 + LlamaIndex Workflow（事件驱动 @step）+ Pydantic v2 + NetworkX + NumPy
- 前端：Next.js / React + Tailwind CSS
- 方法论基础：DDC（主骨架）+ PMEST（分析语法）+ 4 条硬编码约束

**依据 Issue**：#17（主线）、#19（产品定位）、#20（DDC 树）、#21（分类法体系）、#22（Workflow + 三级深度）、#23（事件定义）、#24（知识编码）、#25（工作日志）、#26（架构决策：Workflow-First）

---

## 上下文

### 已完成的状态

旧 MVP（CLD→FCM→D2D 流水线）已全部完成并部署：
- 所有 20 个核心任务 + 8 个可发布增量已关闭
- HF Spaces Demo 已部署
- Infrastructure 层（LLM 工厂、配置、检索、向量化、初始化）稳定运行

### Issue 设计回顾（#19–#26 设计闭环）

| Issue | 关键产出 | 决策状态 |
|-------|---------|---------|
| #19 | 产品转型：多透镜深度洞察 Agent，4 条硬编码约束，硬编码 Agent + 微调并行 | ✅ 确定 |
| #20 | DDC 知识树替代 8 个手选透镜，发光树可视化概念 | ✅ 确定 |
| #21 | 分类法体系：DDC 主 + UDC/CLC/PMEST 扩展，原文引导 | ✅ 确定 |
| #22 | 5 步事件驱动 Workflow + 三级分析深度（Quick/Standard/Deep） | ✅ 确定 |
| #23 | 5 类事件定义（LensJob/LensResult/Relationship/Fusion/InsightOutput） | ✅ 确定 |
| #24 | 知识编码架构：文件系统存储，软硬分层，持续策展 | ✅ 确定 |
| #25 | 设计闭环总结，Phase 0 执行步骤确定 | ✅ 产出下一步 |
| #26 | 架构决策：Workflow-First + Earned Autonomy（确定性骨架 + 有限自主性） | ✅ 确定 |

### Phase 0 直接产出目标

1. **DDC 树骨架** — 前 3 层，编号 + 标签（`backend/ddc/tree.json`）
2. **003 系统学节点策展** — 复用现有 CLD→FCM→D2D 代码作为硬工具
3. **Workflow 空管线** — 5 步事件驱动流跑通（pmest_mapper → lens_worker → relationship_engine → fuser → constraint_engine）
4. **树可视化** — 前端发光树骨架

### 待定事项

来自 #25：
- `old-docs/research/insights/` 下旧文档处置（删除/保留/归档）
- 更广的文档简化

---

## 子计划清单

本 Master Plan 拆分为以下子计划，按执行顺序排列。**串行依赖用 `→` 表示，并行用 `‖` 表示。**

```
SP-0.1 ─→ SP-0.2 → SP-0.3 ─┐
         │                   ├── (SP-0.4 ‖ SP-0.5 ‖ SP-0.6)
         └──→ SP-0.7 ───────┤
                            └──→ SP-0.8 → SP-0.9
```

| 编号 | 名称 | 前置依赖 | 预计复杂度 |
|------|------|---------|-----------|
| SP-0.1 | DDC 树骨架构建 | 无 | 🔵 中 |
| SP-0.2 | PMEST 拆解引擎 | SP-0.1 | 🔵 中 |
| SP-0.3 | 事件驱动 Workflow 骨架 | SP-0.1 | 🔴 高 |
| SP-0.4 | 003 系统学节点策展与工具集成 | SP-0.3（依赖 lens_worker 骨架） | 🟢 低（复用为主） |
| SP-0.5 | 4 条硬编码约束引擎 | SP-0.3 | 🟢 低 |
| SP-0.6 | 三级分析深度控制 | SP-0.3 | 🟡 中低 |
| SP-0.7 | 前端发光树可视化 | SP-0.1（数据可 mock，不阻塞） | 🟡 中 |
| SP-0.8 | API 集成与端到端链路 | SP-0.3 + SP-0.4 + SP-0.5 + SP-0.7 | 🟡 中 |
| SP-0.9 | 端到端测试与文档扫尾 | 各 SP 产出完整 | 🟢 低 |

## SubAgent 声明式分配（注意力管理与上下文隔离）

每个子计划执行时使用独立的 SubAgent，确保上下文边界清晰，防止注意力泄露。

| 编号 | SubAgent 类型 | 隔离理由 | 上下文边界 |
|------|-------------|---------|-----------|
| **SP-0.1** | `general-purpose` | DDC 树是全新模块，不涉及旧代码，需要从零构建 | `backend/ddc/` 目录，不触及 `backend/core/` 或 `backend/infrastructure/` |
| **SP-0.2** | `general-purpose` | PMEST 是独立算法模块，需结合 LLM 工厂，不宜与其他步骤混写 | `backend/core/new_workflow/pmest/` + `backend/infrastructure/llms/`（只读） |
| **SP-0.3** | `general-purpose` | 工作流是核心骨架，需要完整构建 @step 事件流，复杂度高 | `backend/core/new_workflow/` 全部（含 steps + events） |
| **SP-0.4** | `general-purpose` | 仅涉及复用旧模块和编写策展文档，不修改 Workflow 代码 | `backend/ddc/003-systemology/` + `backend/core/modules/`（只读） |
| **SP-0.5** | `general-purpose` | 纯函数约束层，与 LLM 调用完全分离，可独立测试 | `backend/core/new_workflow/constraints/`，零 LLM 依赖 |
| **SP-0.6** | `general-purpose` | 改动极小（仅控制发射数量），可合并进 SP-0.3 同一个 Agent | `backend/core/new_workflow/depth.py` |
| **SP-0.7** | `general-purpose` | 前端 TypeScript/React，与后端完全无关，需独立的上下文 | `web/src/components/DDCTree/` + `web/src/hooks/`，不触及 `backend/` |
| **SP-0.8** | `general-purpose` | 集成层，需要同时理解后端 Workflow 和前端 API 调用 | `backend/fastapi/routes/` + `web/src/` 的路由层 |
| **SP-0.9** | `general-purpose` | 端到端集成测试 + 文档扫尾，不重复各 SP 已交付的单元测试 | `tests/systematology_v2/` + `docs/`，可引用各模块但不修改实现 |

**执行策略**：
- 每个 SP 使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 实施
- 前一个 SP 的 SubAgent 完成后，其产出文件作为下一个 SubAgent 的只读上下文
- **SP-0.1 完成后分两条并行线**：
  - 主线：SP-0.2 → SP-0.3 → (SP-0.4 ‖ SP-0.5 ‖ SP-0.6)  — 后端核心管线
  - 支线：SP-0.7  — 前端发光树（仅依赖 SP-0.1，数据 mock）
  - 两线在 SP-0.8 合并
- SP-0.6 因其改动极小，可合并进 SP-0.3 的 SubAgent 执行，无需单独分配
- SP-0.9 为端到端集成测试扫尾，不重复各 SP 已内嵌的单元测试

---

## 子计划详细定义

### SP-0.1: DDC 树骨架构建

**版本目标**：创建 DDC 树的完整前 3 层骨架，支持按编号 O(1) 查找和按关键词模糊匹配。

**核心决策清单**：
- 前 3 层足够 Phase 0（10 大类 → ~100 中类 → ~1000 小类）
- 存储格式：JSON 树结构 + 扁平索引（双重）
- 无需数据库，文件系统即知识仓库（#24 决策）

**文件改动清单**：
```
backend/ddc/                        ← 新建
├── __init__.py                     ← 包初始化
├── tree.json                       ← DDC 前 3 层骨架（编号→标签）
├── tree.py                         ← DDC 树加载/查找服务
├── models.py                       ← DDC 树相关 Pydantic 模型（DDCNode, DDCBranch）
└── lookup.py                       ← 编号→节点名 O(1) 查找 + 关键词模糊匹配
```

**执行任务清单**（串行执行）：

- [ ] **T1 定义 DDC 树数据模型**
  - 构建：`backend/ddc/models.py` — Pydantic 模型 `DDCNode`, `DDCBranch`
  - 测试：`tests/ddc/test_models.py` — 校验 strict mode、嵌套结构、`lit`/`curated` 字段默认值

- [ ] **T2 录入 tree.json 骨架**
  - 构建：`backend/ddc/tree.json` — 前 3 层，编号+标签，节点格式：`{"code":"003","label":"系统学","parent":"000","children":{}}`
  - 方式：脚本批量生成或手动录入（~1000 节点）
  - 测试：`tests/ddc/test_tree.py` — 校验 JSON schema、各层级数量、编号唯一性

- [ ] **T3 实现 DDC 树加载与查找服务**
  - 构建：`backend/ddc/tree.py` — `load_tree()`, `find_node(code)`, `get_children(code)`, `get_parent(code)`
  - 测试：`tests/ddc/test_tree.py` — 空树、深节点查找、不存在的编号返回 None

- [ ] **T4 实现关键词模糊匹配**
  - 构建：`backend/ddc/lookup.py` — `search_nodes(keyword)` 基于标签模糊匹配，返回匹配节点列表
  - 测试：`tests/ddc/test_lookup.py` — 精确匹配、部分匹配、无匹配、多结果排序

- [ ] **T5 打包与初始化**
  - 构建：`backend/ddc/__init__.py` — 导出 `load_tree`, `find_node`, `search_nodes`
  - 验证：`python -c "from backend.ddc import load_tree; t = load_tree(); print(len(t))"` 正常输出 1000+

---

### SP-0.2: PMEST 拆解引擎

**版本目标**：实现 PMEST（Personality/Matter/Energy/Space/Time）五维问题拆解，输出 PMEST 面→DDC 节点映射。

**核心决策清单**：
- PMEST 是 Step 1（pmest_mapper）的核心算法，不是外挂提示词
- 输出：一个或多个 DDC 节点编号，带权重（匹配度）
- 简单问题映射到 1-3 个节点，复杂问题 5-8 个节点

**文件改动清单**：
```
backend/core/new_workflow/
├── __init__.py
├── pmest/
│   ├── __init__.py
│   ├── analyzer.py                  ← PMEST 五维拆解（LLM 辅助）
│   ├── mapper.py                    ← PMEST 面→DDC 节点映射
│   └── models.py                    ← PMEST 相关模型（PMESTFacet, PMESTResult）
└── ddc/
    ├── __init__.py
    └── navigator.py                 ← DDC 树导航（基于 SP-0.1 的 tree.py）
```

**复用资产**：
- LLM 工厂：`backend/infrastructure/llms/factory.py` → `create_llm()`
- 配置：`backend/infrastructure/config/`

**执行任务清单**（串行执行）：

- [ ] **T1 PMEST 模型定义**
  - 构建：`backend/core/new_workflow/pmest/models.py` — `PMESTFacet`（facet: Literal["P","M","E","S","T"], term, weight）, `PMESTResult`（facets list, mapped_nodes list）
  - 测试：`tests/pmest/test_models.py` — strict mode 校验、非法 facet 拒绝

- [ ] **T2 PMEST 五维拆解**
  - 构建：`backend/core/new_workflow/pmest/analyzer.py` — 调用 LLM 将问题拆为 PMEST 五维，输出结构化 facet
  - 测试：`tests/pmest/test_analyzer.py` — mock LLM 返回、边界输入（空问题、超短问题）

- [ ] **T3 DDC 树导航器**
  - 构建：`backend/core/new_workflow/ddc/navigator.py` — 基于 SP-0.1 的`tree.py` 封装导航接口：`map_facets(pmest_result) → list[node_id]`
  - 测试：`tests/ddc/test_navigator.py` — PMEST facet→DDC 节点映射、无匹配降级、多节点排序

- [ ] **T4 PMEST→DDC 映射器（mapper）**
  - 构建：`backend/core/new_workflow/pmest/mapper.py` — 将每个 PMEST 面映射到 DDC 节点，输出带权重的节点列表
  - 测试：`tests/pmest/test_mapper.py` — 输入 PMEST fac et→输出期望 DDC 节点

---

### SP-0.3: 事件驱动 Workflow 骨架

**版本目标**：实现 5 步事件驱动 Workflow（LlamaIndex Workflow 的 @step 模式），发射和消费 5 类事件，空管线可跑通。

**核心决策清单**：
- 使用 LlamaIndex `Workflow` + `@step` 装饰器（#23 确认）
- 事件继承 Pydantic + Event（严格校验，不信任上一步输出）
- 5 步顺序：pmest_mapper → lens_worker → relationship_engine → fuser → constraint_engine
- lens_worker 内使用 `asyncio.gather` 并行（#22 确认）

**文件改动清单**：
```
backend/core/new_workflow/
├── workflow.py                      ← InsightWorkflow 主类（5 个 @step）
├── events.py                        ← 5 类事件定义
│   ├── LensJobEvent
│   ├── LensResultEvent
│   ├── RelationshipEvent
│   ├── FusionEvent
│   └── InsightOutput
├── steps/
│   ├── __init__.py
│   ├── step1_pmest_mapper.py
│   ├── step2_lens_worker.py
│   ├── step3_relationship_engine.py
│   ├── step4_fuser.py
│   └── step5_constraint_engine.py
└── __init__.py
```

**5 步事件流**（#22、#23 确凿）：
```
StartEvent(question)
  ↓
Step 1: pmest_mapper → list[LensJobEvent]  （发射 N 个并行任务）
  ↓ 框架 fan-out
Step 2: lens_worker → list[LensResultEvent]  （asyncio.gather 并行）
  ↓ 全部就绪
Step 3: relationship_engine → RelationshipEvent  （跨节点关系分析）
  ↓
Step 4: fuser → FusionEvent  （一致+矛盾+根本解释+原文指引）
  ↓
Step 5: constraint_engine → StopEvent(InsightOutput)  （4 道纯函数防线）
```

**复用资产**：
- Pydantic 校验模式：`backend/core/models.py` 的 strict mode 模式
- 基础设施层（LLM 工厂、配置、日志）全量复用

**执行任务清单**（串行执行）：

- [ ] **T1 5 类事件定义**
  - 构建：`backend/core/new_workflow/events.py` — 5 个 Event 类继承 Pydantic BaseModel，strict mode
  - 测试：`tests/workflow/test_events.py` — 事件创建、字段校验、序列化/反序列化

- [ ] **T2 Step 1: pmest_mapper**
  - 构建：`backend/core/new_workflow/steps/step1_pmest_mapper.py` — 接收 StartEvent，调用 PMEST 引擎 → 发射 N 个 LensJobEvent
  - 测试：`tests/workflow/test_pmest_mapper.py` — mock PMEST 引擎、验证事件数量和格式

- [ ] **T3 Step 2: lens_worker**
  - 构建：`backend/core/new_workflow/steps/step2_lens_worker.py` — 接收 list[LensJobEvent]，asyncio.gather 并行加载节点透镜 → 输出 LensResultEvent
  - 测试：`tests/workflow/test_lens_worker.py` — mock 透镜加载、验证并行调用次数、节点无策展时降级

- [ ] **T4 Step 3: relationship_engine**
  - 构建：`backend/core/new_workflow/steps/step3_relationship_engine.py` — 跨节点关系分析，输出 RelationshipEvent
  - 测试：`tests/workflow/test_relationship_engine.py` — 2 节点关系分析、单节点跳过、无关系降级

- [ ] **T5 Step 4: fuser**
  - 构建：`backend/core/new_workflow/steps/step4_fuser.py` — 透镜融合：一致/矛盾/最根本解释 + 原文指引，输出 FusionEvent
  - 测试：`tests/workflow/test_fuser.py` — 矛盾检测、一致合成、原文指引生成

- [ ] **T6 Step 5: constraint_engine**
  - 构建：`backend/core/new_workflow/steps/step5_constraint_engine.py` — 调用 4 条约束管道（SP-0.5），输出 StopEvent(InsightOutput)
  - 依赖：SP-0.5 约束引擎（纯函数，可先 mock 占位）
  - 测试：`tests/workflow/test_constraints.py` — 约束通过、部分约束失败、全失败降级

- [ ] **T7 InsightWorkflow 串联**
  - 构建：`backend/core/new_workflow/workflow.py` — 5 个 @step 串联，depth 参数初始化
  - 测试：`tests/workflow/test_workflow_integration.py` — Quick/Standard/Deep 三级全路径跑通、mock LLM

---

### SP-0.4: 003 系统学节点策展与工具集成

**版本目标**：策展 DDC 003（系统学）节点，将现有 CLD→FCM→D2D 代码集成为此节点的硬工具。

**核心决策清单**：
- 知识格式：差异清单（~30 行），只写 LLM 不擅长的部分（#24 确认）
- CLD/FCM/D2D 是 003 节点下的可选工具，不是全局管线（#20 确认）
- `knowledge.md` → 诊断问题 + 经典模式 + 常见盲区
- `tools/` → Python 代码直接调用

**文件改动清单**：
```
backend/ddc/003-systemology/
├── knowledge.md                     ← 软知识差异清单（~30 行）
│   - 核心直觉：系统由反馈结构驱动，而非事件
│   - 诊断问题：这个系统的关键延迟在哪？什么回路主导行为？
│   - 经典模式：增长上限、转移负担、公地悲剧、富者愈富
│   - 常见盲区：把相关当因果、忽略延迟、线性外推
└── tools/
    ├── __init__.py
    ├── cld_builder.py               ← 封装 CLD 模块（module.py）
    ├── fcm_simulator.py             ← 封装 FCM 模块
    └── d2d_analyzer.py              ← 封装 D2D 模块
```

**复用资产**：
- `backend/core/modules/cld/` — 整个 CLD 模块
- `backend/core/modules/fcm/` — 整个 FCM 模块
- `backend/core/modules/d2d/` — 整个 D2D 模块

**执行任务清单**（串行执行，复用为主）：

- [ ] **T1 编写 knowledge.md 差异清单**
  - 构建：`backend/ddc/003-systemology/knowledge.md` — 核心直觉(3行) + 诊断问题(5问) + 经典模式(5个) + 常见盲区(5条)
  - 验收：总字数 ~30 行，只写 LLM 不擅长的内容

- [ ] **T2 封装 CLD 工具**
  - 构建：`backend/ddc/003-systemology/tools/cld_builder.py` — 包装 `CLDModule.run()`，适配 lens_worker 的调用接口
  - 测试：`tests/ddc/tools/test_cld_tool.py` — 调用封装后的工具，验证输出格式

- [ ] **T3 封装 FCM 工具**
  - 构建：`backend/ddc/003-systemology/tools/fcm_simulator.py` — 包装 FCM 模块，适配 lens_worker 接口
  - 测试：`tests/ddc/tools/test_fcm_tool.py`

- [ ] **T4 封装 D2D 工具**
  - 构建：`backend/ddc/003-systemology/tools/d2d_analyzer.py` — 包装 D2D 模块，适配 lens_worker 接口
  - 测试：`tests/ddc/tools/test_d2d_tool.py`

- [ ] **T5 工具注册到 lens_worker**
  - 构建：在 `step2_lens_worker.py` 中添加"加载节点策展→注册可用工具"的逻辑
  - 集成测试：验证 lens_worker 加载 003 节点后，CLD/FCM/D2D 工具可用

---

### SP-0.5: 4 条硬编码约束引擎

**版本目标**：实现 #19 确认的 4 条硬编码防线，作为 Step 5（constraint_engine）的核心。

**核心决策清单**：
- 全部为纯函数，无 LLM 调用（#23 确认）
- 与旧 guardrails 设计思想一致但更精简

**4 条防线**：
1. **来源门控** — 每条断言必须有来源或显式标注"推测"
2. **透镜覆盖检查** — 输出不能停留在事件层面叙事，必须涉及至少一个透镜的核心概念
3. **表达压缩** — 硬编码摘要规则（论点数量限制、冗余检测）
4. **盲区自查** — 对照节点盲区清单自动检查输出是否遗漏

**文件改动清单**：
```
backend/core/new_workflow/constraints/
├── __init__.py
├── source_gate.py                   ← 来源门控
├── lens_coverage.py                 ← 透镜覆盖检查
├── compression.py                   ← 表达压缩
├── blind_spot_check.py              ← 盲区自查
└── pipeline.py                      ← 4 条约束管道编排
```

---

### SP-0.6: 三级分析深度控制

**版本目标**：实现 Quick（1 节点）/ Standard（3 节点）/ Deep（全量）三级深度（#22 确凿）。

**核心决策清单**：
- 通过控制 `pmest_mapper` 发射的 `LensJobEvent` 数量实现
- 外层 Workflow 结构不变，无条件分支代码
- 默认 Standard

**文件改动清单**：
- 主要在 SP-0.3 的 `step1_pmest_mapper.py` 中控制发射数量
- 新增：`backend/core/new_workflow/depth.py` — 深度配置常量 + 节点数量计算

---

### SP-0.7: 前端发光树可视化

**版本目标**：DDC 树前端可视化，问题点亮树上节点，点击节点查看透镜洞察。

**核心决策清单**：
- Tailwind + React 实现
- 发光状态：🔆 全亮（有策展+工具）/ 🔅 半亮（LLM 自动）/ ⚫ 暗（未挂载）（#24 确认）
- 首次 Phase 0：静态骨架 + 模拟点亮数据

**文件改动清单**：
```
web/src/
├── components/DDCTree/
│   ├── DDCTree.tsx                  ← DDC 树可视化主组件
│   ├── DDCNode.tsx                  ← 单个节点组件（发光状态）
│   ├── DDCNodeDetail.tsx            ← 节点详情面板
│   └── types.ts                     ← DDC 树前端类型定义
├── hooks/
│   └── useDDCTree.ts               ← 树数据获取 Hook
└── pages/
    └── systematology/
        └── index.tsx                ← 测试页面
```

---

### SP-0.8: API 集成与端到端链路

**版本目标**：连接新 Workflow 到 FastAPI，前端可调通端到端。

**核心决策清单**：
- 新路由与旧 API 共存（非破坏性）
- 前端接入新 Workflow 的后端端点

**文件改动清单**：
```
backend/fastapi/
├── routes/
│   └── systematology_v2.py          ← 新 Workflow API 端点
└── schemas.py                       ← 新增请求/响应模型（v2）
```

---

### SP-0.9: 端到端测试与文档扫尾

**版本目标**：作为各 SP 已内嵌单元测试的补充，覆盖端到端集成测试、文档完整性检查、质量门禁审计。

> **与各 SP 测试任务的关系**：每个 SP 的 T1–T5 已包含对应模块的**单元测试**构建（如 `tests/ddc/test_tree.py` 随 SP-0.1 交付）。SP-0.9 不重复这些，而是聚焦于跨模块集成测试和文档完备性。

**核心决策清单**：
- 不重复各 SP 已交付的单元测试
- 聚焦于端到端集成（frontend → API → Workflow → DDC Lens → 约束 → 输出）
- 文档扫尾：README、API 文档、策展格式说明
- 质量门禁审计（对照验证标准逐项核查）

**文件改动清单**：
```
tests/
└── systematology_v2/
    └── test_api_e2e.py                   ← 端到端集成测试（各 SP 单元测试已在各自 SP 内交付）
docs/
├── README.md                             ← 项目概览补充 Phase 0 新架构说明
├── api.md                                ← API 端点文档（新 Workflow 路由）
└── ddc-curation-guide.md                 ← 策展格式说明（新增节点参考）
```

---

## 执行顺序与依赖图（优化后）

```
SP-0.1 (DDC 树骨架)
  ├──→ SP-0.2 (PMEST 引擎) → SP-0.3 (Workflow 骨架) ──主线（后端核心）
  │                           ├──→ SP-0.4 (003 策展)      ‖
  │                           ├──→ SP-0.5 (约束引擎)      ‖ 三条平行
  │                           └──→ SP-0.6 (深度控制)      ‖
  │
  └──→ SP-0.7 (前端树可视化) ────────────────支线（前端，mock）
                                          │
                                          ▼
                                    SP-0.8 (API 集成)
                                          │
                                          ▼
                                    SP-0.9 (端到端 + 文档)
```

> **与原始版本的变化**：SP-0.7 从 SP-0.3 之后提前到与 SP-0.2 并行（仅依赖 SP-0.1）；SP-0.5 从 SP-0.4 ‖ SP-0.6 之后提级为同级并行（三线仅依赖 SP-0.3）；SP-0.9 从"重复各 SP 单元测试"重定义为"端到端集成 + 文档扫尾"。

### 关键并行窗口
- **SP-0.5（约束引擎）与 SP-0.4（003 策展）、SP-0.6（深度控制）三者并行** — 均仅依赖 SP-0.3
- SP-0.7（前端树）与 SP-0.2（PMEST 引擎）并行启动 — 仅依赖 SP-0.1，数据 mock

---

## 执行步骤记录

根据 `plan-rules.md` 约束，子计划执行过程中须记录以下内容：

| 维度 | 记录内容 | 记录位置 |
|------|---------|---------|
| Checkpoint | 每个子计划完成时记录实际耗时、产出物是否完整、偏差说明 | 各 SubPlan 执行日志，执行完成后汇总到 `docs/long-task-plan/` |
| 异常 | hook 拦截记录（文件越界、结构校验失败）、计划偏移详情、回滚决策 | `docs/long-task-plan/` + 子计划执行日志 |
| 阻塞项 | 依赖缺失、测试失败、前置未就绪 | 即时处理，处理后标记解决 |

**记录格式建议**（每条一个条目）：

```
YYYY-MM-DD HH:MM | SP-0.x | CHECKPOINT/EXCEPTION/BLOCKER | 描述 | 状态(PASS/FAIL/BLOCKED)
```

执行各子计划时，在 `docs/long-task-plan/` 下创建对应的执行记录文件（如 `exec-log-sp-0.1.md`）。Phase 0 结束时汇总为 `exec-log-phase0-summary.md`。

---

## 附录：Issue 追溯链

```
#17 (Master: Creating-Systematology-Refactor-MVP)
  ├── #18 (文档整理与简化 — DONE)
  └── #19 (产品定位讨论) 
        └── #20 (DDC 知识树方案)
              └── #21 (分类法体系深化)
                    └── #22 (事件驱动 Workflow + 三级深度)
                          └── #23 (工作流事件定义 + Agent 模式对比)
                                └── #24 (知识体系编码 + 持续策展)
                                      └── #25 (工作日志 — 设计闭环总结)
                                            └── #26 (架构决策：Workflow-First + Earned Autonomy)
```

每个子计划执行时需锚定到对应 Issue 的决策文档。

---

## 验证标准

### Phase 0 总体验收

1. **DDC 树加载** — `backend/ddc/tree.py` 加载 tree.json，编号查找 O(1)，1000+ 节点正确
2. **PMEST 拆解** — 输入"房价为什么涨" → 输出 [332.8(住房市场), 330(经济学), 300(社会学)]（权重排序）
3. **5 步 Workflow 跑通** — Quick 模式 1 节点 → 1 次 Lens 调用 → 约束通过 → 输出 InsightOutput
4. **003 系统学策展** — `knowledge.md` + `tools/` 可被 lens_worker 加载和调用
5. **4 条约束生效** — 来源缺失标记"推测"，透镜覆盖不足发出 warning，表达超长压缩，盲区遗漏提示
6. **前端树点亮** — 输入问题后 DDC 树展示被点亮的节点（🔆/🔅/⚫）
7. **端到端** — frontend → API → Workflow → DDC Lens → 约束 → 输出展示

### 质量门禁

- 所有新建 Pydantic 模型使用 strict mode + `extra="forbid"`（继承旧架构约定）
- 约束引擎保持纯函数，无 LLM 调用
- Workflow @step 之间通过 Event 类型路由，无共享可变状态
- 事件定义不可绕过程序边界校验
- 每个子计划产出至少包括单元测试
