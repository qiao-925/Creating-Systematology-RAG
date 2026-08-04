# Figma 设计稿生成探索记录（废案）

> 本文档作为探索设计、前端相关实践的探索记录。
> 核心问题：运行效率，其次是逆向还原度。
> 思路：先生成设计稿，再逆向前端代码，通过 Claude Code + Figma MCP 生成可参考的设计稿，再导出代码。

---

## 一、探索背景

项目早期尝试建立一套"Figma 先行"的设计工作流：

1. 通过 Claude Code 调用 Figma MCP 直接在 Figma 中生成设计稿。
2. 在 Figma 中完成风格探索、布局迭代和视觉定稿。
3. 将定稿设计稿作为真源，反向指导前端代码实现（Design → Code）。

该路线最终被废弃，转向 **Code-first 原型 + Design Tokens 直接落地** 的模式。

---

## 二、历史时间线（基于 Git 历史还原）

### 2026-05-15 — 前端 UI 优化 + thinking-block 组件
- 新增 `web/src/components/chat/thinking-block.tsx` 等聊天组件。
- 设计 mockup 仍以 HTML（`design-mockup-v2.html`）为主。
- **Figma 状态**：未介入，HTML 为设计真源。

### 2026-05-19 — 文件路径放置规则 + 跨端同步
- 建立 `.claude/path-rules.yaml` + PreToolUse hook 硬拦截。
- 为后续设计文档规范化打下基础。

### 2026-05-20 — 设计阶段一：Figma-only + 七版风格探索
- **决策**：弃用 HTML capture，新 Figma 文件为真源。
- **新增文档**：
  - `docs/design/figma-phase1-workflow.md`
  - `docs/design/style-exploration-matrix.md`
  - `docs/design/thinking-observability-spec.md`
- **Figma 基础文件**：`0AAWUyDNrAulCBsstGR73k`（旧免费账号，Untitled）
- **初版参考**：`6ajDseXpLEBRGu12Ta4BRM`（Systematology V2 Design Mockup）
- **七版候选风格**（Awesome Design MD）：
  - Vercel / Linear / Claude / Cursor / Notion / Stripe / Figma DS
- **Figma 文件结构（3 页上限，因 Starter 计划限制）**：
  - `01 — Canonical (Vercel)`：初版完整 Agent 问答屏
  - `02 — Style Explorations (7×)`：7 套风格并排对比
  - `03 — Thinking & Workflow`：Perplexity 式 Thinking 规格

### 2026-05-21 — 探索式生成方向确立
- **方向调整**：放弃 GAN 循环，转向探索式生成。
- **新增**：`design-anchoring-summary.md`（设计锚定摘要，核心概念/信息架构/组件清单/反模式）。
- **收集 Figma 已生成稿**：确认基础文件包含 `01/02/03` 三个可复用稿，`02` 最适合作为桌面主稿骨架。
- **创建增量交付文件**：`figma-design-generation-plan-v10`（`9cfzfIzNqO0SwU4LJvztv1`）。
- **V11 生成**：`2feKEdDOTNZI4DiA6L8iQx`
- **V13 生成**（Cursor + GPT5.5）：`EzOFBPnk35ANqcFXuuTOba`

### 2026-05-22 — V20 计划
- 新增 `docs/design/figma-design-generation-plan-v20.md`。
- 核心策略：收集并复用 Figma 中已生成的高质量 CLDFlow 设计稿，在新文件中进行增量生成。

### 2026-05-23 — V21 计划 + 原型图 + 自动存档 Hook
- **Commit**：`616c591` — plan 自动存档 hook + v21 设计计划与原型图。
- **新增**：
  - `docs/design/figma-design-generation-plan-v21.md`
  - `docs/design/v21-prototype/v10-report.png`
  - `docs/design/v21-prototype/v11-report.png`
  - `docs/design/v21-prototype/v13-report.png`
  - `.claude/hooks/archive_plan_hook.py`
- **V21 目标**：基于 V20 已验证的 report page，延伸生成 runtime page 和 index page，形成三页主稿。
- **Human-note 中记录的 Figma 文件链接**：
  - V10：`https://www.figma.com/design/9cfzfIzNqO0SwU4LJvztv1/figma-design-generation-plan-v10`
  - V11：`https://www.figma.com/design/2feKEdDOTNZI4DiA6L8iQx/Figma-设计稿生成计划-V11`
  - V13（多个副本）：`EzOFBPnk35ANqcFXuuTOba` / `UJPvlYAP961U4VpGiumA0z` / `K0ga2PH77YFL6LzsOw3bC4`

### 2026-05-23 — Runtime Page 统一设计稿 + 方向转折
- **Commit**：`79b596b` — Runtime Page 统一设计稿 + CLD 可视化优化。
- **关键转折**：
  - 合并 Report Page 和 Runtime Page 为**单页双状态设计**。
  - **清理旧版设计文档**：删除 `v20.md`、`v21.md`、`human-note`、`v21-prototype/`。
  - 新增 `docs/design/runtime-page-design-plan.md`。
  - 新增 HTML 原型：`runtime-page-desktop.html`、`runtime-page-mobile.html`。
  - Figma 设计稿：Night/Day 双主题，1080px 高度。
  - CLD 画布：圆形层级布局 + 曲线贝塞尔边线 + R1/B1 环标签。
  - 迁移旧截图到 `docs/design/runtime page/screenshots/`。

### 2026-05-24 — Design Tokens V10 + 组件映射 + 截图清理
- **Commit**：`ac3de45` — design frames, design tokens v10, component mapping, new skills, and screenshot cleanup。
- **新增**：
  - `docs/design/design-tokens-v10.json`（oklch 色彩系统）
  - `docs/design/component-code-mapping.md`
  - `docs/design/frame-01-main-draft.png` ~ `frame-06-entry-v3.png`
  - `docs/design/inventory/` 多帧设计稿截图
  - `.claude/skills/top-design`、`refactoring-ui`、`web-typography`
- **删除**：旧版 `figma-screenshot.png`、`figma-v8-screenshot.png`、`runtime page/screenshots/` 早期截图。
- **新增 Plan**：`fusion-focus-dashboard-plan.md`

---

## 三、Figma 文件演变记录

| 版本 | fileKey | 状态 | 说明 |
|------|---------|------|------|
| 基础版 | `0AAWUyDNrAulCBsstGR73k` | 旧免费账号 | 初始探索文件，Untitled |
| V2 Mockup | `6ajDseXpLEBRGu12Ta4BRM` | 旧 | Systematology V2 Design Mockup |
| Phase1 主文件 | `GetdOs1IPlJcW5mdrKhVH3` | **当前保留** | 阶段一 3 页结构（Canonical/Styles/Thinking） |
| V10 | `9cfzfIzNqO0SwU4LJvztv1` | 保留 | 增量交付文件，report page 基础版 |
| V10（旧） | `fy8BihJ82jWPyADhJsJwRD` | 旧 | 早期 V10 副本 |
| V11 | `2feKEdDOTNZI4DiA6L8iQx` | 保留 | report page 迭代 |
| V13 | `EzOFBPnk35ANqcFXuuTOba` | 保留 | report page 最新（cursor-gpt5.5） |
| V13 副本1 | `UJPvlYAP961U4VpGiumA0z` | 旧 | |
| V13 副本2 | `K0ga2PH77YFL6LzsOw3bC4` | 旧 | |

### Figma MCP 读取记录（2026-05-26 现场探测）

- **账号**：`noneplus@outlook.com`（Peter）
- **Plans**：
  - `noneplus's team` — View seat, student tier
  - `CLDFlow` — Full seat (expert), student tier
- **Rate Limit 状态**：Education plan 月度读工具配额已耗尽（`get_metadata` 触发 `Upgrade your plan` 提示）。
- `6ajDseXpLEBRGu12Ta4BRM` 的 metadata：仅 1 个 Page（`Page 1`），说明该文件结构极简或已被清理。

---

## 四、关键计划文档内容摘要

### V10 计划（`figma-design-generation-plan-v10.md`）
- **目标**：基于 Figma 基础版做增量延伸，补全 7 个 UI 区域（Header / 消息区 / Thinking / CLD / Source / Leverage / 输入区）。
- **增量基线**：
  - `01 — Canonical (Full)`：信息完整，画幅偏窄。
  - `02 — Canonical Desktop (Vercel)`：桌面比例清晰，主结构完整 → **作为主骨架**。
  - `03 — Exploratory (Phase 1 Draft)`：探索备份。
- **反模式底线**：紫色渐变+白卡片+大圆角、无差别阴影堆叠、只换 accent 色不改布局、hero section 式首屏堆砌、过度装饰、所有内容做成对话气泡、只有粗骨架没有实现细节。

### V20 计划（`figma-design-generation-plan-v20.md`）
- 内容与 V10 高度相似，核心策略一致：收集并复用已有高质量稿，在新文件中增量生成。
- **已被 79b596b 删除**。

### V21 计划（`figma-design-generation-plan-v21.md`）
- **目标**：基于 V20 report page，延伸生成 runtime page 和 index page，形成三页主稿。
- **三页定义**：
  - Index Page：项目门户/启动入口（参考 Vercel/Linear 首页）。
  - Runtime Page：Agent 问答交互主界面（参考 DeepSeek/Manus/ChatGPT）。
  - Report Page：分析结果展示（已有 v10/v11/v13）。
- **关键约束**：不使用旧文件 `GetdOs1IPlJcW5mdrKhVH3`，直接创建新设计稿。
- **已被 79b596b 删除**。

---

## 五、自动化脚本与工具

### 1. `scripts/figma_rate_limit_test.py`
- **用途**：探测 Figma MCP 每日/月度调用上限。
- **机制**：循环调用 `get_metadata` 300 次，追踪 HTTP 429 / Retry-After / 月度配额耗尽。
- **结论**：View seat Education 计划读工具约 6 次/月，`use_figma` 写入理论上豁免读配额但实际仍受限流影响。

### 2. `scripts/figma_phase1_build.py`
- **用途**：批量执行 Phase1 的 5 个 `use_figma` JS 脚本。
- **FILE_KEY**：`GetdOs1IPlJcW5mdrKhVH3`
- **BASE_URL**：优先本地桌面 MCP（`http://127.0.0.1:3845/mcp`），其次远程 `https://mcp.figma.com/mcp`。

### 3. `scripts/figma-phase1/*.js`

| # | 文件 | 功能 |
|---|------|------|
| 0 | `00_inspect.js` | 读取文件页面结构、顶层节点信息 |
| 1 | `01_page01_clean.js` | 清空 `01 — Canonical (Vercel)` 页面 |
| 2 | `02_page01_canonical.js` | 创建 Canonical Agent Chat 帧（1280×900），含 Header/消息流/Thinking/输入区 |
| 3 | `03_page02_styles.js` | 创建 7 版风格探索帧（480×720），每帧含完整骨架 |
| 4 | `04_page03_thinking.js` | 创建 Thinking & Workflow 页面，含 Light/Dark 双主题状态机 |

---

## 六、速率限制问题（核心障碍之一）

- **账号席位**：View seat（Education / Starter 计划）。
- **读工具配额**：约 6 次/月（`get_metadata`、`get_design_context`、`get_screenshot` 等）。
- **写工具**：`use_figma` 写入画布理论上不占用读配额，但 Education plan 整体存在 MCP 调用上限。
- **实际影响**：
  - 无法批量读取 Figma 文件元数据或截图验证。
  - Agent 执行设计计划时频繁触发 `Upgrade your plan`。
  - 每次调用需间隔 5s+，执行效率极低。
- **应对**：
  - 编写 `figma-mcp-rate-limits-and-curl-demo.md` 详细记录限速与重试策略。
  - 编写 `figma_rate_limit_test.py` 探测上限。
  - 推荐使用 Figma 桌面版 MCP（`http://127.0.0.1:3845/mcp`）规避远程配额。

---

## 七、关键结论与废案原因

### 7.1 运行效率问题

1. **Figma MCP 速率限制严重**：Education/Starter 计划下，读工具月度配额极低（~6 次/月），导致设计稿验证和迭代成本极高。
2. **use_figma 写入效率低**：每次 `use_figma` 调用需通过 Figma Plugin API 逐节点创建（文本/矩形/自动布局），复杂页面需要数十次调用，且每次需等待 5s+ 间隔。
3. **人工 taste 评审瓶颈**：设计计划要求"人类评审决定收敛方向"，但 Agent 无法自主完成风格选型，导致每次迭代需等待人类反馈，无法持续推进。

### 7.2 逆向还原度问题

1. **Figma → Code 的还原损耗**：即使设计稿在 Figma 中完成，导出为代码时（无论是通过 Figma Dev Mode 还是手工映射），Design Tokens（oklch 色彩、间距系统）和组件层级都需要二次转译，无法直接落地到 Tailwind v4 + shadcn/ui。
2. **HTML 原型成为更优中介**：79b596b 之后，团队发现直接在 HTML/CSS 中做原型（`runtime-page-desktop.html` / `runtime-page-mobile.html`），再提取 Design Tokens（`design-tokens-v10.json`）和组件映射（`component-code-mapping.md`），比 Figma → Code 的路线还原度更高、迭代更快。

### 7.3 方向转折

- **79b596b** 明确标志转折：
  - 删除 v20/v21 计划和原型图。
  - 从"多文件多版本迭代"（v10 → v11 → v13 → v21）转向"Runtime Page 统一设计稿"。
  - 以 HTML 原型替代 Figma 作为阶段一交付物。
- **ac3de45** 进一步固化：
  - 提取 `design-tokens-v10.json`（oklch 系统）。
  - 建立 `component-code-mapping.md`。
  - 以截图库存（`inventory/`）替代实时 Figma 文件作为设计参考。

### 7.4 废案定论

**"Figma 先行 + 逆向代码"路线正式废弃。** 后续设计工作流调整为：

1. **Code-first 原型**：直接在 HTML/Next.js 中构建可交互原型。
2. **Design Tokens 同步**：从代码中提取 token，反向写入设计系统文档。
3. **Figma 仅作辅助参考**：不再作为真源，仅用于快速草图或对外展示（如有需要）。

---

## 八、相关文件链接（Git 历史可还原）

### 设计计划文档（部分已被删除，可从 Git 历史恢复）

- `docs/design/figma-design-generation-plan-v10.md`（现存，路径 `docs/design/`）
  - 历史版本：`docs/design/v0.0.1/figma-design-generation-plan-v10.md`（79b596b 前）
- `docs/design/figma-design-generation-plan-v20.md`（**已删除**，79b596b）
- `docs/design/figma-design-generation-plan-v21.md`（**已删除**，79b596b）
- `docs/design/runtime-page-design-plan.md`（现存）
- `docs/design/figma-phase1-workflow.md`（**已删除**，232d93b）
- `docs/design/style-exploration-matrix.md`（**已删除**，232d93b）
- `docs/design/thinking-observability-spec.md`（**已删除**，232d93b）
- `docs/design/figma-mcp-rate-limits-and-curl-demo.md`（**已删除**，232d93b）
- `docs/design/human-note`（**已删除**，79b596b）

### 脚本与工具

- `scripts/figma_rate_limit_test.py`（现存）
- `scripts/figma_phase1_build.py`（现存）
- `scripts/figma-phase1/00_inspect.js`
- `scripts/figma-phase1/01_page01_clean.js`
- `scripts/figma-phase1/02_page01_canonical.js`
- `scripts/figma-phase1/03_page02_styles.js`
- `scripts/figma-phase1/04_page03_thinking.js`
- `scripts/figma-phase1/README.md`

### Design Tokens 与组件映射

- `docs/design/design-tokens-v10.json`（现存）
- `docs/design/component-code-mapping.md`（现存）
- `docs/design/design-anchoring-summary.md`（现存）

### 截图库存（部分现存）

- `docs/design/inventory/`（ac3de45 新增，含 runtime/report/entry/fusion/cld 等帧）
- `docs/design/frame-01-main-draft.png` ~ `frame-06-entry-v3.png`
- `docs/design/v21-prototype/v10-report.png`（**已删除**，79b596b）
- `docs/design/v21-prototype/v11-report.png`（**已删除**，79b596b）
- `docs/design/v21-prototype/v13-report.png`（**已删除**，79b596b）
- `docs/design/runtime page/screenshots/`（79b596b 迁移后，ac3de45 部分清理）

---

## 九、恢复被删文件的方法

以下文件虽在当前工作树中已删除，但均保留在 Git 历史中，可随时恢复：

```bash
# V20 计划（最后一次存在于 232d93b）
git show 232d93b:docs/design/figma-design-generation-plan-v20.md

# V21 计划（最后一次存在于 616c591）
git show 616c591:docs/design/figma-design-generation-plan-v21.md

# Phase1 工作流等（最后一次存在于 a121e06）
git show a121e06:docs/design/figma-phase1-workflow.md
git show a121e06:docs/design/style-exploration-matrix.md
git show a121e06:docs/design/thinking-observability-spec.md
git show a121e06:docs/design/figma-mcp-rate-limits-and-curl-demo.md

# Human-note（最后一次存在于 616c591）
git show 616c591:docs/design/human-note

# V21 原型图（最后一次存在于 616c591）
git show 616c591:docs/design/v21-prototype/v10-report.png > v10-report.png
```

---

*记录整理时间：2026-05-26*
*整理方式：Git 历史回溯 + Figma MCP 现场探测（`whoami` 成功，`get_metadata` 触发 Education plan 限额）*
