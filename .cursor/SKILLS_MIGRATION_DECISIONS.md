# Skills 迁移决策总结

> 基于功能领域分析，记录所有 Rules 和 Commands 迁移为 Skills 的决策结果

---

## 1. 功能领域决策总览

| 领域 | Skills 数量 | Skills 名称 | 调用方式 | Scripts |
|------|-----------|-----------|---------|---------|
| **1. 代码质量** | 3个 | python-coding-standards, file-size-limit, single-responsibility | 全部自动 | 无 |
| **2. 文档规范** | 2个 | documentation-standards, doc-driven-development | 全部自动 | 无 |
| **3. 架构设计** | 2个 | architecture-cognition, architecture-design | 全部自动 | 无 |
| **4. 任务管理** | 2个 | task-planning, task-closure | 全部自动 | 2个 |
| **5. 测试与诊断** | 1个 | testing-and-diagnostics | 自动 | 3个 |
| **6. 前端开发** | 1个 | frontend-development | 自动 | 1个 |
| **7. 规则管理** | 1个 | skill-management | 自动 | 1个 |
| **8. 沟通与协作** | 1个 | concise-communication | 自动 | 无 |
| **9. 项目原则** | 1个 | project-principles | 自动 | 无 |
| **总计** | **14个** | | | **7个** |

---

## 2. 详细决策记录

### 2.1 功能领域1：代码质量

**Skills 组织**：
- `python-coding-standards/` - 核心编码规范（自动调用）
- `file-size-limit/` - 文件行数限制（自动调用）
- `single-responsibility/` - 单一职责原则（自动调用）

**内容组织**：SKILL.md + references/

**调用方式**：全部自动调用

**Scripts**：暂不需要

**来源 Rules**：
- `coding_practices.mdc` → `python-coding-standards` + `file-size-limit`
- `single-responsibility-principle.mdc` → `single-responsibility`

---

### 2.2 功能领域2：文档规范

**Skills 组织**：
- `documentation-standards/` - 文档编写规范（自动调用）
- `doc-driven-development/` - 文档驱动开发（自动调用）

**内容组织**：SKILL.md + references/

**调用方式**：两个都自动调用

**Scripts**：暂不需要

**来源 Rules**：
- `documentation_guidelines.mdc` → `documentation-standards`
- `documentation_driven_development.mdc` → `doc-driven-development`

---

### 2.3 功能领域3：架构设计

**Skills 组织**：
- `architecture-cognition/` - 全局架构认知（自动调用，所有代码工作时）
- `architecture-design/` - 架构设计规范（自动调用，特定目录工作时）

**内容组织**：SKILL.md + references/

**调用方式**：两个都自动调用

**Scripts**：暂不需要

**项目上下文**：先保留在 `architecture-cognition` 中

**来源 Rules**：
- `global_architecture_cognition.mdc` → `architecture-cognition`
- `architecture_design_guidelines.mdc` → `architecture-design`

---

### 2.4 功能领域4：任务管理

**Skills 组织**：
- `task-planning/` - 任务规划（自动调用，包含规划规范 + 需求决策）
- `task-closure/` - 任务收尾（自动调用，合并日志生成 + 优化分析）

**内容组织**：SKILL.md + references/ + scripts/

**调用方式**：
- Skill：自动调用
- Scripts：手动调用（`/generate-task-plan`、`/generate-task-log`）

**Scripts**：
- `generate_task_plan.py`（对应 `/generate-task-plan`）
- `generate_task_log.py`（合并 `generate-task-log` + `run-optimization-review`）

**删除内容**：
- `run-rule-check` 命令
- `execute-post-hooks` 聚合命令

**来源 Rules**：
- `task_planning_guidelines.mdc` + `workflow_requirements_and_decisions.mdc` → `task-planning`
- `task_closure_guidelines.mdc` → `task-closure`（删除 run-rule-check 相关内容）

**来源 Commands**：
- `generate-task-plan` → `generate_task_plan.py`
- `generate-task-log` + `run-optimization-review` → `generate_task_log.py`

---

### 2.5 功能领域5：测试与诊断

**Skills 组织**：
- `testing-and-diagnostics/` - 测试与诊断（自动调用，包含单元测试 + 浏览器测试）

**内容组织**：SKILL.md + references/ + scripts/

**调用方式**：
- Skill：自动调用（代码变更后自动判断测试类型）
- Scripts：主要自动触发，也可手动调用

**Scripts**：
- `run_test_workflow.py` - 单元测试工作流（聚合 select + run + summarize）
- `run_browser_tests.py` - 浏览器测试工作流（整合所有 browser Commands）
- `auto_diagnose.py` - 诊断流程

**测试逻辑**：
- 后端变更（`src/**`）→ 执行单元测试
- 前端变更（`frontend/**`）→ 执行浏览器测试
- 全栈变更 → 先单元测试，再浏览器测试

**来源 Rules**：
- `testing_and_diagnostics_guidelines.mdc` → `testing-and-diagnostics`

**来源 Commands**：
- `select-tests` + `run-unit-tests` + `summarize-test-results` → `run_test_workflow.py`
- `browser-test` + `browser-a11y` + `browser-visual-regression` + `browser-restart-and-test` → `run_browser_tests.py`
- `auto-diagnose` → `auto_diagnose.py`

---

### 2.6 功能领域6：前端开发

**Skills 组织**：
- `frontend-development/` - 前端开发（自动调用，包含 Streamlit 规范 + UI 自然语言编辑）

**内容组织**：SKILL.md + references/ + scripts/

**调用方式**：
- Skill：自动调用（在 `frontend/**` 工作时）
- Script：手动调用（用户主动使用 UI 编辑工具）

**Scripts**：
- `browser_edit.py` - UI 自然语言编辑（包含启动逻辑）

**删除内容**：
- `browser-start` 命令（逻辑已整合到 `browser-edit`）

**来源 Rules**：
- `streamlit_native_components.mdc` → `frontend-development`
- `browser_visual_editor_integration.mdc` → `frontend-development`（开发部分）

**来源 Commands**：
- `browser-edit` → `browser_edit.py`（包含启动逻辑）

---

### 2.7 功能领域7：规则管理

**Skills 组织**：
- `skill-management/` - Skills 管理（自动调用，包含格式规范 + 设计规范）

**内容组织**：SKILL.md + references/ + scripts/

**调用方式**：
- Skill：自动调用（创建/修改 Skills 时）
- Script：手动调用（用户主动设计 Skills 时）

**Scripts**：
- `design_skill.py`（对应 `/design-rule`，更新为设计 Skills）

**内容更新**：
- 基于官方文档更新为 Skills 管理规范
- 包含 Skills 格式规范（SKILL.md 格式）
- 包含 Skills 设计最佳实践
- 保存官方文档引用

**官方文档引用**：
- [Cursor Skills 官方文档](https://cursor.com/cn/docs/context/skills)
- [Agent Skills 开放标准](https://agentskills.io/home)

**来源 Rules**：
- `cursor-rules-format.mdc` → `skill-management`（更新为 Skills 格式）
- `rule_authoring_guidelines.mdc` → `skill-management`（更新为 Skills 设计）

**来源 Commands**：
- `design-rule` → `design_skill.py`（更新为设计 Skills）

---

### 2.8 功能领域8：沟通与协作

**Skills 组织**：
- `concise-communication/` - 简洁沟通规范（自动调用）

**内容组织**：SKILL.md + references/

**调用方式**：自动调用（所有对话中自动应用）

**Scripts**：不需要（纯规范，无执行工具）

**来源 Rules**：
- `concise_communication.mdc` → `concise-communication`

---

### 2.9 功能领域9：项目原则

**Skills 组织**：
- `project-principles/` - 项目聚焦原则（自动调用）

**内容组织**：SKILL.md + references/

**调用方式**：自动调用（所有设计决策中自动应用）

**Scripts**：不需要（纯规范，无执行工具）

**来源 Rules**：
- `personal-project-focus.mdc` → `project-principles`

---

## 3. 迁移策略总结

### 3.1 核心原则

1. **全量迁移**：所有 Rules 和 Commands 迁移到 Skills
2. **按功能领域组织**：按功能领域重新组织，而非简单映射
3. **Skills 是上下文+执行的一体化**：每个 Skill 包含知识（SKILL.md）和执行能力（scripts/）
4. **自动调用优先**：大部分 Skills 设置为自动调用，让 Agent 智能判断

### 3.2 删除内容

- `run-rule-check` 命令
- `execute-post-hooks` 聚合命令
- `browser-start` 命令（逻辑整合到 `browser-edit`）

### 3.3 合并内容

- `workflow_requirements_and_decisions` + `task_planning_guidelines` → `task-planning`
- `generate-task-log` + `run-optimization-review` → `generate_task_log.py`
- `select-tests` + `run-unit-tests` + `summarize-test-results` → `run_test_workflow.py`
- 浏览器测试 Commands → `run_browser_tests.py`

### 3.4 更新内容

- `cursor-rules-format.mdc` → 更新为 Skills 格式规范
- `rule_authoring_guidelines.mdc` → 更新为 Skills 设计规范
- `design-rule` → 更新为 `design_skill.py`

---

## 4. 最终 Skills 结构

```
.cursor/
├── rules/                    # 清空或只保留最小配置
│   └── (空或删除)
│
└── skills/                   # 所有能力统一在这里（14个 Skills）
    ├── python-coding-standards/
    ├── file-size-limit/
    ├── single-responsibility/
    ├── documentation-standards/
    ├── doc-driven-development/
    ├── architecture-cognition/
    ├── architecture-design/
    ├── task-planning/
    ├── task-closure/
    ├── testing-and-diagnostics/
    ├── frontend-development/
    ├── skill-management/
    ├── concise-communication/
    └── project-principles/
```

---

## 5. 版本信息

- **创建日期**：2026-01-23
- **版本**：v1.0
- **基于**：功能领域分析和官方文档
