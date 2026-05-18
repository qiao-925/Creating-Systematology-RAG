# 子计划 A：后端 Pipeline

> 交付 CLDFlow 的完整后端——数据模型、输入增强、CLD 因果链路、FCM 仿真、D2D 杠杆分析、编排、报告、API。这是整个产品的核心。

## 版本目标

- 做什么：交付完整的 CLD → FCM → D2D 因果分析后端 Pipeline，含数据模型、输入增强、编排护栏、API 端点、配置体系
- 为什么：后端是 CLDFlow 的核心可交付物，前端/测试/部署全部依赖此 Pipeline 的可用性

### 成功标准

- 通过一条完整的 CLD → FCM → D2D 主链路
- 关键输入输出具备严格 schema 校验（Pydantic strict mode）
- 任一模块失败时可返回结构化失败报告
- POST /api/cldflow/analyze 可返回结构化 JSON

### 范围

**In Scope**
- 核心数据模型（Pydantic）
- 输入增强：HyDE、多查询、停止规则、来源分级
- Lead Agent 编排骨架（LlamaIndex AgentWorkflow）
- CLD 模块：视角生成、专家提取、节点归并、冲突检测、裁判机制
- FCM 模块：语言权重映射、权重矩阵、Kosko 仿真、场景对比
- D2D 模块：扰动分析、不确定性区间、杠杆点排序
- 报告层：综合洞察、证据追溯、失败终态
- API 端点 + 配置体系

**Out of Scope**
- 前端 UI（子计划 B）
- 测试体系（子计划 C）
- 部署与文档（子计划 D）
- Phase 2/3 的候选工具自动选择
- GraphML 全量支持、贝叶斯权重聚合
- D2D 解释生成 Agent

## 文档锚定

- 锚定：`ARCHITECTURE.md` — 主链路架构定义、接口契约
- 锚定：`backend/infrastructure/config/models.py` — 数据模型定义
- 锚定：`backend/core/` — 后端核心源码
- 同步：`application.yml` — 配置项

## 决策清单

### 核心决策

- [x] D1 编排框架：LlamaIndex AgentWorkflow，复用 `research_kernel/agent.py` 样板
- [x] D2 CLDNode 字段：`id, label, description`（以 models.py 为准）
- [x] D4 FCM 仿真引擎：NumPy 直接实现（FCMpy 因 tqdm 冲突移除）
- [x] D5 ParsedQuery.documents 类型：LlamaIndex `Document` 组件
- [x] D7 D2D 解释 Agent：MVP 不做，纯计算输出
- [x] D8 输入增强数据源：arXiv + Semantic Scholar + FRED + World Bank + OECD（全部 5 个）

### 支撑决策

- [x] D3 CausalLink.relation：`Literal["influences", "causes", "enables", "inhibits", "supports", "requires"]`
- [x] D6 PerspectiveSpec 类型：Pydantic model，复用 `perspectives/generator.py` 的 Perspective 结构
- [x] D9 HyDE 实现模型：DeepSeek-V3
- [x] D10 节点归并 Embedding：MiniLM-L6-v2

## 任务清单

### 阶段 1：基础骨架

- [x] T1 统一迁移边界与 MVP 范围
  - 产出：总体计划书
  - 验收：范围明确
  - 失败路径：—

- [x] T2 设计 CLDFlow 核心数据模型
  - 产出：`backend/infrastructure/config/models.py`（31 个 Pydantic 模型）
  - 验收：strict mode 可校验
  - 失败路径：降级 — 减少模型数量，先覆盖核心

- [x] T3 修复代码不一致 + 补齐目录骨架
  - 修复项：CLDNode 字段统一 / edges 类型统一 / RunContext 命名统一 / CausalLink.relation 枚举 / ParsedQuery.documents 类型升级 / 补充缺失 schema
  - 补齐目录：`orchestration/`, `modules/fcm/`, `modules/d2d/`, `input/`
  - 验收：所有模块 import 无报错
  - 失败路径：降级 — 逐项修复，不阻塞后续

- [x] T4 建立输入层 MVP
  - 产出：`backend/core/input/enhance.py`, `retrieve.py`, `stop_rules.py`, `pipeline.py`
  - 验收：输入研究问题 → 输出 `ParsedQuery`（含真实文档）
  - 失败路径：降级 — 用硬编码文档先跑通链路

- [x] T5 建立 RunContext 与 Budget Guard
  - 产出：`backend/core/orchestration/guardrails.py`（Pipeline Rail, Budget Guard, Schema Guard, Isolation Guard, Self-Review Gate）
  - 验收：RunContext 初始化独立，Budget Guard 基于 budget_tokens/tokens_used 工作
  - 失败路径：降级 — 先实现 Budget Guard，其余护栏后续补

### 阶段 2：CLD 链路

- [x] T6 建立 Lead Agent 编排骨架
  - 产出：`backend/core/orchestration/lead_agent.py`, `tools.py`, `prompts.py`
  - 验收：可串联 CLD / FCM / D2D，Pipeline Rail 生效
  - 失败路径：降级 — 用硬编码顺序串联

- [x] T7 实现 CLD 视角生成
  - 产出：`backend/core/modules/cld/perspectives/`（classifier, evaluator, generator, registry）
  - 验收：为同一问题生成 3-5 个视角
  - 失败路径：降级 — 固定 3 个模板视角

- [x] T8 实现 CLD Specialist 提取
  - 产出：`backend/core/modules/cld/specialist.py`
  - 验收：输出符合 CausalLink schema，支持 asyncio.gather 并行
  - 失败路径：重试 — 调整 prompt；降级 — 串行执行

- [x] T9 实现节点归并与冲突检测
  - 产出：`backend/core/modules/cld/merge.py`, `conflict.py`
  - 验收：归并正确，冲突分级（低 <0.3 / 中 0.3-0.5 / 高 >0.5）
  - 失败路径：降级 — 跳过归并，直接拼接

- [x] T10 实现 CLD 裁判与自审门禁
  - 产出：`backend/core/modules/cld/judge.py`
  - 验收：自审失败不进入下游
  - 失败路径：降级 — 跳过裁判，直接取第一个视角输出

- [x] T11 实现 SharedCLD 组装
  - 产出：`backend/core/modules/cld/module.py`
  - 验收：串联 T7-T10，输出 SharedCLD 可被 FCM/D2D 消费
  - 失败路径：降级 — 用 placeholder 先跑通链路

### 阶段 3：FCM / D2D（可并行）

- [x] T12 实现 FCM 权重映射
  - 产出：`backend/core/modules/fcm/mapper.py`
  - 验收：8 档映射表固定、可测试
  - 失败路径：—

- [x] T13 实现 FCM 批量评级与矩阵构建
  - 产出：`backend/core/modules/fcm/rater.py`
  - 验收：SharedCLD → WeightedFCM
  - 失败路径：降级 — 用固定权重矩阵

- [x] T14 实现 FCM 仿真引擎
  - 产出：`backend/core/modules/fcm/simulator.py`
  - 验收：Kosko 迭代收敛，返回稳定态；不收敛 → 硬失败
  - 失败路径：重试 — 调整收敛阈值；降级 — 用简单线性传播

- [x] T15 实现 D2D 扰动分析
  - 产出：`backend/core/modules/d2d/sensitivity.py`
  - 验收：对 SharedCLD 运行，输出影响力分数
  - 失败路径：—

- [x] T16 实现 D2D 不确定性与排序
  - 产出：`backend/core/modules/d2d/uncertainty.py`, `ranking.py`
  - 验收：输出 LeverageAnalysis
  - 失败路径：降级 — 跳过不确定性，只输出排序

### 阶段 4：报告 + API + 配置

- [x] T17 实现报告层融合
  - 产出：`backend/core/reporting/reporting.py`
  - 验收：生成 StructuredReport 或 StructuredFailureReport
  - 失败路径：降级 — 硬编码模板报告

- [x] G2 创建 CLDFlow API 端点
  - 产出：`backend/core/api.py`（FastAPI router, POST /api/cldflow/analyze, GET /api/cldflow/health）
  - 验收：`curl POST /api/cldflow/analyze` 返回 JSON
  - 失败路径：降级 — 只暴露 Python 接口，不走 HTTP

- [x] G3 添加 CLDFlow 配置项
  - 产出：`application.yml` 新增 `cldflow` 配置段
  - 验收：`config.get_cldflow_config()` 可读取所有配置
  - 失败路径：降级 — 硬编码默认值

- [x] G5 instructor 集成
  - 产出：`backend/core/modules/cld/specialist.py` 重构
  - 验收：Specialist 输出通过 Pydantic schema 校验
  - 失败路径：降级 — 用手动 JSON 解析

- [x] G6 Judge 降级策略
  - 产出：`backend/core/modules/cld/judge.py` + `backend/core/orchestration/tools.py`
  - 验收：无 OpenAI key 时 Judge 用 DeepSeek 正常工作
  - 失败路径：—

## 执行记录

- [x] 05-15 阶段 1-3 全部完成（T1-T16）
- [x] 05-16 阶段 4 完成（T17, G2-G3, G5-G6）
- [x] 05-18 执行验证：53/53 测试通过，31 个模型类，2 个 API 路由

## 附录：接口契约

**A1：输入层 → Lead Agent**
- 输入：`research_question: str`
- 输出：`ParsedQuery`（query_text, documents: list[Document], context）

**A2：Lead Agent → CLD Module**
- 工具：`run_cld_analysis`
- 输入：`CLDAnalysisInput`（research_question, documents, perspective_hints, max_perspectives）
- 输出：`CLDAnalysisOutput`（shared_cld, perspectives_used, confidence, diagnostics）

**A3：Lead Agent → FCM Module**
- 工具：`run_fcm_analysis`
- 输入：`FCMAnalysisInput`（shared_cld, intervention_scenarios, simulation_config）
- 输出：`FCMAnalysisOutput`（weighted_fcm, diagnostics）

**A4：Lead Agent → D2D Module**
- 工具：`run_d2d_analysis`
- 输入：`D2DAnalysisInput`（shared_cld, variable_types, perturbation_pct）
- 输出：`D2DAnalysisOutput`（leverage_analysis, diagnostics）

**A5：Lead Agent → 报告层**
- 输入：shared_cld, weighted_fcm, leverage_analysis, run_context
- 输出：`StructuredReport` | `StructuredFailureReport`

## 附录：失败与降级矩阵

- 检索为空 → 硬失败：改写重试 1 次后终止
- Schema 校验失败 → 硬失败：单视角重试 ≤3 次，视角数 <2 则终止
- 节点归并/冲突自审失败 → 硬失败：修复回路，失败则终止
- FCM 部分边缺失评级 → 软失败：降低该边置信度，继续聚合
- FCM 不收敛 → 硬失败：参数回退重试 1 次，仍失败则终止
- D2D 区间过宽 → 软失败：继续输出，显式标记 low confidence

## 附录：Agent 模式

- 输入层：单 Agent + 并发工具（DeepSeek-V3）
- CLD 视角生成：单 Agent（DeepSeek-V3）
- CLD Specialist：**多 Agent 并行**（DeepSeek-V3）— 视角真独立
- CLD 裁判：单 Agent（GPT-4o-mini）— 高分歧仲裁，可降级 DeepSeek
- FCM 评级：单 Agent（DeepSeek-V3）— 全局图语义依赖
- D2D：纯工具（无 LLM）— NumPy 计算
- 报告层：单 Agent 多轮（DeepSeek-V3）— 全局一致叙述
