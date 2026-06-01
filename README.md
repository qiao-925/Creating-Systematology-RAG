---
title: Systematology Agent
emoji: "\U0001F9E0"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Systematology Agent

> 围绕**动态假设（Dynamic Hypothesis）研究**的 AI Agent 工具链：从文本中提取关键变量与因果关系，构建因果环路图（CLD），进而执行模糊认知图仿真（FCM）与动态杠杆点分析（D2D），服务于复杂系统的因果建模与杠杆分析
---

## 1. 快速开始

**2. 配置 API Keys**

```bash
# 方式一：gh token 自动同步（推荐，需安装 GitHub CLI）
gh auth login
make env-pull                           # 自动拉取并解密 .env

# 方式二：手动配置
cp .env.example .env
# 编辑 .env，填入 API Key（至少一个 LLM 提供商）
```

> 支持的 LLM 提供商（通过 LiteLLM 统一调用）：
> - `DEEPSEEK_API_KEY` — DeepSeek（[获取地址](https://platform.deepseek.com/api_keys)）
> - `MIMO_API_KEY` — 小米 MiMO
> - `KIMI_API_KEY` — Kimi / Moonshot
>
> 至少配置其中一个即可运行。

**3. 安装并启动**
```bash
make              # 安装依赖 + 运行测试
```

**4. 启动前端**
```bash
cd web && npm install && npm run dev   # http://localhost:3000
```

**5. 运行 Systematology 分析**
```bash
curl -X POST http://localhost:8000/api/systematology/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "How do fiscal subsidies affect housing affordability?"}'
```

> 📖 配置详情 → [配置管理指南](docs/CONFIG_SETUP.md)

---

## 2. 常用命令

### 开发与测试

| 命令 | 说明 |
|------|------|
| `make` | 安装依赖 + 运行完整测试 |
| `make run` | 启动前端（cd web && npm run dev） |
| `make start` | 一键启动（安装 + 测试 + 运行） |
| `make dev` | 开发模式（安装 + 快速测试） |
| `make test-unit` | 仅运行单元测试 |
| `make test-fast` | 跳过慢速测试 |

### 密钥管理

| 命令 | 说明 |
|------|------|
| `gh auth login` | 登录 GitHub（前置步骤） |
| `make env-pull` | 从私有 Gist 拉取并解密 `.env` |
| `make env-push` | 加密当前 `.env` 并推送到 Gist |
| `make env-init` | 首次初始化：加密 `.env` → 创建 Gist |
| `make env-example` | 从 `.env.example` 创建模板 |

> 📖 配置详情 → [配置管理指南](docs/CONFIG_SETUP.md)

### Systematology API

| 命令 | 说明 |
|------|------|
| `curl -X POST http://localhost:8000/api/systematology/analyze -d '{"question":"..."}'` | 运行分析 |
| `curl http://localhost:8000/api/systematology/health` | 健康检查 |

### 验证与评估

| 命令 | 说明 |
|------|------|
| `make verify-observability` | 验证可观测性 + 评估体系（真实 API 调用） |
| `make e2e-smoke` | E2E 冒烟测试（1 题快速验证） |
| `make e2e-regression` | E2E 回归测试（多题质量验证） |

---

## 3. 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计](ARCHITECTURE.md) | 工作流程、目录结构、数据统计 |
| [Systematology MVP 计划](docs/Systematology-MVP-plan.md) | CLD → FCM → D2D 分析流水线设计与进度 |
| [Systematology MVP 审查](docs/Systematology-MVP-review.md) | MVP 实现审查报告与后续建议 |
| [配置管理指南](docs/CONFIG_SETUP.md) | gh token 同步、.env 配置、部署场景 |
| [部署指南](docs/DEPLOYMENT.md) | HF Spaces 部署、本地 Docker、环境变量参考 |

---
