# CLDFlow MVP 可执行计划书

> 交付一条稳定、可验证、可扩展的 CLD → FCM → D2D 主链路。

## 版本目标

- 做什么：交付完整的 CLD → FCM → D2D 因果分析主链路，含输入增强、结构化报告、测试闭环
- 为什么：系统缺乏结构化因果分析能力，需要先跑通核心流程再迭代

### 成功标准

- 通过一条完整的 CLD → FCM → D2D 主链路
- 关键输入输出具备严格 schema 校验（Pydantic strict mode）
- 任一模块失败时可返回结构化失败报告
- 至少有一组可复现测试样例覆盖完整流水线
- 非 LLM 代码行覆盖率 ≥ 80%

### 范围

**In Scope**
- 输入增强：HyDE、多查询、停止规则、来源分级
- Lead Agent 编排骨架（LlamaIndex AgentWorkflow）
- CLD 模块：视角生成、专家提取、节点归并、冲突检测、裁判机制
- FCM 模块：语言权重映射、权重矩阵、Kosko 仿真、场景对比
- D2D 模块：扰动分析、不确定性区间、杠杆点排序
- 报告层：综合洞察、证据追溯、失败终态
- 测试体系：单测、集成测试、端到端校验、回归样例

**Out of Scope**
- Phase 2/3 的候选工具自动选择
- GraphML 全量支持、贝叶斯权重聚合
- 复杂的人类协作流程、生产级多租户与权限系统
- 老 RAG 工程的一次性全量重构
- D2D 解释生成 Agent（MVP 阶段不需要）

## 文档锚定

- 锚定：`ARCHITECTURE.md` — 主链路架构定义、接口契约
- 锚定：`README.md` — 用户入口、安装说明
- 同步：`pytest.ini` / `Makefile` — 测试路径

## 决策清单

### 核心决策

- [x] D1 编排框架：选项 A LlamaIndex AgentWorkflow / B 自定义轻量编排器 → 选 A，复用 `research_kernel/agent.py` 样板
- [x] D2 CLDNode 字段：以 `models.py` 为准：`id, label, description`（D24 UUID + D23 删除置信度 + D25 删除 strength）
- [x] D4 FCM 仿真引擎：FCMpy（D21 技术栈锁定）
- [x] D5 ParsedQuery.documents 类型：LlamaIndex `Document` 组件
- [x] D7 D2D 解释 Agent：MVP 不做，纯计算输出
- [x] D8 输入增强数据源：arXiv + Semantic Scholar + FRED + World Bank + OECD（全部 5 个）

### 支撑决策

- [x] D3 CausalLink.relation：`Literal["influences", "causes", "enables", "inhibits", "supports", "requires"]`
- [x] D6 PerspectiveSpec 类型：定义 Pydantic model，复用 `perspectives/generator.py` 的 Perspective 结构
- [x] D9 HyDE 实现模型：DeepSeek-V3（D17 模型分工）
- [x] D10 节点归并 Embedding：MiniLM-L6-v2（D21 技术栈锁定）
- [x] D11 测试 mock 方案：mock `llama_index.core.llms.LLM.complete()` 方法
- [x] D12 黄金样例场景：财政补贴 + Prop 13（1978加州房产税）

> 来源：`docs/research with brainstorm/issue-15-CLDFlow架构设计与实现-v2.md` + 用户确认。

## 任务清单

### 阶段 1：基础修复与骨架

- [x] T1 统一迁移边界与 MVP 范围
  - 产出：本计划书
  - 失败路径：—

- [x] T2 设计 CLDFlow 核心数据模型
  - 产出：`models.py` 11 个模型
  - 验收：strict mode 可校验
  - 失败路径：降级 — 减少模型数量，先覆盖核心

- [x] T3 修复代码不一致 + 补齐目录骨架
  - 修复项：CLDNode 字段统一 / edges 类型统一 / RunContext 命名统一 / CausalLink.relation 枚举 / ParsedQuery.documents 类型升级 / 补充缺失 schema
  - 补齐目录：`orchestration/`, `modules/fcm/`, `modules/d2d/`, `input/`
  - 验收：所有模块 import 无报错，mypy 通过
  - 失败路径：降级 — 逐项修复，不阻塞后续

- [x] T4 建立输入层 MVP
  - 产出：`input/enhance.py`, `input/retrieve.py`, `input/stop_rules.py`
  - 验收：输入研究问题 → 输出 `ParsedQuery`（含真实文档）
  - 失败路径：降级 — 用硬编码文档先跑通链路

- [x] T5 建立 RunContext 与 Budget Guard
  - 产出：`orchestration/guardrails.py`（Pipeline Rail, Budget Guard, Schema Guard, Isolation Guard, Self-Review Gate）
  - 验收：RunContext 初始化独立，Budget Guard 基于 budget_tokens/tokens_used 工作
  - 失败路径：降级 — 先实现 Budget Guard，其余护栏后续补

### 阶段 2：CLD 链路

- [x] T6 建立 Lead Agent 编排骨架
  - 产出：`orchestration/lead_agent.py`, `tools.py`, `prompts.py`
  - 验收：可串联 CLD / FCM / D2D，Pipeline Rail 生效
  - 失败路径：降级 — 用硬编码顺序串联，不用 Agent 编排

- [x] T7 实现 CLD 视角生成
  - 产出：`modules/cld/perspectives.py`
  - 验收：为同一问题生成 3-5 个视角
  - 失败路径：降级 — 固定 3 个模板视角

- [x] T8 实现 CLD Specialist 提取
  - 产出：`modules/cld/specialist.py`
  - 验收：输出符合 CausalLink schema，支持 asyncio.gather 并行
  - 失败路径：重试 — 调整 prompt；降级 — 串行执行

- [x] T9 实现节点归并与冲突检测
  - 产出：`modules/cld/merge.py`, `conflict.py`
  - 验收：归并正确，冲突分级（低 <0.3 / 中 0.3-0.5 / 高 >0.5）
  - 失败路径：降级 — 跳过归并，直接拼接

- [x] T10 实现 CLD 裁判与自审门禁
  - 产出：`modules/cld/judge.py`
  - 验收：自审失败不进入下游
  - 失败路径：降级 — 跳过裁判，直接取第一个视角输出

- [x] T11 实现 SharedCLD 组装
  - 产出：`modules/cld/module.py`
  - 验收：串联 T7-T10，输出 SharedCLD 可被 FCM/D2D 消费
  - 失败路径：降级 — 用 placeholder 先跑通链路

### 阶段 3：衍生分析（FCM / D2D 可并行）

- [x] T12 实现 FCM 权重映射
  - 产出：`modules/fcm/mapper.py`
  - 验收：7 档映射表固定、可测试
  - 失败路径：—

- [x] T13 实现 FCM 批量评级与矩阵构建
  - 产出：`modules/fcm/rater.py`
  - 验收：SharedCLD → WeightedFCM
  - 失败路径：降级 — 用固定权重矩阵

- [x] T14 实现 FCM 仿真引擎
  - 产出：`modules/fcm/simulator.py`
  - 验收：Kosko 迭代收敛，返回稳定态；不收敛 → 硬失败
  - 失败路径：重试 — 调整收敛阈值；降级 — 用简单线性传播

- [x] T15 实现 D2D 扰动分析
  - 产出：`modules/d2d/sensitivity.py`
  - 验收：对 SharedCLD 运行，输出影响力分数
  - 失败路径：—

- [x] T16 实现 D2D 不确定性与排序
  - 产出：`modules/d2d/uncertainty.py`, `ranking.py`
  - 验收：输出 LeverageAnalysis
  - 失败路径：降级 — 跳过不确定性，只输出排序

### 阶段 4：报告 + 测试

- [x] T17 实现报告层融合
  - 产出：`reporting.py`
  - 验收：生成 StructuredReport 或 StructuredFailureReport
  - 失败路径：降级 — 硬编码模板报告

- [x] T18 建立测试夹具与黄金样例
  - 产出：2-3 个黄金样例，LLM mock 策略
  - 验收：测试可重复运行，无网络依赖
  - 失败路径：降级 — 先用 1 个样例

- [x] T19 建立单元测试与集成测试
  - 产出：模型校验、映射、归并、冲突、仿真、扰动、主链路集成测试
  - 验收：非 LLM 代码行覆盖率 ≥ 80%
  - 失败路径：降级 — 先覆盖核心路径

- [x] T20 输出 review 报告与后续建议
  - 产出：完成度、风险、阻塞、Phase 2a 建议
  - 验收：交由人类监督确认

### 阶段 5：可发布增量（G2-G8）

> G1 已移除：项目已有 `scripts/env_sync.py` + `make env-pull` 的 Gist 加密同步系统。

- [x] G2 创建 CLDFlow API 端点
  - 产出：`backend/business/cldflow/api.py`（FastAPI router）
  - 验收：`curl POST /api/cldflow/analyze` 返回 JSON
  - 失败路径：降级 — 只暴露 Python 接口，不走 HTTP

- [x] G3 添加 CLDFlow 配置项
  - 产出：`application.yml` 新增 `cldflow` 配置段
  - 验收：`config.get_cldflow_config()` 可读取所有配置
  - 失败路径：降级 — 硬编码默认值

- [x] G4 CLDFlow 前端页面
  - 产出：`frontend/components/cldflow_panel.py`
  - 验收：Streamlit 页面可输入问题并展示分析结果
  - 失败路径：跳过 — 后续迭代补

- [x] G5 instructor 集成
  - 产出：`modules/cld/specialist.py` 重构
  - 验收：Specialist 输出通过 Pydantic schema 校验
  - 失败路径：降级 — 用手动 JSON 解析

- [x] G6 Judge 降级策略
  - 产出：`modules/cld/judge.py` + `orchestration/tools.py`
  - 验收：无 OpenAI key 时 Judge 用 DeepSeek 正常工作
  - 失败路径：—

- [x] G7 README 安装说明
  - 产出：`README.md` 更新
  - 验收：新用户按 README 可在 5 分钟内跑通
  - 失败路径：—

- [x] G8 sentence-transformers 预加载
  - 产出：`scripts/preload_models.py` + Makefile 目标
  - 验收：`make preload-models` 后离线可用
  - 失败路径：—

## 执行记录

- [x] 05-15 阶段 1-4 全部完成（20/20 任务）
- [x] 05-16 阶段 5 全部完成（G2-G8）
- [x] 05-16 产品转型：RAG 应用 → CLDFlow Agent（63edd1c，673 files changed）
- [x] 05-18 HF Spaces Demo 部署：免费 Docker 托管，多阶段构建，双进程架构

### 产品转型执行链路（2026-05-16）

```
1. 技术栈调研 → LiteLLM SDK-only 风险可控，接入 DeepSeek + MiMO + Kimi
2. 后端迁移  → api/ → fastapi/，business/ → core/，infrastructure/ 保留
3. 旧系统分解 → 可复用部分沉淀到 infrastructure/，Chat/Research 删除
4. API 清理  → 移除 Chat/Research router、runtime_config
5. 文档更新  → README 重写、ARCHITECTURE 更新、pytest/Makefile 同步
6. 提交      → 63edd1c: 673 files changed, 5788 insertions(+), 70341 deletions(-)
```

### 转型关键决策

- [x] T1 LiteLLM 保留：SDK-only 风险可控，无替代方案能统一三模型
- [x] T2 旧系统处理：选 C（拆解复用），可复用部分沉淀到 infrastructure/
- [x] T3 Chat/Research 模式：删除，与 CLDFlow 零耦合，保留是死代码
- [x] T4 API 层命名：api/ → fastapi/，更直观
- [x] T5 core 层命名：business/ → core/，更简洁
- [x] T6 perspectives 归属：合并到 cld/，唯一消费者是 CLD 模块

### 已知遗留

- `llama-index-llms-openai` / `llama-index-llms-deepseek`：pyproject.toml 中仍存在，已通过 LiteLLM 替代，待删除
- Embedding 方案：HuggingFace Local vs API，暂未启用
- Reranker：SentenceTransformer / BGE，暂未启用

### HF Spaces Demo 部署（2026-05-18）

**目标**：免费部署一个可访问的 demo，无需运维。

**部署地址**：https://peter7310-cldflow.hf.space

**架构**：
```
HF Spaces (Docker, 免费 2vCPU/16GB)
├── Next.js 前端 (standalone, :7860)  ← 对外暴露
│   └── /api/* 代理 → FastAPI
└── FastAPI 后端 (uvicorn, :8000)     ← 内部
    └── DeepSeek API (LLM)
```

**技术决策**：
- [x] D1 部署平台：HF Spaces（免费 Docker 托管）
- [x] D2 服务架构：单容器双进程（uvicorn + next start），start.sh 启动
- [x] D3 构建方式：多阶段 Dockerfile（Node.js 构建 + Python 运行时）
- [x] D4 非必需模块：embedding/chroma/ragas 缺少 key 时静默跳过，不阻塞启动

**环境变量**：
| 变量 | 必需 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | LLM 调用 |
| `HF_TOKEN` | 否 | Embedding（hf-inference 模式） |
| `CHROMA_CLOUD_*` | 否 | 向量数据库 |

**构建修复记录**：
1. `package-lock.json` 不同步 → `npm install` 重新生成
2. Next.js standalone COPY 路径错误 → `.next/standalone/`（非 `.next/standalone/web/`）
3. Python 镜像缺 Node.js → 添加 nodesource 安装
4. `/app/logs` 权限问题 → 预创建目录 + chown

**文件变更**：
- `Dockerfile` — 多阶段重写（Node.js build + Python runtime）
- `start.sh` — 新建，双进程启动脚本
- `web/next.config.ts` — 添加 `output: "standalone"`
- `web/src/lib/api.ts` — STREAM_BASE 移除硬编码端口
- `backend/fastapi/main.py` — CORS 支持环境变量
- `README.md` — 添加 HF Spaces YAML frontmatter

**HF MCP 管理**：
```bash
claude mcp add hf-mcp-server -- npx -y @llmindset/hf-mcp-server
```

---

## 参考附录

### 附录 A：接口契约速查

> 详细接口定义见 `ARCHITECTURE.md`。

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

### 附录 B：失败与降级矩阵

- 检索为空 → 硬失败：改写重试 1 次后终止
- Schema 校验失败 → 硬失败：单视角重试 ≤3 次，视角数 <2 则终止
- 节点归并/冲突自审失败 → 硬失败：修复回路，失败则终止
- FCM 部分边缺失评级 → 软失败：降低该边置信度，继续聚合
- FCM 不收敛 → 硬失败：参数回退重试 1 次，仍失败则终止
- D2D 区间过宽 → 软失败：继续输出，显式标记 low confidence

### 附录 C：Agent 模式速查

- 输入层：单 Agent + 并发工具（DeepSeek-V3）
- CLD 视角生成：单 Agent（DeepSeek-V3）
- CLD Specialist：**多 Agent 并行**（DeepSeek-V3）— 视角真独立
- CLD 裁判：单 Agent（GPT-4o-mini）— 高分歧仲裁
- FCM 评级：单 Agent（DeepSeek-V3）— 全局图语义依赖
- D2D：纯工具（无 LLM）— NumPy 计算
- 报告层：单 Agent 多轮（DeepSeek-V3）— 全局一致叙述

### 附录 D：可复用模块映射

- T4 输入增强 → `backend/infrastructure/retrieval/`（调用现有检索器）
- T6 Lead Agent → `backend/infrastructure/agent/`（复用 AgentWorkflow 模式）
- T7 视角生成 → `backend/core/modules/cld/perspectives/`（复用 PerspectiveGenerator + TemplateRegistry）
- T6/T8/T10 LLM → `backend/infrastructure/llms/factory.py`（调用 create_llm via LiteLLM）
- T6 可观测性 → `backend/infrastructure/observers/`（注入 observer）
- T6 日志 → `backend/infrastructure/logger.py`（调用 get_logger()）
- T6 格式化 → `backend/infrastructure/formatting/`（复用输出格式化）

### 附录 E：AI 自主授权

**授权**：依赖安装 / T3 代码修复 / 文件创建 / 测试编写 / G2 API 端点 / G3 配置项 / G5 instructor 集成 / G6 降级策略 / G8 预加载脚本

**不授权**：架构决策变更 / 外部 API key 配置 / 删除已有文件或破坏性重构

### 附录 F：质量门禁

- 所有结构化对象通过 Pydantic strict mode 校验
- 关键路径禁止裸异常与静默失败
- 模块失败落入 StructuredFailureReport
- 测试未覆盖的能力不得视为 MVP 完成
- 单个代码文件 ≤ 300 行

### 附录 G：依赖清单

**Python 包**：networkx ✅ / sentence-transformers ✅ / instructor ✅ / numpy ✅ / ~~fcmpy~~（移除，用 NumPy 直接实现）

**外部服务**：DeepSeek API（必需）/ OpenAI API（可选，可降级为 DeepSeek）/ HuggingFace（可选）
