# Cursor Agent 工作流组件职责边界与应用场景分析

> 明确 Rules、Skills、Commands、Hooks、Browser 五大组件的核心职责、功能重叠区域与应用场景决策树。

---

## 1. 组件分类体系

### 1.1 两大模块划分

```
Cursor Agent 工作流
├── 上下文构建模块（Context Building）
│   ├── Rules（规则）
│   └── Skills（技能）
│
└── 工作流建设模块（Workflow Construction）
    ├── Commands（命令）
    ├── Hooks（钩子）
    └── Browser（浏览器）
```

### 1.2 核心区别

| 维度 | 上下文构建 | 工作流建设 |
|------|-----------|-----------|
| **作用对象** | AI Agent 的"认知" | AI Agent 的"行为" |
| **作用时机** | 持续影响（被动） | 主动触发（主动） |
| **作用范围** | 全局/场景级 | 任务/步骤级 |
| **变更频率** | 低频（稳定规范） | 中频（流程优化） |
| **依赖关系** | 独立存在 | 依赖上下文构建 |

---

## 2. 组件职责边界定义

### 2.1 Rules（规则）

**核心职责**：定义 AI Agent 的**行为边界**和**决策原则**

**本质**：
- **静态约束**：长期有效的规范、标准、原则
- **场景触发**：通过 `alwaysApply`、`autoAttach`、`globs` 控制加载时机
- **认知注入**：影响 AI 如何理解任务、如何做决策

**典型内容**：
- ✅ 代码规范（类型提示、命名、结构）
- ✅ 架构原则（分层、依赖、接口）
- ✅ 工作流程（何时测试、何时收尾）
- ✅ 设计决策（聚焦原则、技术选型）

**边界约束**：
- ❌ **不包含**具体执行步骤（那是 Commands）
- ❌ **不包含**一次性操作（那是临时指令）
- ❌ **不包含**复杂逻辑流程（那是 Hooks）

**应用场景**：
```
场景：编写 Python 代码
→ Rules 触发：coding_practices.mdc
→ 影响：AI 知道必须加类型提示、文件≤300行、使用 logger
→ 结果：生成的代码自动符合规范
```

---

### 2.2 Skills（技能）

**核心职责**：扩展 AI Agent 的**能力边界**和**知识范围**

**本质**：
- **能力扩展**：让 AI 掌握特定领域的知识/工具
- **工具集成**：封装外部工具、API、框架的使用方法
- **知识注入**：提供领域特定的最佳实践

**典型内容**：
- ✅ 框架使用技能（LlamaIndex、Streamlit）
- ✅ 工具集成技能（Git、Docker、测试工具）
- ✅ 领域知识技能（RAG 架构、向量检索）

**边界约束**：
- ❌ **不包含**行为规范（那是 Rules）
- ❌ **不包含**执行流程（那是 Commands/Hooks）
- ❌ **不包含**一次性操作（那是临时指令）

**与 Rules 的区别**：
| 维度 | Rules | Skills |
|------|-------|--------|
| **关注点** | "应该怎么做" | "能做什么" |
| **作用方式** | 约束行为 | 扩展能力 |
| **内容性质** | 规范、原则 | 知识、工具 |
| **示例** | "文件必须≤300行" | "如何使用 LlamaIndex 构建 RAG" |

**应用场景**：
```
场景：使用 LlamaIndex 构建 RAG
→ Skills 提供：LlamaIndex API 知识、最佳实践
→ 影响：AI 知道如何正确调用 API、如何组织代码
→ 结果：生成的代码符合框架使用规范
```

---

### 2.3 Commands（命令）

**核心职责**：定义**可复用的执行流程**和**标准化操作**

**本质**：
- **动态动作**：具体的执行步骤、操作序列
- **可复用性**：通过 `/command-name` 重复调用
- **标准化**：统一的操作流程、输入输出格式

**典型内容**：
- ✅ 测试流程：`/select-tests` → `/run-unit-tests` → `/summarize-test-results`
- ✅ 收尾流程：`/generate-task-log` → `/run-optimization-review`
- ✅ 诊断流程：`/auto-diagnose`

**边界约束**：
- ❌ **不包含**行为规范（那是 Rules）
- ❌ **不包含**能力扩展（那是 Skills）
- ❌ **不包含**复杂编排（那是 Hooks）

**与 Rules 的关系**：
```
Rules 定义"何时执行" → Commands 定义"如何执行"
示例：
- Rule: testing_and_diagnostics_guidelines.mdc
  → 触发条件：代码变更交付
  → 强制命令链：/select-tests → /run-unit-tests → /summarize-test-results
- Commands: 具体实现每个命令的执行步骤
```

**应用场景**：
```
场景：代码变更后需要测试
→ Rule 触发：testing_and_diagnostics_guidelines.mdc
→ Rule 要求：执行测试命令链
→ Commands 执行：/select-tests → /run-unit-tests → /summarize-test-results
→ 结果：完成标准化测试流程
```

---

### 2.4 Hooks（钩子）

**核心职责**：**聚合多个 Commands**，实现**复杂工作流的自动化编排**

**本质**：
- **命令聚合**：将多个 Commands 组合成完整流程
- **自动化编排**：按顺序执行、错误处理、状态传递
- **一键执行**：简化复杂流程的调用

**典型内容**：
- ✅ 收尾流程聚合：`/execute-post-hooks` = `/generate-task-log` + `/run-optimization-review` + `/run-rule-check`
- ✅ 测试流程聚合：`/run-full-test-suite` = `/select-tests` + `/run-unit-tests` + `/summarize-test-results`

**边界约束**：
- ❌ **不包含**行为规范（那是 Rules）
- ❌ **不包含**能力扩展（那是 Skills）
- ❌ **不包含**单一操作（那是 Commands）

**与 Commands 的区别**：
| 维度 | Commands | Hooks |
|------|----------|-------|
| **粒度** | 单一操作/小流程 | 复杂流程聚合 |
| **组成** | 原子操作 | 多个 Commands |
| **调用** | 独立调用 | 聚合调用 |
| **示例** | `/generate-task-log` | `/execute-post-hooks`（包含3个命令） |

**应用场景**：
```
场景：任务收尾需要执行多个步骤
→ 手动方式：依次调用 /generate-task-log → /run-optimization-review → /run-rule-check
→ Hooks 方式：直接调用 /execute-post-hooks（自动执行3个命令）
→ 结果：简化操作，减少错误
```

---

### 2.5 Browser（浏览器）

**核心职责**：提供**可视化交互**和**端到端测试**能力

**本质**：
- **可视化编辑**：拖拽操作、实时预览、视觉调整
- **自动化测试**：截图、控制台监控、网络追踪
- **端到端验证**：在真实浏览器环境中验证功能

**典型内容**：
- ✅ UI 可视化编辑：调整样式、布局、交互
- ✅ 自动化测试：功能测试、视觉回归、响应式测试
- ✅ 无障碍审计：WCAG 合规性检查

**边界约束**：
- ❌ **不包含**代码规范（那是 Rules）
- ❌ **不包含**后端逻辑（那是 Commands）
- ❌ **不包含**复杂编排（那是 Hooks）

**与其他组件的关系**：
```
Browser 是"执行环境"，其他组件是"执行逻辑"
- Rules 可以定义"何时使用 Browser"（如 browser_visual_editor_integration.mdc）
- Commands 可以定义"如何使用 Browser"（如 /browser-test）
- Hooks 可以聚合 Browser 相关操作
```

**应用场景**：
```
场景：前端 UI 开发
→ Rule 触发：browser_visual_editor_integration.mdc
→ Browser 操作：打开应用 → 可视化编辑 → 应用更改
→ 结果：UI 调整完成，代码自动更新
```

---

## 3. 功能重叠区域分析

### 3.1 重叠区域识别

#### 重叠1：Rules vs Commands（"何时" vs "如何"）

**重叠点**：Rules 可以定义"强制命令链"，Commands 可以定义"执行步骤"

**边界定义**：
- **Rules**：定义"何时执行"、"必须执行"、"执行顺序"
- **Commands**：定义"如何执行"、"具体步骤"、"输入输出"

**决策树**：
```
问题：需要定义执行流程？
├─ 是规范/原则/约束？ → Rules
│  └─ 示例：代码变更后必须执行测试
│
└─ 是具体操作步骤？ → Commands
   └─ 示例：如何执行测试（/run-unit-tests）
```

#### 重叠2：Commands vs Hooks（"单一" vs "聚合"）

**重叠点**：都可以定义执行流程

**边界定义**：
- **Commands**：单一操作或小流程（1-3 步）
- **Hooks**：复杂流程聚合（3+ 步，涉及多个 Commands）

**决策树**：
```
问题：需要定义执行流程？
├─ 单一操作或小流程（≤3步）？ → Commands
│  └─ 示例：/generate-task-log
│
└─ 复杂流程聚合（>3步，涉及多个命令）？ → Hooks
   └─ 示例：/execute-post-hooks（聚合3个命令）
```

#### 重叠3：Rules vs Skills（"约束" vs "扩展"）

**重叠点**：都可以影响 AI 的行为

**边界定义**：
- **Rules**：约束行为（"应该/禁止"）
- **Skills**：扩展能力（"能做什么"）

**决策树**：
```
问题：需要影响 AI 行为？
├─ 是约束/规范/原则？ → Rules
│  └─ 示例：文件必须≤300行
│
└─ 是能力/知识/工具？ → Skills
   └─ 示例：如何使用 LlamaIndex
```

#### 重叠4：Browser vs Commands（"环境" vs "逻辑"）

**重叠点**：都可以执行操作

**边界定义**：
- **Browser**：执行环境（可视化、浏览器环境）
- **Commands**：执行逻辑（步骤、流程）

**决策树**：
```
问题：需要执行操作？
├─ 需要可视化/浏览器环境？ → Browser
│  └─ 示例：UI 编辑、端到端测试
│
└─ 是代码/脚本操作？ → Commands
   └─ 示例：运行测试、生成日志
```

---

## 4. 应用场景决策树

### 4.1 场景1：定义代码规范

**问题**：需要定义"文件必须≤300行"的规范

**决策流程**：
```
1. 这是约束/规范？ → ✅ 是
2. 需要持续影响 AI？ → ✅ 是
3. 是行为边界？ → ✅ 是
→ 选择：Rules（coding_practices.mdc）
```

### 4.2 场景2：定义测试流程

**问题**：需要定义"代码变更后执行测试"的流程

**决策流程**：
```
1. 这是规范/原则？ → ✅ 是（何时执行）
2. 需要定义执行步骤？ → ✅ 是（如何执行）
→ 选择：
   - Rules：定义"何时执行"（testing_and_diagnostics_guidelines.mdc）
   - Commands：定义"如何执行"（/select-tests, /run-unit-tests）
```

### 4.3 场景3：聚合收尾流程

**问题**：需要一键执行"日志+分析+校验"

**决策流程**：
```
1. 涉及多个 Commands？ → ✅ 是（3个命令）
2. 需要自动化编排？ → ✅ 是
→ 选择：Hooks（/execute-post-hooks）
```

### 4.4 场景4：前端 UI 开发

**问题**：需要调整 UI 样式

**决策流程**：
```
1. 需要可视化编辑？ → ✅ 是
2. 需要浏览器环境？ → ✅ 是
→ 选择：Browser（可视化编辑器）
→ 可选：Rules 定义何时使用（browser_visual_editor_integration.mdc）
```

### 4.5 场景5：扩展 AI 能力

**问题**：需要让 AI 掌握 LlamaIndex 的使用

**决策流程**：
```
1. 是能力扩展？ → ✅ 是
2. 是知识/工具？ → ✅ 是
→ 选择：Skills（LlamaIndex 使用技能）
```

---

## 5. 组件协作模式

### 5.1 典型协作流程

```
任务启动
  ↓
Rules 加载（定义行为边界）
  ↓
Skills 加载（扩展能力）
  ↓
任务执行
  ↓
Commands 执行（具体操作）
  ↓
Hooks 聚合（复杂流程）
  ↓
Browser 验证（可视化/测试）
  ↓
任务完成
```

### 5.2 协作示例：代码变更后的测试流程

```
1. Rules 触发
   → testing_and_diagnostics_guidelines.mdc
   → 定义：代码变更后必须执行测试

2. Commands 执行
   → /select-tests（选择测试）
   → /run-unit-tests（执行测试）
   → /summarize-test-results（汇总结果）

3. 如果失败，Hooks 聚合
   → /auto-diagnose（自动诊断）

4. 如果需要 UI 验证，Browser 执行
   → 打开应用 → 截图 → 验证
```

---

## 6. 重构建议

### 6.1 当前问题

1. **Rules 与 Commands 边界不清**：部分 Rules 包含过多执行细节
2. **Hooks 使用不足**：复杂流程仍手动调用多个 Commands
3. **Browser 集成不完整**：缺少 Browser 相关的 Commands/Hooks
4. **Skills 缺失**：项目中没有明确的 Skills 定义

### 6.2 优化方向

1. **Rules 精简**：只保留"何时"、"应该/禁止"，移除"如何"细节
2. **Commands 标准化**：统一输入输出格式，明确执行步骤
3. **Hooks 扩展**：为常用复杂流程创建 Hooks
4. **Browser 集成**：创建 Browser 相关的 Commands（如 `/browser-test`）
5. **Skills 补充**：为关键领域知识创建 Skills

---

## 7. 版本信息

- **创建日期**：2026-01-23
- **版本**：v1.0
- **目标**：明确组件职责边界，解决功能重叠问题
