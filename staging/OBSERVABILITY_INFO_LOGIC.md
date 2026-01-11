# 可观测性信息逻辑说明文档

> 本文档详细说明页面显示的可观测性信息的逻辑、数据来源和含义

**创建时间**: 2026-01-11  
**版本**: v1.0  
**状态**: 📋 文档草案

---

## 1. 概述

页面按执行流程显示两类可观测性信息：
- **LlamaDebug 调试信息**：6个阶段，展示查询执行的详细过程
- **RAGAS 评估信息**：4个阶段，展示RAG系统质量评估结果

---

## 2. LlamaDebug 调试信息（6个阶段）

### 2.1 📝 阶段1：查询阶段

**数据来源**：`LlamaDebugObserver.on_query_end()` 收集的查询基础信息

**显示内容**：
- **查询内容** (`query`)：用户输入的原始查询文本
- **事件总数** (`events_count`)：本次查询过程中发生的所有回调事件总数
- **LLM调用** (`llm_calls`)：调用大语言模型的次数（统计事件类型中包含 'llm' 的事件）
- **检索调用** (`retrieval_calls`)：调用检索/向量搜索的次数（统计事件类型中包含 'retrieval' 或 'retrieve' 的事件）
- **总耗时** (`total_time`)：查询执行总耗时（所有阶段耗时之和）
- **事件类型统计** (`event_type_counts`)：每种事件类型的数量统计
  - 例如：`CBEventType.LLM: 2` 表示有2个LLM调用事件
  - 例如：`CBEventType.TEMPLATING: 1` 表示有1个模板处理事件

**数据逻辑**：
- 从 `LlamaDebugHandler.get_event_pairs()` 获取事件对列表
- 遍历事件对，统计事件类型和调用次数
- 计算各阶段耗时总和

---

### 2.2 🔍 阶段2：检索阶段

**数据来源**：从事件对的 Payload 中提取检索相关信息

**显示内容**：
- **检索调用次数** (`retrieval_calls`)：检索操作的次数
- **检索耗时** (`retrieval_time`)：检索阶段总耗时（从 `stage_times` 中筛选包含 'retriev' 的事件耗时）
- **引用来源数** (`sources_count`)：检索到的文档/节点数量
- **检索查询** (`retrieval_queries`)：用于检索的查询文本列表（最多显示5个）
  - 从事件 Payload 中提取包含 'query' 且事件类型为 'retrieval' 的字段
- **检索到的节点** (`retrieved_nodes`)：检索到的节点详情列表（最多显示5个）
  - 从事件 Payload 中提取包含 'node' 或 'chunk' 的字段
- **引用来源详情** (`sources`)：每个来源的详细信息（最多显示10个）
  - `text`：来源文本（截断到200字符）
  - `score`：相似度分数
  - `metadata`：来源元数据（文件名、位置等）
  - `id`：来源的唯一标识符

**数据逻辑**：
- 从事件 Payload 中提取检索相关字段
- 从 `sources` 参数中提取来源信息
- 按相似度排序（如果有）

---

### 2.3 🤖 阶段3：LLM调用阶段

**数据来源**：从事件对的 Payload 中提取 LLM 相关信息

**显示内容**：
- **LLM调用次数** (`llm_calls`)：LLM API 调用次数
- **Prompt Tokens** (`prompt_tokens`)：Prompt 消耗的 Token 数
- **Completion Tokens** (`completion_tokens`)：生成消耗的 Token 数
- **Total Tokens** (`total_tokens`)：总 Token 消耗
- **LLM调用总耗时** (`llm_time`)：LLM 调用总耗时（从 `stage_times` 中筛选包含 'llm' 的事件耗时）
- **LLM Prompts** (`llm_prompts`)：发送给 LLM 的完整 Prompt 列表（最多显示5个）
  - 从事件 Payload 中提取包含 'prompt' 或 'formatted_prompt' 的字段
- **LLM Responses** (`llm_responses`)：LLM 返回的完整响应列表（最多显示5个）
  - 从事件 Payload 中提取包含 'response' 或 'message' 的字段

**数据逻辑**：
- 遍历事件对，识别 LLM 类型事件
- 从 Payload 中提取 Token 信息（包含 'token' 的字段）
- 从 Payload 中提取 Prompt 和 Response 文本
- 累计 Token 使用量

---

### 2.4 ✨ 阶段4：生成阶段

**数据来源**：查询结果和事件统计

**显示内容**：
- **答案长度** (`answer_length`)：生成答案的字符数
- **生成耗时** (`generation_time`)：答案生成阶段耗时（从 `stage_times` 中筛选包含 'synthesize' 或 'generate' 的事件耗时）
- **答案预览** (`answer`)：生成的完整答案（截断到500字符）

**数据逻辑**：
- 从 `answer` 参数获取答案文本
- 计算答案长度
- 从事件耗时中筛选生成相关事件

---

### 2.5 ⏱️ 阶段5：性能指标

**数据来源**：事件对的时间戳计算

**显示内容**：
- **各阶段耗时明细** (`stage_times`)：每个事件类型的详细耗时
  - 格式：`事件类型: 耗时（秒）`
  - 按耗时从高到低排序

**数据逻辑**：
- 遍历事件对，计算每个事件的持续时间（结束时间 - 开始时间）
- 按事件类型分组累计耗时
- 排序显示

---

### 2.6 🔍 阶段6：事件详情

**数据来源**：完整的事件对信息

**显示内容**：
- **事件对详情** (`event_pairs`)：所有事件对的完整信息（最多显示20个）
  - **事件类型** (`event_type`)：事件类型（如 LLM、RETRIEVE、TEMPLATING 等）
  - **持续时间** (`duration`)：事件执行耗时
  - **开始事件** (`start_event`)：事件开始的详细信息（截断到500字符）
  - **开始时间** (`start_time`)：事件开始的时间戳
  - **结束事件** (`end_event`)：事件结束的详细信息（截断到500字符）
  - **结束时间** (`end_time`)：事件结束的时间戳
  - **Payload详情** (`payload`)：事件的完整 Payload（包含所有字段）

**数据逻辑**：
- 从 `LlamaDebugHandler.get_event_pairs()` 获取事件对
- 提取每个事件对的详细信息
- 计算时间差得到持续时间
- 提取 Payload 中的所有字段

---

## 3. RAGAS 评估信息（4个阶段）

### 3.1 📥 阶段1：数据收集阶段

**数据来源**：`RAGASEvaluator.on_query_end()` 收集的评估数据

**显示内容**：
- **状态** (`pending_evaluation`)：评估状态（⏳ 待评估 / ✅ 已评估）
- **答案长度** (`answer_length`)：生成答案的字符数
- **上下文数** (`contexts_count`)：用于评估的上下文数量
- **来源数** (`sources_count`)：检索到的来源数量
- **收集时间** (`timestamp`)：数据收集的时间戳
- **查询内容** (`query`)：用户输入的查询文本
- **答案内容** (`answer`)：生成的完整答案
- **上下文数据** (`contexts`)：所有上下文的文本列表（最多显示10个，每个截断到500字符）
- **来源详情** (`sources`)：每个来源的详细信息（最多显示10个）
  - `text`：来源文本（截断到200字符）
  - `score`：相似度分数
  - `metadata`：来源元数据
- **Ground Truth** (`ground_truth`)：真值答案（如果有）
- **Trace ID** (`trace_id`)：追踪标识符

**数据逻辑**：
- 从 `sources` 参数中提取上下文文本
- 保存查询、答案、上下文、来源等评估所需数据
- 存储到 `session_state.ragas_logs` 供前端显示

---

### 3.2 📊 阶段2：批量评估状态

**数据来源**：`session_state.ragas_logs` 中的评估状态

**显示内容**：
- **总记录数**：所有收集的评估记录总数
- **待评估**：标记为 `pending_evaluation=True` 的记录数
- **已评估**：已完成评估的记录数
- **批量评估进度**：待评估记录数 / 批量大小（默认10）
- **评估队列信息**：当前记录在队列中的位置
- **评估时间** (`evaluation_timestamp`)：评估完成的时间戳（如果已评估）

**数据逻辑**：
- 统计 `session_state.ragas_logs` 中的记录状态
- 计算批量评估进度（达到 `batch_size` 时自动触发评估）
- 显示评估队列信息

---

### 3.3 📈 阶段3：评估指标详情

**数据来源**：RAGAS 评估结果（`evaluation_result`）

**显示内容**：
- **评估指标概览**：所有评估指标的评分（最多显示5个）
  - **faithfulness**（忠实度）：答案是否忠实于上下文
  - **context_precision**（上下文精确度）：检索到的上下文是否精确
  - **context_recall**（上下文召回率）：是否检索到所有相关上下文
  - **answer_relevancy**（答案相关性）：答案是否与查询相关
  - **context_relevancy**（上下文相关性）：上下文是否与查询相关
- **指标评分**：每个指标的数值（0-1之间）
  - 🟢 ≥0.8：优秀
  - 🟡 ≥0.6：良好
  - 🔴 <0.6：需改进
- **指标说明**：每个指标的含义和评估方法

**数据逻辑**：
- 从 `evaluation_result` 中提取评估指标
- 根据评分值显示不同颜色和状态
- 显示指标说明（如果有）

---

### 3.4 📋 阶段4：评估数据质量

**数据来源**：评估数据和结果的质量检查

**显示内容**：
- **数据完整性检查**：检查查询、答案、上下文是否完整
- **质量评分**：基于数据完整性的质量评分
- **建议**：数据质量改进建议（如果有）

**数据逻辑**：
- 检查评估数据的完整性
- 计算数据质量评分
- 提供改进建议

---

## 4. 数据流转逻辑

```
用户查询
  ↓
RAGEngine.query() / query_stream()
  ↓
ObserverManager.on_query_start()  ← 记录查询开始
  ↓
QueryProcessor.process()  ← 意图理解和查询改写（当前未传递到观察器）
  ↓
QueryEngine.query()  ← 执行查询（LlamaIndex 内部）
  ↓
LlamaDebugHandler  ← 自动记录事件对
  ↓
ObserverManager.on_query_end()  ← 记录查询结束
  ↓
LlamaDebugObserver.on_query_end()  ← 提取事件信息，存储到 session_state
RAGASEvaluator.on_query_end()  ← 收集评估数据，存储到 session_state
  ↓
前端显示（chat_display.py）  ← 从 session_state 读取并显示
```

---

## 5. 数据限制说明

为了控制内存占用和显示性能，系统对以下数据进行了限制：

- **事件对**：最多保存前20个
- **来源**：最多保存前10个
- **LLM Prompts/Responses**：最多保存前5个
- **检索查询/节点**：最多保存前5个
- **上下文**：最多保存前10个
- **文本截断**：
  - 答案：500字符
  - 来源：200字符
  - 节点：500字符
  - 上下文：500字符

---

## 6. 关键代码位置

### 6.1 后端数据收集

- **LlamaDebugObserver**: `backend/infrastructure/observers/llama_debug_observer.py`
  - `on_query_end()`: 提取事件信息并存储到 session_state
- **RAGASEvaluator**: `backend/infrastructure/observers/ragas_evaluator.py`
  - `on_query_end()`: 收集评估数据并存储到 session_state

### 6.2 前端显示

- **LlamaDebug 显示**: `frontend/components/chat_display.py`
  - `_render_llamadebug_full_info()`: 按执行流程渲染 LlamaDebug 全量信息
- **RAGAS 显示**: `frontend/components/chat_display.py`
  - `_render_ragas_full_info()`: 按执行流程渲染 RAGAS 全量信息

---

## 7. 已知限制

### 7.1 未实现的功能

根据 `docs/llamadebug_available_info.md`，以下信息当前未实现：

- **查询改写结果** (`rewritten_query`)：查询改写后的文本
- **查询意图** (`query_intent`)：查询意图分析结果
- **LLM模型名称** (`llm_model`)：使用的LLM模型
- **LLM参数** (`llm_params`)：LLM调用参数（temperature、max_tokens等）
- **检索策略** (`retrieval_strategy`)：使用的检索策略
- **Top K值** (`top_k`)：检索返回的Top K值
- **错误信息** (`errors`)：执行过程中的错误
- **警告信息** (`warnings`)：执行过程中的警告

### 7.2 原因分析

- **查询改写和意图理解**：虽然 `QueryProcessor` 有这些功能，但结果未传递到观察器
- **配置信息**：需要从配置对象中获取，当前未集成
- **错误处理**：需要捕获异常并记录，当前未实现

---

## 8. 后续优化建议

### 8.1 数据收集增强

1. **传递查询处理结果**：将 `QueryProcessor.process()` 的结果传递到观察器
2. **提取配置信息**：从配置对象中提取模型名称、参数等信息
3. **错误捕获**：捕获并记录执行过程中的错误和警告

### 8.2 显示优化

1. **查询改写显示**：在查询阶段显示改写后的查询
2. **意图理解显示**：显示查询类型、复杂度、意图等
3. **配置信息显示**：显示使用的模型、参数、策略等

### 8.3 性能优化

1. **异步处理**：考虑异步处理观察器信息提取
2. **数据压缩**：对大量数据进行压缩存储
3. **分页显示**：对大量事件对进行分页显示

---

## 9. 参考文档

- `docs/llamadebug_available_info.md`：LlamaDebugHandler 全量信息清单
- `agent-task-log/2026-01-08-1_【refactor】移除Phoenix并集成内置观察器到页面-完成总结.md`：任务完成总结

---

## 10. 版本历史

- **v1.0** (2026-01-11)：初始版本，包含完整的可观测性信息逻辑说明

