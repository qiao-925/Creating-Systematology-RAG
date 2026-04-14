# AGENTS.md

> 地图，不是说明书。详细知识见 docs/ 下的对应文档。
> 渐进式披露：从核心原则到层细节，按需深入。

## 项目定位

以系统科学为方法论内核的深度研究 Agent，输出可审计、可评估、可复现的结构化研究。

- 技术栈：`Python 3.12 + uv + Streamlit`（`frontend/` 是 Python，不是 Node）
- 编排：`agent-nightshift`
- 三支柱：领域定制 · 可审计 · 评估反馈

## 架构不变量

1. **三层依赖方向**：前端→业务→基础设施，禁止反向。见 `docs/CLDFlow-invariants.md` I-1
2. **CLD 输出必须符合 JSON Schema**：见 `docs/CLDFlow-invariants.md` I-2
3. **CLD→FCM→D2D 流水线不可拆**：见 `docs/CLDFlow-invariants.md` I-3
4. **全自动协作，无人工介入点**：见 `docs/CLDFlow-invariants.md` I-4
5. **数据边界解析（Parse, Don't Validate）**：见 `docs/CLDFlow-invariants.md` I-5
6. **研究运行隔离**：见 `docs/CLDFlow-invariants.md` I-6
7. **自审通过才传递**：见 `docs/CLDFlow-invariants.md` I-7

## 工作信念

见 `docs/core-beliefs.md`。核心：

- 地图优于说明书（AGENTS.md ≤ 100行）
- 执行不变量，不微管实现（边界内允许自主）
- 仓库即唯一事实源（不在仓库中的=不存在）
- Agent 困境 = 信号（缺什么补什么，不"更努力"）
- 纪律在脚手架，不在代码

## 文档地图

### 核心文档（docs/ 根目录）

| 文档 | 内容 |
|------|------|
| `docs/core-beliefs.md` | 工作信念（15命题，三层结构） |
| `docs/CLDFlow-invariants.md` | 7个不可变约束 |
| `docs/CLDFlow-defaults.md` | 实现默认值（可调） |
| `docs/CLDFlow-architecture.md` | CLDFlow业务架构（流程图+五层职责+接口契约+数据流） |
| `docs/architecture.md` | 系统架构设计 |

### 各层详细设计（docs/cldflow/）

| 文件 | 层 | 内容 |
|------|-----|------|
| `input-enhancement.md` | 输入层 | 查询增强+停止条件+数据源分级 |
| `cld-extraction.md` | CLD | 提取策略+Prompt模板 |
| `cld-node-merging.md` | CLD | 节点归并算法 |
| `cld-conflict-resolution.md` | CLD | 冲突检测+消解策略 |
| `cld-data-format.md` | CLD | Pydantic数据模型+自审验证 |
| `dynamic-agent.md` | CLD | 动态视角Agent生成 |
| `fcm-weight-conversion.md` | FCM | 语言权重→数值映射 |
| `fcm-simulation.md` | FCM | Kosko仿真算法+激活函数 |
| `fcm-aggregation.md` | FCM | 多专家权重聚合 |
| `d2d-sensitivity-analysis.md` | D2D | 敏感性分析+杠杆点分类 |
| `d2d-uncertainty.md` | D2D | 不确定区间计算 |
| `conductor-orchestration.md` | 跨层 | Conductor编排状态机 |
| `code-quality-evaluator.md` | 跨层 | 代码生成质量评估 |
| `perspectives-implementation.md` | 跨层 | 已实现的视角模板系统 |

### 调研与探索（docs/research/）

| 目录 | 内容 |
|------|------|
| `docs/research/insights/` | 产品方向、竞品分析、生态图谱、架构洞察、MCP工具 |
| `docs/research/harness-engineering/` | Harness Engineering文章拆解与学习路径 |
| `docs/research/orient-report.md` | 研究Agent MVP能力评估 |

### 工程参考（docs/engineering/）

| 文件 | 内容 |
|------|------|
| `frontend-layout-stability.md` | 前端布局稳定性 |
| `performance-optimization-ragservice.md` | RAG服务性能优化 |
| `quick-start-advanced.md` | 高级快速启动 |

### 架构治理

| 文件 | 内容 |
|------|------|
| `skills/cs-rag-architecture-guideline/SKILL.md` | 架构治理规则 |

## 验证

- Setup/Verify 命令：见 `.agent/project.yaml`
- 窄修复：先加/更新最小相关测试，再跑 verify
- 不用性能测试或 GitHub E2E 作为默认验证路径

## 约束

- 不改依赖、认证、公开 API、模型/Provider 默认值、向量存储持久化语义——除非任务明确允许
- 不改 `data/`、`logs/`、`sessions/`、`.env`、`.venv/`、`agent-task-log/`——除非 Issue 明确要求
- 可写路径以 `.agent/project.yaml` 的 `workspace.writable_paths` 为准
- `.working-memory/` 始终可写（auto-checkpoint 用）

## 执行上下文

- 当前 Issue 执行上下文：`.agent/runtime/issue-plan.md`
- 工作记忆看板：`.working-memory/board.md`
- 进行中任务：`.working-memory/ongoing/`
- Auto-checkpoint：每 3 轮对话，配置见 `.agent/runtime/working-memory-boost.md`
