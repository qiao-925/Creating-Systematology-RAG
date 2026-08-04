# V2 LLM 统一 + 配置架构设计（2026-08-04）

> 对应 GitHub issue #28 的三个方向之二（LLM 统一）与之三（env 配置），经调研后定稿。

## 决策

### 1. LLM 统一：沿用 LiteLLM + 模型 ID 配置化（v1 已实现，无需新设计）

调研结论：统一接入本地（Ollama）、单模型 API key（DeepSeek/OpenAI 等）、HF 托管三类来源的主流范式是 **LiteLLM 模型名前缀**（`ollama/`、`deepseek/`、`huggingface/`），v1 的 `factory.py` + `LLMModelConfig` 已是该范式。V2 **沿用**，只补 3 个微改动：

1. `LLMModelConfig` 增加可选 `api_base` 字段（Ollama / HF 端点需要）
2. `api_key_env` 改为可选（Ollama 为 `null` 时不传 api_key，不再 raise）
3. `get_default_llm_id()` 增加 `LLM_MODEL_ID` 环境变量覆盖（换模型只改配置）

### 2. 配置架构：yaml 唯一 + Doppler 注入，彻底删除 env 概念

| 层 | 内容 | 进 git |
|----|------|--------|
| `application.yml` | 唯一配置文件：静态配置 + 模型注册表 + `api_key_env` 引用环境变量名 | ✅ |
| **Doppler** | secrets/环境覆盖真相源，`doppler run` 注入 | — |
| `.env` / `.env.example` / python-dotenv | **全部删除** | ❌ |

- 用户决策：**无 `.env`、无 `.env.example`、纯 `doppler run`**（无离线 `.env` 兜底路径）
- 不引入 `${ENV}` 占位符展开——v1 的 `api_key_env` + `os.getenv()` 已是「yaml 引用环境变量名、值来自环境」的形态

### 3. Doppler 集成

- **本地开发**：`make run`/`make test` 后端用 `doppler run` 包装；代码 `os.getenv` 零改动
- **HF Spaces 部署**（无 Doppler 原生集成）：Dockerfile 装 Doppler CLI → HF Secrets 存 `DOPPLER_TOKEN`（service token）→ 启动命令 `doppler run -- ./start.sh`
- **一次性设置**：`doppler login` + `doppler setup --project wayfinding --config dev`（交互式，用户本人执行）；`.doppler.yaml`（无 secrets）建议提交

## 模型注册表（application.yml 已预置）

```yaml
model:
  llms:
    default: deepseek-chat        # 被 env LLM_MODEL_ID 覆盖
    available:
      - { id: deepseek-chat,    litellm_model: deepseek/deepseek-chat,       api_key_env: DEEPSEEK_API_KEY }
      - { id: deepseek-reasoner, litellm_model: deepseek/deepseek-reasoner,  api_key_env: DEEPSEEK_API_KEY, supports_reasoning: true }
      - { id: ollama-llama3,    litellm_model: ollama/llama3,               api_base: http://localhost:11434, api_key_env: null }
      - { id: hf-endpoint,      litellm_model: huggingface/<org>/<model>,    api_base: https://<endpoint>.endpoints.huggingface.cloud, api_key_env: HF_TOKEN }
```

三类来源任选其一，改 `LLM_MODEL_ID` 零代码切换。

## 排除项（调研后明确不做）

- **不引入配置中心**（Apollo/Nacos）：需自建服务，单应用规模不匹配；对比过 Infisical/Doppler，选 Doppler（Python SDK 需求不成立，`doppler run` 即注入，官方 Python SDK `doppler-sdk` 是 secrets 管理 API 非运行时注入）
- **不搞自动降级**（key 缺失切 Ollama）：静默换模型质量不可控，key 缺失应明确报错
- **不用 Gist 加密同步**：issue #28 已决定砍掉；Doppler 取代该需求

## 落地清单（V2 骨架期）

- [x] 根 Makefile：`run`/`test` 用 `doppler run` 包装后端
- [x] 根 `application.yml`：yaml 唯一配置 + 三类模型注册表
- [x] `.gitignore`：删除 `.env`/`*.env.local` 条目
- [x] README：Quick Start 改为 Doppler 流程
- [ ] V2 后端代码 3 微改动（见「决策 1」）
- [ ] HF Spaces：Dockerfile 装 CLI + `DOPPLER_TOKEN` + `doppler run` 启动
