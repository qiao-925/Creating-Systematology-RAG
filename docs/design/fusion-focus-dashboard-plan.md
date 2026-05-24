# CLDFlow 三屏设计方案

> 入口页 → 运行时分析视图 → 静态仪表盘视图
> 生成时间：2026-05-24

## 页面架构

```
Entry (入口页)
  │  输入研究问题
  │  或选择示例问题
  ▼
Focus (运行时分析视图)
  │  对话 + CLD 图实时构建
  │  ViewToggle ──切换──▶
  ▼
Dashboard (静态仪表盘视图)
    三栏全览 · 导出 · 分享
```

## 入口页 (Entry)

- 极简布局：Logo + 大号问题输入框 + 4 个推荐问题
- 底部「上次分析」快捷入口，点击直接跳转到 Dashboard 视图
- 设计稿见 Figma frame: `V10-Fusion | Entry (入口页)`

## 核心判断

两个视图共享同一份数据（CLD 图、来源、杠杆排序、叙事分析），差异纯粹在布局和信息密度。融合的关键是让用户在两种布局之间无缝切换。

## 切换机制

Header 或 CLD 工具栏中的 `ViewToggle`：

```
[ ◉ 分析 ] [ ○ 总览 ]
```

- **分析（Focus）**：运行时默认视图，2 栏布局，对话驱动，CLD 图占 55%
- **总览（Dashboard）**：静态结果视图，3 栏布局，所有信息一屏可见

切换时不重新请求数据，只改变组件布局。

## 组件映射

两个视图使用相同的底层组件，排列方式不同：

| 功能模块 | 分析视图 (Focus) | 总览视图 (Dashboard) | 共享组件 |
|---------|-----------------|---------------------|---------|
| 对话/思考 | 左侧滚动对话流 | 左侧 Thinking Pipeline 卡片 | `ThinkingBlock` |
| CLD 图 | 右侧 55% 大画布 | 中央 50% 画布 | `CLDCanvas` |
| 来源 | 对话中的来源列表 | 左侧来源卡片 | `SourceCards` |
| 杠杆排序 | 对话中的内联表格 | 右侧杠杆排序表 | `LeverageRanking` |
| 叙事分析 | 对话中的分析文本 | 右侧叙事卡片 | `NarrativeCard` |
| 输入 | 底部输入栏 | 底部输入栏 | `ChatInput` |

## 融合架构

```
CLDFlowShell                         ← 顶层容器，管理 viewMode 状态
├── HeaderBar                        ← 已有，增加 ViewToggle
│   └── ViewToggle (分析 | 总览)
├── FocusView (viewMode === 'focus')           ← 2 栏运行时
│   ├── ConversationPanel (45%)
│   │   ├── MessageList
│   │   ├── ThinkingBlock
│   │   ├── SourceCards (inline)
│   │   └── LeverageRanking (inline)
│   └── CLDCanvas (55%)
│       ├── Toolbar
│       └── Graph
├── DashboardView (viewMode === 'dashboard')   ← 3 栏总览
│   ├── LeftRail (312px)
│   │   ├── ThinkingPipeline
│   │   └── SourceCards (stacked)
│   ├── CenterCanvas (flex)
│   │   ├── CLDCanvas
│   │   └── FCMWeighting / SelfCheck (optional)
│   └── RightRail (312px)
│       ├── LeverageRanking
│       └── NarrativeCard
└── InputBar                                    ← 共享底部输入
```

## 组件清单

### 已有但需重构
- `CLDGraph` → 提取为独立 `CLDCanvas.tsx`
- `LeverageRanking` → 提取为 `leverage-ranking.tsx`，增加不确定性区间条

### 需要新建
- `SourceCards` — 带 T1/T2/T3 可信度徽章
- `ThinkingPipeline` — 三步骤卡片（检索→建图→评估）
- `NarrativeCard` — 长文分析摘要 + 置信度 pill
- `ViewToggle` — 分析/总览模式切换
- `CLDFlowShell` — 顶层布局容器

### 需要修改
- `page.tsx`：cldflow 模式渲染 CLDFlowShell
- `chat-store.ts`：增加 CLDFlow 分析结果状态

## 状态管理

CLDFlow 分析结果从 local state 提升到 chat-store：

```typescript
cldflowResult: CLDFlowResponse | null;
cldflowLoading: boolean;
cldflowError: string | null;
```

## 实现路径

| 阶段 | 任务 | 影响范围 |
|------|------|---------|
| P1 提取组件 | 提取 CLDCanvas、LeverageRanking | 纯重构 |
| P2 新建组件 | SourceCards、ThinkingPipeline、NarrativeCard、ViewToggle | 新增组件 |
| P3 创建布局 | FocusView、DashboardView、CLDFlowShell | 布局层面 |
| P4 状态提升 | CLDFlow 状态迁移到 chat-store | store + panel |
| P5 连线 | page.tsx + header-bar.tsx 接入 | 入口层 |
| P6 交互增强 | 动画、导出、响应式 | 渐进增强 |

## 关键决策

- 两个视图共享同一份数据，切换时不重新请求
- Dashboard 视图仅在分析结果返回后可用
- 两种视图均保留底部输入栏，Dashboard 中的追问切换回 Focus 时以新消息形式呈现
