# 七版设计风格对比矩阵（Awesome Design MD）

> 用于 Figma `02 — Style Explorations` 手工或 MCP 恢复后继续绘制。  
> 骨架统一：Canonical 布局（无 Tab、扁平消息、Thinking 三步）。

## 对比维度

| 维度 | 说明 |
|------|------|
| 气质 | 与「因果分析 / 研究 Agent」匹配度 |
| 可读性 | 长文、表格、暗色 |
| 实现成本 | 与 Next.js + shadcn + Geist 距离 |
| 可观测性 | Thinking 步骤是否易区分 |

## Token 一览

| 风格 | 主色 accent | 画布 canvas | 墨 ink | 链接 link | 软底 soft | 分割线 hairline |
|------|-------------|-------------|--------|-----------|-----------|-----------------|
| **Vercel** | `#0070f3` | `#ffffff` | `#171717` | `#0070f3` | `#f5f5f5` | `#ebebeb` |
| **Linear** | `#5e6ad2` | `#010102` | `#f7f8f8` | `#5e6ad2` | `#0f1011` | `#23252a` |
| **Claude** | `#cc785c` | `#faf9f5` | `#141413` | `#cc785c` | `#efe9de` | `#e6dfd8` |
| **Cursor** | `#f54e00` | `#f7f7f4` | `#26251e` | `#f54e00` | `#fafaf7` | `#e6e5e0` |
| **Notion** | `#5645d4` | `#ffffff` | `#1a1a1a` | `#0075de` | `#f6f5f4` | `#e5e3df` |
| **Stripe** | `#533afd` | `#ffffff` | `#0d253d` | `#533afd` | `#f6f9fc` | `#e3e8ee` |
| **Figma DS** | `#000000` | `#ffffff` | `#000000` | `#000000` | `#f7f7f5` | `#e6e6e6` |

### Cursor 专用：Thinking 步骤色（可选）

| 步骤 | 背景 token | 用途 |
|------|------------|------|
| 检索 | `#dfa88f` | timeline-thinking |
| 建图 | `#9fbbe0` | timeline-read |
| 评估 | `#c0a8dd` | timeline-edit |

## 各风格一句话定位

1. **Vercel** — 极简工程感，与现有 Geist 栈一致；当前 Canonical 基线。
2. **Linear** — 暗色专业工具；适合高密度数据，但全站暗色成本高。
3. **Claude** — 暖色编辑感；人文、长文友好，主色珊瑚偏「对话」。
4. **Cursor** — 奶油底 + 橙 CTA；自带 AI 时间线 pastel，与 Thinking 最契合。
5. **Notion** — 紫 CTA + 多彩卡片；偏通用办公，略分散注意力。
6. **Stripe** — 靛蓝金融可信；适合杠杆表，偏支付/数据产品气质。
7. **Figma DS** — 黑白编辑 + 大块 pastel；活泼但可能削弱「研究严肃感」。

## 推荐评审顺序

1. 先看 **Vercel / Cursor / Linear**（Agent 工具谱系）
2. 再看 **Claude / Stripe**（长文与表格）
3. 最后 **Notion / Figma DS**（是否过于「生产力通用」）

## Figma 落版建议（Page 02）

- 帧宽 986px（与 Canonical 同宽），横向间距 120px
- 每帧顶部 24px 标签：`Style: {name}` + 主色色条
- 仅替换：Header 底、logo 块、Thinking 边框/完成色、用户消息底、链接/引用色
- 正文与 CLD/Leverage 区块阶段一可保持灰度线框

## 七版名单（已确认 2026-05-20）

Vercel · Linear · Claude · Cursor · Notion · Stripe · Figma DS — 与用户拍板一致，见 `figma-phase1-workflow.md`。

## Figma 落版状态（2026-05-21 更新）

Page 02 已创建 7 帧（完整骨架版，480×600px），2 列布局：
- Row 1: Vercel (32:2) + Linear (27:47)
- Row 2: Claude (28:2) + Cursor (28:47)
- Row 3: Notion (29:2) + Stripe (29:47)
- Row 4: Figma (30:2)

每帧包含：Header + 用户消息 + Thinking 三步 + 助手摘要 + CLD 图 + 输入区
各帧设计 token 已按对应 DESIGN.md 完整应用（色彩、字体、阴影、按钮风格）

文件：https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k

## 选型记录（待填）

| 字段 | 值 |
|------|-----|
| 七版候选 | 已确认（2026-05-20） |
| 选定风格 | _待评审_ |
| 选定日期 | |
| 评审人 | |
| 备注 | P1 Canonical + P2 七版已完成，待用户选型 |
