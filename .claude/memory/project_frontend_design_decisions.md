---
name: project-frontend-design-decisions
description: CLDFlow 前端设计方向决策 — Vercel 设计语言 + Agent 问答结构，Figma MCP 工作流验证
metadata: 
  node_type: memory
  type: project
  originSessionId: 2fad5c49-1381-4332-b529-655eb4b29afb
---

## 前端设计方向（2026-05-19 确定）

**设计语言（阶段一探索中）**：Awesome Design MD 七版对比（Vercel / Linear / Claude / Cursor / Notion / Stripe / Figma DS），**尚未最终选型**。Vercel 为当前 Figma Canonical 基线。

**Why:** 用户要求先收敛设计稿、弃用 HTML mockup，在 Figma 完成风格实验后再改代码。

**How to apply:** 阶段一只改 Figma + `docs/design/`；阶段二实现参照 `docs/design/style-exploration-matrix.md` 选定风格。

## UI 结构决策

采用 **Agent 问答式布局**（非传统三栏 Dashboard）：
- **无模式切换**：去掉 Chat/Research/CLDFlow 三个 tab，统一为单一聊天入口。Agent 根据问题自动判断分析路径
- 无侧边栏（MVP 阶段保持简洁）
- 扁平消息流（无气泡），用户右对齐，助手左对齐
- 分步 Thinking 指示器（Perplexity 风格）
- CLD 图/FCM 结果内联渲染在消息流中（非侧边面板）
- 行内引用 [1][2] + 底部来源卡片

**参考来源**：ChatGPT、Claude、v0.dev、Perplexity 的 UI 模式对比分析。

## MVP 范围裁剪（2026-05-19 锚定）

MVP 只做 Chat 视角，不做模式拆分：
- Header：logo + 设置按钮，无 tab
- CLD 图可视化（B8）延后，MVP 用文本渲染节点/边
- FCM/D2D 可视化（B9）延后，MVP 用现有 LeverageRanking 组件
- Thinking steps：MVP 可先用简单 spinner，后端返回结构化步骤后再做分步指示器

## Figma MCP 工作流（2026-05-20 收敛）

- **MCP 账号**：`noneplus@outlook.com`（2026-05-20 用户确认）
- **真源文件**：https://www.figma.com/design/GetdOs1IPlJcW5mdrKhVH3（CLDFlow — Design Phase 1）
- **初版参考（只读）**：https://www.figma.com/design/6ajDseXpLEBRGu12Ta4BRM/CLDFlow-V2-Design-Mockup
- **流程**：仅 Figma MCP；**弃用** HTML capture
- **限制**：Starter 3 Pages + View 席位写入受限 + MCP 月度额度
- 文档：`docs/design/figma-phase1-workflow.md`

## 计划文档

- 路径：`docs/CLDFlow MVP Builder/tracks/B-前端-Demo.md`（注意中文文件名）
- 已更新：D6/D7 决策、设计方向章节、执行记录

## 设计参考资源

- **awesome-design-md**：https://github.com/voltagent/awesome-design-md — 73 个品牌的 DESIGN.md，Vercel 版在 `design-md/vercel/DESIGN.md`
- **DESIGN.md 格式**：Google Stitch 提出的纯文本设计系统文档，AI Agent 可直接读取生成一致 UI
