# 决策日志

每次核心任务追加一条。只增不改，天然时间线。人类扫一眼即可理解"这个东西是什么、为什么存在、文件之间什么关系"。

---

## 2026-05-19 文件路径放置规则

**问题**：agent 执行中文件乱放，违反高内聚低耦合。调研确认当前无任何机制能在 Claude Code 普通会话中阻止文件放错位置。

**方案**：PreToolUse hook 硬拦截 + `.claude/rules/` 模块化规则（对齐官方推荐）

**资产清单**：

| 文件 | 变更 | 说明 |
|------|------|------|
| `.claude/path-rules.yaml` | 新增 | hook 读取的机器可读配置，定义 zone 白名单和 root_files |
| `.claude/hooks/validate_path_hook.py` | 新增 | PreToolUse hook，Write 新文件时校验路径，exit 2 拦截 |
| `.claude/rules/path-placement.md` | 新增 | 人类可读的目录放置规则（zone 表格 + 硬性规则） |
| `.claude/rules/plan-doc-spec.md` | 新增 | 从 CLAUDE.md 搬出的 plan 文档规范 |
| `CLAUDE.md` | 重构 | 精简为 @import 入口（19→9 行） |
| `.claude/settings.json` | 修改 | 注册 PreToolUse hook + 修复旧 hook 的 Windows 硬编码路径 |
| `AGENTS.md` | 修改 | 新增约束体系概览 section |
| `docs/references/README.md` | 修改 | 锚定 Claude Code Rules/Hooks/AGENTS.md 官方文档 |

**关系**：hook 读 yaml 配置 → rules 是人类可读版本 → CLAUDE.md @import rules → AGENTS.md 提供全局概览

**关键设计决策**：
- 新文件（Write）必须落入已定义 zone，否则被拦截；已有文件（Edit）不受约束
- hook 通过 `os.path.exists()` 区分新旧文件，历史数据不清理
- 全局 gitignore 中 `.claude` 改为更精确的规则（只忽略 memory/settings.local.json/projects/）

**调研参考**：
- [Claude Code Rules 文档](https://code.claude.com/docs/zh-CN/memory)
- [Claude Code Hooks 文档](https://code.claude.com/docs/zh-CN/hooks)
- 详细调研记录：`docs/references/README.md` → Agent 工程约束 section

---

## 2026-05-20 设计阶段一 — Figma-only + 七版风格探索文档

**问题**：需收敛设计流程（弃 HTML mockup）、在 Figma 完成布局与风格实验，代码实现延后。

**方案**：新 Figma 文件为真源；`docs/design/` 落工作流、七版 token 矩阵、Thinking 可观测性规格。

**资产清单**：

| 文件 | 变更 | 说明 |
|------|------|------|
| `docs/design/figma-phase1-workflow.md` | 新增 | 阶段一 Figma-only 流程 |
| `docs/design/style-exploration-matrix.md` | 新增 | 7 版 Awesome Design MD 对比矩阵 |
| `docs/design/thinking-observability-spec.md` | 新增 | Perplexity 式 Thinking 规格 |
| `docs/CLDFlow MVP Builder/tracks/B-前端-Demo.md` | 修改 | 更新 Figma 链接与阶段划分 |
| `.claude/memory/project_frontend_design_decisions.md` | 修改 | 设计决策与 Figma 工作流 |

**Figma**：https://www.figma.com/design/6ajDseXpLEBRGu12Ta4BRM/CLDFlow-V2-Design-Mockup

---

## 2026-05-19 前端 UI 优化 + thinking-block 组件

**问题**：聊天界面需要展示 agent 推理过程，多个组件样式需要优化。

**方案**：新增 thinking-block 组件 + 优化现有 chat 组件样式

**资产清单**：

| 文件 | 变更 | 说明 |
|------|------|------|
| `web/src/components/chat/thinking-block.tsx` | 新增 | agent 推理过程展示组件 |
| `web/src/components/chat/message-bubble.tsx` | 修改 | 消息气泡样式优化 |
| `web/src/components/chat/chat-input.tsx` | 修改 | 输入框样式调整 |
| `web/src/components/chat/header-bar.tsx` | 修改 | 顶部栏样式调整 |
| `web/src/components/chat/markdown-content.tsx` | 修改 | Markdown 渲染优化 |
| `web/src/components/chat/message-list.tsx` | 修改 | 消息列表样式调整 |
| `web/src/components/chat/sources-panel.tsx` | 修改 | 来源面板样式优化 |
| `web/src/app/globals.css` | 修改 | 全局样式更新 |
| `design-mockup-v2.html` | 修改 | 设计稿更新 |
| `docs/CLDFlow MVP Builder/tracks/B-前端-Demo.md` | 修改 | 前端 Demo 文档更新 |

---

## 2026-05-15 CLAUDE.md 模块化 + 跨端同步

**问题**：CLAUDE.md 随规则增多会膨胀，多设备间配置不一致。

**方案**：`@import` 模块化 + `dev-sync` 仓库同步全局配置

**资产清单**：

| 文件 | 变更 | 说明 |
|------|------|------|
| `CLAUDE.md` | 新增 | 项目指令入口，@import 引入规则文件 |
| `AGENTS.md` | 新增 | 跨 agent 全局地图（文档索引） |
| `.claude/settings.json` | 新增 | hook 注册（PostToolUse plan 校验） |
| `.claude/hooks/validate_plan_hook.py` | 新增 | plan 文档结构校验 hook |
