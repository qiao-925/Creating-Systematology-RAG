# 配置管理指南

> 本项目的配置分为两层：静态配置（`application.yml`）和敏感配置（`.env`）。
> 静态配置直接 commit 到仓库，敏感配置通过加密 Gist 同步或手动填写。

## 快速开始

### 方式一：gh token 自动同步（推荐）

```bash
gh auth login                           # 登录 GitHub
make env-pull                           # 自动拉取并解密 .env
```

首次使用需要已有的 `.env` 初始化 Gist：

```bash
# 如果已有 .env（如从其他机器迁移）
make env-init                           # 加密并推送到私有 Gist

# 如果是全新环境，无 .env
cp .env.example .env                    # 复制模板
# 编辑 .env，填入你的 API keys
```

### 方式二：手动配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API keys
```

## 环境变量说明

| 变量 | 必需 | 用途 | 获取地址 |
|------|------|------|----------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek LLM API | https://platform.deepseek.com/api_keys |
| `CHROMA_CLOUD_API_KEY` | 否 | Chroma Cloud 向量数据库 | https://www.trychroma.com |
| `CHROMA_CLOUD_TENANT` | 否 | Chroma Cloud 租户 ID | 同上 |
| `CHROMA_CLOUD_DATABASE` | 否 | Chroma Cloud 数据库名 | 同上 |
| `HF_TOKEN` | 否 | HuggingFace Inference API | https://huggingface.co/settings/tokens |
| `RERANK_MODEL` | 否 | 自定义重排序模型路径 | — |

## 加密同步机制

### 工作原理

```
gh auth token → PBKDF2 派生密钥 → AES-XOR 加密 .env → 存入私有 Gist
```

- 加密密钥从 `gh auth token` 实时派生，无需记忆或存储 passphrase
- 加密后的 blob 存储在私有 GitHub Gist 中（ID 记录在 `.env.remote`）
- `.env.remote` 是公开的（只有 Gist ID，不含密钥），`.env` 被 `.gitignore` 忽略

### 常用命令

| 命令 | 说明 |
|------|------|
| `make env-pull` | 从 Gist 拉取并解密 `.env` |
| `make env-push` | 加密当前 `.env` 并推送到 Gist |
| `make env-init` | 首次初始化：加密 `.env` → 创建 Gist |
| `make env-example` | 从 `.env.example` 创建 `.env` 模板 |

### 跨机器同步流程

```
机器 A（已有 .env）          机器 B（新环境）
─────────────────           ─────────────────
make env-push               gh auth login
  → 加密上传到 Gist           make env-pull
                              → 自动解密到 .env
```

### 优先级

配置加载顺序（从高到低）：

1. **系统环境变量** — CI/CD、生产部署场景，直接注入
2. **`.env` 文件** — 本地开发，`load_dotenv()` 加载
3. **gh token 自动拉取** — `.env` 不存在时，尝试从 Gist 解密

## 部署场景

### GitHub Actions

在仓库 Settings → Secrets and variables → Actions 中配置：

```yaml
# .github/workflows/deploy.yml
env:
  DEEPSEEK_API_KEY: ${{ secrets.DEPSEEK_API_KEY }}
```

### Docker

```bash
docker run -e DEEPSEEK_API_KEY=sk-xxx myapp
```

### 云平台（Vercel / Railway / Zeabur）

在平台的环境变量设置中添加 `DEEPSEEK_API_KEY` 等变量。

## 常见问题

### gh 未登录

```
ERROR: gh not authenticated. Run: gh auth login
```

解决：运行 `gh auth login`，按提示完成 GitHub OAuth 授权。

### Gist 不存在

```
ERROR: Not initialized. Run: python scripts/env_sync.py init
```

解决：先用 `make env-init` 初始化 Gist，或手动创建 `.env`。

### 解密失败

```
Decryption failed: wrong token or corrupted data
```

原因：当前 `gh auth token` 和加密时使用的 token 不同（换了 GitHub 账号）。

解决：在原账号的机器上 `make env-push`，或手动创建 `.env`。
