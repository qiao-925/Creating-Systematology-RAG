---
name: refactor-and-decompose
description: 重构与分解约束的汇聚入口，规划时约定文件边界、收尾时执行结构检查。不新增阶段，与 file-size-limit、single-responsibility 配合使用。
---

# 重构与分解

> 规划时约定模块边界，收尾前强制结构检查，避免代理把功能塞进少数大文件形成技术债务。

---

## 何时使用

- **规划时**：编写或审核计划书中的「文件改动清单」，确保每文件有职责与行数预算（≤300）
- **收尾时**：执行结构检查（再收尾），通过后再生成任务日志与六维分析

---

## 依赖

- `file-size-limit`：单文件 ≤300 行
- `single-responsibility`：文件/函数/模块职责清晰、无循环依赖
- `architecture-design`：架构变更时按需引用

---

## 检查清单

| 项 | 要求 |
|----|------|
| 行数 | 本任务涉及的代码文件均 ≤300 行 |
| 职责 | 每文件一句话可描述、无循环依赖 |
| 边界 | 计划书文件清单含「职责 + 行数预算」 |

---

## 参考资料

- `task-planning/references/planning-workflow.md` - 文件清单格式
- `task-closure/references/closure-workflow.md` - 收尾前结构检查步骤
