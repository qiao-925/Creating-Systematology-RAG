---
name: self-test-trigger
description: 代码修改后由 AI 自行触发运行相关测试，新功能或修 bug 时按约定补充或更新测试用例。适用于用户请求「跑测试」「验证一下」或 Agent 完成 backend/frontend/tests 变更后的验证。
---

# AI 自测触发规范

> 改完就跑、缺测就补：在代码变更后主动运行相关测试，在实现新功能或修 bug 时按规定补充用例。

---

## ⚠️ 核心强制要求

### 何时触发

- 用户明确请求「跑测试」「验证一下」「跑下用例」等。
- Agent 完成对 `backend/`、`frontend/` 或 `tests/` 的代码修改后，需要验证时。

### 代码变更后：主动运行相关测试

- **后端变更**（`backend/**`）→ 运行 `make test-unit` 和/或 `make test-integration`；可按变更范围缩小到具体目录或文件，例如 `pytest tests/unit/...`、`pytest tests/integration/...`。
- **前端变更**（`frontend/**`）→ 若有 UI 测试则运行对应用例（如 `tests/ui/`）；否则可跑 `make test-unit` 做回归。
- **全栈或不确定** → 先 `make test-unit`，再视情况 `make test-integration`。

### 新功能或修 bug：补充或更新测试用例

- 按 [tests/README.md](../../tests/README.md) 的约定**补充或更新测试用例**。
- **通过标准与场景由人指定**；AI 负责编写/修改测试代码并运行。
- 遵循 tests/ 下 README 与 conftest、fixtures 约定，不发明新位置或新风格。

---

## AI Agent 行为要求

### 选择运行范围

- 根据变更路径选择：仅 unit、仅 integration、或两者。
- 必要时使用 `pytest tests/unit/...` 或 `pytest tests/integration/...` 缩小范围，缩短反馈时间。

### 汇报结果

- 运行后**汇报结果**：通过/失败、失败用例与错误摘要。
- 失败时建议修复或提示人类介入，不得在未修复或未说明的情况下报完成。

### 补充用例时

- 单元测试放 [tests/unit/](../../tests/unit/)，集成测试放 [tests/integration/](../../tests/integration/)；命名与结构见各子目录 README。
- 优先使用 [tests/conftest.py](../../tests/conftest.py) 与 [tests/fixtures/](../../tests/fixtures/) 的 fixture。

### 与 testing-and-diagnostics 的配合

- 本 Skill 执行「改完就跑、缺测就补」的轻量流程，不强制创建 TEST_*.md。
- 当用户或任务明确要求「正式测试任务、记录、诊断」时，使用或结合 [testing-and-diagnostics](../testing-and-diagnostics/SKILL.md)（创建 TEST_*.md、完整诊断流程）。

---

## 参考资料

- [tests/README.md](../../tests/README.md) - 测试分层、命令、如何添加用例
- [tests/unit/README.md](../../tests/unit/README.md) - 单元测试规范
- [tests/integration/README.md](../../tests/integration/README.md) - 集成测试规范
