# CLDFlow 设计阶段一 — Figma-only 工作流

> **生效日期**：2026-05-20  
> **MCP 账号**：`noneplus@outlook.com`（2026-05-20 确认）  
> **七版候选**：已确认（Vercel / Linear / Claude / Cursor / Notion / Stripe / Figma DS）  
> **P1**：已授权 Agent 在权限就绪后落 Canonical 无 Tab 主屏  
> **MCP 报错**：Agent 须附 cURL 自测命令 → 见 `figma-mcp-rate-limits-and-curl-demo.md` §8  
> **真源文件（阶段一）**：[CLDFlow — Design Phase 1](https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k)（CLDFlow 团队）
> **MCP 账号**：`noneplus@outlook.com`（Owner，CLDFlow 团队）
> **初版参考**：[CLDFlow V2 Design Mockup](https://www.figma.com/design/6ajDseXpLEBRGu12Ta4BRM/CLDFlow-V2-Design-Mockup?node-id=0-1)  
> **阶段范围**：仅设计稿；`web/` 代码实现冻结至阶段二。

## 流程收敛（对用户决策的落地）

| 旧流程 | 新流程 |
|--------|--------|
| `design-mockup-v2.html` → capture → Figma | **弃用** HTML capture |
| 设计校验对照 HTML 清单 | 对照 **Figma 节点** + 截图 |
| 文档写「已选 Vercel」 | Vercel 仅为 **7 版候选 #1**，待选型 |

## Figma 文件结构（3 页上限）

因 Figma Starter 计划仅 **3 个 Page**，结构压缩为：

| Page | 内容 |
|------|------|
| `01 — Canonical (Vercel)` | 初版完整 Agent 问答屏（无 Chat/Research/CLDFlow Tab） |
| `02 — Style Explorations (7×)` | 7 套 Awesome Design MD 风格并排对比 |
| `03 — Thinking & Workflow` | Perplexity 式 Thinking 规格 + 布局范式说明 |

## 布局范式（已锚定）

- **单一 Agent 入口**：不出现 Chat / Research / CLDFlow 模式 Tab
- **Header**：Logo + 设置（+ 可选主题切换），56px
- **扁平消息流**：用户右对齐灰底；助手左对齐无气泡
- **Thinking**：分步可观测（检索 → 建图 → 评估），见 `docs/design/thinking-observability-spec.md`
- **来源卡 / Leverage 表**：阶段一细节后置

## Awesome Design MD 七版候选

| # | DESIGN.md | 主色 | 画布 |
|---|-----------|------|------|
| 1 | `vercel` | `#0070f3` | `#ffffff` |
| 2 | `linear.app` | `#5e6ad2` | `#010102`（暗色） |
| 3 | `claude` | `#cc785c` | `#faf9f5` |
| 4 | `cursor` | `#f54e00` | `#f7f7f4` |
| 5 | `notion` | `#5645d4` | `#ffffff` |
| 6 | `stripe` | `#533afd` | `#ffffff` |
| 7 | `figma` | `#000000` | `#ffffff` |

选型维度：可读性、专业可信度、与因果分析 Agent 气质、暗色表现、与 Next.js/shadcn 实现成本。

## 阶段二（未开始）

- 将选定风格写入 `web/src/app/globals.css`
- 移除 `header-bar` 三 Tab 与 `page.tsx` 多模式分支
- 按 Figma 节点实现 Thinking 组件
