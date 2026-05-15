# Nightshift 实验操作说明

这份说明的目标只有一个：

把 `agent-nightshift` 接到当前仓库后，使用一条较大的研究型任务做一次 6 到 9 小时的夜间自主实验，观察 agent 在有限自主循环下到底能推进到什么程度。

本次实验的北极星文档是：

- `docs/research/harness-engineering/MVP Version/研究型Agent-MVP定义与执行计划.md`

但要注意：

- 这份文档是实验的 `问题空间 + 方向约束 + 北极星计划`。
- 它不是要求 agent 逐条照抄执行的死板规范。
- 本轮实验允许 agent 在边界内对原计划做重组、批判、收敛和实现取舍。

## 你要复制到哪里

如果手动操作，需要把实验说明复制到 GitHub Issue。

仓库里已经准备好一份可直接使用的草稿：

- `docs/research/harness-engineering/MVP Version/nightshift-issue-实验稿.md`

推荐做法：

1. 到 GitHub 仓库创建一个新 Issue。
2. 标题自行命名，例如：
   - `[nightshift] 研究型 Agent MVP 自主探索实验`
3. 将 `nightshift-issue-实验稿.md` 的正文复制到 Issue body。

如果使用仓库自带的 Issue Form 模板，也可以把草稿内容拆到这些字段里：

- `Goal`
- `Current Phase`
- `Done Definition`
- `Constraints`
- `Review Focus`

## 怎么触发

### 方式一：GitHub 网页触发

前提：

- 目标分支已经存在并推送到远程。
- `.github/workflows/nightshift-execute.yml` 已经在该分支上。
- self-hosted runner 在线。

操作步骤：

1. 打开仓库 GitHub 页面。
2. 进入 `Actions`。
3. 选择工作流 `nightshift-execute`。
4. 点击 `Run workflow`。
5. 填入以下参数：
   - `issue_number`: 实验 Issue 编号
   - `push_ref`: 实验分支，例如 `nightshift/exp-research-agent-mvp`
   - `task`: `execute_plan`
   - `time_budget_hours`: `8`
6. 点击运行。

### 方式二：命令行触发

```bash
gh workflow run nightshift-execute.yml \
  --repo qiao-925/Creating-Systematology-RAG \
  --ref nightshift/exp-research-agent-mvp \
  -f issue_number=<ISSUE_NUMBER> \
  -f push_ref=nightshift/exp-research-agent-mvp \
  -f task=execute_plan \
  -f time_budget_hours=8
```

## 运行后会发生什么

`nightshift-execute` 会在 self-hosted runner 上做这些事：

1. checkout `push_ref` 分支
2. 读取 Issue 正文和最近评论
3. 把 Issue 物化成 `.agent/runtime/issue-plan.md`
4. 执行 `.agent/project.yaml` 中定义的 `setup`
5. 运行 `codex exec`
6. 执行 `verify`
7. 如果阶段完成并满足条件，调用 checkpoint
8. 自动触发只读 review worker

## 第二天看什么

主要看 4 个地方：

1. GitHub Actions 日志
2. Issue 中的 checkpoint 评论
3. 实验分支上的提交
4. 自动 review worker 的结果

## 这次实验最该观察什么

不要只看 workflow 最终是绿还是红。

更重要的是看：

1. agent 有没有自己选出一个像样的主攻方向
2. 它有没有在边界内做取舍，而不是无止境扩张
3. 它最后交付的是不是“可继续推进”的工件
4. 它停下来的理由是否合理

## 当前已知限制

当前仓库 baseline verify 还不是完全干净，至少已有一批旧测试仍在 patch `src.*` 路径，可能导致 verify 阶段报错。

这意味着：

- 如果实验最终失败，不一定是 nightshift 机制失败。
- 更可能是 agent 被仓库现有红测或历史债务拦住。
- 所以第二天应同时看“推进质量”和“停止原因”。

## 推荐参数

- `push_ref`: `nightshift/exp-research-agent-mvp`
- `task`: `execute_plan`
- `time_budget_hours`: `8`

这是比较适中的一轮：

- 比 3 小时更能看到自主循环效果
- 又不会像 9 小时那样把第一次实验的观察成本拉得太高

## 简化版结论

如果你只记一件事，就记这个：

1. 把 `nightshift-issue-实验稿.md` 复制到 GitHub Issue
2. 用 `nightshift/exp-research-agent-mvp` 作为实验分支
3. 在 `Actions -> nightshift-execute` 中填 Issue 编号和分支名
4. 跑一晚
5. 第二天看 checkpoint、提交和 review 结果
