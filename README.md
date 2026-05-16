# CLDFlow Agent

> 将系统动力学（CLD / FCM / D2D）编码为工具链的 AI Agent，用于复杂系统的因果建模与杠杆分析
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

**5. 运行 CLDFlow 分析**
```bash
curl -X POST http://localhost:8000/api/cldflow/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "How do fiscal subsidies affect housing affordability?"}'
```

> 📖 配置详情 → [配置管理指南](docs/CONFIG_SETUP.md)

---

## 2. 技术栈

#### 系统级

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.12 | 类型提示、match statement |
| 包管理 | uv | 快速依赖管理 |
| 前端 | Next.js / React | CLDFlow 分析界面 |
| Web 框架 | FastAPI | REST API + SSE 流式响应 |
| 配置 | Pydantic + YAML + .env | 类型安全配置 |

#### RAG 与 Agent

| 类别 | 技术 | 说明 |
|------|------|------|
| Agent 框架 | LlamaIndex | ReActAgent + AgentWorkflow |
| LLM 网关 | **LiteLLM** | 统一多模型接口，屏蔽提供商差异 |
| LLM 模型 | DeepSeek / MiMO / Kimi | 通过 LiteLLM 统一调用，可热切换 |
| 结构化输出 | Instructor | JSON Schema 强制输出 |
| 向量存储 | Chroma Cloud | 云端托管，无需本地部署 |
| Embedding | HuggingFace Local / API | 可插拔（暂未启用，待确定方案） |
| 重排序 | SentenceTransformer / BGE | 可插拔（暂未启用） |

#### CLDFlow 因果分析

| 类别 | 技术 | 用途 |
|------|------|------|
| 图操作 | NetworkX | CLD 构建、环检测、入度分析 |
| FCM 仿真 | NumPy | Kosko 矩阵迭代、收敛判断 |
| 节点归并 | Sentence Transformer (MiniLM-L6-v2) | 余弦相似度归并 |
| 生成模型 | DeepSeek / MiMO（via LiteLLM） | Specialist Agent |
| 评估模型 | Kimi / DeepSeek（via LiteLLM） | Evaluator / Judge |
| 数据验证 | Pydantic strict mode | 层间边界校验 |

#### 可观测性

| 类别 | 技术 | 说明 |
|------|------|------|
| 日志 | structlog | 结构化追踪 |
| 调试 | LlamaIndex Observers | 事件追踪 |
| 评估 | RAGAS（可选） | 多维度质量评估 |

---

## 3. 常用命令

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

### CLDFlow API

| 命令 | 说明 |
|------|------|
| `curl -X POST http://localhost:8000/api/cldflow/analyze -d '{"question":"..."}'` | 运行分析 |
| `curl http://localhost:8000/api/cldflow/health` | 健康检查 |

### 验证与评估

| 命令 | 说明 |
|------|------|
| `make verify-observability` | 验证可观测性 + 评估体系（真实 API 调用） |
| `make e2e-smoke` | E2E 冒烟测试（1 题快速验证） |
| `make e2e-regression` | E2E 回归测试（多题质量验证） |

---

## 4. 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计](ARCHITECTURE.md) | 工作流程、目录结构、数据统计 |
| [CLDFlow MVP 计划](docs/CLDFlow-MVP-plan.md) | CLD → FCM → D2D 分析流水线设计与进度 |
| [CLDFlow MVP 审查](docs/CLDFlow-MVP-review.md) | MVP 实现审查报告与后续建议 |
| [配置管理指南](docs/CONFIG_SETUP.md) | gh token 同步、.env 配置、部署场景 |

---
