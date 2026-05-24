# 组件→代码映射表

> 来源：design-anchoring-summary.md 组件清单 + Figma 设计稿 v10 实际结构
> 生成时间：2026-05-24

## 核心组件（设计稿 v10 已覆盖）

| 组件 | 设计稿节点 | 代码路径 | 状态 | 说明 |
|------|-----------|---------|------|------|
| Header | Header background + Logo + Product name + Query title | `web/src/components/cldflow/header.tsx` | 待创建 | 含 Logo、查询标题、元数据行、状态 pill、导出按钮 |
| Thinking Pipeline | Thinking Pipeline + 3× Step card | `web/src/components/cldflow/thinking-pipeline.tsx` | 待创建 | 3 步骤卡片，含编号标记、状态、详情 |
| CLD Canvas | Graph canvas inner + 8× CLD node + edges + legend | `web/src/components/cldflow/cld-canvas.tsx` | 待创建 | 因果图画布，含节点、边、循环标记、图例 |
| Leverage Ranking | Leverage Ranking + 5× Rank row + uncertainty bars | `web/src/components/cldflow/leverage-ranking.tsx` | 待创建 | 杠杆排序表，含影响力值、不确定性区间、置信度徽章 |
| Source Cards | Sources + 3× Source card + Tier badge | `web/src/components/cldflow/source-cards.tsx` | 待创建 | 来源卡片列表，含 T1/T2/T3 可信度徽章 |
| Input Bar | Input panel + prompt + chips + send button | `web/src/components/cldflow/input-bar.tsx` | 待创建 | 输入区，含提示文本、建议 chips、发送按钮 |
| Narrative Analysis | Analysis heading + Narrative card + Confidence pill | `web/src/components/cldflow/narrative-card.tsx` | 待创建 | 长文分析摘要卡片 + 可信度 pill |

## 子组件

| 组件 | 设计稿节点 | 代码路径 | 状态 | 说明 |
|------|-----------|---------|------|------|
| Step Card | Step card + Step marker + Step num/title/status/detail | `web/src/components/cldflow/step-card.tsx` | 待创建 | Thinking Pipeline 的单个步骤卡片 |
| Source Card | Source card + Tier badge + title + meta | `web/src/components/cldflow/source-card.tsx` | 待创建 | 单个来源卡片 |
| Tier Badge | Tier badge (T1/T2/T3) | `web/src/components/cldflow/tier-badge.tsx` | 待创建 | 可信度等级徽章 |
| Rank Row | Rank row + rank num + variable + impact + uncertainty bar | `web/src/components/cldflow/rank-row.tsx` | 待创建 | 杠杆排序单行 |
| Confidence Badge | Confidence badge (高/中/低) | `web/src/components/cldflow/confidence-badge.tsx` | 待创建 | 置信度等级徽章 |
| CLD Node | CLD node + label | `web/src/components/cldflow/cld-node.tsx` | 待创建 | 因果图单个节点 |
| Edge Label | Edge label (+/-) | `web/src/components/cldflow/edge-label.tsx` | 待创建 | 边极性标签 |
| Loop Badge | Loop badge (R1/B1) | `web/src/components/cldflow/loop-badge.tsx` | 待创建 | 循环类型标记 |
| Suggestion Chip | Chip + text | `web/src/components/cldflow/suggestion-chip.tsx` | 待创建 | 输入区建议 chips |

## 状态/工具组件

| 组件 | 代码路径 | 状态 | 说明 |
|------|---------|------|------|
| Theme Toggle | `web/src/components/cldflow/theme-toggle.tsx` | 待创建 | 深色/浅色主题切换 |
| Empty State | `web/src/components/cldflow/empty-state.tsx` | 待创建 | 空状态页面 |
| Loading State | `web/src/components/cldflow/loading-state.tsx` | 待创建 | 加载状态 |
| Error State | `web/src/components/cldflow/error-state.tsx` | 待创建 | 错误状态 |

## 已有组件（可复用/参考）

| 组件 | 路径 | 复用价值 |
|------|------|---------|
| cldflow-panel | `web/src/components/cldflow/cldflow-panel.tsx` | 整合容器，可重构为新布局 |
| thinking-block | `web/src/components/chat/thinking-block.tsx` | Thinking 状态逻辑参考 |
| sources-panel | `web/src/components/chat/sources-panel.tsx` | Source Cards 数据结构参考 |
| chat-input | `web/src/components/chat/chat-input.tsx` | Input Bar 交互逻辑参考 |

## 映射规则

1. 所有新组件放入 `web/src/components/cldflow/`
2. 子组件由父组件导入，不单独暴露
3. 状态组件作为 fallback 使用
4. 路径必须实际存在或标注"待创建"
