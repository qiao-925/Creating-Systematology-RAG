# Cursor Commands 迁移说明

> **⚠️ 重要：所有 Commands 已迁移到 Skills scripts/**

---

## 迁移状态

**所有 Commands 已迁移到 `.cursor/skills/*/scripts/` 目录**

- **迁移日期**：2026-01-23
- **新位置**：`.cursor/skills/*/scripts/`
- **迁移方式**：按功能领域整合到对应 Skills

---

## Skill 的手动调用方式

### 直接调用 Skill

**Skill 本身可以通过斜杠命令直接调用**，无需创建额外的 command 文件：

1. **调用方式**：在 Cursor 聊天中输入 `/skill-name` 即可
2. **Skill 名称**：来自 `SKILL.md` 的 frontmatter 中的 `name` 字段
3. **示例**：
   - `/task-closure` - 调用任务收尾 skill
   - `/task-planning` - 调用任务规划 skill
   - `/testing-and-diagnostics` - 调用测试与诊断 skill

### Frontmatter 控制调用方式

在 `SKILL.md` 的 frontmatter 中可以控制调用方式：

```yaml
---
name: task-closure
description: 任务收尾规范...
disable-model-invocation: false  # 默认：Claude 和用户都可以调用
---
```

| 配置 | 用户可调用 | Claude 可调用 | 说明 |
|------|----------|--------------|------|
| 默认（无配置） | ✅ | ✅ | 用户可 `/skill-name`，Claude 也会自动加载 |
| `disable-model-invocation: true` | ✅ | ❌ | 仅用户可调用，Claude 不会自动触发 |
| `user-invocable: false` | ❌ | ✅ | 仅 Claude 可调用，不显示在 `/` 菜单中 |

### 调用 Skill Scripts

如果需要执行 Skill 中的脚本，可以在对话中：
1. 直接调用 Skill：`/task-closure`，然后要求执行脚本
2. 或在对话中明确说明："执行 task-closure 的 generate_task_log.py 脚本"

---

## 迁移映射表

| 原 Commands | 新 Scripts | 功能领域 |
|------------|-----------|---------|
| `task_planning/generate-task-plan.md` | `task-planning/scripts/generate_task_plan.py` | 任务管理 |
| `task_closure/generate-task-log.md` + `task_closure/run-optimization-review.md` | `task-closure/scripts/generate_task_log.py` | 任务管理 |
| `testing_and_diagnostics/select-tests.md` + `run-unit-tests.md` + `summarize-test-results.md` | `testing-and-diagnostics/scripts/run_test_workflow.py` | 测试与诊断 |
| `browser_automation/browser-test.md` + `browser-a11y.md` + `browser-visual-regression.md` + `browser-restart-and-test.md` | `testing-and-diagnostics/scripts/run_browser_tests.py` | 测试与诊断 |
| `testing_and_diagnostics/auto-diagnose.md` | `testing-and-diagnostics/scripts/auto_diagnose.py` | 测试与诊断 |
| `browser_automation/browser-edit.md`（包含 browser-start 逻辑） | `frontend-development/scripts/browser_edit.py` | 前端开发 |
| `rule_design/design-rule.md` | `skill-management/scripts/design_skill.py` | 规则管理 |

**删除的命令**：
- `task_closure/run-rule-check.md` - 已删除
- `task_closure/execute-post-hooks.md` - 已删除
- `browser_automation/browser-start.md` - 逻辑已整合到 `browser-edit`

---

## 如何使用 Scripts

**请参考**：`.cursor/skills/README.md` - Skills 索引和使用指南

**核心变化**：
- Scripts 位于对应 Skills 的 `scripts/` 目录
- 调用方式：手动调用（用户主动触发）或自动触发（根据代码变更类型）
- 功能与原 Commands 一致，但按功能领域重新组织

---

## 版本信息

- **最后更新**：2026-01-23
- **版本**：v2.0（迁移到 Skills scripts/）
