# 跨层 - Conductor编排机制

> 架构概览见：`docs/CLDFlow-architecture.md`
> 默认参数见：`docs/CLDFlow-defaults.md` 跨层/全局

---

## 调度模式

| 层 | 模式 | 说明 |
|----|------|------|
| CLD提取 | 全并行 | Agent独立，无依赖 |
| CLD融合 | 串行 | 归并→冲突→裁判，有顺序 |
| FCM评级 | 全并行 | 各Agent独立评级 |
| FCM聚合+仿真 | 串行 | 先聚合再仿真 |
| D2D | 串行 | 逐节点扰动+仿真 |

---

## 编排框架

Phase 1：自定义轻量编排器（状态机）

Phase 2：迁移到 LlamaIndex AgentWorkflow（冻结原则）

---

## 状态机

```
INIT → INPUT_ENHANCE → CLD_EXTRACT → CLD_MERGE → CLD_CONFLICT → CLD_REVIEW
→ FCM_RATE → FCM_AGGREGATE → FCM_SIMULATE → FCM_REVIEW
→ D2D_SENSITIVITY → D2D_UNCERTAINTY → D2D_REVIEW
→ OUTPUT → DONE
```

每步必须通过自审（不变量I-7）才进入下一步（不变量I-3：流水线不可拆）。

---

## 失败处理

- 单步失败：重试最多3次（可调）
- 重试耗尽：标记失败+记录原因，不进入下游
- 运行隔离（不变量I-6）：不依赖前次运行残留状态

---

*整合自 issue-15-sub_docs: 18-conductor-orchestration.md*
