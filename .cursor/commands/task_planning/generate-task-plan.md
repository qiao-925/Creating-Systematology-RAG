# /generate-task-plan

## 1. Command Summary

- 目的：为长程任务创建符合规范的计划书，包含 Checkpoint 状态表和验收标准
- 触发时机：通常在 AI 与用户讨论后发起，任务评估为复杂（>=3 步）
- 关联规则：`task_planning_guidelines.mdc`
- 模板参考：`agent-task-log/PLAN_TEMPLATE.md`

## 2. 执行步骤

1. **从上下文提取任务信息**：
   - 总结对话中已讨论的任务目标、边界、技术方案
   - 识别已达成的共识和待确认的点
   - **仅在上下文不足时**才向用户询问补充信息

2. **规划 Checkpoint**：
   - 基于讨论内容，将任务拆分为 3-8 个独立阶段
   - 每个 CP 应是可独立交付的单元
   - 定义验收标准（可与用户协商调整）

3. **生成计划书**：
   - 命名：`YYYY-MM-DD-N_【plan】任务名称-实施计划.md`
   - 位置：`agent-task-log/ongoing/`
   - 内容：按 `PLAN_TEMPLATE.md` 填充，整合对话中的决策

4. **确认与调整**：
   - 展示 Checkpoint 划分，邀请用户反馈
   - 根据反馈调整后正式开始执行

## 3. 输出

- 计划书文件路径
- Checkpoint 状态表摘要
- 下一步行动建议

## 4. 关联命令

- `/generate-task-log`：任务完成后生成完成总结并归档
