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
- **认证账号（用户拍板）**：`noneplus@outlook.com`（handle: peter；noneplus's team，**View** seat，Education/student tier）
- 阶段一真源文件：`GetdOs1IPlJcW5mdrKhVH3` — https://www.figma.com/design/GetdOs1IPlJcW5mdrKhVH3
- 主要工具：`create_new_file`、`use_figma`、`get_design_context`（~~`generate_figma_design` HTML capture~~ 已弃用）
- **写入前置**：View 席位无法可靠 `use_figma` 写稿；需对真源文件授予 **Can edit**，或团队内升级为 Edit/Full seat
- 限制：读工具受 **每分钟 + 日/月额度** 约束；Education 计划易触达 MCP paywall；`whoami` 等部分工具豁免（见官方文档）
- 自测与重试：`docs/design/figma-mcp-rate-limits-and-curl-demo.md`（cURL + 5s 重试 + `scripts/figma_mcp_retry_demo.py`）

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
