# CLDFlow MVP 可执行计划书

> 目标：交付一条稳定、可验证、可扩展的 CLD → FCM → D2D 主链路。
> 本文档基于 `ARCHITECTURE.md` 全局校准，对齐实际代码状态，达到"拿到即可开工"的可执行级别。

## 1. 当前状态审计

> 截至 2026-05-15，`backend/business/cldflow/` 实际代码与计划存在以下偏差。

### 1.1 已完成产出

| 文件 | 内容 | 对应任务 |
|------|------|----------|
| `models.py` | 11 个 Pydantic/dataclass 模型（`ParsedQuery`, `CLDNode`, `CausalLink`, `SharedCLD`, `WeightedFCM`, `NodeImpact`, `LeverageAnalysis`, `StructuredReport`, `StructuredFailureReport`, `RunContext`, `FailureRecord`） | T2 |
| `service.py` | `CLDFlowAppService` placeholder 实现 | T3 部分 |
| `__init__.py` | 包入口 | T3 部分 |
| `guardrails.py` | 3 个守卫函数（`ensure_question_is_valid`, `ensure_cld_ready`, `ensure_budget_remaining`） | T5 部分 |
| `modules/cld/module.py` | `CLDModule` placeholder 实现 | T11 部分 |
| `modules/cld/schema.py` | `CLDAnalysisInput`, `CLDAnalysisOutput` | T11 部分 |
| `tests/test_cldflow_mvp.py` | 2 个基础测试用例 | T18 部分 |

### 1.2 代码内部不一致（必须在 T3 中修复）

| 问题 | 位置 | 描述 |
|------|------|------|
| **CLDNode 字段不匹配** | `models.py:20` vs `modules/cld/module.py:17` | `models.py` 定义 `id, label, description`；`module.py` 使用 `name, description, source_refs` — 两套 schema |
| **edges 类型不匹配** | `models.py:41` vs `modules/cld/module.py:34` | `SharedCLD.edges` 声明为 `list[CausalLink]`，但 `module.py` 传入 `list[dict]` |
| **RunContext 命名不一致** | `guardrails.py:6` vs `models.py:97` | `guardrails.py` 引用 `CLDFlowRunContext`，`models.py` 定义为 `RunContext` |
| **CausalLink.relation 缺少约束** | `models.py:33` | `relation: str = "influences"` 允许任意字符串，应为 Literal 枚举 |
| **ParsedQuery.documents 类型需升级** | `models.py:17` | 当前为 `list[dict[str, Any]]`，需改为 LlamaIndex `Document` 类型（D5 决策） |

### 1.3 决策确认清单（全部已闭合）

> 来源：`docs/research with brainstorm/issue-15-CLDFlow架构设计与实现-v2.md` + 用户确认。

| # | 问题 | 决策结果 | 来源 |
|---|------|----------|------|
| D1 | 编排框架 | **LlamaIndex AgentWorkflow**（覆盖早期 D11"自定义轻量编排器"） | 用户确认 + `research_kernel/agent.py` 样板 |
| D2 | CLDNode 字段 | 以 `models.py` 为准：`id, label, description` | D24(UUID) + D23(删除置信度) + D25(删除 strength) |
| D3 | CausalLink.relation | `Literal["influences", "causes", "enables", "inhibits", "supports", "requires"]` | 用户确认 |
| D4 | FCM 仿真引擎 | FCMpy | D21 技术栈锁定 |
| D5 | ParsedQuery.documents 类型 | LlamaIndex `Document` 组件 | 用户确认 |
| D6 | PerspectiveSpec 类型 | 定义 Pydantic model，复用 `perspectives/generator.py` 的 Perspective 结构 | 现有代码 |
| D7 | D2D 解释 Agent | MVP 不做，纯计算输出 | 架构文档"可选" |
| D8 | 输入增强数据源 | arXiv + Semantic Scholar + FRED + World Bank + OECD（全部 5 个） | D16 |
| D9 | HyDE 实现模型 | DeepSeek-V3 | D17 模型分工 |
| D10 | 节点归并 Embedding | MiniLM-L6-v2 | D21 技术栈锁定 |
| D11 | 测试 mock 方案 | mock `llama_index.core.llms.LLM.complete()` 方法 | 用户确认 |
| D12 | 黄金样例场景 | 财政补贴 + Prop 13（1978加州房产税） | 研究文档验证案例锁定 |

## 2. MVP 定义

主链路目标：

1. 接收研究问题与输入材料
2. 完成输入增强与来源过滤
3. 生成结构化 `SharedCLD`
4. 基于 `SharedCLD` 运行最小可用 FCM 与 D2D
5. 输出结构化报告或结构化失败报告
6. 建立最小测试闭环，保证链路可复现

## 3. 范围

### In Scope

- 输入增强：HyDE、多查询、停止规则、来源分级
- Lead Agent 编排骨架（LlamaIndex AgentWorkflow）
- CLD 模块：视角生成、专家提取、节点归并、冲突检测、裁判机制
- FCM 模块：语言权重映射、权重矩阵、Kosko 仿真、场景对比
- D2D 模块：扰动分析、不确定性区间、杠杆点排序
- 报告层：综合洞察、证据追溯、失败终态
- 测试体系：单测、集成测试、端到端校验、回归样例

### Out of Scope

- Phase 2/3 的候选工具自动选择
- GraphML 全量支持
- 贝叶斯权重聚合
- 复杂的人类协作流程
- 生产级多租户与权限系统
- 老 RAG 工程的一次性全量重构
- D2D 解释生成 Agent（MVP 阶段不需要）

## 4. 成功标准

- 通过一条完整的 CLD → FCM → D2D 主链路
- 关键输入输出具备严格 schema 校验（Pydantic strict mode）
- 任一模块失败时可返回结构化失败报告
- 至少有一组可复现测试样例覆盖完整流水线
- 非 LLM 代码行覆盖率 ≥ 80%

## 5. 任务拆分

### 阶段 1：基础修复与骨架

#### T1. 统一迁移边界与 MVP 范围 — **已完成**

- 产出：本计划书

#### T2. 设计 CLDFlow 核心数据模型 — **已完成**

- 产出：`models.py` 11 个模型
- 验收：strict mode 可校验

#### T3. 修复代码不一致 + 补齐目录骨架 — **进行中**

- 修复项：
  1. 统一 `CLDNode` 字段为 `id, label, description`（以 `models.py` 为准）
  2. 统一 `SharedCLD.edges` 类型为 `list[CausalLink]`
  3. `guardrails.py` 中 `CLDFlowRunContext` → `RunContext`
  4. `CausalLink.relation` 改为 `Literal["influences", "causes", "enables", "inhibits", "supports", "requires"]`
  5. `ParsedQuery.documents` 从 `list[dict[str, Any]]` 改为 `list[Document]`（LlamaIndex Document，D5 决策）
  6. `CLDAnalysisInput.documents` 从 `list[str]` 改为 `list[Document]`
  7. 补充缺失 schema：`FCMAnalysisInput/Output`, `D2DAnalysisInput/Output`, `PerspectiveSpec`, `Scenario`, `SimConfig`
- 补齐目录：`orchestration/`, `modules/fcm/`, `modules/d2d/`, `input/`
- 验收：所有模块 import 无报错，`mypy` 通过

#### T4. 建立输入层 MVP

- 产出：`input/enhance.py`（HyDE + 多查询）, `input/retrieve.py`（来源分级检索）, `input/stop_rules.py`（饱和度检测）
- 验收：输入研究问题 → 输出 `ParsedQuery`（含真实文档）
- 依赖：`backend/infrastructure/llms/factory.py`（LLM 创建）, `backend/business/rag_engine/retrieval/`（检索能力）
- 设计延迟：HyDE prompt、多查询角度生成策略、饱和度检测算法在实施时设计
- **可与 T3 并行**

#### T5. 建立 RunContext 与 Budget Guard — **进行中**

- 产出：`orchestration/guardrails.py`（Pipeline Rail, Budget Guard, Schema Guard, Isolation Guard, Self-Review Gate）
- 验收：`RunContext` 初始化独立，Budget Guard 基于 `budget_tokens`/`tokens_used` 工作
- **已完成**：`RunContext` dataclass, 基础 guardrails
- **待完成**：完整 5 项护栏实现

### 阶段 2：CLD 链路

#### T6. 建立 Lead Agent 编排骨架

- 产出：`orchestration/lead_agent.py`, `tools.py`, `prompts.py`
- 实现方式：LlamaIndex `AgentWorkflow` + `ReActAgent`（复用 `research_kernel/agent.py` 模式）
- 验收：可串联 CLD / FCM / D2D，Pipeline Rail 生效
- 依赖：`backend/infrastructure/llms/factory.py`

#### T7. 实现 CLD 视角生成

- 产出：`modules/cld/perspectives.py`
- 实现方式：复用 `backend/perspectives/` 的 `PerspectiveGenerator` + `TemplateRegistry`
- 验收：为同一问题生成 3-5 个视角
- 依赖：`backend/perspectives/generator.py`, `backend/perspectives/registry.py`

#### T8. 实现 CLD Specialist 提取

- 产出：`modules/cld/specialist.py`
- 实现方式：每个视角独立 LLM 调用，使用 Instructor 强制 JSON Schema 输出
- 验收：输出符合 `CausalLink` schema，支持 `asyncio.gather` 并行
- 依赖：DeepSeek-V3（D17）, Instructor 库
- 设计延迟：因果链提取 prompt 骨架在实施时设计

#### T9. 实现节点归并与冲突检测

- 产出：`modules/cld/merge.py`, `conflict.py`
- 实现方式：MiniLM-L6-v2 计算余弦相似度（D21），阈值 >0.8 归并
- 验收：归并正确，冲突分级（低 <0.3 / 中 0.3-0.5 / 高 >0.5）
- 依赖：`sentence-transformers` 库
- 设计延迟：归并聚类算法、冲突度计算公式在实施时设计

#### T10. 实现 CLD 裁判与自审门禁

- 产出：`modules/cld/judge.py`
- 实现方式：GPT-4o-mini（D17）做高分歧仲裁（非投票），自审输出质量
- 验收：自审失败不进入下游（I-7）
- 设计延迟：仲裁 prompt（输入：各视角 CausalLink 列表 → 输出：融合后 CausalLink）在实施时设计

#### T11. 实现 SharedCLD 组装 — **部分完成**

- 产出：`modules/cld/module.py`（替换 placeholder 为真实实现）
- 验收：串联 T7-T10，输出 `SharedCLD` 可被 FCM/D2D 消费
- **已完成**：`CLDModule` 骨架, `CLDAnalysisInput/Output` schema

### 阶段 3：衍生分析（FCM / D2D 可并行）

#### T12. 实现 FCM 权重映射

- 产出：`modules/fcm/mapper.py`
- 实现方式：7 档映射表（±L/M/H/VH → ±0.3/0.5/0.7/0.9），纯 Python
- 验收：映射表固定、可测试

#### T13. 实现 FCM 批量评级与矩阵构建

- 产出：`modules/fcm/rater.py`
- 实现方式：单 Agent（DeepSeek-V3）基于完整 CLD 批量评级
- 验收：`SharedCLD` → `WeightedFCM`
- 设计延迟：批量评级 prompt（"看完整图，对每条边评级 ±L/M/H/VH"）在实施时设计

#### T14. 实现 FCM 仿真引擎

- 产出：`modules/fcm/simulator.py`
- 实现方式：FCMpy Kosko 迭代（D21），收敛阈值 `|Δstate| < 1e-6`
- 验收：返回稳定态或失败（不收敛 → 硬失败）
- 设计延迟：FCMpy API 用法在实施时确认

#### T15. 实现 D2D 扰动分析

- 产出：`modules/d2d/sensitivity.py`
- 实现方式：NumPy 矩阵运算，单节点 10% 扰动（D9）
- 验收：对 `SharedCLD` 运行，输出影响力分数

#### T16. 实现 D2D 不确定性与排序

- 产出：`modules/d2d/uncertainty.py`, `ranking.py`
- 实现方式：权重置信度传播 → 区间估计，按影响力+置信度排序
- 验收：输出 `LeverageAnalysis`

### 阶段 4：报告 + 测试

#### T17. 实现报告层融合

- 产出：`reporting.py`
- 实现方式：Lead Agent 做语义融合（单 Agent 多轮），不做硬编码数据转换
- 验收：生成 `StructuredReport` 或 `StructuredFailureReport`

#### T18. 建立测试夹具与黄金样例

- 产出：2-3 个黄金样例，LLM mock 策略
- mock 方案：mock LlamaIndex LLM 层（`llama_index.core.llms.LLM`），返回预定义 JSON
- 黄金样例场景：财政补贴政策分析 + Prop 13（1978加州房产税）长期影响分析（D12）
- 设计延迟：具体输入文本和预期输出结构在实施时定义
- 验收：测试可重复运行，无网络依赖

#### T19. 建立单元测试与集成测试

- 产出：模型校验、映射、归并、冲突、仿真、扰动、主链路集成测试
- 验收：非 LLM 代码行覆盖率 ≥ 80%

#### T20. 输出 review 报告与后续建议

- 产出：完成度、风险、阻塞、Phase 2a 建议
- 验收：交由人类监督确认

### 阶段 5：可发布增量（G2-G8）

> **G1 已移除**：项目已有 `scripts/env_sync.py` + `make env-pull` 的 Gist 加密同步系统，`.env` 通过 `make env-pull` 从私有 Gist 拉取即可，无需 `.env.example`。
> CLDFlow 所需的 `DEEPSEEK_API_KEY` 已在 Gist 中配置。`OPENAI_API_KEY`（Judge Agent 可选）按 G6 降级策略，不配置也能工作。

#### G2. 创建 CLDFlow API 端点 — **P0**

- 产出：`backend/business/cldflow/api.py`
- 实现方式：FastAPI router，复用 `CLDFlowAppService` + `LeadAgent`
- 端点：
  - `POST /api/cldflow/analyze` — 接收 `{question, documents?}`，返回 `StructuredReport`
  - `GET /api/cldflow/health` — 健康检查
- 依赖：`fastapi`, `backend.core.cldflow.orchestration.lead_agent`
- 验收：`curl -X POST http://localhost:8000/api/cldflow/analyze -d '{"question":"..."}'` 返回 JSON

#### G3. 添加 CLDFlow 配置项 — **P0**

- 产出：`application.yml` 新增 `cldflow` 配置段
- 内容：
  ```yaml
  cldflow:
    specialist_model: deepseek-chat    # Specialist Agent 模型
    judge_model: deepseek-chat         # Judge Agent 模型（可改为 gpt-4o-mini）
    max_perspectives: 3                # 默认视角数
    budget_turns: 10                   # Lead Agent 最大轮次
    budget_tokens: 100000              # Token 预算
    timeout_seconds: 180               # 超时秒数
    fcm:
      max_iterations: 100              # Kosko 最大迭代
      convergence_threshold: 1.0e-6    # 收敛阈值
    d2d:
      perturbation_pct: 0.1            # 扰动百分比
  ```
- 验收：`config.get_cldflow_config()` 可读取所有配置

#### G4. CLDFlow 前端页面 — **P1**

- 产出：`frontend/components/cldflow_panel.py` + 集成到 `frontend/main.py`
- 实现方式：Streamlit 组件，输入研究问题 → 展示分析报告
- UI 元素：
  - 文本输入框（研究问题）
  - 文件上传（可选文档）
  - "开始分析" 按钮
  - 结果展示：CLD 图（networkx + pyvis）、FCM 场景对比表、杠杆点排序
- 依赖：`pyvis`（新增，用于 CLD 图可视化）
- 验收：Streamlit 页面可输入问题并展示分析结果

#### G5. `instructor` 集成 — **已完成**

- 产出：修改 `modules/cld/specialist.py`
- 实现方式：定义 `SpecialistOutput`/`SpecialistNode`/`SpecialistLink` Pydantic 模型，通过 `instructor.from_openai` 强制结构化输出，fallback 到 `_parse_and_validate()` 手动解析 + Pydantic 校验
- 验收：Specialist 输出通过 Pydantic schema 校验，无效 relation 自动拒绝

#### G6. Judge 降级策略 — **已完成**

- 产出：修改 `modules/cld/judge.py` + `modules/cld/module.py` + `orchestration/tools.py`
- 实现方式：`get_judge_llm()` 函数，`OPENAI_API_KEY` 存在时用 GPT-4o-mini，否则用配置的 `judge_model`（默认 DeepSeek）
- 验收：无 OpenAI key 时 Judge 正常工作（用 DeepSeek），`judge_model` 从 `application.yml` 的 `cldflow.judge_model` 读取

#### G7. README 安装说明 — **已完成**

- 产出：`README.md` 更新
- 内容：快速开始（gh token 同步）、CLDFlow 流水线说明、API curl 示例、配置项说明、文档导航更新
- 验收：新用户按 README 可在 5 分钟内跑通

#### G8. sentence-transformers 预加载 — **已完成**

- 产出：`scripts/preload_models.py`
- 集成：`Makefile` 新增 `make preload-models` 目标
- 验收：`make preload-models` 后离线可用

## 6. 执行顺序

```
阶段 1（基础）     T3 + T4 + T5  （并行，T3 先修 schema 再继续）
阶段 2（CLD链路）  T6 → T7 → T8 → T9 → T10 → T11
阶段 3（衍生分析）  T12 → T13 → T14  |  T15 → T16       （并行）
阶段 4（报告+测试） T17 → T18 → T19 → T20
阶段 5（可发布）    G3  →  G2 + G5 + G6  →  G4  →  G7 + G8
                  （P0 配置）（P0+P1 集成）   （前端） （P2 文档）
```

### 当前状态

- 阶段 1-4：✅ 全部完成（20/20 任务）
- 阶段 5：✅ 全部完成（G2-G8，G1 已由 env sync 覆盖）

## 7. AI 自主授权

> 以下操作授权 AI Agent 自主执行，无需逐项确认。

| 授权范围 | 说明 |
|----------|------|
| **依赖安装** | AI 可自主将缺失包加入 `pyproject.toml` 并执行 `uv sync`。安装前需确认包名和版本约束与本计划一致 |
| **代码修复** | T3 的 7 项修复（schema 统一、类型升级、目录补齐）授权 AI 自主执行 |
| **文件创建** | 各任务产出的新文件（`orchestration/`, `modules/fcm/`, `modules/d2d/`, `input/` 下的模块）授权 AI 自主创建 |
| **测试编写** | T18-T19 的测试用例、mock fixture 授权 AI 自主编写 |
| **G2 API 端点** | `cldflow/api.py` 创建授权 AI 自主执行 |
| **G3 配置项** | `application.yml` 新增 `cldflow` 配置段授权 AI 自主执行 |
| **G5 instructor 集成** | `specialist.py` 重构为使用 instructor 授权 AI 自主执行 |
| **G6 降级策略** | `judge.py` 降级逻辑授权 AI 自主执行 |
| **G8 预加载脚本** | `scripts/preload_models.py` + Makefile 目标授权 AI 自主执行 |

**不授权**：
- 架构决策变更（如改变 Agent 模式、修改不变量）
- 外部 API key 配置
- 删除已有文件或破坏性重构

## 8. 质量门禁

- 所有结构化对象通过 Pydantic strict mode 校验
- 关键路径禁止裸异常与静默失败
- 模块失败落入 `StructuredFailureReport`
- 测试未覆盖的能力不得视为 MVP 完成
- 单个代码文件 ≤ 300 行

## 9. 依赖清单

> AI Agent 可自主执行安装（见 §7 授权）。

### 9.1 Python 包依赖

| 依赖 | 用途 | 当前状态 |
|------|------|----------|
| `networkx` | CLD 图操作、环检测 | ✅ 已安装 |
| `sentence-transformers` | 节点归并余弦相似度（MiniLM-L6-v2） | ✅ 已安装 |
| `instructor` | LLM 结构化 JSON 输出 | ✅ 已安装（未集成） |
| `numpy` | D2D 扰动计算、FCM 矩阵运算 | ✅ 已安装 |
| ~~`fcmpy`~~ | FCM Kosko 仿真 | ❌ 移除（tqdm 版本冲突），用 NumPy 直接实现 |

> 已有依赖：`llama-index`, `pydantic`, `openai`, `structlog`, `fastapi`, `streamlit`, `chromadb` 等无需新增。

### 9.2 外部服务依赖（用户需配置）

| 服务 | 环境变量 | 用途 | 必需 |
|------|----------|------|------|
| DeepSeek API | `DEEPSEEK_API_KEY` | Specialist Agent (V3), 评测 (V3) | ✅ 是 |
| OpenAI API | `OPENAI_API_KEY` | Judge Agent (GPT-4o-mini) | 可选（可降级为 DeepSeek） |
| HuggingFace | `HF_ENDPOINT` | sentence-transformers 模型下载 | 可选（有字符串回退） |

### 9.3 MVP 可发布缺口清单

> 以下为从"代码完成"到"可发布使用"的增量工作。

| # | 缺口 | 类型 | 说明 | 优先级 |
|---|------|------|------|--------|
| ~~G1~~ | ~~`.env.example` 缺失~~ | ~~配置~~ | 已由 `make env-pull` 覆盖，Gist 中已配置 DEEPSEEK_API_KEY | **已覆盖** |
| G2 | CLDFlow API 端点 | 集成 | FastAPI router，供前端/外部调用 | **已完成** |
| G3 | CLDFlow 配置项 | 配置 | `application.yml` 中添加 CLDFlow 模型预设 | **已完成** |
| G4 | CLDFlow 前端页面 | 集成 | React 页面，输入问题 → 展示报告 | **已完成** |
| G5 | `instructor` 集成 | 代码 | `specialist.py` 使用 instructor + Pydantic schema 校验 | **已完成** |
| G6 | Judge 降级策略 | 代码 | Judge 默认用 DeepSeek，可选 GPT-4o-mini | **已完成** |
| G7 | README 安装说明 | 文档 | 包含 CLDFlow 的 setup + 运行指引 | **已完成** |
| G8 | sentence-transformers 预加载 | 脚本 | 首次运行需下载 ~80MB 模型 | **已完成** |

## 10. 可复用模块映射

| CLDFlow 任务 | 复用来源 | 复用方式 |
|--------------|----------|----------|
| T4 输入增强 | `backend/business/rag_engine/retrieval/` | 调用现有检索器 |
| T4 输入增强 | `backend/business/rag_engine/processing/` | 调用查询处理 |
| T6 Lead Agent | `backend/business/research_kernel/agent.py` | 参考 AgentWorkflow 模式 |
| T7 视角生成 | `backend/perspectives/generator.py` | 直接复用 `PerspectiveGenerator` |
| T7 视角生成 | `backend/perspectives/registry.py` | 直接复用 `TemplateRegistry` |
| T6/T8/T10 LLM | `backend/infrastructure/llms/factory.py` | 调用 `create_llm()` |
| T6 可观测性 | `backend/infrastructure/observers/` | 注入 observer |
| T6 日志 | `backend/infrastructure/logger.py` | 调用 `get_logger()` |

---

# 附录 A：接口契约速查

> 详细接口定义见 [`ARCHITECTURE.md`](../ARCHITECTURE.md)。

## A1：输入层 → Lead Agent

```yaml
输入: research_question: str
输出: ParsedQuery
  ├── query_text: str
  ├── documents: list[Document]        # LlamaIndex Document（D5 决策）
  └── context: dict[str, Any]
```

## A2：Lead Agent → CLD Module

```yaml
工具: run_cld_analysis
输入: CLDAnalysisInput          # 已定义于 modules/cld/schema.py，需更新 documents 类型
  ├── research_question: str
  ├── documents: list[Document]    # LlamaIndex Document（D5 决策）
  ├── perspective_hints: list[str] | None
  └── max_perspectives: int = 3
输出: CLDAnalysisOutput          # 已定义于 modules/cld/schema.py
  ├── shared_cld: SharedCLD
  ├── perspectives_used: list[str]
  ├── confidence: float
  └── diagnostics: dict
```

## A3：Lead Agent → FCM Module

```yaml
工具: run_fcm_analysis
输入: FCMAnalysisInput           # 待定义于 modules/fcm/schema.py
  ├── shared_cld: SharedCLD
  ├── intervention_scenarios: list[Scenario] | None
  └── simulation_config: SimConfig | None
输出: FCMAnalysisOutput
  ├── weighted_fcm: WeightedFCM
  └── diagnostics: dict
```

## A4：Lead Agent → D2D Module

```yaml
工具: run_d2d_analysis
输入: D2DAnalysisInput           # 待定义于 modules/d2d/schema.py
  ├── shared_cld: SharedCLD
  ├── variable_types: dict[str, Literal["stock","flow","auxiliary","constant"]]
  └── perturbation_pct: float = 0.1
输出: D2DAnalysisOutput
  ├── leverage_analysis: LeverageAnalysis
  └── diagnostics: dict
```

## A5：Lead Agent → 报告层

```yaml
输入:
  ├── shared_cld: SharedCLD
  ├── weighted_fcm: WeightedFCM | None
  ├── leverage_analysis: LeverageAnalysis | None
  └── run_context: RunContext
输出: StructuredReport | StructuredFailureReport
```

# 附录 B：失败与降级矩阵

| 场景 | 类型 | 处理 | 输出 |
|------|------|------|------|
| 检索为空 | 硬失败 | 改写重试 1 次后终止 | 失败摘要 |
| Schema 校验失败 | 硬失败 | 单视角重试 ≤3 次，视角数 <2 则终止 | 失败摘要 |
| 节点归并/冲突自审失败 | 硬失败 | 修复回路，失败则终止 | 失败摘要 |
| FCM 部分边缺失评级 | 软失败 | 降低该边置信度，继续聚合 | 低置信度报告 |
| FCM 不收敛 | 硬失败 | 参数回退重试 1 次，仍失败则终止 | 失败摘要 |
| D2D 区间过宽 | 软失败 | 继续输出，显式标记 low confidence | 低置信度报告 |

# 附录 C：Agent 模式速查

| 层 | 模式 | LLM | 理由 |
|----|------|-----|------|
| 输入层 | 单 Agent + 并发工具 | DeepSeek-V3 | 子任务工具性 |
| CLD 视角生成 | 单 Agent | DeepSeek-V3 | 复用 perspectives 模块 |
| CLD Specialist | **多 Agent 并行** | DeepSeek-V3 (D17) | 视角真独立 |
| CLD 裁判 | 单 Agent | GPT-4o-mini (D17) | 高分歧仲裁 |
| FCM 评级 | 单 Agent | DeepSeek-V3 | 全局图语义依赖 |
| D2D | 纯工具 | 无 | NumPy 计算 |
| 报告层 | 单 Agent 多轮 | DeepSeek-V3 | 全局一致叙述 |
