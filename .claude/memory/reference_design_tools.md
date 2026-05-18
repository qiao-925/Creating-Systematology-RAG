---
name: reference-design-tools
description: 前端设计工具链参考 — Figma MCP、awesome-design-md、v0.app 的定位与用法
metadata: 
  node_type: memory
  type: reference
  originSessionId: 2fad5c49-1381-4332-b529-655eb4b29afb
---

## Figma MCP（已配置）

- MCP server：`plugin:figma:figma` → `https://mcp.figma.com/mcp`
- 认证账号：hashassemble@gmail.com（Full seat, starter tier）
- 主要工具：`create_new_file`、`generate_figma_design`（capture 模式）、`use_figma`、`get_design_context`
- 捕捉流程：HTML → 本地服务器 → capture.js 脚本 → 写入 Figma
- 限制：starter 计划每月 6 次工具调用（写入操作豁免）

## awesome-design-md

- 仓库：https://github.com/voltagent/awesome-design-md
- 路径：`design-md/{brand}/DESIGN.md`（不是 `designs/`）
- 格式：YAML frontmatter + Markdown 章节（色彩、字体、组件、布局、阴影、Do's/Don'ts）
- 用法：复制 DESIGN.md 到项目根目录，AI Agent 参照它生成 UI

## v0.app

- 地址：https://v0.app
- 定位：浏览器端 AI UI 生成工具，生成 shadcn/ui + Tailwind 组件
- 无公开 API，纯交互式使用
- 适合快速原型，但产出不可持久化（对比 Figma 文件）
