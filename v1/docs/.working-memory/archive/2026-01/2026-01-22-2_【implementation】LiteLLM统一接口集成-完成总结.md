# 2026-01-22 【implementation】LiteLLM统一接口集成-完成总结

## 1. 任务概述

| 字段 | 内容 |
|------|------|
| 任务类型 | implementation |
| 触发方式 | 用户请求 |
| 目标 | 集成 LiteLLM 统一接口，支持多模型并存和前端动态切换 |

## 2. 需求背景

**用户需求**：
- 不是简单的系统级模型切换，而是支持多模型并存
- 前端提供选择器，用户可随时切换模型（类似 Cursor 的模型选择体验）
- 后续扩展模型（如 Qwen）更方便

**技术选型**：
- 选择 LiteLLM 作为统一接口（支持 100+ 模型）
- 使用 `llama-index-llms-litellm` 与 LlamaIndex 集成
- 保持向后兼容，不影响现有代码

## 3. 关键步骤

### 3.1 配置层：多模型定义

**实施内容**：
1. 在 `application.yml` 中定义多模型配置结构
2. 在 `models.py` 中新增 `LLMModelConfig` 和 `LLMModelsConfig` 模型
3. 在 `settings.py` 中实现配置访问方法：
   - `get_default_llm_id()`：获取默认模型 ID
   - `get_available_llm_models()`：获取所有可用模型列表
   - `get_llm_model_config(model_id)`：根据模型 ID 获取配置

**配置示例**：
```yaml
model:
  llms:
    default: deepseek-chat
    available:
      - id: deepseek-chat
        name: DeepSeek Chat
        litellm_model: deepseek/deepseek-chat
        api_key_env: DEEPSEEK_API_KEY
        temperature: 0.7
        max_tokens: 4096
        supports_reasoning: false
```

### 3.2 工厂函数重构

**文件**：`backend/infrastructure/llms/factory.py`

**实施内容**：
1. 新增 `create_llm(model_id)` 函数（推荐使用）
2. 新增 `get_available_models()` 函数（供前端使用）
3. 新增 `get_model_info(model_id)` 函数（获取模型信息）
4. 保留向后兼容接口：`create_deepseek_llm_for_query()`, `create_deepseek_llm_for_structure()`

**核心实现**：
- 通过 LiteLLM 统一接口创建 LLM 实例
- 自动从配置读取 API Key、temperature、max_tokens 等参数
- 支持推理模型的特殊处理（temperature 参数忽略）

### 3.3 日志包装器改造

**文件**：`backend/infrastructure/llms/deepseek_logger.py`

**实施内容**：
1. 将 `DeepSeekLogger` 重命名为 `LLMLogger`（通用日志包装器）
2. 支持任意 LlamaIndex LLM 实例（不再局限于 DeepSeek）
3. 保留所有日志记录功能（请求、响应、推理链）
4. 保留向后兼容：`wrap_deepseek()` 仍可用

### 3.4 前端：模型选择器

**文件**：`frontend/components/sidebar.py`

**实施内容**：
1. 新增 `_render_model_selector()` 函数
2. 在侧边栏显示模型选择下拉框
3. 切换模型时更新 `session_state.selected_model`
4. 显示模型特性提示（如"支持推理链"）

### 3.5 状态管理

**文件**：`frontend/utils/state.py`

**实施内容**：
- 在 `init_session_state()` 中初始化 `selected_model` 状态
- 默认使用 `config.get_default_llm_id()`

### 3.6 业务层适配

**修改文件**：
- `backend/business/chat/manager.py`：支持 `model_id` 参数
- `backend/business/rag_api/rag_service.py`：支持 `model_id` 参数
- `backend/infrastructure/initialization/registry.py`：从 `session_state` 读取模型选择
- `frontend/components/chat_input_with_mode.py`：传入当前选择的模型

## 4. 交付结果

### 4.1 新增依赖

- `llama-index-llms-litellm>=0.6.0`（已添加到 `pyproject.toml`）

### 4.2 修改文件

| 文件 | 改动 |
|------|------|
| `pyproject.toml` | 添加 `llama-index-llms-litellm` 依赖 |
| `application.yml` | 新增多模型配置（`model.llms`） |
| `backend/infrastructure/config/models.py` | 新增 `LLMModelConfig`, `LLMModelsConfig` |
| `backend/infrastructure/config/settings.py` | 新增多模型配置访问方法 |
| `backend/infrastructure/llms/factory.py` | 重构为多模型工厂，新增 `create_llm()` |
| `backend/infrastructure/llms/deepseek_logger.py` | 改造为通用 `LLMLogger` |
| `backend/infrastructure/llms/__init__.py` | 更新导出（新增接口 + 向后兼容） |
| `frontend/components/sidebar.py` | 新增模型选择器组件 |
| `frontend/utils/state.py` | 新增模型选择状态管理 |
| `backend/business/chat/manager.py` | 支持 `model_id` 参数 |
| `backend/business/rag_api/rag_service.py` | 支持 `model_id` 参数 |
| `backend/infrastructure/initialization/registry.py` | 从 `session_state` 读取模型选择 |
| `frontend/components/chat_input_with_mode.py` | 传入当前选择的模型 |

### 4.3 配置示例

当前配置了 2 个模型：
- `deepseek-chat`：DeepSeek Chat（默认）
- `deepseek-reasoner`：DeepSeek Reasoner（支持推理链）

预留了 Qwen、GPT-4o 等模型的配置模板（已注释）

## 5. 技术要点

### 5.1 统一接口设计

```python
from backend.infrastructure.llms import create_llm, get_available_models

# 创建 LLM 实例
llm = create_llm(model_id="deepseek-chat")

# 获取可用模型列表
models = get_available_models()
```

### 5.2 向后兼容

- 保留所有旧接口（`create_deepseek_llm_for_query` 等）
- 旧代码无需修改即可继续工作
- 新代码推荐使用 `create_llm(model_id)`

### 5.3 模型切换机制

- **作用域**：会话级别（切换后，当前会话的后续消息用新模型）
- **状态管理**：通过 `session_state.selected_model` 保存
- **特性提示**：切换时提示模型是否支持推理链

## 6. 测试验证

### 6.1 导入测试

```bash
✅ 导入成功
✅ 可用模型数量: 2
✅ 默认模型: deepseek-chat
```

### 6.2 配置测试

```bash
✅ 默认模型 ID: deepseek-chat
✅ 模型配置找到: DeepSeek Chat
   LiteLLM 模型: deepseek/deepseek-chat
✅ 所有检查通过
```

### 6.3 应用启动测试

- ✅ `make run` 成功启动，无错误
- ✅ Streamlit 应用在 `http://localhost:8501` 正常运行
- ✅ 语法检查通过
- ✅ Linter 检查通过

## 7. 设计决策

| 决策点 | 选择 | 说明 |
|--------|------|------|
| 模型切换作用域 | 会话级别 | 切换后，当前会话的后续消息用新模型 |
| 特性降级策略 | 提示用户 | 切换时提示"该模型不支持推理链"等 |
| 成本/限流 | 不考虑 | 研究项目，假设配置正确 |
| 向后兼容 | 完全兼容 | 保留所有旧接口，旧代码无需修改 |

## 8. 后续建议

### 8.1 扩展模型

在 `application.yml` 中取消注释并配置：
- Qwen Plus（需要 `DASHSCOPE_API_KEY`）
- GPT-4o（需要 `OPENAI_API_KEY`）
- Claude 3.5 Sonnet（需要 `ANTHROPIC_API_KEY`）

### 8.2 功能增强

- [ ] 添加模型切换时的成本提示
- [ ] 添加模型性能对比功能
- [ ] 支持模型参数自定义（temperature、max_tokens 等）

### 8.3 优化建议

- [ ] 考虑添加模型缓存机制（避免频繁创建实例）
- [ ] 考虑添加模型健康检查（API Key 验证）
- [ ] 考虑添加模型使用统计

## 9. 遗留问题

无

## 10. 相关文件

- 实施方案：`.cursor/plans/集成_litellm_统一接口_2911cd1f.plan.md`
- 配置参考：`application.yml`（`model.llms` 部分）
- API 文档：https://docs.litellm.ai/
