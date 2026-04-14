# 2026-01-22 【implementation】Prompt优化与模型适配层实现-完成总结

## 1. 任务概述

| 字段 | 内容 |
|------|------|
| 任务类型 | implementation |
| 开始时间 | 2026-01-22 |
| 完成状态 | ✅ 已完成 |
| 关联任务 | LiteLLM 统一接口集成（前置） |

### 1.1 任务目标

1. **Prompt 优化**：基于 Anthropic/OpenAI/DeepSeek 官方最佳实践，优化现有 prompt 模板
2. **模型适配层实现**：根据模型类型（通用/推理）自动适配消息格式

### 1.2 背景

- LiteLLM 集成完成后，支持多模型切换
- 不同模型类型对 prompt 格式有不同要求：
  - 通用模型（GPT-4o, DeepSeek-Chat）：支持 system + user 分开
  - 推理模型（o1, DeepSeek-Reasoner）：官方建议避免 system prompt

---

## 2. 关键决策

### 2.1 Prompt 优化方案

通过交互式讨论确定：

| 决策点 | 选择 |
|--------|------|
| 结构方案 | 4-Block XML 重构 + Few-Shot 示例 |
| 失败模式 | 坦诚说明 + 基于通用知识给出参考方向 |
| 风格量化 | 保持灵活，信任模型判断 |
| 输出格式 | 结构化 JSON（便于程序解析） |

### 2.2 模型适配方案

| 决策点 | 选择 |
|--------|------|
| 维护策略 | 一套 prompt 内容 + 代码层适配 |
| 适配依据 | `model_config.supports_reasoning` 字段 |
| 消息格式 | 通用模型: [SYSTEM, USER]；推理模型: [USER] |

---

## 3. 实施内容

### 3.1 Prompt 优化（3 个文件）

| 文件 | 优化内容 |
|------|---------|
| `prompts/rag/chat.txt` | XML 4-Block 结构 + 失败模式处理 + 回答示例 |
| `prompts/query/rewrite.txt` | XML 分块 + 独立约束块 + 2 个 few-shot 示例 |
| `prompts/agentic/planning.txt` | 结构化 JSON 输出 + 决策规则 + 3 个场景示例 |

### 3.2 模型适配层实现

#### 3.2.1 新增文件

`backend/infrastructure/llms/message_builder.py`：

```python
def build_chat_messages(
    system_prompt: str,
    user_query: str,
    model_id: Optional[str] = None,
) -> List[ChatMessage]:
    """根据模型类型组装消息列表"""
    # 判断是否为推理模型
    is_reasoning = model_config.supports_reasoning if model_config else False
    
    if is_reasoning:
        # 推理模型：全部放入 user
        return [ChatMessage(role=MessageRole.USER, content=f"{system_prompt}\n\n{user_query}")]
    else:
        # 通用模型：system + user 分开
        return [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_query)
        ]
```

#### 3.2.2 修改文件

| 文件 | 修改内容 |
|------|---------|
| `backend/business/rag_api/fastapi_routers/chat.py` | 使用 `build_chat_messages()` 组装消息 |
| `backend/business/rag_engine/core/engine_streaming.py` | 使用 `build_chat_messages()` 组装消息 |
| `backend/infrastructure/llms/__init__.py` | 导出 `build_chat_messages`, `is_reasoning_model` |

---

## 4. 测试验证

### 4.1 模块功能测试

```bash
uv run python -c "
from backend.infrastructure.llms.message_builder import build_chat_messages, is_reasoning_model
..."
```

### 4.2 测试结果

| 测试项 | 结果 |
|--------|------|
| 通用模型消息组装 | ✅ 2条消息 [SYSTEM + USER] |
| 推理模型消息组装 | ✅ 1条消息 [USER only] |
| `is_reasoning_model()` 判断 | ✅ deepseek-chat=False, deepseek-reasoner=True |
| Linter 检查 | ✅ 无错误 |

---

## 5. 交付成果

### 5.1 文件清单

**新增：**
- `backend/infrastructure/llms/message_builder.py`

**修改：**
- `prompts/rag/chat.txt`
- `prompts/query/rewrite.txt`
- `prompts/agentic/planning.txt`
- `prompts/README.md`
- `backend/business/rag_api/fastapi_routers/chat.py`
- `backend/business/rag_engine/core/engine_streaming.py`
- `backend/infrastructure/llms/__init__.py`

### 5.2 适配逻辑图

```
模型类型判断 (supports_reasoning)
        │
        ├── False (通用模型: deepseek-chat, GPT-4o)
        │   └── [SYSTEM, USER] 分开
        │
        └── True (推理模型: deepseek-reasoner, o1)
            └── [USER] 合并
```

---

## 6. 参考资料

- [Anthropic Claude 4 Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)
- [OpenAI Prompt Engineering](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
- [DeepSeek R1 Prompting Guidelines](https://deepwiki.com/deepseek-ai/DeepSeek-R1/3.3-prompting-guidelines)

---

## 7. 后续建议

1. **效果验证**：用实际查询对比优化前后的回答质量
2. **示例迭代**：根据实际 bad case 补充 few-shot 示例
3. **监控**：关注 JSON 输出的格式稳定性
