# AGENTS.md

> 地图，不是说明书。详细知识见 docs/ 下的对应文档。
> 渐进式披露：从核心原则到层细节，按需深入。

## 项目定位

以系统科学为方法论内核的深度研究 Agent，输出可审计、可评估、可复现的结构化研究。

- 技术栈：`Python 3.12 + uv + Streamlit`（`frontend/` 是 Python，不是 Node）
- 编排：`agent-nightshift`
- 三支柱：领域定制 · 可审计 · 评估反馈

## 架构不变量

1. **三层依赖方向**：前端→业务→基础设施，禁止反向。见 `docs/ARCHITECTURE.md` §1.3
2. **CLD 输出必须符合 JSON Schema**：见 `docs/ARCHITECTURE.md` §1.3
3. **CLD 前置 + FCM/D2D 可选可并行**（原"流水线不可拆"已演进）：CLD 为根，FCM 与 D2D 是 CLD 的并列衍生分析，由 Lead Agent 按需组合调用，护栏强制 CLD 就绪才可调用衍生工具。见 `docs/ARCHITECTURE.md` §1.3
4. **全自动协作，无人工介入点**：见 `docs/ARCHITECTURE.md` §1.3
5. **数据边界解析（Parse, Don't Validate）**：见 `docs/ARCHITECTURE.md` §1.3
6. **研究运行隔离**：见 `docs/ARCHITECTURE.md` §1.3
7. **自审通过才传递**：见 `docs/ARCHITECTURE.md` §1.3

## 工作信念

见 `docs/ARCHITECTURE.md` §1.2。核心：

- 地图优于说明书（AGENTS.md ≤ 100行）
- 执行不变量，不微管实现（边界内允许自主）
- 仓库即唯一事实源（不在仓库中的=不存在）
- Agent 困境 = 信号（缺什么补什么，不"更努力"）
- 纪律在脚手架，不在代码

## 文档地图

### 核心文档（docs/ 根目录）

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 系统架构唯一事实源（核心设计、业务架构、工程架构、工作流程、核心模块、目录结构、数据统计） |

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
