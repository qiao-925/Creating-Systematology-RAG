# Figma 设计稿生成计划 V21

## 版本目标

- 做什么：基于 V20 已验证的 report page 设计稿，延伸生成 runtime page 和 index page，形成 CLDFlow 完整三页主稿
- 为什么：report page 已有高质量参考稿（v10/v11/v13），但 runtime page（Agent 问答交互）和 index page（项目门户）尚未设计，三页合一才能覆盖完整用户旅程
- 交付物：Figma 文件，保存至 CLDFlow（team::1638940025494981125），文件名 `figma-design-generation-plan-v21`
- 参考基础：V20 计划 + 已有 v10/v11/v13 Figma 设计稿

## 三页定义

| 页面 | 定位 | 设计风格参考 | 核心内容 |
|------|------|-------------|---------|
| **Index Page** | 项目门户/启动入口 | Vercel 官网、Linear 首页 | 项目简介、核心功能说明、启动入口 CTA、技术栈标签 |
| **Runtime Page** | Agent 问答交互主界面 | DeepSeek、Manus、ChatGPT | 消息流、Thinking 状态、CLD 内联渲染、输入区 |
| **Report Page** | 分析结果展示 | 已有 v10/v11/v13 设计稿 | CLD 因果图、Source Cards、Leverage Table、导出 |

## 执行规则

> 同 V20 执行规则，优先级高于任务清单。

### 硬性约束

1. **逐任务执行** — 按任务顺序依次执行
2. **强制自检** — 每个任务完成后对照验收标准自检
3. **全量完成** — 执行所有任务后再输出最终结果
4. **失败升级** — 记录原因并继续后续任务
5. **反模式红线** — 不得出现附录 A 中的任何一项
6. **设计稿文件名** — 必须与计划版本一致（`figma-design-generation-plan-v21`）
7. **不使用旧文件** — 不使用 GetdOs1IPlJcW5mdrKhVH3，直接创建新设计稿

### 禁止行为

- 跳过自检直接进入下一个任务
- 遇到不确定时自行跳过而非记录
- 忽略反模式清单
- 未完成所有任务就停止

## 文档锚定

| 锚定文档 | 关系 |
|----------|------|
| [V20 计划](docs/design/figma-design-generation-plan-v20.md) | 基础——执行规则、反模式清单、评估框架复用 |
| `docs/design/design-anchoring-summary.md` | 必读——核心概念、信息架构、组件清单 |
| [v10 设计稿](https://www.figma.com/design/9cfzfIzNqO0SwU4LJvztv1/figma-design-generation-plan-v10) | 参考——report page 基础 |
| [v11 设计稿](https://www.figma.com/design/2feKEdDOTNZI4DiA6L8iQx/Figma-设计稿生成计划-V11) | 参考——report page 迭代 |
| [v13 设计稿](https://www.figma.com/design/EzOFBPnk35ANqcFXuuTOba/Figma-设计稿生成计划-V13-cursor-gpt5.5) | 参考——report page 最新 |

### 同步更新清单

- [ ] 生成完成后更新 `design-anchoring-summary.md` 的组件清单（新增 runtime/index 相关组件）

## 决策清单

### 核心决策

| # | 决策 | 选项 | 状态 | 理由 |
|---|------|------|------|------|
| D1 | Runtime 设计风格 | A) DeepSeek 极简问答 B) Manus 工具调用可视化 C) 融合 | **待闭合** | 需要结合 CLDFlow 的 Thinking 三步特色 |
| D2 | Index Page 定位 | A) 纯信息展示 B) 交互式引导 C) 带 demo 预览 | **待闭合** | 门户页需要降低使用门槛 |
| 3 | Report Page 复用策略 | A) 直接复用 v13 B) 基于 v13 增量优化 C) 重新设计 | **建议 B** | v13 质量已较高，增量优化更可控 |

### 支撑决策

| # | 决策 | 选项 | 状态 | 理由 |
|---|------|------|------|------|
| D4 | 设计一致性 | 三页共用 design tokens | **已闭合** | Vercel 设计语言统一 |

## 任务清单

### Phase 0：素材准备与分析

- [ ] T0.1 通读 V20 计划与锚定文档
  - 产出：确认理解三层递进结构、信息架构、反模式清单
  - 验收：能复述 Thinking 三步流程、CLD 数据结构
  - 失败路径：分段通读

- [ ] T0.2 分析已有 Figma 设计稿
  - 产出：v10/v11/v13 的 report page 结构分析，提取可复用元素
  - 验收：列出可复用组件清单（CLD 画布、Source Cards、Leverage Table 等）
  - 失败路径：基于截图分析
  - 参考：v10/v11/v13 Figma 文件链接

- [ ] T0.3 调研 Runtime Page 参考
  - 产出：DeepSeek、Manus、ChatGPT 的 UI 模式分析
  - 验收：总结 3 个关键设计特征，提炼适用于 CLDFlow 的模式
  - 失败路径：基于已有知识分析
  - 参考：DeepSeek、Manus 官网

### Phase 1：Runtime Page 设计

**目标**：生成 Agent 问答交互界面，融合 CLDFlow Thinking 三步特色。

- [ ] T1.1 Runtime Page 布局设计
  - 产出：页面布局结构（消息流 + Thinking 面板 + CLD 内联区 + 输入区）
  - 验收：布局支持长对话滚动、Thinking 状态可视化、CLD 图内联展示
  - 失败路径：先做线性布局，后续迭代优化
  - 硬性约束：不得使用对话气泡（反模式），采用扁平消息流

- [ ] T1.2 Runtime Page 组件细化
  - 产出：消息组件、Thinking 步骤指示器、CLD 内联渲染、Source 引用行内标注
  - 验收：每个组件有明确的视觉状态（默认/进行中/完成/失败）
  - 失败路径：先实现核心组件（消息 + Thinking + 输入），其余后续补充
  - 硬性约束：Thinking 三步必须清晰可区分

- [ ] T1.3 Runtime Page 自检
  - 产出：对照验收标准自评
  - 验收：支持完整问答流程可视化、Thinking 状态清晰、CLD 可交互
  - 失败路径：记录未通过项，标注原因

### Phase 2：Index Page 设计

**目标**：生成项目门户页面，提供启动入口和项目介绍。

- [ ] T2.1 Index Page 内容规划
  - 产出：页面内容结构（Hero + 功能说明 + 技术栈 + CTA）
  - 验收：内容覆盖项目核心价值、使用方式、技术栈
  - 失败路径：先做最简结构（Hero + CTA），后续迭代
  - 硬性约束：不得使用 hero section 式首屏堆砌（反模式），保持简洁

- [ ] T2.2 Index Page 视觉设计
  - 产出：Vercel 风格极简门户页，近白底 + 墨黑主色
  - 验收：视觉风格与 runtime/report 页面一致
  - 失败路径：复用 Vercel DESIGN.md 的组件模式
  - 硬性约束：使用 oklch 色彩系统

- [ ] T2.3 Index Page 自检
  - 产出：对照验收标准自评
  - 验收：项目价值传达清晰、CTA 明确、视觉一致
  - 失败路径：记录未通过项

### Phase 3：Report Page 优化

**目标**：基于已有 v13 设计稿进行增量优化。

- [ ] T3.1 Report Page 增量优化
  - 产出：基于 v13 优化 CLD 画布交互、Source Cards 可信度标识、Leverage Table 排序
  - 验收：7 个区域全部完善，与 V20 T1.2 验收标准对齐
  - 失败路径：优先保证核心 5 区域（Header/Thinking/CLD/Source/Leverage）
  - 硬性约束：保留 v13 已有布局结构

- [ ] T3.2 Report Page 自检
  - 产出：对照附录 B 五项检查
  - 验收：Thinking 三步清晰、CLD 区域充足、Source 可扫描、Leverage 可排序、长文易读
  - 失败路径：记录未通过项

### Phase 4：整体定稿

- [ ] T4.1 三页一致性检查
  - 产出：三页 design tokens 一致性验证
  - 验收：色彩、字体、间距、组件风格统一
  - 失败路径：统一调整不一致项

- [ ] T4.2 最终交付
  - 产出：Figma 文件存档至 CLDFlow team
  - 验收：文件可正常打开编辑，三页完整
  - 失败路径：截图存档作为降级方案

## 执行日志

- [x] 05-23 计划创建（V21）
- [ ] Phase 0：素材准备与分析
- [ ] Phase 1：Runtime Page 设计
- [ ] Phase 2：Index Page 设计
- [ ] Phase 3：Report Page 优化
- [ ] Phase 4：整体定稿

---

## 附录 A：反模式底线（复用 V20）

- 紫色渐变 + 白卡片 + 大圆角
- 无差别阴影堆叠
- 只换 accent 色不改布局
- hero section 式首屏堆砌
- 过度装饰的插画/噪点纹理
- 所有内容做成对话气泡
- 只有粗骨架没有实现细节

## 附录 B：CLDFlow 专属检查项（复用 V20）

- [ ] Thinking 三步（检索/建图/评估）是否清晰可区分？
- [ ] CLD 因果图区域是否有足够空间？
- [ ] Source Cards 是否可扫描？
- [ ] Leverage Table 是否可排序？
- [ ] 长文分析结果是否易读？

## 附录 C：Runtime Page 参考分析

### DeepSeek 设计特征
- 极简白底，消息流无气泡
- Thinking 过程可见（展开/折叠）
- 代码块高亮内联
- 输入区底部固定

### Manus 设计特征
- 工具调用过程可视化（步骤卡片）
- 左侧对话流 + 右侧工具执行面板
- 文件/图片结果内联展示
- 多模态输入支持

### CLDFlow Runtime 融合方向
- 扁平消息流（非气泡）+ Thinking 三步可视化
- CLD 图/FCM 结果内联渲染在消息流中
- 行内引用 [1][2] + 底部 Source Cards
- 输入区底部固定，支持复杂问题描述

## 附录 D：已有设计稿资源

| 版本 | Figma 链接 | 已有内容 | 复用策略 |
|------|-----------|---------|---------|
| v10 | [链接](https://www.figma.com/design/9cfzfIzNqO0SwU4LJvztv1/figma-design-generation-plan-v10) | Report page 基础版 | 提取 CLD/Source/Leverage 组件 |
| v11 | [链接](https://www.figma.com/design/2feKEdDOTNZI4DiA6L8iQx/Figma-设计稿生成计划-V11) | Report page 迭代 | 提取优化后的组件 |
| v13 | [链接](https://www.figma.com/design/EzOFBPnk35ANqcFXuuTOba/Figma-设计稿生成计划-V13-cursor-gpt5.5) | Report page 最新 | 作为 Report page 基线 |
