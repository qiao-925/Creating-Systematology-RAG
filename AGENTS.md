# AGENTS.md

此文档用于构建执行 Agent 的全局地图理解。

## 文档地图

```
ARCHITECTURE.md                   ← 架构设计（工作流 + 技术栈 + 目录结构 + 数据统计）
README.md                         ← 项目说明 + 快速开始 + CLDFlow 使用指南
AGENTS.md                         ← 本文件：Agent 全局地图

docs/
├── decision-log.md               ← 决策日志（每次核心任务的资产变更记录，只增不改）
├── CLDFlow-MVP-plan.md           ← CLDFlow 可执行计划书（T1-T20 + G1-G8，全部完成）
├── CLDFlow-MVP-review.md         ← CLDFlow MVP 审查报告
├── CONFIG_SETUP.md               ← 配置管理指南（gh token 同步 + .env 说明）
├── KeyDecision-list.md           ← 关键决策记录（D1-D12）
├── references/                   ← 设计参考库（外部模式借鉴）
└── research with brainstorm/     ← 研究与头脑风暴材料（论文 + 架构设计）
```

## 约束体系

三层防线确保文件放置和文档规范：rules 提供软引导，hooks 执行硬拦截，yaml 配置作为单一真相源。

| 文件 | 位置 | 作用 | 加载时机 |
|------|------|------|---------|
| `CLAUDE.md` | 项目根 | 精简入口，@import 引入 rules | 每次会话 |
| `.claude/rules/path-placement.md` | .claude/rules/ | 目录放置规则（zone 白名单） | 每次会话 |
| `.claude/rules/plan-doc-spec.md` | .claude/rules/ | plan 文档结构规范 | 每次会话 |
| `.claude/path-rules.yaml` | .claude/ | hook 读取的机器可读配置 | hook 触发时 |
| `.claude/hooks/validate_path_hook.py` | .claude/hooks/ | PreToolUse：拦截新文件到错误路径 | Write/Edit 时 |
| `.claude/hooks/validate_plan_hook.py` | .claude/hooks/ | PostToolUse：校验 plan 文档结构 | Write 时 |

**关键行为**：
- 新文件（Write）必须落入已定义的 zone，否则被 hook 拦截（exit 2）
- 已有文件（Edit）不受约束（历史文件可自由编辑）
- 新增 zone 编辑 `.claude/path-rules.yaml`，同时更新 `.claude/rules/path-placement.md`
- 详细参考：[Claude Code Rules 文档](https://code.claude.com/docs/zh-CN/memory)、[Hooks 文档](https://code.claude.com/docs/zh-CN/hooks)

