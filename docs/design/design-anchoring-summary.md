# CLDFlow 设计锚定摘要

> 从调研文档中提取的设计相关信息，用于锚定设计稿方向。
> 来源：`docs/Research & Brainstorm/` 目录下的调研和头脑风暴文档。

## 核心概念（设计必须理解）

### CLDFlow 是什么

CLDFlow 是一个**方法论驱动的 Agent 系统**，用于分析复杂系统（宏观政策、社会问题）的因果结构。它不是聊天机器人，而是一个**结构化分析工具**——用户输入一个研究问题，系统输出因果图、权重分析和杠杆点建议。

### 三层递进结构

CLDFlow 的核心是三层递进的分析流水线，每一层产出不同的可视化内容：

| 层 | 名称 | 做什么 | 用户看到什么 |
|----|------|--------|-------------|
| **CLD** | 因果回路图 | 从文献中提取变量和因果关系 | 节点 + 有向边的图（正/负极性） |
| **FCM** | 模糊认知图 | 给因果关系加权重（-1 到 +1） | 带权重的因果图 + 稳态仿真结果 |
| **D2D** | 图到动力学 | 敏感性分析，找杠杆点 | 杠杆点排序表 + 不确定性区间 |

**类比**：CLD = 地图，FCM = 加权重的地图，D2D = 可仿真的导航。

### Thinking 三步流程

用户提问后，系统内部执行三个步骤，设计上需要让用户感知到这个过程：

1. **检索**：从学术数据库（arXiv、Semantic Scholar、FRED 等）搜索相关文献
2. **建图**：3 个 Agent 并行从文献中提取因果关系，然后融合为一张共享 CLD
3. **评估**：对 CLD 进行权重赋值（FCM）、仿真推演、敏感性分析（D2D），输出杠杆点

**设计约束**：这三步必须在 UI 中清晰可区分，用户需要知道系统"正在做什么"以及"做到了哪一步"。

## 信息架构（页面需要承载的数据）

### 主页面区域与数据对应

| UI 区域 | 对应数据 | 数据特征 | 设计要点 |
|---------|---------|---------|---------|
| **Header** | 研究问题 + 系统状态 | 单行文本 + 状态标签 | 问题需要突出显示 |
| **消息区** | 对话历史 | 问答对列表 | 需支持长文 |
| **Thinking** | 三步流程的执行状态 | 3 个步骤 × 状态（进行中/完成/失败） | 步骤间有依赖关系，需要进度感 |
| **CLD 因果图** | 节点 + 有向边 | 图结构，节点数可达 50-100+ | 需要大面积展示区，支持缩放/拖拽 |
| **Source Cards** | 检索到的文献来源 | 卡片列表（标题、来源、可信度等级） | 需要可扫描，快速判断来源质量 |
| **Leverage Table** | D2D 杠杆点排序 | 表格（变量名、影响力、不确定性区间） | 需要可排序，数值需要单位/说明 |
| **输入区** | 用户输入 | 文本输入框 | 需要支持复杂问题描述 |

### 数据结构（来自架构设计）

```typescript
// 节点
Node {
  id: string          // UUID
  label: string       // 变量名（如"财政补贴力度"）
  description?: string
}

// 因果关系
CausalLink {
  source: Node
  target: Node
  polarity: '+' | '-'  // 正/负极性
  strength?: number     // FCM 权重 [-1, 1]，Phase 1 可选
}

// 共享 CLD
SharedCLD {
  nodes: Node[]
  links: CausalLink[]
  confidence?: number
}

// 杠杆点分析
LeverageAnalysis {
  variable: string
  impact: number        // 影响力得分
  uncertainty: [number, number]  // 不确定性区间
  rank: number
}
```

## 用户流程

```
用户输入研究问题
    ↓
系统显示 Thinking 第1步：检索（进度指示）
    ↓
Source Cards 逐步出现（文献来源）
    ↓
系统显示 Thinking 第2步：建图（进度指示）
    ↓
CLD 因果图出现（节点 + 边，可交互）
    ↓
系统显示 Thinking 第3步：评估（进度指示）
    ↓
Leverage Table 出现（杠杆点排序）
    ↓
用户可追问、调整、导出
```

**设计约束**：
- 流程是**渐进式**的，不是一次性展示所有内容
- 每一步的产出需要**独立可见**，用户可以只看 CLD 不看 Source
- 最终页面需要同时展示所有区域（不是分屏/分页）

## 设计约束（从领域特性推导）

### 空间约束

- **CLD 因果图需要大面积**：节点数可达 50-100+，边可能交叉，需要足够的画布空间和交互能力（缩放、拖拽、聚焦）
- **Thinking 需要紧凑**：三步状态是辅助信息，不应占据过多空间，但必须一眼可见
- **Leverage Table 需要可排序**：数值型数据，用户需要按影响力/不确定性排序

### 信息密度

- **Source Cards 需要可扫描**：用户需要快速判断"这个来源靠不靠谱"，所以可信度等级（T1/T2/T3）需要视觉突出
- **长文分析结果需要易读**：系统可能输出很长的分析文本，需要合理的排版和分段

### 色彩语义

- **正/负极性**：CLD 的因果关系有正（+）和负（-）两种极性，需要用颜色区分（如蓝/红或绿/红）
- **状态指示**：Thinking 三步需要状态色（进行中/完成/失败）
- **可信度分级**：Source Cards 的 T1/T2/T3 需要视觉层级

### 技术栈约束

- Next.js 16 + React 19 + Tailwind CSS v4 + shadcn
- 色彩系统使用 oklch（感知均匀色彩空间）
- 组件库基于 shadcn，设计稿需要与 shadcn 的组件风格兼容

## 反模式（必须避免）

来自调研中反复强调的设计原则：

- **不要做成聊天机器人**：CLDFlow 是结构化分析工具，不是对话助手。消息区只是输入/输出的载体，核心价值在 CLD/FCM/D2D 的可视化
- **不要隐藏分析过程**：Thinking 三步是用户信任系统的关键，必须透明可见
- **不要把因果图做小**：CLD 是核心输出，需要最大视觉权重
- **不要忽略数据可信度**：Source Cards 的来源分级直接影响用户对结果的信任

## 设计稿同步记录

### Report Page 定稿

- 计划文档：`docs/design/report page/report-page-finalization-plan.md`
- 设计规范：`docs/design/report page/report-page-spec.md`
- Figma 文件：https://www.figma.com/design/NnaxrhyA2t5iSt8EszbX7y/report-page-final-v1
- 位置：CLDFlow 团队（team::1638940025494981125）
- 状态：**已完成**，Day/Night 双主题完整

### Index Page 设计计划

- 计划文档：`docs/design/index page/figma-design-generation-plan-v10.md`
- Figma 文件：https://www.figma.com/design/9yJ1fQ8i68IsmQLcRGg00s（帧 ID: 13:2）
- 位置：CLDFlow 团队（team::1638940025494981125）
- 核心模块：Hero 区域、核心能力展示（CLD/FCM/D2D）、使用流程、导航入口
- 组件映射：Index Hero / Feature Cards / Process Steps
- 状态：**已完成**，深色主题，与 report page 统一视觉风格

### Runtime Page 设计稿

- 计划文档：`docs/design/runtime page/runtime-page-design-plan.md`
- Figma 文件：https://www.figma.com/design/GbbKF1sXeK1VDuClrOfrT1
- 位置：CLDFlow 团队（team::1638940025494981125）
- 状态：**已完成**，桌面端（1440×900）+ 移动端（375×812），Day/Night 双主题
- 设计 Token：`docs/design/runtime page/design-tokens.json`
- 组件映射：`docs/design/runtime page/component-mapping.md`
- 布局方案：双栏工作台（消息流 ~60% + CLD 画布 ~40%），与 Report Page 一致

### 当前 Figma 设计稿

- 文件：`figma-design-generation-plan-v21`
- 版本：V21
- URL：https://www.figma.com/design/9yJ1fQ8i68IsmQLcRGg00s
- 位置：CLDFlow 团队（team::1638940025494981125）
- 状态：已创建，三页完整（Runtime / Index / Report）

### 实际 Token 值（定稿 v1）

> 说明：完整的 oklch 语义 token 已定义在 `docs/design/report page/design-tokens.json`。
> 以下为关键 token 摘要。Day/Night 双套，通过 `data-theme` 属性切换。

| Token 角色 | Night (oklch) | Day (oklch) |
|------------|--------------|-------------|
| 页面背景 | `oklch(0.10 0.01 250)` | `oklch(0.97 0.005 80)` |
| 主卡片背景 | `oklch(0.12 0.015 250)` | `oklch(0.94 0.005 80)` |
| 次级卡片背景 | `oklch(0.15 0.015 250)` | `oklch(0.90 0.005 80)` |
| 主标题文字 | `oklch(0.93 0.01 250)` | `oklch(0.15 0.01 250)` |
| 次级说明文字 | `oklch(0.65 0.02 250)` | `oklch(0.42 0.01 250)` |
| 正向状态 | `oklch(0.65 0.18 155)` | `oklch(0.50 0.16 155)` |
| 主操作蓝 | `oklch(0.65 0.18 250)` | `oklch(0.55 0.20 250)` |

### 组件清单与代码映射

> 详细映射见 `docs/design/report page/component-mapping.md`

| 设计组件 | 代码路径 | 状态 | 页面 |
|----------|----------|------|------|
| Header | `web/src/components/cldflow/header.tsx` | 待创建 | Report/Runtime |
| Thinking Bar | `web/src/components/cldflow/thinking-bar.tsx` | 待创建 | Report/Runtime |
| Source Cards | `web/src/components/cldflow/source-cards.tsx` | 待创建 | Report |
| Source Card | `web/src/components/cldflow/source-card.tsx` | 待创建 | Report/Runtime |
| CLD Canvas | `web/src/components/cldflow/cld-canvas.tsx` | 待创建 | Report/Runtime |
| Leverage Table | `web/src/components/cldflow/leverage-table.tsx` | 待创建 | Report/Runtime |
| Input Bar | `web/src/components/cldflow/input-bar.tsx` | 待创建 | Report/Runtime |
| Theme Toggle | `web/src/components/cldflow/theme-toggle.tsx` | 待创建 | Report/Runtime |
| Tier Badge | `web/src/components/cldflow/tier-badge.tsx` | 待创建 | Report/Runtime |
| Message Area | `web/src/components/cldflow/message-area.tsx` | 待创建 | Runtime |
| User Message | `web/src/components/cldflow/user-message.tsx` | 待创建 | Runtime |
| Thinking Inline | `web/src/components/cldflow/thinking-inline.tsx` | 待创建 | Runtime |
| Source Citations | `web/src/components/cldflow/source-citations.tsx` | 待创建 | Runtime |
| History Drawer | `web/src/components/cldflow/history-drawer.tsx` | 待创建 | Runtime |
| Empty State | `web/src/components/cldflow/empty-state.tsx` | 待创建 | Runtime |
| Loading State | `web/src/components/cldflow/loading-state.tsx` | 待创建 | Runtime |
| Error State | `web/src/components/cldflow/error-state.tsx` | 待创建 | Runtime |
| Index Hero | `web/src/components/cldflow/index-hero.tsx` | 待创建 | Index |
| Feature Cards | `web/src/components/cldflow/feature-cards.tsx` | 待创建 | Index |
| Process Steps | `web/src/components/cldflow/process-steps.tsx` | 待创建 | Index |

## 参考来源

| 文档 | 提取内容 |
|------|---------|
| `issue-15-CLDFlow架构设计与实现-v2.md` | 三层递进结构、决策清单、数据结构 |
| `issue-15-CLDFlow架构设计与实现.md` | 五层运行架构、学科谱系、关键洞察 |
| `论文阅读路线图.md` | 技术基础验证、核心输出能力 |
| `LLM-CLD-阅读记录.md` | 两阶段方法、架构约束 vs prompt 工程 |
| `FCMpy-阅读记录.md` | FCM 数学定义、多专家融合、权重语义 |
