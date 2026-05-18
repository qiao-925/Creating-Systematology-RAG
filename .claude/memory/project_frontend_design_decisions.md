---
name: project-frontend-design-decisions
description: CLDFlow 前端设计方向决策 — Vercel 设计语言 + Agent 问答结构，Figma MCP 工作流验证
metadata: 
  node_type: memory
  type: project
  originSessionId: 2fad5c49-1381-4332-b529-655eb4b29afb
---

## 前端设计方向（2026-05-19 确定）

**设计语言**：Vercel 风格（近白底 #fff + 墨黑 #171717 + 极简），基于 awesome-design-md 仓库的 Vercel DESIGN.md。

**Why:** 用户希望走主流 Agent 问答界面的设计范式，Vercel 的设计语言与项目技术栈（Next.js + Geist 字体 + shadcn/ui）天然匹配。

**How to apply:** 所有前端 UI 实现都应参照 Vercel DESIGN.md 的色彩、字体、间距、阴影体系。

## UI 结构决策

采用 **Agent 问答式布局**（非传统三栏 Dashboard）：
- 无侧边栏（MVP 阶段保持简洁）
- 扁平消息流（无气泡），用户右对齐，助手左对齐
- 分步 Thinking 指示器（Perplexity 风格）
- CLD 图/FCM 结果内联渲染在消息流中（非侧边面板）
- 行内引用 [1][2] + 底部来源卡片

**参考来源**：ChatGPT、Claude、v0.dev、Perplexity 的 UI 模式对比分析。

## Figma MCP 工作流（已验证可用）

- 安装：`claude plugin install figma@claude-plugins-official`
- 认证：首次使用时自动 OAuth，账号 hashassemble@gmail.com（Full seat）
- 流程：创建 HTML 设计稿 → 本地服务器 serve → Figma capture 脚本捕捉 → 写入 Figma 文件
- Figma 文件：https://www.figma.com/design/yZwrYKc5C8tGFW6OxPN0Kj
- V1（Dashboard 三栏）：node-id=1-2
- V2（Agent 问答式）：node-id=4-2 ← 当前方向

## 计划文档

- 路径：`docs/CLDFlow MVP Builder/tracks/B-前端-Demo.md`（注意中文文件名）
- 已更新：D6/D7 决策、设计方向章节、执行记录

## 设计参考资源

- **awesome-design-md**：https://github.com/voltagent/awesome-design-md — 73 个品牌的 DESIGN.md，Vercel 版在 `design-md/vercel/DESIGN.md`
- **DESIGN.md 格式**：Google Stitch 提出的纯文本设计系统文档，AI Agent 可直接读取生成一致 UI
