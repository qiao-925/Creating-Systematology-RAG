# Cursor Rules 迁移说明

> **⚠️ 重要：所有 Rules 已迁移到 Skills**

---

## 迁移状态

**所有 Rules 已迁移到 `.cursor/skills/` 目录**

- **迁移日期**：2026-01-23
- **新位置**：`.cursor/skills/`
- **迁移方式**：按功能领域重新组织，而非简单映射

---

## 迁移映射表

| 原 Rules | 新 Skills | 功能领域 |
|---------|----------|---------|
| `coding_practices.mdc` | `python-coding-standards/` + `file-size-limit/` | 代码质量 |
| `single-responsibility-principle.mdc` | `single-responsibility/` | 代码质量 |
| `documentation_guidelines.mdc` | `documentation-standards/` | 文档规范 |
| `documentation_driven_development.mdc` | `doc-driven-development/` | 文档规范 |
| `global_architecture_cognition.mdc` | `architecture-cognition/` | 架构设计 |
| `architecture_design_guidelines.mdc` | `architecture-design/` | 架构设计 |
| `task_planning_guidelines.mdc` + `workflow_requirements_and_decisions.mdc` | `task-planning/` | 任务管理 |
| `task_closure_guidelines.mdc` | `task-closure/` | 任务管理 |
| `testing_and_diagnostics_guidelines.mdc` | `testing-and-diagnostics/` | 测试与诊断 |
| `streamlit_native_components.mdc` + `browser_visual_editor_integration.mdc` | `frontend-development/` | 前端开发 |
| `cursor-rules-format.mdc` + `rule_authoring_guidelines.mdc` | `skill-management/` | 规则管理 |
| `concise_communication.mdc` | `concise-communication/` | 沟通与协作 |
| `personal-project-focus.mdc` | `project-principles/` | 项目原则 |

---

## 如何使用 Skills

**请参考**：`.cursor/skills/README.md` - Skills 索引和使用指南

**核心变化**：
- Skills 是上下文+执行的一体化（知识 + 脚本）
- 按功能领域组织，而非按 Rules/Commands 分类
- 大部分 Skills 自动调用，让 Agent 智能判断

---

## 版本信息

- **最后更新**：2026-01-23
- **版本**：v5.0（迁移到 Skills）
