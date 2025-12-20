# 流式输出测试指南

## 概述

本文档说明如何测试真正的流式输出功能，包括 FastAPI 和 Streamlit 两个接口。

## 1. FastAPI 流式接口测试

### 1.1 启动服务

```bash
# 启动 FastAPI 服务
python -m uvicorn src.business.rag_api.main:app --host 0.0.0.0 --port 8000
```

### 1.2 测试流式对话接口

使用 curl 测试：

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是系统科学？",
    "session_id": null
  }' \
  --no-buffer
```

使用 Python 测试：

```python
import requests
import json

url = "http://localhost:8000/chat/stream"
data = {
    "message": "什么是系统科学？",
    "session_id": None
}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            chunk_data = json.loads(line_str[6:])
            print(f"Type: {chunk_data['type']}, Data: {chunk_data.get('data', '')[:50]}...")
```

### 1.3 预期结果

- 应该看到多个 `{'type': 'token', 'data': '...'}` 事件
- 最后应该看到 `{'type': 'sources', 'data': [...]}` 事件
- 如果有推理链，应该看到 `{'type': 'reasoning', 'data': '...'}` 事件
- 最后应该看到 `{'type': 'done', 'data': {...}}` 事件

## 2. Streamlit 流式显示测试

### 2.1 启动 Streamlit 应用

```bash
streamlit run app.py
```

### 2.2 测试步骤

1. 打开浏览器访问 `http://localhost:8501`
2. 在输入框中输入问题，例如："什么是系统科学？"
3. 观察流式输出效果：
   - 应该看到答案逐 token 实时显示
   - 应该看到光标效果（"▌"）在答案末尾
   - 答案完成后，光标应该消失
   - 应该显示引用来源（如果有）
   - 应该显示推理链（如果启用且存在）

### 2.3 预期行为

- **实时性**：答案应该实时显示，不需要等待完整答案生成
- **流畅性**：不应该有明显的延迟或卡顿
- **完整性**：答案、引用来源、推理链都应该正确显示

## 3. 验证要点

### 3.1 流式输出验证

- [ ] FastAPI 接口返回流式事件（token、sources、reasoning、done）
- [ ] Streamlit 界面实时显示答案
- [ ] 没有模拟延迟（不是逐字符输出完整答案）

### 3.2 功能完整性验证

- [ ] 引用来源正确提取和显示
- [ ] 推理链正确提取和显示（如果启用）
- [ ] 会话历史正确更新
- [ ] 错误处理正确（流式过程中出错时）

### 3.3 性能验证

- [ ] 流式输出的实时性（token 延迟 < 100ms）
- [ ] 长文本流式输出的稳定性
- [ ] 多个并发请求的处理能力

## 4. 常见问题

### 4.1 流式输出不工作

**可能原因**：
- DeepSeek API 密钥未设置
- 网络连接问题
- LlamaIndex 版本不兼容

**解决方法**：
- 检查 `.env` 文件中的 `DEEPSEEK_API_KEY`
- 检查网络连接
- 检查日志中的错误信息

### 4.2 推理链未显示

**可能原因**：
- 未使用 `deepseek-reasoner` 模型
- 推理链显示未启用
- API 未返回推理链

**解决方法**：
- 检查 `application.yml` 中的模型配置
- 检查 `DEEPSEEK_ENABLE_REASONING_DISPLAY` 配置
- 检查日志中的推理链提取信息

### 4.3 引用来源为空

**可能原因**：
- 知识库未索引
- 检索策略配置问题
- 相似度阈值过高

**解决方法**：
- 检查知识库索引状态
- 检查检索策略配置
- 调整相似度阈值

## 5. 调试技巧

### 5.1 查看日志

```bash
# 查看流式查询日志
tail -f logs/app.log | grep "流式"
```

### 5.2 检查响应格式

在代码中添加调试输出：

```python
async for chunk in chat_manager.stream_chat(message):
    print(f"Chunk type: {chunk['type']}, Data length: {len(str(chunk.get('data', '')))}")
```

### 5.3 验证 DeepSeek API 调用

检查 `DeepSeekLogger` 的日志输出，确认：
- `stream_chat` 方法被调用
- 流式响应正确接收
- 推理链内容正确提取

## 6. 性能基准

### 6.1 预期性能指标

- **首次 Token 延迟**：< 500ms
- **Token 间隔**：< 100ms
- **完整响应时间**：取决于答案长度和模型响应速度

### 6.2 测试场景

1. **短问题**（< 50 字符）：测试基本流式功能
2. **长问题**（> 200 字符）：测试流式稳定性
3. **多轮对话**：测试会话历史处理
4. **并发请求**：测试系统负载能力

## 7. 测试检查清单

- [ ] FastAPI `/chat/stream` 接口正常工作
- [ ] Streamlit 界面流式显示正常工作
- [ ] 引用来源正确显示
- [ ] 推理链正确显示（如果启用）
- [ ] 会话历史正确更新
- [ ] 错误处理正确
- [ ] 性能满足要求
- [ ] 日志记录完整















