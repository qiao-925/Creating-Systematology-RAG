# 子计划 D：部署与文档

> 将 Systematology 部署为可访问的 Demo——Docker 多阶段构建、HF Spaces 托管、完整文档。独立于前后端和测试，可并行推进。

## 版本目标

- 做什么：完成 HF Spaces Docker 部署（多阶段构建 + 双进程），输出完整文档（README + ARCHITECTURE + 配置说明）
- 为什么：部署是"代码能跑"到"用户能用"的最后一公里，文档是新用户的入口

### 成功标准

- HF Spaces 可访问：https://peter7310-systematology.hf.space
- Docker 多阶段构建成功
- 新用户按 README 可在 5 分钟内跑通

### 范围

**In Scope**
- Dockerfile 多阶段构建（Node.js + Python）
- start.sh 双进程启动（uvicorn + next start）
- HF Spaces 配置（frontmatter + 环境变量）
- README 快速开始 + 命令参考
- ARCHITECTURE 架构文档
- 配置说明文档

**Out of Scope**
- CI/CD（后续迭代）
- 生产级监控（HF Spaces 自带）
- 多租户与权限系统

## 文档锚定

- 锚定：`Dockerfile` — 多阶段构建配置
- 锚定：`start.sh` — 双进程启动脚本
- 锚定：`README.md` — 用户入口
- 锚定：`ARCHITECTURE.md` — 架构文档
- 同步：`application.yml` — 配置项
- 同步：`pyproject.toml` — 依赖声明

## 决策清单

### 核心决策

- [x] D1 部署平台：HF Spaces（免费 Docker 托管，2vCPU/16GB）
- [x] D2 服务架构：单容器双进程（uvicorn :8000 + next start :7860）
- [x] D3 构建方式：多阶段 Dockerfile（Node.js 构建 + Python 运行时）

### 支撑决策

- [x] D4 非必需模块：embedding/chroma/ragas 缺少 key 时静默跳过，不阻塞启动
- [x] D5 sentence-transformers 预加载：`scripts/preload_models.py` + Makefile 目标

## 任务清单

### 阶段 1：部署配置

- [x] G8 sentence-transformers 预加载
  - 产出：`scripts/preload_models.py` + Makefile 目标
  - 验收：`make preload-models` 后离线可用
  - 失败路径：—

- [x] D6 Dockerfile 多阶段构建
  - 产出：`Dockerfile`（Stage 1: Node.js build → Stage 2: Python runtime + 复制前端产物）
  - 验收：`docker build .` 成功，镜像包含前后端
  - 失败路径：降级 — 单阶段构建

- [x] D7 start.sh 双进程启动
  - 产出：`start.sh`（uvicorn backend.fastapi.main:app :8000 & next start :7860）
  - 验收：两个进程同时运行，前端代理 /api/* 到后端
  - 失败路径：降级 — 只启动后端

- [x] D8 HF Spaces 配置
  - 产出：README.md HF Spaces YAML frontmatter（sdk: docker, app_port: 7860）
  - 验收：HF Spaces 可识别并构建
  - 失败路径：—

### 阶段 2：文档

- [x] G7 README 安装说明
  - 产出：`README.md`（HF Spaces frontmatter + 快速开始 + 命令参考 + 文档导航）
  - 验收：新用户按 README 可在 5 分钟内跑通
  - 失败路径：—

- [x] D9 ARCHITECTURE 更新
  - 产出：`ARCHITECTURE.md`（代码地图、技术栈表、横切关注点）
  - 验收：反映当前代码架构
  - 失败路径：—

- [x] D10 配置说明
  - 产出：`docs/Systematology MVP Builder/CONFIG_SETUP.md`
  - 验收：环境变量和配置项说明完整
  - 失败路径：—

### 阶段 3：产品转型

- [x] D11 RAG → Systematology 产品转型
  - 执行链路：
    1. 技术栈调研 → LiteLLM SDK-only 风险可控，接入 DeepSeek + MiMO + Kimi
    2. 后端迁移 → api/ → fastapi/，business/ → core/，infrastructure/ 保留
    3. 旧系统分解 → 可复用部分沉淀到 infrastructure/，Chat/Research 删除
    4. API 清理 → 移除 Chat/Research router、runtime_config
    5. 文档更新 → README 重写、ARCHITECTURE 更新、pytest/Makefile 同步
  - 产出：63edd1c（673 files changed）
  - 验收：旧系统完全清理，新架构独立运行

### 阶段 4：验证

- [ ] D12 构建验证
  - 产出：`cd web && npm run build` 成功
  - 验收：Next.js standalone build 无错误
  - 失败路径：—

- [ ] D13 端到端验证（需真实 LLM API key）
  - 产出：启动服务 → curl POST /api/systematology/analyze → 收到结构化响应
  - 验收：完整链路跑通
  - 失败路径：记录失败点

## 执行记录

- [x] 05-16 G7-G8 完成，产品转型完成（63edd1c）
- [x] 05-18 HF Spaces 部署完成（Dockerfile, start.sh, frontmatter）
- [x] 05-18 D9-D10 文档完成
- [ ] D12-D13 待验证

### 构建修复记录

1. `package-lock.json` 不同步 → `npm install` 重新生成
2. Next.js standalone COPY 路径错误 → `.next/standalone/`（非 `.next/standalone/web/`）
3. Python 镜像缺 Node.js → 添加 nodesource 安装
4. `/app/logs` 权限问题 → 预创建目录 + chown

### 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | LLM 调用 |
| `HF_TOKEN` | 否 | Embedding（hf-inference 模式） |
| `CHROMA_CLOUD_*` | 否 | 向量数据库 |

### 已知遗留

- `llama-index-llms-openai` / `llama-index-llms-deepseek`：pyproject.toml 中仍存在，已通过 LiteLLM 替代，待删除
- Embedding 方案：HuggingFace Local vs API，暂未启用
- Reranker：SentenceTransformer / BGE，暂未启用

## 附录：AI 自主授权

**授权**：依赖安装 / 文件创建 / 配置修改 / 文档更新
**不授权**：架构决策变更 / 外部 API key 配置 / 删除已有文件或破坏性重构
