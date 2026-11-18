# 设计工作流规则

所有设计相关计划必须锚定到设计工作流，并在执行前验证依赖就绪。

## 适用范围

以下计划属于"设计相关计划"：
- 文件名含 `设计`、`design`、`原型`、`prototype`、`UI`、`UX`
- 内容涉及 UI 生成、Figma 操作、设计评审、组件库配置
- 内容涉及 design tokens、设计系统、视觉稿

## 规则一：锚定设计工作流

设计相关计划的"文档锚定"节**必须**包含：

```
| `docs/design/设计工作流.md` | 工作流定义（定位到具体阶段：P1/P2/P3/P3.5/P4/P5） |
```

锚定时明确该计划对应工作流的哪个阶段，不得跳过。

## 规则二：执行前依赖检查

执行设计相关任务前，必须验证以下依赖就绪：

### Claude Code 插件（外部能力）

| 插件 | 检查方式 | 缺失时处理 |
|------|---------|-----------|
| **Design** | `/plugins` 确认已安装 | 提示用户安装：`claude plugin install design` |
| **Frontend Design** | `/plugins` 确认已安装 | 提示用户安装：`claude plugin install frontend-design` |
| **Context7** | MCP server 列表中确认 | 提示用户配置 MCP server |

### 项目 Skills（内部知识）

| Skill | 检查方式 | 缺失时处理 |
|-------|---------|-----------|
| `cs-rag-architecture-guideline` | `skills/` 目录下存在对应 SKILL.md | 从 `skills-lock.json` 恢复或手动创建 |
| `component-code-mapping` | `docs/design/component-code-mapping.md` 存在 | 执行前先创建该文件 |

### Figma MCP（P4 阶段专用）

| 工具 | 检查方式 | 缺失时处理 |
|------|---------|-----------|
| `use_figma` | MCP 工具列表中确认 | 提示用户配置 Figma MCP server |
| `generate_figma_design` | MCP 工具列表中确认 | 同上 |
| `search_design_system` | MCP 工具列表中确认 | 同上 |

### 检查流程

```
1. 识别计划是否属于设计相关（参照"适用范围"）
2. 如果是 → 读取"文档锚定"节，确认已锚定设计工作流
3. 读取"执行规则"节，确认依赖检查项
4. 执行前逐项验证插件/skill/MCP 就绪状态
5. 缺失项 → 执行失败路径（安装/创建），不得跳过
```

## 规则三：P3.5 原型生成前置条件

执行 P3.5（Code-first 原型生成）前，必须确认：

- [ ] Tailwind + shadcn/ui 已配置（`web/` 目录下有 `tailwind.config.ts` 和 `components.json`）
- [ ] Design Tokens 已定义（`design-tokens-v10.json` 或 Tailwind theme 配置）
- [ ] 现有组件可复用（`web/src/components/ui/` 目录存在）

缺失时：先完成基础搭建任务（T1.1），再进入原型生成。

## 规则四：P4 Figma 导出前置条件

执行 P4（Figma 设计稿导出）前，必须确认：

- [ ] P3.5 原型已通过人工 Review
- [ ] Figma MCP server 已配置且可用
- [ ] `figma-use` skill 已加载

缺失时：暂停执行，等待前置条件满足。
