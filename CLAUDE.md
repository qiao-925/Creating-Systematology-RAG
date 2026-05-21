# CLAUDE.md

@.claude/rules/plan-doc-spec.md
@.claude/rules/path-placement.md
@.claude/rules/plan-execution.md

## 文档地图
项目全局文档索引与约束体系概览见 [AGENTS.md](AGENTS.md)。

## 跨端同步
Claude Code 全局配置（settings、skills、plugins、memory、会话历史）通过专用仓库 `dev-sync` 同步。
仓库地址：https://github.com/qiao-925/dev-sync（私有）
新机器首次使用时 clone 该仓库并运行 `setup.sh`（Linux）或 `setup.cmd`（Windows）。
