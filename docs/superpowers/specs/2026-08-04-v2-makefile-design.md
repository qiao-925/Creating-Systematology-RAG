# V2 Makefile 设计（2026-08-04）

> 对应 GitHub issue #28 三个方向的第一个落地项：Make 封装。为 V2（Wayfinding）根目录重写，v1 的 Makefile 保留在 `v1/` 只读。

## 决策

V2 Makefile 重写为**三块结构**，每块一个主命令，全部英文描述：

| 主命令 | 内容 | 说明 |
|--------|------|------|
| `make run` | 依赖安装 + 前后端启动 | 默认目标（`.DEFAULT_GOAL := run`），自包含，不拆子目标 |
| `make test` | 全量测试 + 覆盖率报告 | `uv run pytest --cov=backend` |
| `make clean` | 清理缓存 + 依赖本体 | 删 `.venv` / `web/node_modules` + 项目内缓存 |

**辅助项已删除**：`env-example` 与 `help` 不保留；env 配置（`cp .env.example .env`）由 README 说明，Makefile 不再负责。

## 关键实现

- **`make run` 并行启动**：方案 A — trap 内联。`(cd web && npm run dev) &` 前端(:3000) 后台，`uv run uvicorn backend.fastapi.main:app --reload` 后端(:8000) 前台；`trap 'kill 0' INT TERM` 保证 Ctrl-C 一起收掉前后端。零额外文件。
- **`make test`**：`uv run pytest`（uv 默认自动 sync，缺依赖自动装）+ `--cov-report=term-missing` 终端覆盖率。
- **`make clean` 范围**：项目本地依赖（`.venv`、`web/node_modules`）+ 项目内缓存（`__pycache__`、`.pytest_cache`、`htmlcov`、`.coverage`、`web/.next`）。**不动全局 uv/npm 缓存**（跨项目共享）。

## 假设与后续

- 后端启动命令 `uv run uvicorn backend.fastapi.main:app --reload` 基于 v1 栈假设，V2 后端落地后可能微调。
- 依赖 `web/` 目录（Next.js）尚未创建，`make run` 需等目录落地后可用。
- 测试目录 `tests/` 与 `backend/` 同样待 V2 创建。

## 相对 v1 的删除清单

- Gist 加密三件套：`env-init` / `env-push` / `env-pull`（issue #28 第 3 节：砍加密）
- 组合目标：`all` / `ready` / `start` / `dev`（统一由自包含 `run` 承担）
- 细粒度测试目标：`test-unit` / `test-integration` / `test-github-e2e` / `test-cov` / `test-fast` / `e2e-smoke` / `e2e-regression` / `verify-observability`（统一由 `test` 承担）
- `install` / `install-test` / `preload-models` / `help` / `env-example`
