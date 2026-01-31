# Cursor Rules 迁移说明

> 当前规则已迁移为 Skills；使用前请先查阅对应 Skill。

---

## 迁移状态
- 所有规则已迁移到 `.cursor/skills/` 目录。
- 迁移日期：2026-01-23
- 组织方式：按功能领域重新分组。

## 迁移对照表
| 原 Rules | 新 Skills | 功能领域 |
|---------|-----------|---------|
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
| `concise_communication.mdc` | `concise-communication/` | 沟通 |
| `personal-project-focus.mdc` | `project-principles/` | 项目原则 |

## 使用 Skills
- 参考 `.cursor/skills/README.md` 了解索引与调用方式。
- Skills = 上下文 + 执行脚本，可自动按需触发。

## 新增指引：第三方 API 先查文档
- 编写/修改使用第三方库的代码前，先调用 `doc-driven-development` Skill。
- 在 Cursor 提问中加 `use context7` 抓官方文档；若 Context7 不可用，按 `references/tech-stack-docs.md` 的 Firecrawl 备用 URL 抓取。
- 确认文档中的 API/参数/示例后再实现，避免幻觉 API。

---

## 版本信息
- 最后更新：2026-01-31
- 版本：6.0（含新增文档优先指引）
