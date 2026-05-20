# 子计划 B：前端 Demo

> 交付 CLDFlow 的前端界面——用户通过 Web 页面输入研究问题、查看因果分析结果。独立于后端，可并行开发。

## 版本目标

- 做什么：交付 Next.js 前端 Demo，支持 CLDFlow 分析输入、结果展示、API 对接
- 为什么：用户需要通过 Web 界面与 CLDFlow 交互，Demo 是可发布 MVP 的必要组成部分

### 成功标准

- 用户可在页面输入研究问题并触发分析
- 分析结果（CLD/FCM/D2D）可在页面展示
- 前端可正确调用后端 API 并处理响应

### 范围

**In Scope**
- Next.js 项目结构与路由
- CLDFlow 分析组件（输入 + 结果展示）
- API 对接层
- 基础 UI 组件（shadcn/ui）

**Out of Scope**
- 后端逻辑（子计划 A）
- 测试体系（子计划 C）
- 部署配置（子计划 D）
- 复杂的图可视化（后续迭代）

## 文档锚定

- 锚定：`web/` — Next.js 前端源码
- 锚定：`ARCHITECTURE.md` — 前后端交互架构
- 同步：`backend/core/api.py` — API 端点需与前端对齐

## 决策清单

### 核心决策

- [x] D1 前端框架：Next.js 16 (App Router)
- [x] D2 UI 组件库：shadcn/ui
- [x] D3 状态管理：Zustand

### 支撑决策

- [x] D4 样式方案：Tailwind CSS
- [x] D5 API 对接：fetch + zod 校验
- [x] D6 设计语言：Vercel 风格（近白底 #fff + 墨黑 #171717 + Geist 字体）
- [x] D7 UI 结构：Agent 问答式布局（扁平消息流、内联产出、无侧边栏）
- [x] D8 模式切换：**取消 Chat/Research/CLDFlow 三 tab**，统一为单一聊天入口，Agent 自动判断分析路径

## 任务清单

### 阶段 1：项目骨架

- [x] B1 Next.js 项目搭建
  - 产出：`web/` 完整项目结构（package.json, tsconfig, next.config.ts, tailwind）
  - 验收：`npm run build` 成功
  - 失败路径：—

- [x] B2 基础页面与布局
  - 产出：`web/src/app/layout.tsx`, `page.tsx`, `globals.css`
  - 验收：根页面可渲染，主题切换可用
  - 失败路径：降级 — 纯 HTML 先跑通

- [x] B3 通用 UI 组件
  - 产出：`web/src/components/ui/`（shadcn 组件：button, card, input, select 等）
  - 验收：组件可复用，样式一致
  - 失败路径：降级 — 用原生 HTML 元素

### 阶段 2：CLDFlow 功能

- [x] B4 CLDFlow 分析组件
  - 产出：`web/src/components/cldflow/cldflow-panel.tsx`
  - 验收：可输入研究问题，展示分析结果（CLD 节点/边、FCM 稳定态、D2D 杠杆排序）
  - 失败路径：降级 — 硬编码 demo 数据

- [x] B5 API 对接层
  - 产出：`web/src/lib/api.ts`（API client, 请求/响应类型）
  - 验收：前端可调用 `/api/cldflow/analyze` 并正确解析响应
  - 失败路径：降级 — 用 mock 数据先跑通 UI

- [x] B6 Chat 组件
  - 产出：`web/src/components/chat/`
  - 验收：对话式交互可用
  - 失败路径：跳过 — 后续迭代补

- [x] B7 Settings 页面
  - 产出：`web/src/components/settings/`
  - 验收：配置项可查看和修改
  - 失败路径：跳过 — 后续迭代补

### 阶段 3：增强（后续迭代）

- [ ] B8 CLD 图可视化
  - 产出：因果图的交互式可视化组件（reactflow/d3/cytoscape）
  - 验收：节点和边可渲染，支持缩放和拖拽
  - 失败路径：跳过 — 用文本列表展示

- [ ] B9 FCM/D2D 结果可视化
  - 产出：权重矩阵热力图、影响力排序图表
  - 验收：数据可视化清晰
  - 失败路径：跳过 — 用纯文本展示

## 设计方向

**设计语言**：Vercel 风格，基于 [awesome-design-md](https://github.com/voltagent/awesome-design-md) 的 `design-md/vercel/DESIGN.md`。
- 色彩：近白底 #fff + 墨黑 #171717 + link blue #0070f3
- 字体：Geist Sans + Geist Mono
- 阴影：堆叠式多层阴影（非单层重影）
- 间距：4px 基础单位，大留白 + 紧凑内部
- 圆角：按钮 pill（100px），卡片 8-12px

**UI 结构**：Agent 问答式布局（参考 ChatGPT / Claude / v0 / Perplexity）
- **无模式切换**：去掉 Chat/Research/CLDFlow tab，单一聊天入口
- 无侧边栏（MVP 阶段保持简洁）
- 扁平消息流（无气泡），用户右对齐，助手左对齐
- 分步 Thinking 指示器（Perplexity 风格：检索 → 构建图 → 评估）
- CLD 图 / FCM 结果内联渲染在消息流中（非侧边面板）
- 行内引用 [1][2] + 底部来源卡片

**Figma 设计稿（阶段一真源）**：
- 文件（阶段一）：https://www.figma.com/design/0AAWUyDNrAulCBsstGR73k（CLDFlow 团队）
- 项目文件夹：https://www.figma.com/files/team/1638836103345957465/project/603731489
- Canonical：Agent 问答式、无 Tab（初版 capture 已对齐）
- 工作流：`docs/design/figma-phase1-workflow.md`
- 七版风格矩阵：`docs/design/style-exploration-matrix.md`
- Thinking 规格：`docs/design/thinking-observability-spec.md`
- ~~HTML mockup~~：已弃用，不再作为校验真源

## MVP 范围锚定（2026-05-19）

**做**：
- Header：logo + 设置按钮，无 tab
- 消息布局扁平化（去气泡、去头像）
- 色彩切换到 Vercel blue `#0070f3`
- Source cards 水平排列
- Leverage table Vercel 风格微调

**不做（延后迭代）**：
- B8 CLD 图可视化（reactflow/cytoscape）→ MVP 用文本渲染
- B9 FCM/D2D 结果可视化 → MVP 用现有组件
- Thinking 分步指示器 → MVP 先用 spinner，等后端结构化步骤

## 执行记录

- [x] 05-16 前端从 Streamlit 迁移到 Next.js
- [x] 05-18 B1-B7 全部完成
- [x] 05-19 设计方向探索：确定 Vercel 设计语言 + Agent 问答式布局，生成 Figma 设计稿 V2
- [x] 05-19 设计锚定：去掉 Chat/Research/CLDFlow 三 tab，统一为单一聊天入口；MVP 范围裁剪确认
- [x] 05-20 设计阶段一：Figma-only 流程锚定 + 文档（见 `docs/design/`）
- [x] 05-20 用户确认：七版名单 + P1 授权 + MCP 报错附 cURL（见 `figma-mcp-rate-limits-and-curl-demo.md` §8）
- [x] 05-20 Figma：P1 Canonical 两帧完成（Landing + Conversation/Thinking），文件 `0AAWUyDNrAulCBsstGR73k`
- [x] 05-20 Perplexity 调研文档存档：`docs/research/perplexity-style-eval-survey.md`
- [x] 05-20 Figma：P2 七版风格探索完成（Page 02），待用户选型
- [x] 05-21 Figma：Canonical 骨架重建（完整版：CLD 图 + FCM 表 + 来源卡），用户确认基础版
- [x] 05-21 Figma：P2 七版风格探索重建（完整骨架版），Page 02 已更新
- [ ] 05-20 设计选型：从七版中选定主风格并记录于 `style-exploration-matrix.md`
- [ ] **阶段二** UI 代码重构：按选定 Figma 实现（扁平消息、无 tab、Thinking 分步）
- [ ] **阶段二** 设计校验：对照 Figma 节点截图，不再使用 HTML mockup
- [ ] B8-B9 可视化增强待后续迭代（需参照 V2 设计稿实现）

## 设计校验清单

阶段二代码完成后，必须逐项对照 **Figma 选定帧**（亮/暗双模式）确认。
阶段一设计校验见 `docs/design/figma-phase1-workflow.md` 与 `docs/design/style-exploration-matrix.md`。

- [ ] Header：仅 logo + 设置按钮，无 tab
- [ ] 消息布局：扁平无气泡、无头像，用户右对齐灰底，助手左对齐无背景
- [ ] 色彩：accent 为 Vercel blue `#0070f3`，非 emerald
- [ ] Thinking block：spinner 样式与设计稿一致
- [ ] Source cards：水平排列，序号方块 + 标题截断
- [ ] Leverage table：排名序号、进度条、分数样式一致
- [ ] 暗色模式：切换后所有元素可读、对比度达标
- [ ] 输入区：textarea + 发送按钮，Enter 发送提示

## 附录：前后端交互

- 前端通过 `web/src/lib/api.ts` 调用后端
- 后端 API：`POST /api/cldflow/analyze`（AnalyzeRequest → AnalyzeResponse）
- 部署时 Next.js standalone 在 :7860，代理 `/api/*` 到 FastAPI :8000
