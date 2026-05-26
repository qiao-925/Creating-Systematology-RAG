# Code-first 原型生成计划 V2

## 版本目标

- **做什么**：重构原型为两页面架构 — Home 输入页 + Runtime 分析页，通过路由跳转连接
- **为什么**：
  - V1 计划用顶部模式切换器（Chat/Research/Systematology）连接页面，这是错误的架构
  - 实际产品是线性流程：Home 输入问题 → 跳转 Runtime 分析页
  - Chat 和 Research 模式不再需要，只保留 Systematology 一条路径
  - 去掉模式切换后，页面结构更清晰，用户体验更直觉

**页面范围**：
1. **Home 输入页**（`/`）— 搜索框 + 建议问题卡片，输入后跳转 Runtime
2. **Runtime 分析页**（`/runtime`）— 双栏布局：消息区 + CLD 画布（三种实现可切换）

## 文档锚定

| 锚定文档 | 关系 |
|----------|------|
| `docs/design/设计工作流.md` | 工作流定义（定位到 P3.5 阶段） |
| `docs/design/component-code-mapping.md` | 组件映射表（需同步更新） |

## 决策清单

### 核心决策

| # | 决策 | 选项 | 状态 | 理由 |
|---|------|------|------|------|
| D1 | 页面架构 | A. 单页状态切换 / B. Next.js 路由双页 | **B（已定）** | 用户明确要求页面间是跳转关系，不是切换 |
| D2 | 保留模式 | A. Chat+Research+Systematology / B. 仅 Systematology | **B（已定）** | 用户明确只要 Systematology 路径 |
| D3 | 数据传递 | A. URL search params / B. Zustand store / C. context | **A（已定）** | 最简单，`/runtime?q=xxx`，无额外依赖 |
| D4 | CLD 画布实现 | A. SVG / B. React Flow / C. D3.js | **三选一切换** | 保留 V1 设计，原型阶段冗余体验 |

### 支撑决策

| # | 决策 | 选项 | 状态 |
|---|------|------|------|
| S1 | 组件库 | shadcn/ui | **已定** |
| S2 | 主题 | 深色优先 | **已定** |
| S3 | 状态管理 | 页面级 useState | **已定** |
| S4 | 图标库 | Lucide | **已定** |

## 任务清单

### 阶段一：路由与页面拆分

- [x] T1.1 创建 Runtime 页面路由
  - 产出：`web/src/app/runtime/page.tsx`（从当前 `components/systematology/runtime-page.tsx` 迁移为页面级组件）
  - 验收：`/runtime` 路由可访问，渲染 Runtime 页面
  - 失败路径：降级为单页状态切换

- [x] T1.2 Home 页精简
  - 产出：重写 `web/src/app/page.tsx` — 只保留 Systematology 入口（搜索框 + 建议卡片），移除 Chat/Research 模式
  - 验收：Home 页只显示搜索界面，无模式切换器
  - 失败路径：保留现有 Home 但隐藏模式切换

- [x] T1.3 Home → Runtime 跳转
  - 产出：Home 页 `handleSend` 调用 `router.push('/runtime?q=xxx')`
  - 验收：输入问题或点击建议卡片后跳转到 `/runtime?q=...`
  - 失败路径：降级为 window.location 跳转

- [x] T1.4 Runtime 页读取 question
  - 产出：Runtime 页从 `searchParams.q` 读取问题，自动触发分析
  - 验收：访问 `/runtime?q=xxx` 自动开始分析
  - 失败路径：手动输入问题

### 阶段二：HeaderBar 简化

- [x] T2.1 移除模式切换
  - 产出：修改 `header-bar.tsx` — 移除 `mode`/`onModeChange` props 和模式切换 UI
  - 验收：HeaderBar 不再显示 Chat/Research/Systematology 切换按钮
  - 失败路径：CSS 隐藏模式切换

- [x] T2.2 Runtime HeaderBar 适配
  - 产出：Runtime 页的 HeaderBar 显示问题标题 + 状态指示器 + 返回首页按钮
  - 验收：点击返回按钮回到 `/`
  - 失败路径：浏览器后退

### 阶段三：死代码清理

- [x] T3.1 移除 Chat/Research 相关代码
  - 产出：
    - 移除 `page.tsx` 中 `MessageList`、`useChatStream`、`useChatStore`、`ResearchResultCard` 等 Chat/Research 相关 import 和逻辑
    - 移除 `SystematologyPanel` 死代码 import
    - 移除 `AppMode` 中 `"chat"` 和 `"research"` 类型（或保留但不再使用）
  - 验收：`npm run build` 无未使用 import 警告
  - 失败路径：注释掉而非删除

- [x] T3.2 清理 HeaderBar 残留逻辑
  - 产出：移除 HeaderBar 中 `useChatStore`、`resetChat`、`hasMessages` 等 Chat 相关逻辑
  - 验收：HeaderBar 不依赖 chat-store
  - 失败路径：保留但标记为 deprecated

### 阶段四：集成验证

- [x] T4.1 端到端流程验证
  - 产出：完整流程可运行：Home 输入 → 跳转 Runtime → 自动分析 → 左右面板更新
  - 验收：`npm run build` 通过；dev server 可测试完整流程
  - 失败路径：逐环节调试

- [x] T4.2 更新 component-code-mapping.md
  - 产出：更新组件映射表，反映新架构
  - 验收：文档与代码一致
  - 失败路径：标记过期条目

## 执行规则

### 硬性约束（违反则任务失败）

1. **页面间是跳转关系** — Home 和 Runtime 是独立页面，通过 Next.js router 跳转
2. **无模式切换器** — HeaderBar 不得显示 Chat/Research/Systematology 切换按钮
3. **CLD 画布保留三种实现** — SVG/React Flow/D3.js 均保留，带切换按钮
4. **Design Tokens** — 颜色/字体/间距使用 Tailwind theme tokens
5. **TypeScript** — 所有组件必须有完整的 props 类型定义

### 禁止行为

- 在 HeaderBar 中添加模式切换 UI
- 创建 Chat/Research 相关的新组件
- 硬编码颜色值
- 跳过自检

### 自主推进规则

- 自检通过 → 自动继续下一个任务
- 自检失败 → 执行失败路径，如仍无法解决 → 暂停升级
- 任务标注 `[需确认]` → 等待人类确认

## 执行 prompt 模板

### 通用模板

```
读取 `docs/design/Code-first 原型生成计划 V2.md`。

当前执行任务：T{X.X} {任务名称}

硬性约束：
- 页面间是跳转关系（Next.js router），不是模式切换
- HeaderBar 不得显示模式切换 UI
- 使用项目技术栈（React + Next.js + Tailwind v4 + shadcn/ui）
- 颜色/字体/间距使用 globals.css 中的 Tailwind theme tokens

验收标准：
- {从任务清单提取}

失败路径：
- {从任务清单提取}

参考资源：
- Home 页：web/src/app/page.tsx
- Runtime 页：web/src/components/systematology/runtime-page.tsx
- HeaderBar：web/src/components/chat/header-bar.tsx
- 现有 UI：web/src/components/ui/

自主推进规则：
- 自检通过 → 自动继续
- 自检失败 → 执行失败路径 → 暂停升级
```

## 执行记录

（V2 重新生成，V1 执行记录归档至下方）

### V1 执行记录（已归档，对应旧架构）

- [x] T1.1 依赖安装与 Design Tokens 配置 — 05-26
- [x] T1.2 布局骨架 — 05-26
- [x] T2.1-T2.10 Runtime 分析页组件 — 05-26
- [x] T3.1-T3.3 Home 输入页组件 — 05-26
- [x] T4.1-T4.5 类型适配层 + API 集成 + 响应式 + 死代码清理 + 组件映射 — 05-27

### V2 执行记录

- [x] T1.1 创建 Runtime 页面路由 — 05-27
- [x] T1.2 Home 页精简 — 05-27
- [x] T1.3 Home → Runtime 跳转 — 05-27
- [x] T1.4 Runtime 页读取 question — 05-27
- [x] T2.1 移除模式切换 — 05-27
- [x] T2.2 Runtime HeaderBar 适配 — 05-27
- [x] T3.1 移除 Chat/Research 相关代码 — 05-27
- [x] T3.2 清理 HeaderBar 残留逻辑 — 05-27
- [x] T4.1 端到端流程验证 — 05-27
- [x] T4.2 更新 component-code-mapping.md — 05-27

## 关键文件

| 文件 | 操作 |
|------|------|
| `web/src/app/page.tsx` | 重写（Home 页，移除 Chat/Research） |
| `web/src/app/runtime/page.tsx` | 新建（Runtime 页面级入口） |
| `web/src/components/systematology/runtime-page.tsx` | 修改（移除页面级路由逻辑，改为纯组件） |
| `web/src/components/chat/header-bar.tsx` | 修改（移除模式切换） |
| `docs/design/component-code-mapping.md` | 更新 |

## 验证方式

1. `npm run build` — 无 TypeScript 错误
2. Home 页：`/` 显示搜索框 + 建议卡片，无模式切换器
3. 跳转：输入问题 → 跳转 `/runtime?q=xxx`
4. Runtime 页：自动分析，左右面板动态更新
5. 返回：点击 HeaderBar 返回按钮回到 `/`
