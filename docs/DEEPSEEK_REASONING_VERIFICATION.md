# DeepSeek 推理链多轮对话验证文档

## 验证目标

确保在多轮对话中，`reasoning_content` 不会被传递到下一轮对话的 `messages` 中，符合 DeepSeek API 要求。

## 验证点

### 1. ChatMessage 结构验证

**验证内容**：`ChatMessage` 对象只包含 `role` 和 `content` 字段，不包含 `reasoning_content`。

**验证位置**：
- `src/chat/manager.py:158-159` - `load_session()` 方法
- `src/chat/manager.py:213-215` - `add_turn()` 方法

**验证结果**：
- ✅ `ChatMessage` 构造函数只接受 `role` 和 `content` 参数
- ✅ `memory.put()` 只传递 `ChatMessage(role=MessageRole.USER, content=turn.question)`
- ✅ `turn.answer` 中不包含 `reasoning_content`（推理链已提取并分离）

**代码位置**：
```python
# src/chat/manager.py:158-159
self.memory.put(ChatMessage(role=MessageRole.USER, content=turn.question))
self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=turn.answer))
```

### 2. ChatMemoryBuffer 验证

**验证内容**：`ChatMemoryBuffer` 只存储 `role` 和 `content`，不存储 `reasoning_content`。

**验证位置**：
- `src/chat/manager.py:89-91` - `ChatMemoryBuffer` 初始化
- `src/chat/manager.py:158-159` - `memory.put()` 调用

**验证结果**：
- ✅ `ChatMemoryBuffer` 内部使用 `ChatMessage` 对象
- ✅ `ChatMessage` 只包含 `role` 和 `content`
- ✅ `reasoning_content` 存储在 `ChatTurn.reasoning_content` 中，不进入 `memory`

### 3. DeepSeekLogger 消息过滤验证

**验证内容**：`DeepSeekLogger` 在调用 API 前过滤 `reasoning_content`。

**验证位置**：
- `src/llms/deepseek_logger.py:139-143` - `_chat_with_logging()` 方法
- `src/llms/deepseek_logger.py:256-262` - `_stream_chat_with_logging()` 方法
- `src/llms/reasoning.py:98-140` - `clean_messages_for_api()` 函数

**验证结果**：
- ✅ `clean_messages_for_api()` 函数确保只传递 `role` 和 `content`
- ✅ 在 `chat()` 和 `stream_chat()` 方法中都应用了消息清理
- ✅ 如果消息包含 `reasoning_content`，会被自动移除

**代码位置**：
```python
# src/llms/deepseek_logger.py:139-143
cleaned_messages = clean_messages_for_api(messages)
response = self._llm.chat(cleaned_messages, **kwargs)
```

### 4. 推理链提取与存储验证

**验证内容**：`reasoning_content` 被正确提取，但不进入对话历史。

**验证位置**：
- `src/chat/manager.py:179` - `extract_reasoning_content()` 调用
- `src/chat/manager.py:210-215` - 推理链存储逻辑

**验证结果**：
- ✅ `reasoning_content` 从响应中提取
- ✅ 只存储 `answer` 到 `memory`，不存储 `reasoning_content`
- ✅ `reasoning_content` 可选存储到 `ChatTurn`（根据配置）

**代码位置**：
```python
# src/chat/manager.py:179
reasoning_content = extract_reasoning_content(response)

# src/chat/manager.py:210-215
store_reasoning = config.DEEPSEEK_STORE_REASONING if reasoning_content else False
if store_reasoning:
    self.current_session.add_turn(message, answer, sources, reasoning_content)
else:
    self.current_session.add_turn(message, answer, sources)
```

### 5. 会话加载验证

**验证内容**：加载历史会话时，只恢复 `role` 和 `content`，不恢复 `reasoning_content`。

**验证位置**：
- `src/chat/manager.py:151-161` - `load_session()` 方法
- `src/chat/session.py:67-84` - `ChatTurn.add_turn()` 方法

**验证结果**：
- ✅ `load_session()` 只恢复 `turn.question` 和 `turn.answer`
- ✅ `turn.reasoning_content`（如果存在）不会被恢复到 `memory`
- ✅ 向后兼容：旧会话文件可能不包含 `reasoning_content`

**代码位置**：
```python
# src/chat/manager.py:157-159
for turn in self.current_session.history:
    self.memory.put(ChatMessage(role=MessageRole.USER, content=turn.question))
    self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=turn.answer))
```

## 验证结论

### ✅ 已验证的安全机制

1. **ChatMessage 结构安全**：`ChatMessage` 只包含 `role` 和 `content`，不包含 `reasoning_content`
2. **ChatMemoryBuffer 安全**：`ChatMemoryBuffer` 内部只存储 `ChatMessage` 对象，不包含 `reasoning_content`
3. **DeepSeekLogger 过滤**：在 API 调用前自动过滤 `reasoning_content`，双重保险
4. **推理链分离**：`reasoning_content` 被提取并分离，不进入对话历史

### ✅ 符合 DeepSeek API 要求

根据 DeepSeek API 文档，多轮对话时：
- ✅ 只传递 `role` 和 `content` 到 `messages`
- ✅ `reasoning_content` 不包含在 `messages` 中
- ✅ `reasoning_content` 从响应中提取，但不用于下一轮对话

## 测试建议

### 手动测试场景

1. **多轮对话测试**：
   - 发起第一轮对话，检查是否有 `reasoning_content`
   - 发起第二轮对话，检查 API 请求的 `messages` 是否包含 `reasoning_content`
   - 检查日志，确认 `reasoning_content` 被正确过滤

2. **会话加载测试**：
   - 保存包含 `reasoning_content` 的会话
   - 加载会话，检查 `memory` 中是否包含 `reasoning_content`
   - 发起新对话，检查 API 请求是否包含 `reasoning_content`

3. **配置测试**：
   - 启用/禁用推理链存储
   - 启用/禁用推理链显示
   - 验证配置生效

### 单元测试场景

1. 测试 `clean_messages_for_api()` 函数
2. 测试 `ChatMessage` 结构
3. 测试 `ChatMemoryBuffer` 存储逻辑
4. 测试 `load_session()` 恢复逻辑

## 相关代码文件

- `src/chat/manager.py` - 对话管理器，多轮对话核心逻辑
- `src/chat/session.py` - 会话数据结构
- `src/llms/deepseek_logger.py` - API 调用日志和消息过滤
- `src/llms/reasoning.py` - 推理链处理工具函数
- `src/llms/factory.py` - LLM 工厂函数

## 更新日期

2025-11-04

