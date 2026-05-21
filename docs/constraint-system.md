# 约束体系

三层防线确保文件放置和文档规范：rules 提供软引导，hooks 执行硬拦截，yaml 配置作为单一真相源。

| 文件 | 位置 | 作用 | 加载时机 |
|------|------|------|---------|
| `CLAUDE.md` | 项目根 | 精简入口，@import 引入 rules | 每次会话 |
| `.claude/rules/path-placement.md` | .claude/rules/ | 目录放置规则（zone 白名单） | 每次会话 |
| `.claude/rules/plan-doc-spec.md` | .claude/rules/ | plan 文档结构规范 | 每次会话 |
| `.claude/rules/plan-execution.md` | .claude/rules/ | plan 任务执行流程规则（单任务、自检、自主推进） | 每次会话 |
| `.claude/path-rules.yaml` | .claude/ | hook 读取的机器可读配置 | hook 触发时 |
| `.claude/hooks/validate_path_hook.py` | .claude/hooks/ | PreToolUse：拦截新文件到错误路径 | Write/Edit 时 |
| `.claude/hooks/validate_plan_hook.py` | .claude/hooks/ | PostToolUse：校验 plan 文档结构 | Write 时 |

## 关键行为

- 新文件（Write）必须落入已定义的 zone，否则被 hook 拦截（exit 2）
- 已有文件（Edit）不受约束（历史文件可自由编辑）
- plan 文档（Write）必须包含 7 个 section，否则被 hook 拦截（exit 2）
- 新增 zone 编辑 `.claude/path-rules.yaml`，同时更新 `.claude/rules/path-placement.md`

## 参考

- [Claude Code Rules 文档](https://code.claude.com/docs/zh-CN/memory)
- [Claude Code Hooks 文档](https://code.claude.com/docs/zh-CN/hooks)
