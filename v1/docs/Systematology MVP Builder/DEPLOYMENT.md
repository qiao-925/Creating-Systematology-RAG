# 部署指南

> Systematology Agent 的部署架构、环境配置与故障排查。

## 1. 架构概览

单容器双进程架构，部署在 Hugging Face Spaces（免费 Docker 托管）：

```
HF Spaces (Docker, 免费 2vCPU/16GB)
├── Next.js 前端 (standalone, :7860)  ← 对外暴露
│   └── /api/* 代理 → FastAPI
└── FastAPI 后端 (uvicorn, :8000)     ← 内部
    └── DeepSeek API (LLM)
```

- **前端**：Next.js standalone 模式，监听端口 7860，通过 `next.config.ts` 的 rewrite 规则将 `/api/*` 代理到后端
- **后端**：FastAPI + uvicorn，监听端口 8000（容器内部）
- **启动**：`start.sh` 同时启动两个进程，`wait -n` 任一退出即终止容器

## 2. HF Spaces 部署

### 配置

`README.md` 顶部的 YAML frontmatter：

```yaml
---
title: Systematology Agent
emoji: "\U0001F9E0"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---
```

HF Spaces 会自动读取仓库根目录的 `Dockerfile` 进行构建。

### 部署地址

https://peter7310-systematology.hf.space

### 免费额度

- 2 vCPU / 16 GB RAM
- 无持久化存储（容器重启后数据丢失）
- 空闲 48 小时后休眠（首次访问需等待冷启动）

### 环境变量配置

在 HF Spaces 仓库设置（Settings → Variables and secrets）中添加：

| 变量 | 必需 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API 密钥 |
| `HF_TOKEN` | 否 | HuggingFace Token（HF Inference Embedding） |
| `CHROMA_CLOUD_API_KEY` | 否 | Chroma Cloud 向量数据库 |
| `CHROMA_CLOUD_TENANT` | 否 | Chroma Cloud Tenant |
| `CHROMA_CLOUD_DATABASE` | 否 | Chroma Cloud Database |

非必需模块（embedding / chroma / ragas）缺少 key 时静默跳过，不阻塞启动。

## 3. 本地 Docker 开发

```bash
# 构建镜像
docker build -t systematology .

# 运行容器
docker run -p 7860:7860 \
  -e DEEPSEEK_API_KEY=sk-xxx \
  systematology
```

访问 http://localhost:7860 即可。

> 注意：`.dockerignore` 已排除 `.env`、`tests/`、`logs/`、`web/node_modules/` 等文件。

## 4. 本地开发（非 Docker）

```bash
# 安装 Python 依赖
make install

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 启动后端
uvicorn backend.fastapi.main:app --reload --port 8000

# 启动前端（另一个终端）
cd web && npm install && npm run dev
```

前端开发服务器运行在 http://localhost:3000，通过 rewrite 代理 `/api/*` 到后端 8000 端口。

## 5. 环境变量参考

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `DEEPSEEK_API_KEY` | 是 | — | DeepSeek API 密钥（[获取](https://platform.deepseek.com/api_keys)） |
| `HF_TOKEN` | 否 | — | HuggingFace Token（[获取](https://huggingface.co/settings/tokens)） |
| `CHROMA_CLOUD_API_KEY` | 否 | — | Chroma Cloud API 密钥 |
| `CHROMA_CLOUD_TENANT` | 否 | — | Chroma Cloud Tenant |
| `CHROMA_CLOUD_DATABASE` | 否 | — | Chroma Cloud Database |
| `CORS_ORIGINS` | 否 | `*` | CORS 允许的源（逗号分隔） |
| `EMBEDDING_MODEL` | 否 | `BAAI/bge-base-zh-v1.5` | Embedding 模型 |
| `HF_ENDPOINT` | 否 | `https://hf-mirror.com` | HuggingFace 镜像端点 |

## 6. 构建流程详解

Dockerfile 采用两阶段构建：

### Stage 1：前端构建（node:20-slim）

```dockerfile
COPY web/package.json web/package-lock.json ./
RUN npm ci                    # 安装全部依赖
COPY web/ ./
RUN npm run build             # Next.js standalone 构建
RUN npm ci --omit=dev         # 裁剪为生产依赖
```

### Stage 2：运行时（python:3.12-slim）

```dockerfile
RUN useradd -m -u 1000 user   # HF Spaces 要求非 root 用户
RUN pip install uv             # Python 包管理器
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制后端代码
COPY --chown=user backend/ application.yml scripts/ data/ skills/ ./

# 从前端构建产物复制 standalone 输出
COPY --from=frontend-builder /build/web/.next/standalone/web/ web/.next/standalone/
COPY --from=frontend-builder /build/web/.next/static/ web/.next/standalone/.next/static/
COPY --from=frontend-builder /build/web/public/ web/.next/standalone/public/
```

## 7. 故障排查

### 构建失败：package-lock.json 不同步

```
npm ERR! `npm ci` found changes to package-lock.json
```

**解决**：本地重新生成 lock 文件后提交：
```bash
cd web && npm install
```

### 构建失败：Next.js standalone COPY 路径错误

**症状**：容器启动后前端 404 或静态资源缺失。

**原因**：Next.js standalone 输出的实际路径是 `.next/standalone/`，不是 `.next/standalone/web/`。当前 Dockerfile 已正确处理（从 `/build/web/.next/standalone/web/` 复制到 `web/.next/standalone/`）。

### 构建失败：Python 镜像缺少 Node.js

**解决**：使用两阶段构建，Node.js 仅在 Stage 1 安装。当前 Dockerfile 已采用此方案。

### 容器启动失败：/app/logs 权限问题

**解决**：Dockerfile 中已通过 `--chown=user` 确保目录权限。如遇问题，在 Dockerfile 中添加：
```dockerfile
RUN mkdir -p /app/logs && chown user:user /app/logs
```

### 非必需模块缺失

embedding / chroma / ragas 模块在缺少对应环境变量时会静默跳过，不影响核心 Systematology 分析功能。日志中会输出 warning 但不会阻塞启动。

## 8. Zeabur 部署（遗留）

项目保留 `zeabur.json` 作为 Zeabur 平台的部署配置参考。当前主要部署目标是 HF Spaces，Zeabur 配置可能与最新架构不完全同步。

```bash
# Zeabur 部署（如需使用）
# 1. 在 Zeabur 控制台连接 GitHub 仓库
# 2. 配置环境变量（见上方环境变量参考）
# 3. Zeabur 会自动读取 zeabur.json 和 Dockerfile
```
