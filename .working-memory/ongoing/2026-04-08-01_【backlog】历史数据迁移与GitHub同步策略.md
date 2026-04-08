# 【backlog】历史数据迁移与 GitHub 同步策略

> 一句话目标：完成 263 个历史任务的数据迁移，明确 GitHub 同步边界

## Checkpoint

| CP | 内容 | 状态 |
|----|------|------|
| 1 | 评估历史数据范围与关联 Issue | ⬜ |
| 2 | 确定迁移方案（全量/摘要/渐进） | ⬜ |
| 3 | 执行迁移并进行完整性检查 | ⬜ |
| 4 | 验证新 skill 与 GitHub 双向同步 | ⬜ |

## 当前上下文

- 决策：采用摘要迁移方案（方案 B）
- 阻塞：需确认历史任务中哪些绑定了 GitHub Issue
- 下一动作：扫描 `_DEPRECATED_agent-task-log/` 中的 Issue 关联

## 待讨论问题

1. 263 个归档任务是否需要统计到 board.md「月度归档速览」？ #12
2. 旧系统中是否有进行中的任务绑定了 open 的 GitHub Issue？ #12
3. 新任务何时创建 GitHub Issue？（自动/手动/按需） #12

---
*Issue: #12 | Created: 2026-04-08 | Updated: 2026-04-08 | Source: working-memory-boost*
