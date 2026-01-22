# AI Agent 任务日志

> AI Agent 执行任务的完整记录，支持 Plan + Checkpoint 工作流。

---

## 目录结构

| 目录/文件 | 说明 |
|-----------|------|
| [ongoing/](ongoing/) | 进行中的任务（计划书或执行中的日志） |
| [archive/](archive/) | 已归档（按月份组织） |
| [TASK_TYPES.md](TASK_TYPES.md) | 任务类型定义 |
| [PLAN_TEMPLATE.md](PLAN_TEMPLATE.md) | 计划书模板 |

---

## 工作流

### 完整流程（长程任务）

```
Plan 阶段              Execution 阶段           Closure 阶段
     │                      │                       │
     ▼                      ▼                       ▼
/generate-task-plan    按 CP 执行            /generate-task-log
     │                 更新 CP 状态                 │
     ▼                      │                       ▼
ongoing/xxx.md  ─────────────────────────>  archive/YYYY-MM/
```

### 简化流程（简单任务）

```
Execute → /generate-task-log → archive/
```

---

## 任务类型

参见 [TASK_TYPES.md](TASK_TYPES.md) 了解任务类型定义。

**关键类型**：
- `plan`：规划类任务，使用 Checkpoint 机制

---

## 命名规范

```
YYYY-MM-DD-N_【task_type】任务名称-文档类型.md
```

- `YYYY-MM-DD`: 日期
- `N`: 当日序号
- `task_type`: 任务类型（plan/implementation/refactor/bugfix 等）
- `文档类型`: 实施计划/完成总结/快速摘要等

---

## Plan + Checkpoint 机制

### 何时使用

| 复杂度 | 特征 | 处理方式 |
|--------|------|----------|
| 简单 | 1-2 步 | 直接执行 |
| 中等 | 3-5 步 | 建议创建计划书 |
| 复杂 | >5 步 | **必须**创建计划书 |

### 计划书结构

1. **Checkpoint 状态表**（核心）
2. 背景与目标
3. 技术方案
4. 实施步骤（含验收标准）
5. 风险与注意事项
6. 文件改动清单

### 状态标记

| 标记 | 含义 |
|------|------|
| ⬜ | 待开始 |
| 🔄 | 进行中 |
| ✅ | 已完成 |
| ⏸️ | 暂停 |
| ❌ | 取消 |

---

## 相关命令

| 命令 | 用途 |
|------|------|
| `/generate-task-plan` | 创建计划书（Plan 阶段） |
| `/generate-task-log` | 生成完成总结（Closure 阶段） |

---

## 相关规则

- `task_planning_guidelines.mdc`：任务规划规范
- `task_closure_guidelines.mdc`：任务收尾规范

---

**最后更新**: 2026-01-22
