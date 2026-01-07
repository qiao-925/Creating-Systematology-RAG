# LlamaDebugHandler 全量信息清单

## 📋 可提取的信息列表

### 1. 基础统计信息
- [x] **事件总数** (`events_count`) - 查询执行过程中的事件数量
- [x] **LLM调用次数** (`llm_calls`) - LLM API调用次数
- [x] **检索调用次数** (`retrieval_calls`) - 检索操作次数
- [x] **Token使用量** (`total_tokens`) - 总Token消耗（如果可用）
- [x] **答案长度** (`answer_length`) - 生成答案的字符数
- [x] **引用来源数** (`sources_count`) - 检索到的文档数量

### 2. 查询和答案信息
- [x] **查询内容** (`query`) - 用户输入的原始查询
- [x] **答案内容** (`answer`) - 生成的完整答案（可截断）
- [x] **答案预览** (`answer_preview`) - 答案的前N个字符

### 3. 引用来源详情
- [x] **来源文本** (`sources[].text`) - 每个来源的文本内容
- [x] **相似度分数** (`sources[].score`) - 每个来源的相似度分数
- [x] **来源元数据** (`sources[].metadata`) - 来源的元数据（文件名、位置等）
- [x] **来源ID** (`sources[].id`) - 来源的唯一标识符

### 4. 事件对信息
- [x] **事件对列表** (`event_pairs`) - 所有事件对的列表
- [x] **开始事件** (`event_pairs[].start_event`) - 事件开始的详细信息
- [x] **结束事件** (`event_pairs[].end_event`) - 事件结束的详细信息
- [x] **事件类型** (`event_pairs[].event_type`) - 事件类型（LLM、RETRIEVE、CHUNKING等）
- [x] **事件时间戳** (`event_pairs[].timestamp`) - 事件发生的时间
- [x] **事件持续时间** (`event_pairs[].duration`) - 事件执行耗时（如果可用）

### 5. 事件类型统计
- [x] **所有事件类型** (`event_types`) - 出现过的所有事件类型列表
- [x] **事件类型计数** (`event_type_counts`) - 每种事件类型的数量

### 6. LLM相关详细信息
- [x] **LLM Prompt** (`llm_prompts`) - 发送给LLM的完整Prompt
- [x] **LLM响应** (`llm_responses`) - LLM返回的完整响应
- [ ] **LLM模型名称** (`llm_model`) - 使用的LLM模型（需要从配置中获取）
- [ ] **LLM参数** (`llm_params`) - LLM调用参数（temperature、max_tokens等）
- [x] **Prompt Token数** (`prompt_tokens`) - Prompt消耗的Token数
- [x] **Completion Token数** (`completion_tokens`) - 生成消耗的Token数
- [x] **LLM调用耗时** (`llm_latency`) - 每次LLM调用的耗时（通过stage_times计算）

### 7. 检索相关详细信息
- [x] **检索查询** (`retrieval_queries`) - 用于检索的查询文本
- [ ] **检索策略** (`retrieval_strategy`) - 使用的检索策略（需要从配置中获取）
- [x] **检索到的节点** (`retrieved_nodes`) - 检索到的所有节点详情
- [ ] **节点相似度分数** (`node_scores`) - 每个节点的相似度分数（需要从节点中提取）
- [x] **检索耗时** (`retrieval_latency`) - 检索操作耗时（通过stage_times计算）
- [ ] **Top K值** (`top_k`) - 检索返回的Top K值（需要从配置中获取）

### 8. 节点和文档信息
- [ ] **节点ID列表** (`node_ids`) - 所有节点的ID
- [ ] **节点文本** (`node_texts`) - 所有节点的文本内容
- [ ] **节点元数据** (`node_metadata`) - 所有节点的元数据
- [ ] **文档ID** (`document_ids`) - 文档的唯一标识符
- [ ] **文档路径** (`document_paths`) - 文档的文件路径

### 9. 性能指标
- [x] **总耗时** (`total_time`) - 查询执行总耗时
- [x] **检索阶段耗时** (`retrieval_time`) - 检索阶段耗时（通过stage_times计算）
- [x] **生成阶段耗时** (`generation_time`) - 答案生成阶段耗时（通过stage_times计算）
- [x] **各阶段耗时明细** (`stage_times`) - 每个阶段的详细耗时

### 10. 错误和警告
- [ ] **错误信息** (`errors`) - 执行过程中的错误
- [ ] **警告信息** (`warnings`) - 执行过程中的警告
- [ ] **异常堆栈** (`exception_traceback`) - 异常堆栈信息

### 11. 上下文信息
- [ ] **使用的索引** (`index_name`) - 使用的向量索引名称
- [ ] **Embedding模型** (`embedding_model`) - 使用的Embedding模型
- [ ] **查询改写结果** (`rewritten_query`) - 查询改写后的文本（如果有）
- [ ] **查询意图** (`query_intent`) - 查询意图分析结果（如果有）

### 12. 事件Payload详情
- [ ] **事件Payload** (`event_payloads`) - 每个事件的完整Payload
- [ ] **Formatted Prompt** (`formatted_prompts`) - 格式化后的Prompt
- [ ] **Messages** (`messages`) - LLM消息列表
- [ ] **Response** (`responses`) - LLM响应对象

## 🔍 事件类型枚举（CBEventType）

根据 LlamaIndex 文档，常见的事件类型包括：

- `LLM` - LLM调用事件
- `RETRIEVE` - 检索事件
- `EMBEDDING` - Embedding生成事件
- `CHUNKING` - 文档分块事件
- `NODE_PARSING` - 节点解析事件
- `QUERY` - 查询事件
- `SYNTHESIZE` - 合成/生成事件
- `TREE` - 树结构事件
- `SUB_QUESTION` - 子问题事件

## 📝 使用建议

1. **基础调试**：选择 1-3 项（基础统计、查询答案、引用来源）
2. **详细分析**：选择 1-6 项（包含LLM和检索详情）
3. **性能优化**：选择 1, 9 项（统计信息和性能指标）
4. **问题诊断**：选择 1-6, 10 项（包含错误信息）

## 🎯 当前实现状态

### ✅ 已实现的信息（最新版本）

**基础统计信息**：
- ✅ 事件总数、LLM调用次数、检索调用次数
- ✅ Token使用量（total/prompt/completion）
- ✅ 答案长度、引用来源数

**查询和答案**：
- ✅ 查询内容、答案内容（可截断）

**引用来源**：
- ✅ 来源文本、相似度分数、元数据、ID

**事件对信息**：
- ✅ 事件类型、开始/结束事件、Payload详情、时间戳、持续时间

**事件类型统计**：
- ✅ 所有事件类型列表、事件类型计数

**LLM详细信息**：
- ✅ LLM Prompts（前5个）
- ✅ LLM Responses（前5个）
- ✅ Prompt/Completion Token数
- ✅ LLM调用耗时（通过stage_times）

**检索详细信息**：
- ✅ 检索查询（前5个）
- ✅ 检索到的节点（前5个）
- ✅ 检索耗时（通过stage_times）

**性能指标**：
- ✅ 总耗时、各阶段耗时明细

### ⚠️ 需要从配置或其他来源获取的信息

- ⚠️ LLM模型名称（需要从LLM配置中获取）
- ⚠️ LLM参数（temperature等，需要从LLM配置中获取）
- ⚠️ 检索策略（需要从查询引擎配置中获取）
- ⚠️ Top K值（需要从查询引擎配置中获取）
- ⚠️ 错误和警告（需要捕获异常）

### 📊 数据提取统计

- **事件对**: 保存前20个
- **来源**: 保存前10个
- **LLM Prompts**: 保存前5个
- **LLM Responses**: 保存前5个
- **检索查询**: 保存前5个
- **检索节点**: 保存前5个

