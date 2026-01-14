# Agentic RAG 实现问题与注意事项

## 已知问题

### 1. 结果提取逻辑（简化实现）

**位置**：`backend/business/rag_engine/agentic/extraction.py`

**问题**：
- `extract_sources_from_agent()` 和 `extract_reasoning_from_agent()` 是简化实现
- 当前实现尝试从响应对象直接提取，但 ReActAgent.chat() 返回的对象可能不直接包含这些信息
- 实际需要从 Agent 的工具调用历史中提取 sources

**影响**：
- 可能无法正确提取引用来源（sources）
- 可能无法提取推理链（reasoning）

**建议**：
- 需要访问 Agent 的内部状态（如 `agent.chat_history` 或工具调用历史）
- 从工具调用结果中提取 source_nodes
- 参考 LlamaIndex 文档了解 ReActAgent 的返回结构

### 2. 流式查询实现（降级版本）

**位置**：`backend/business/rag_engine/agentic/engine.py` 的 `stream_query()` 方法

**问题**：
- 当前实现是降级版本，不是真正的流式输出
- 先执行完整查询，然后逐字符 yield，不是实时流式

**影响**：
- 用户体验：流式效果是模拟的，不是真正的实时流式
- 性能：需要等待完整查询完成才能开始显示

**建议**：
- 后续版本需要实现真正的流式输出
- 需要支持 Agent 的流式响应

### 3. 成本控制未完全实现

**位置**：`backend/business/rag_engine/agentic/engine.py` 的 `max_llm_calls` 参数

**问题**：
- `max_llm_calls` 参数已定义（默认35次），但没有实际的跟踪逻辑
- 当前仅通过 `max_iterations` 间接控制（默认5次）

**影响**：
- 无法精确控制 LLM 调用次数
- 可能超出预期的成本限制

**建议**：
- 实现 LLM 调用次数跟踪
- 包装 LLM 实例，在每次调用时计数
- 超出限制时立即停止

## 潜在问题

### 4. Agent 返回结果类型不确定

**问题**：
- ReActAgent.chat() 的返回类型可能因 LlamaIndex 版本而异
- 当前使用 `str(response)` 提取答案，可能不是最佳方式

**建议**：
- 运行时测试确认返回类型
- 根据实际返回结构调整提取逻辑

### 5. 工具调用历史访问

**问题**：
- 需要从 Agent 的工具调用历史中提取 sources
- 当前实现可能无法访问这些信息

**建议**：
- 检查 ReActAgent 是否提供工具调用历史访问接口
- 可能需要使用回调或事件监听器来捕获工具调用结果

## 已修复的问题

1. ✅ RAGService 的 chat_manager 初始化缺少 `use_agentic_rag` 参数
2. ✅ AgenticQueryEngine 缺少 `stream_query` 方法（已添加降级版本）
3. ✅ 未使用的导入（`get_response_synthesizer`, `asyncio`）
4. ✅ AgenticQueryEngine 缺少 `handle_fallback` 调用（已添加，与 ModularQueryEngine 保持一致）
5. ✅ trace_info 在降级场景下的 retrieval_time 字段可能缺失（已修复，添加了安全检查）

## 代码质量

- ✅ 所有文件 ≤ 300 行
- ✅ 无 linter 错误
- ✅ 类型提示完整
- ✅ 接口与 ModularQueryEngine 一致

## 建议的测试重点

1. **功能测试**：
   - 验证 Agent 能够正确选择检索策略
   - 验证工具调用正常工作
   - 验证降级策略有效

2. **结果提取测试**：
   - 验证 sources 提取是否正确
   - 验证 reasoning 提取是否正确
   - 测试不同查询场景下的结果格式

3. **错误处理测试**：
   - 测试超时处理
   - 测试降级策略
   - 测试异常恢复

4. **API 兼容性测试**：
   - 验证返回格式与 ModularQueryEngine 一致
   - 验证接口完全兼容

