# 组件-代码映射表

> 更新日期：2026-05-27（V2 架构重构后）

## 页面路由

| 路由 | 文件 | 说明 |
|------|------|------|
| `/` | `web/src/app/page.tsx` | Home 输入页（搜索框 + 建议卡片） |
| `/runtime` | `web/src/app/runtime/page.tsx` | Runtime 分析页入口（读取 searchParams.q） |

## Systematology 组件

| 组件 | 文件路径 | 用途 | Props |
|------|---------|------|-------|
| `RuntimePage` | `web/src/components/systematology/runtime-page.tsx` | Runtime 主页面（双栏 + API 集成） | `initialQuestion?: string` |
| `CLDCanvasSwitcher` | `web/src/components/systematology/cld-canvas-switcher.tsx` | CLD 画布三方案切换 | `data: CLDData` |
| `CLDCanvasSVG` | `web/src/components/systematology/cld-canvas-svg.tsx` | SVG 手写画布 | `data: CLDData` |
| `CLDCanvasReactFlow` | `web/src/components/systematology/cld-canvas-reactflow.tsx` | React Flow 画布 | `data: CLDData` |
| `CLDCanvasD3` | `web/src/components/systematology/cld-canvas-d3.tsx` | D3.js 力导向画布 | `data: CLDData` |
| `ThinkingPipeline` | `web/src/components/systematology/thinking-pipeline.tsx` | 分析步骤进度 | `steps?: Step[]` |
| `SourceCards` | `web/src/components/systematology/source-cards.tsx` | 来源文献卡片 | `sources?: Source[]` |
| `LeverageTable` | `web/src/components/systematology/leverage-table.tsx` | 杠杆点排序表 | `points?: LeveragePoint[]` |

## 数据适配层

| 函数 | 文件路径 | 用途 |
|------|---------|------|
| `adaptCLDData` | `web/src/components/systematology/cl-data-adapter.ts` | API nodes/edges → 画布 CLDData |
| `adaptLeveragePoints` | `web/src/components/systematology/cl-data-adapter.ts` | API leverage_ranking → LeverageTable props |

## 数据类型

| 类型 | 文件路径 | 用途 |
|------|---------|------|
| `CLDData` | `web/src/components/systematology/cld-canvas-types.ts` | 画布数据（含坐标 + 极性） |
| `SystematologyReport` | `web/src/types/index.ts` | 后端 API 成功响应 |
| `SystematologyNode` | `web/src/types/index.ts` | 后端 API 节点 |
| `SystematologyEdge` | `web/src/types/index.ts` | 后端 API 边 |

## 共享组件

| 组件 | 文件路径 | 用途 | Props |
|------|---------|------|-------|
| `HeaderBar` | `web/src/components/chat/header-bar.tsx` | 顶部导航栏 | `questionTitle?`, `status?`, `onNewConversation?`, `onBack?`, `onSettingsClick?` |
| `ChatInput` | `web/src/components/chat/chat-input.tsx` | 输入框 | `onSend`, `disabled?`, `placeholder?`, `variant?` |
| `SuggestionPills` | `web/src/components/chat/suggestion-pills.tsx` | 建议问题卡片 | `onSelect` |
| `SettingsSheet` | `web/src/components/settings/settings-sheet.tsx` | 设置面板 | `open`, `onOpenChange` |
| `ThemeToggle` | `web/src/components/theme-toggle.tsx` | 主题切换 | — |

## UI 组件（shadcn/ui）

| 组件 | 文件路径 |
|------|---------|
| `Button` | `web/src/components/ui/button.tsx` |
| `Input` | `web/src/components/ui/input.tsx` |
| `Badge` | `web/src/components/ui/badge.tsx` |
| `Dialog` | `web/src/components/ui/dialog.tsx` |
| `Sheet` | `web/src/components/ui/sheet.tsx` |
| `Tabs` | `web/src/components/ui/tabs.tsx` |
| `Select` | `web/src/components/ui/select.tsx` |
| `Switch` | `web/src/components/ui/switch.tsx` |
| `Slider` | `web/src/components/ui/slider.tsx` |
| `ScrollArea` | `web/src/components/ui/scroll-area.tsx` |
| `Separator` | `web/src/components/ui/separator.tsx` |
| `Collapsible` | `web/src/components/ui/collapsible.tsx` |
| `Label` | `web/src/components/ui/label.tsx` |

## 已弃用（未使用）

| 组件 | 文件路径 | 原因 |
|------|---------|------|
| `SystematologyPanel` | `web/src/components/systematology/systematology-panel.tsx` | V1 旧版面板，已被 RuntimePage 替代 |
| `MessageList` | `web/src/components/chat/message-list.tsx` | Chat 模式已移除 |
| `MessageBubble` | `web/src/components/chat/message-bubble.tsx` | Chat 模式已移除 |
| `ThinkingBlock` | `web/src/components/chat/thinking-block.tsx` | Chat 模式已移除 |
| `SourcesPanel` | `web/src/components/chat/sources-panel.tsx` | Chat 模式已移除 |
| `ResearchResult` | `web/src/components/chat/research-result.tsx` | Research 模式已移除 |
