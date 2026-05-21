# Figma 设计稿生成计划 V20

## 版本目标

- 做什么：收集并复用 Figma 中已生成的高质量 CLDFlow 设计稿，在新文件中进行增量生成，形成可直接指导前后端代码实现的完整主稿
- 为什么：基础版已有可用的布局骨架，且当前 Figma 文件中已出现多个质量较高的候选稿；增量生成比从零生成更可控，也能保留已验证的视觉判断
- 参考基础版：[Figma 设计稿](https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k/Untitled?node-id=0-1)
- 当前交付稿：[figma-design-generation-plan-v10](https://www.figma.com/design/9cfzfIzNqO0SwU4LJvztv1)
- 交付物：Figma 文件，保存至 CLDFlow（team::1638940025494981125），文件名与计划版本一致
- 增量原则：以基础版中的高质量节点为素材库，优先复用 `02 — Canonical Desktop (Vercel)` 的桌面结构，并吸收 `03 — Exploratory (Phase 1 Draft)` 的探索细节；只补强信息密度、可扫描性、CLD 画布、Source 可信度、D2D 表格与输入区，不推翻已有主结构

## 执行规则

> 本节定义 agent 执行计划时的行为约束，优先级高于任务清单中的任何描述。

### 硬性约束（违反则任务失败）

1. **逐任务执行** — 按任务顺序依次执行，每个任务完成后再进入下一个
2. **强制自检** — 每个任务完成后，对照验收标准逐项自检，未通过的项触发对应失败路径
3. **全量完成** — 执行所有任务后再输出最终结果，中间过程不需要报告
4. **失败升级** — 触发失败路径后仍无法解决的，记录原因并继续后续任务，最终汇总到交付物中
5. **反模式红线** — 生成的设计不得出现附录 A 中的任何一项

### 禁止行为

- 跳过自检直接进入下一个任务
- 遇到不确定时自行跳过而非记录
- 忽略反模式清单（附录 A）中的任何一项
- 未完成所有任务就停止

### 最终交付格式

全部任务完成后输出：

```
## 交付物

{Figma 文件路径或设计稿截图}

## 执行摘要

| 任务 | 状态 | 产出 | 备注 |
|------|------|------|------|
| T0.1 | 通过 | {产出描述} | — |
| T0.2 | 跳过 | — | 触发跳过路径：Plugin Marketplace 不可用 |
| T1.1 | 通过 | {产出描述} | — |
| ... | ... | ... | ... |

## 未通过项

{列出所有触发失败路径的任务，说明原因和采取的降级措施}
```

### 执行 prompt 模板

> 执行时填入 agent prompt。

```
读取 `docs/design/figma-design-generation-plan-v10.md`。

按任务清单顺序执行全部任务，完成后输出最终交付物。

硬性约束：
- 基于 Figma 基础版做延伸，不得从零生成
- 保留基础版的布局结构和视觉基调，只补全和完善
- 每个任务完成后对照验收标准自检，未通过则执行失败路径
- 全部完成后输出交付物 + 执行摘要 + 未通过项
- 反模式清单（附录 A）中所有项不得出现

参考资源：
- Figma 基础版：https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k/Untitled?node-id=0-1
- design-anchoring-summary.md（核心概念、信息架构、用户流程、组件清单、反模式清单）
- 附录 D（资源清单）
```

## 文档锚定

| 锚定文档 | 关系 |
|----------|------|
| [Figma 基础版](https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k/Untitled?node-id=0-1) | 必读——延伸起点，布局骨架和视觉基调的基础 |
| `docs/design/design-anchoring-summary.md` | 必读——核心概念、信息架构、用户流程、领域约束、组件清单、反模式清单 |
| `ARCHITECTURE.md` | 约束——技术栈（Next.js 16 + React 19 + Tailwind v4 + shadcn + oklch） |

### 同步更新清单

- [ ] 生成设计稿后更新 `design-anchoring-summary.md` 的 token 实际值和组件清单

## 决策清单

### 核心决策

| # | 决策 | 选项 | 状态 | 理由 |
|---|------|------|------|------|
| D1 | 设计生成方式 | A) 探索式生成 B) 锚定式生成（锁定单一 DESIGN.md） | **已闭合 A** | 素材充足 + 人类 taste 判断，避免风格单一 |
| D2 | 设计稿产出形式 | A) HTML/CSS 原型 B) Figma 文件 C) 两者 | **已闭合 B** | Figma 文件可直接对接开发协作，HTML 原型作为中间产物按需生成 |
| D3 | 风格方向 | 七版候选中自由探索 | **已闭合：开放探索** | 不预设方向，每轮由人类评审决定是否收敛 |

### 支撑决策

| # | 决策 | 选项 | 状态 | 理由 |
|---|------|------|------|------|
| D4 | Skills 安装范围 | A) 只装设计类 B) 设计+工程全装 C) 按需逐步装 | **已闭合 C** | Phase 0 先装设计类，工程类按需补充 |
| D5 | 评估方式 | 人类 taste + 反模式清单 + 四维评分框架 | **已闭合** | 自动循环已放弃，人类判断为主 |

## 任务清单

### Phase 0：素材准备

**目标**：安装设计 skills，准备生成所需的全部知识素材。

- [ ] T0.1 安装 wondelai/skills 设计类 skills
  - 产出：refactoring-ui / web-typography / top-design / ux-heuristics / microinteractions / design-everyday-things 就绪
  - 验收：`npx skills add` 命令全部成功，skill 文件出现在项目中
  - 失败路径：降级 — 仓库不可用则从 awesome-design-md 手动提取对应参考文档
  - 硬性约束：6 个 skill 全部安装，不得跳过任何一个
  - 参考：附录 D 设计知识 Skills 表

- [ ] T0.2 安装 Jeffallan/claude-skills 前端工程 skills
  - 产出：Next.js Developer / React Expert / Playwright Expert 就绪
  - 验收：Plugin Marketplace 安装成功
  - 失败路径：跳过 — 依赖已有项目代码参考，不影响设计稿生成
  - 硬性约束：无（可跳过）

- [ ] T0.3 通读锚定文档
  - 产出：确认理解核心概念（CLD/FCM/D2D 三层递进）、信息架构（7 个 UI 区域）、用户流程、设计约束
  - 验收：能复述 Thinking 三步流程、CLD 因果图的数据结构、Source Cards 的可信度分级
  - 失败路径：重试 — 分段通读，先核心概念后信息架构
  - 硬性约束：必须通读 `design-anchoring-summary.md` 全文，不得只读摘要
  - 参考：`docs/design/design-anchoring-summary.md`

- [ ] T0.4 浏览 awesome-design-md preview.html
  - 产出：建立 3-5 个品牌的视觉直觉
  - 验收：能说出每个参考品牌的核心设计特征
  - 失败路径：跳过 — 仓库不可用则跳过，依赖已有锚定文档
  - 硬性约束：至少浏览 3 个品牌
  - 参考：awesome-design-md 仓库

### Phase 1：基于基础版延伸

**目标**：基于 Figma 基础版延伸，补全缺失组件、完善细节，产出完整设计稿。

- [ ] T1.1 理解基础版
  - 产出：基础版设计稿的结构分析（已有哪些区域、缺失哪些、视觉基调是什么）
  - 验收：能列出基础版已有的 UI 区域和缺失的区域，与 design-anchoring-summary.md 的信息架构表对照
  - 失败路径：降级 — 若无法访问 Figma 文件，基于截图分析
  - 硬性约束：必须先理解再动手，不得跳过分析直接修改
  - 参考：基础版 Figma 文件、`docs/design/design-anchoring-summary.md` 信息架构表

- [ ] T1.2 延伸生成
  - 产出：在基础版上补全缺失区域、完善已有区域，生成完整设计稿（Header / 消息区 / Thinking / CLD / Source / Leverage / 输入区）
  - 验收：7 个区域全部有内容，视觉风格与基础版连贯
  - 失败路径：降级 — 拆分为组件逐个延伸（先补缺失区域，再完善已有区域）
  - 硬性约束：保留基础版的布局结构和视觉基调；不得使用附录 A 反模式
  - 参考：基础版 Figma 文件、`docs/design/design-anchoring-summary.md` 信息架构表、附录 A 反模式底线

- [ ] T1.3 自评 + 优化
  - 产出：对照附录 C 四维评分框架自评，针对弱项进行一轮优化
  - 验收：四个维度（设计质量/原创性/工艺/功能性）均有自评，弱项已优化
  - 失败路径：跳过 — 若自评全部达标则跳过优化
  - 硬性约束：必须完成自评，优化范围仅限自评发现的弱项，不得改动基础版已有的布局结构
  - 参考：附录 C 评估框架、附录 A 反模式底线

- [ ] T1.4 版本存档
  - 产出：最终版设计稿存档（Figma 版本历史或截图）
  - 验收：最终版可访问
  - 失败路径：跳过 — Figma 自动保存则无需额外操作

### Phase 2：设计稿定稿

**目标**：将最终设计稿落定为可交付物，用于指导代码实现。

- [ ] T2.1 最终自检
  - 产出：附录 B 检查项逐项通过的自检报告
  - 验收：附录 B 的 5 项检查全部通过
  - 失败路径：降级 — 未通过项标注原因，不阻塞后续任务
  - 硬性约束：附录 B 的 5 项检查必须全部完成，未通过项必须记录

- [ ] T2.2 提取 Design Tokens
  - 产出：JSON/TS 格式的 token 文件（色值、字体、间距、阴影）
  - 验收：token 值与 ARCHITECTURE.md 的 oklch 色彩系统一致
  - 失败路径：降级 — 手工从 CSS 提取核心 token（色值 + 间距）
  - 硬性约束：必须使用 oklch 色彩系统，不得使用 hex/rgb

- [ ] T2.3 组件→代码映射
  - 产出：design-anchoring-summary.md 每个组件对应到 `web/src/components/` 路径的映射表
  - 验收：9 个组件全部有映射
  - 失败路径：降级 — 先映射核心 5 个（Header / 消息区 / Thinking / CLD / 输入区）
  - 硬性约束：映射路径必须实际存在或标注"待创建"

- [ ] T2.4 （可选）导入 Figma
  - 产出：通过 Figma MCP 重建或手动导入
  - 验收：Figma 文件可正常打开编辑
  - 失败路径：跳过 — HTML/CSS 直接作设计参考
  - 硬性约束：无（可选任务）

## 执行日志

- [x] 05-21 计划创建（V1-V5）
- [x] 05-21 方向调整：放弃 GAN 循环，转向探索式生成
- [x] 05-21 计划重构（V6-V7）：闭合待决决策，规范文档结构
- [x] 05-21 计划优化（V8）：增加执行规则、checkpoint 机制、硬性/建议分层
- [x] 05-21 创建设计锚定摘要（`design-anchoring-summary.md`），从调研文档提取领域知识
- [x] 05-21 收集 Figma 已生成稿：确认基础文件包含 `01 — Canonical (Full)`、`02 — Canonical Desktop (Vercel)`、`03 — Exploratory (Phase 1 Draft)` 三个可复用稿；其中 `02` 最适合作为桌面主稿骨架
- [x] 05-21 创建增量交付文件：`figma-design-generation-plan-v10`（https://www.figma.com/design/9cfzfIzNqO0SwU4LJvztv1）
- [ ] Phase 0：素材准备
- [x] Phase 1：高质量稿收集与增量基线确定
- [ ] Phase 1.5：增量生成
- [ ] Phase 2：设计稿定稿

## 增量生成基线（05-21）

| Figma 节点 | 质量判断 | 复用策略 |
|------------|----------|----------|
| `01 — Canonical (Full)` | 信息完整，但画幅偏窄，适合作为纵向完整性参考 | 复用七区完整性与顺序，不作为最终桌面布局 |
| `02 — Canonical Desktop (Vercel)` | 桌面比例清晰，Header / Thinking / CLD / Leverage / Source / Input 主结构完整 | 作为本轮增量生成主骨架 |
| `03 — Exploratory (Phase 1 Draft)` | 与 `02` 结构相近，可作为探索备份 | 提取局部细节，不做主稿 |

### 本轮增量生成目标

- 在新文件 `figma-design-generation-plan-v10` 中生成一个完整主稿，避免污染基础文件
- 保留深色专业分析工具基调，不使用“紫色渐变 + 白卡片 + 大圆角”等反模式
- 将 `02` 的线性滚动稿升级为更像真实产品的分析工作台：左侧流程与来源、中心大 CLD 画布、右侧杠杆与置信度面板、底部输入区
- 补足 Source Cards 的 T1/T2/T3 可信度标识、Leverage Table 的排序/不确定性区间、Thinking 三步状态与 CLD 图例

---

## 附录 A：反模式底线

> 以下为设计中必须避免的模式，无论探索方向如何。agent 生成设计时逐项对照，出现任何一项则判定任务失败。

- 紫色渐变 + 白卡片 + 大圆角
- 无差别阴影堆叠
- 只换 accent 色不改布局
- hero section 式首屏堆砌
- 过度装饰的插画/噪点纹理
- 所有内容做成对话气泡
- 只有粗骨架没有实现细节

## 附录 B：CLDFlow 专属检查项

> T2.1 最终评审的验收依据，5 项全部通过才算合格。

- [ ] Thinking 三步（检索/建图/评估）是否清晰可区分？
- [ ] CLD 因果图区域是否有足够空间？
- [ ] Source Cards 是否可扫描？
- [ ] Leverage Table 是否可排序？
- [ ] 长文分析结果是否易读？

## 附录 C：评估框架（来自 Anthropic）

> 用途：人类评审时的思考框架，不用于自动循环。当 T1.2 人类无法给出具体反馈时，用此框架逐项评估。

| 维度 | 核心问题 |
|------|---------|
| **设计质量** | 是否有连贯的视觉身份？颜色/字体/布局是否创造独特氛围？ |
| **原创性** | 是否有自定义决策？还是模板/库默认/AI 通用模式？ |
| **工艺** | 字体层级、间距一致性、色彩和谐、对比度是否达标？ |
| **功能性** | 用户能否理解界面功能、找到主要操作、完成任务？ |

## 附录 D：资源清单

### 设计知识 Skills

| Skill | 用途 | 安装方式 |
|-------|------|----------|
| refactoring-ui | 实用 UI 设计：灰度优先、间距尺度、色彩调色板 | `npx skills add wondelai/skills/refactoring-ui` |
| web-typography | Web 排版：字体配对、行高行宽、CSS clamp() | `npx skills add wondelai/skills/web-typography` |
| top-design | 顶级网站设计：Awwwards 级沉浸式体验 | `npx skills add wondelai/skills/top-design` |
| ux-heuristics | 可用性评估：Nielsen 10 原则 | `npx skills add wondelai/skills/ux-heuristics` |
| microinteractions | 微交互设计：触发器、规则、反馈 | `npx skills add wondelai/skills/microinteractions` |
| design-everyday-things | 设计心理学：affordance、signifier、反馈 | `npx skills add wondelai/skills/design-everyday-things` |

### 参考资源

| 资源 | 说明 | 关系 |
|------|------|------|
| awesome-design-md | 73 个品牌的 DESIGN.md | 风格参考池，按需取用 |
| `docs/design/design-anchoring-summary.md` | 核心概念、信息架构、组件清单、反模式清单 | 必读输入 |
| Anthropic 设计文章 | Generator + Evaluator 框架 | 评估方法论参考 |
| Frontend Design Toolkit | 11 种命名美学风格、Theme Block 格式 | 风格命名参考 |

### 外部工具

| 工具 | 用途 | 状态 |
|------|------|------|
| Figma MCP Server | 生成/编辑 Figma 设计稿 | 已配置 |
| Playwright MCP | 浏览器预览、截图 | 待确认 |
| Claude Code CLI | 设计稿生成主引擎 | 当前会话 |
