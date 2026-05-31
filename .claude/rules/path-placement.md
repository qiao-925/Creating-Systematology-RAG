# 目录放置规则

新文件必须放入对应的模块目录。PreToolUse hook 会强制校验。

## Zone 一览

| Zone | 目录 | 内容类型 |
|------|------|---------|
| Backend | `backend/` | Python：FastAPI、core 逻辑、infrastructure、prompts |
| Backend tests | `tests/` | 后端单元/集成测试 |
| Frontend source | `web/src/` | TypeScript、React 组件、hooks、stores、CSS |
| Frontend config | `web/` 根 | next.config.ts、package.json、tsconfig.json |
| Integration/E2E tests | `tests/` | 跨系统集成和 E2E 测试 |
| Documentation | `docs/` | Markdown 文档、计划、研究笔记 |
| Scripts | `scripts/` | 工具和运维脚本 |
| Skills | `skills/` | Claude Code skill 定义 |
| Root config | 项目根 | pyproject.toml、Makefile、Dockerfile、README.md 等 |

## 硬性规则

- Python 文件只能放在 `backend/` 或 `scripts/`
- TypeScript/CSS 文件只能放在 `web/`
- 测试文件只能放在 `tests/`
- 文档只能放在 `docs/`
- 根目录新文件必须在 `path-rules.yaml` 的 `root_files` 白名单中

## 新增 Zone

编辑 `.claude/path-rules.yaml` 添加新 zone 和 patterns。
