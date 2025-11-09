# /execute-post-hooks

- 目的：一键执行任务收尾流程，包括日志、优化分析与规则校验。
- 触发时机：确认进入收尾流程且希望自动化执行全流程时。
- 关联规则：`task_closure_guidelines.mdc`
- 依赖命令：`/generate-task-log`、`/run-optimization-review`、`/run-rule-check`

## 2. 输入
- 必需：任务基本信息（类型、名称、背景）、测试结果、关键产出。
- 可选：额外附件、需要特别说明的风险或遗留问题。

## 3. 执行步骤
1. 调用 `/generate-task-log`，生成任务日志并获取文件路径。
2. 在日志中继续执行 `/run-optimization-review`，完成优化分析段落。
3. 最后执行 `/run-rule-check`，补充规则执行校验信息。
4. 汇总三个步骤的输出，向用户确认结果或进一步行动。

## 4. 输出
- 任务日志文件路径（含优化分析、规则校验）。
- 流程执行摘要（成功/失败及原因）。

