# Cursor Rules 规则索引与使用指南

> 本目录用于指导 Cursor AI 在不同任务场景下准确加载与执行项目专用规则，并落地“Rules（静态约束）—Commands（动态动作）—Agent（执行体）”分层协同模型。

---

## 1. 分层协同模型

### 1.1 角色定位
- **Rules（静态约束）**：长期有效的边界、触发条件与强制命令链，统一结构为“场景说明 → 触发条件 → 必执行命令 → 基线约束”。
- **Commands（动态动作）**：位于 `.cursor/commands/` 的可复用操作脚本，可由 Agent 根据规则触发或人工调用。
- **Agent**：读取规则 → 判断触发条件 → 选择命令 → 汇报执行结果，并在失败时协调补救。

### 1.2 触发闭环
1. 识别任务场景并加载对应规则。
2. 根据规则列出的触发条件判断是否需执行命令链。
3. 顺序调用命令，记录日志与产出物。
4. 如命令失败，Agent 负责调用备用命令或升级排障。

### 1.3 规则 → 命令映射

| 规则文件 | 场景说明 | 触发条件 | 强制命令链 | 基线约束示例 |
| --- | --- | --- | --- | --- |
| `workflow_requirements_and_decisions.mdc` | 方案确认 | 任务目标不清、存在多方案或需权衡 | — | 输出需求概述、方案对比与决策记录 |
| `testing_and_diagnostics_guidelines.mdc` | 测试与诊断 | 代码变更交付、测试失败或排障请求 | `/select-tests` → `/run-unit-tests` → `/summarize-test-results`（失败使用 `/auto-diagnose`） | 记录测试结果、补救计划与升级路径 |
| `coding_practices.mdc` | 代码编写规范 | 涉及 `src/`、`tests/` 代码改动 | — | 类型提示、日志与异常处理一致 |
| `documentation_guidelines.mdc` | 文档撰写规范 | 编辑 Markdown / 日志 / 规则文件 | — | 标题编号、日期格式、引用规范 |
| `architecture_design_guidelines.mdc` | 架构方案设计 | 牵涉跨模块或 RAG 流程调整 | — | 分层边界清晰、依赖无循环 |
| `personal-project-focus.mdc` | 个人项目聚焦原则 | 所有设计决策和功能开发 | — | 聚焦核心、避免大而全、拥抱临时方案 |
| `rule_authoring_guidelines.mdc` | 规则创建/优化 | 需要新增或重构规则 | `/design-rule` | 核对元数据、模板与评审要求 |
| `task_closure_guidelines.mdc` | 任务收尾 | 进入收尾阶段或用户指示 | `/generate-task-log` → `/run-optimization-review` → `/run-rule-check`（可选 `/execute-post-hooks`） | 日志命名、六维分析、规则执行率统计 |

### 1.4 命令体系速览

| 命令 | 触发时机 | 使用说明 | 关联规则 |
| --- | --- | --- | --- |
| `/auto-diagnose` | 排障流程或执行异常 | 引导排查与升级判断 | `testing_and_diagnostics_guidelines.mdc` |
| `/select-tests` | 代码改动完成准备测试 | 生成推荐测试列表 | `testing_and_diagnostics_guidelines.mdc` |
| `/run-unit-tests` | 获得测试列表后 | 逐条执行测试脚本 | `testing_and_diagnostics_guidelines.mdc` |
| `/summarize-test-results` | 单测完成 | 汇总命令与结果 | `testing_and_diagnostics_guidelines.mdc` |
| `/generate-task-log` | 进入后置流程 | 生成命名规范日志 | `task_closure_guidelines.mdc` |
| `/run-optimization-review` | 日志生成后 | 撰写六维优化分析 | `task_closure_guidelines.mdc` |
| `/run-rule-check` | 优化分析完成后 | 统计规则执行情况 | `task_closure_guidelines.mdc` |
| `/execute-post-hooks` | 需要一键收尾 | 顺序执行日志→分析→校验 | `task_closure_guidelines.mdc` |
| `/design-rule` | 设计/评审规则时 | 输出模板与检查清单 | `rule_authoring_guidelines.mdc` |

命令文件按场景划分目录：
- `.cursor/commands/testing_and_diagnostics/`
- `.cursor/commands/task_closure/`
- `.cursor/commands/rule_design/`

---

## 2. 规则执行总览

- 明确当前任务类型（方案讨论、代码实现、文档撰写、规则优化等）。
- 根据规则列出的触发条件判断是否需执行命令链。
- 完成主要交付后，执行 `/generate-task-log` → `/run-optimization-review` → `/run-rule-check`，或直接调用 `/execute-post-hooks`。

| 触发方式 | 说明 | 示例 |
| --- | --- | --- |
| **Always** | 无条件加载的基础规范 | 代码/文档规范、收尾流程等 |
| **Auto Attached** | Cursor 根据命中路径自动附加 | 在 `src/business/**` 内工作自动加载架构规范 |
| **Agent Requested** | 需用户显式指令才加载 | 请求“设计/优化规则”时调用 `rule_authoring_guidelines.mdc` |

**交付协作约定**
- 当主要交付完成且你未提出新的修改请求时，我会主动询问“是否进入后置流程？”——你确认后即执行全部后置命令。
- 如果你输入“收尾”“进入后置流程”“执行后置流程”等关键字，我会立即进入后置阶段。
- 如需暂缓执行，请明确告知；我将等待下一次触发以确保持有人类兜底。

---

## 3. 规则编写指南（基于 Cursor 官方建议）

- **控制长度**：单条规则文件不超过 500 行，必要时拆分为可组合的小规则。
- **聚焦可执行**：使用 Checklist 或步骤式语句描述明确行动要求，避免冗长叙述。
- **范围清晰**：说明适用场景、触发条件与输出要求，减少歧义。
- **引用示例**：复杂流程以引用文件形式提供，正文只保留核心要求。
- **一致复用**：在对话中复用同一套精简规则，避免上下文插入一次性提示。
- **持续更新**：规则演进后同步维护本 README，确保入口文档与实际规则一致。

---

## 4. 规则维护流程与行数审计

### 7.1 维护流程
- 触发条件：新增任务类型、优化现有规则、官方规范更新或出现执行痛点。
- 步骤：收集需求 → 更新本 README 规则组合 → 在对应 `.mdc` 文件落地修改 → 运行后置命令生成日志、复盘与规则校验。
- 验收：确认相关任务成功执行且通过规则校验，并记录于 `agent-task-log/`。

### 7.2 行数审计清单
- [ ] 审查每条新增/修改的规则文件，确认行数 ≤ 500。
- [ ] 检查是否存在重复内容，可否通过引用统一。
- [ ] 核对标题、触发方式、适用场景是否清晰一致。
- [ ] 在规则开头注明版本与最后更新时间，保持可追溯性。
- [ ] 更新本 README 的规则索引与版本信息。

---

## 8. 版本信息

- **最后更新**：2026-01-14
- **版本**：v4.3（新增个人项目聚焦原则规则）
