# Cursor Skills 索引

> 统一的能力扩展体系，按功能领域组织，实现"上下文是认知，工作流是行为"的统一体系

---

## 1. 概述

本项目将所有 Rules 和 Commands 迁移到 Skills，实现统一的能力管理：

- **Skills 是上下文+执行的一体化**：每个 Skill 包含知识（SKILL.md）和执行能力（scripts/）
- **按功能领域组织**：15个 Skills，覆盖9个功能领域
- **自动调用优先**：大部分 Skills 设置为自动调用，让 Agent 智能判断

---

## 2. Skills 索引（按功能领域）

### 2.1 代码质量（4个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `python-coding-standards/` | Python 编码规范（类型提示、日志、命名、注释） | 自动调用 | 无 |
| `file-size-limit/` | 文件行数限制（≤300行硬性要求） | 自动调用 | 无 |
| `single-responsibility/` | 单一职责原则 | 自动调用 | 无 |
| `file-header-comments/` | 代码文件顶部注释规范（适用于所有代码文件） | 自动调用 | 无 |

### 2.2 文档规范（2个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `documentation-standards/` | 文档编写规范（标题编号、日期格式、引用规范） | 自动调用 | 无 |
| `doc-driven-development/` | 文档驱动开发流程 | 自动调用 | 无 |

### 2.3 架构设计（2个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `architecture-cognition/` | 全局架构认知 | 自动调用 | 无 |
| `architecture-design/` | 架构设计规范 | 自动调用 | 无 |

### 2.4 任务管理（2个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `task-planning/` | 任务规划规范（包含需求决策和计划书创建） | 自动调用 | `generate_task_plan.py` |
| `task-closure/` | 任务收尾规范（日志生成和优化分析） | 自动调用 | `generate_task_log.py` |

### 2.5 测试与诊断（1个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `testing-and-diagnostics/` | 测试与诊断工作流（单元测试 + 浏览器测试） | 自动调用 | `run_test_workflow.py`<br>`run_browser_tests.py`<br>`auto_diagnose.py` |

### 2.6 前端开发（1个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `frontend-development/` | 前端开发规范（Streamlit 规范 + UI 自然语言编辑） | 自动调用 | `browser_edit.py` |

### 2.7 规则管理（1个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `skill-management/` | Skills 管理规范（格式规范 + 设计规范） | 自动调用 | `design_skill.py` |

### 2.8 沟通与协作（1个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `concise-communication/` | 简洁沟通规范 | 自动调用 | 无 |

### 2.9 项目原则（1个）

| Skill | 描述 | 调用方式 | Scripts |
|-------|------|---------|---------|
| `project-principles/` | 项目聚焦原则 | 自动调用 | 无 |

---

## 3. 使用指南

### 3.1 Skills 本质

**Skills = Commands 的增强版**：
- ✅ 提供与 Commands 相同的斜杠命令功能（`/skill-name`）
- ✅ 支持自动调用（Agent 根据上下文智能判断）
- ✅ 支持手动调用（用户主动触发）
- ✅ 可包含执行脚本（`scripts/` 目录）
- ✅ 可包含参考文档（`references/` 目录）

### 3.2 Skills 结构

每个 Skill 包含：

```
skill-name/
├── SKILL.md          # 主文件（知识 + 规范，定义斜杠命令）
├── references/       # 参考文档（渐进式加载）
│   └── *.md
└── scripts/          # 执行脚本（可选）
    └── *.py
```

### 3.2 调用方式

**Skills 本质等同于 Commands 的功能**，但提供了更灵活的调用控制：

- **自动调用**：大部分 Skills 设置为自动调用（默认 `disable-model-invocation: false`），Agent 会根据上下文智能判断何时使用
- **手动调用**：所有 Skills 都可以通过斜杠命令手动调用（`/skill-name`），特别适用于：
  - 需要用户参与的工作流（如 `/task-closure`、`/task-planning`）
  - 有副作用的操作（如部署、提交）
  - 需要控制时机的任务

**Scripts**：位于 `scripts/` 目录的 Python 脚本，通常需要手动调用或通过 Skill 间接调用

### 3.3 调用示例

**自动调用**（Agent 根据上下文判断）：
- 编写 Python 代码时 → 自动应用 `python-coding-standards`
- 创建文档时 → 自动应用 `documentation-standards`
- 架构设计时 → 自动应用 `architecture-design`

**手动调用**（用户主动触发）：
- `/task-planning` - 创建任务计划书
- `/task-closure` - 生成任务日志
- `/testing-and-diagnostics` - 运行测试工作流

**快速参考**：

| 功能 | Skill 调用 | Script 调用 |
|------|-----------|------------|
| 任务规划 | `/task-planning` | 通过 Skill 间接调用 `generate_task_plan.py` |
| 任务收尾 | `/task-closure` | 通过 Skill 间接调用 `generate_task_log.py` |
| 测试诊断 | `/testing-and-diagnostics` | 通过 Skill 间接调用 `run_test_workflow.py` 等 |

---

## 4. 迁移说明

### 4.1 迁移来源

- **Rules**：`.cursor/rules/*.mdc` → Skills
- **Commands**：`.cursor/commands/**/*.md` → Skills scripts/

### 4.2 迁移策略

- **全量迁移**：所有 Rules 和 Commands 迁移到 Skills
- **按功能领域组织**：按功能领域重新组织，而非简单映射
- **合并优化**：相关功能合并，删除冗余

### 4.3 参考文档

- [Cursor Skills 官方文档](https://cursor.com/cn/docs/context/skills)
- [Agent Skills 开放标准](https://agentskills.io/home)
- `.cursor/SKILLS_MIGRATION_DECISIONS.md` - 迁移决策总结
- `.cursor/WORKFLOW_COMPONENTS_ANALYSIS.md` - 组件职责边界分析

---

## 5. 版本信息

- **创建日期**：2026-01-23
- **版本**：v1.0
- **状态**：迁移进行中
