# 2026-01-21 【implementation】RAG链路意图理解和查询改写Agent化-完成总结

## 1. 任务概述

### 1.1 元信息
- **任务类型**：implementation
- **执行日期**：2026-01-21
- **关联模块**：`backend/business/rag_engine/agentic/`

### 1.2 任务目标
将 RAG 链路中的意图理解和查询改写功能 Agent 化，集成到现有 Agentic RAG 的规划 Agent 中，让 Agent 自主决定是否需要进行意图理解、查询改写和多意图分解。

### 1.3 背景
- 原有 `QueryProcessor` 基于规则+LLM 的固定流程处理查询
- Agentic RAG 需要更灵活的查询处理能力
- 参考业界实践（美团、腾讯云）的多策略改写方案

---

## 2. 关键决策

### 2.1 集成方案选择
**决策**：与现有规划 Agent 集成（而非独立 Agent）

**理由**：
- 复用现有 Agent 基础设施
- 减少额外调用开销
- 保持架构简洁

### 2.2 工具设计
新增 3 个查询处理工具：
| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `analyze_intent` | 意图理解 | 复杂/模糊查询 |
| `rewrite_query` | 查询改写 | needs_rewrite=true |
| `decompose_multi_intent` | 多意图分解 | 包含多个问题 |

---

## 3. 实施内容

### 3.1 新增文件
| 文件 | 行数 | 说明 |
|------|------|------|
| `query_processing_impl.py` | 195 | 核心实现（意图分析、改写、分解） |
| `query_processing_tools.py` | 76 | FunctionTool 封装 |
| `test_query_processing_tools.py` | 149 | 单元测试 |
| `test_query_processing_agent.py` | 147 | 集成测试 |

### 3.2 修改文件
| 文件 | 变更内容 |
|------|----------|
| `planning.py` | 集成查询处理工具，新增 `enable_query_processing` 参数 |
| `planning.txt` | 更新 Agent Prompt，增加查询处理工具说明 |
| `__init__.py` | 导出新工具创建函数 |

### 3.3 代码规范
- ✅ 所有文件 ≤ 300 行
- ✅ 类型提示完整
- ✅ 日志规范（使用 logger）
- ✅ 错误处理和降级机制

---

## 4. 测试结果

### 4.1 测试执行
```bash
uv run --no-sync python -m pytest tests/unit/agentic/test_query_processing_tools.py \
  tests/integration/test_query_processing_agent.py -v
```

### 4.2 测试结果
```
✅ 15 passed in 12.15s

单元测试 (9个):
- test_create_query_processing_tools
- test_extract_json_plain/markdown/generic_block
- test_analyze_intent_success/error_fallback
- test_rewrite_query_success
- test_decompose_multi_intent_success/single_intent

集成测试 (6个):
- test_create_all_tools
- test_create_agent_with/without_query_processing
- test_analyze_intent/rewrite_query/decompose_multi_intent_real_llm (需API key)
```

---

## 5. 交付成果

### 5.1 功能交付
规划 Agent 现在支持 6 个工具：
- 查询处理：`analyze_intent`, `rewrite_query`, `decompose_multi_intent`
- 检索工具：`vector_search`, `hybrid_search`, `multi_search`

### 5.2 链路对比
| 维度 | 传统 RAG | Agentic RAG（更新后） |
|------|----------|----------------------|
| 查询处理 | QueryProcessor 统一处理 | 3个工具按需调用 |
| 决策方式 | 规则+固定流程 | Agent 自主决策 |
| 灵活性 | 固定管道 | 动态组合 |

### 5.3 文件结构
```
backend/business/rag_engine/agentic/agent/tools/
├── __init__.py                    # 导出
├── query_processing_impl.py       # 核心实现 [新增]
├── query_processing_tools.py      # 工具封装 [新增]
└── retrieval_tools.py             # 检索工具
```

---

## 6. 遗留与后续

### 6.1 已完成
- ✅ 意图理解工具
- ✅ 查询改写工具（保留实体、扩展语义）
- ✅ 多意图分解工具
- ✅ 单元测试和集成测试

### 6.2 后续优化
- ⚠️ 上下文依赖处理（对话历史）
- ⚠️ 指代消解（"这个"、"那个"）
- ⚠️ 语义相似度验证（过滤低质量改写）
- ⚠️ 词典改写模块（降低 LLM 成本）

---

## 7. 参考文档
- `staging/query_rewriting_analysis_and_improvements.md` - 查询改写分析
- `staging/Agentic RAG 系统实施执行计划书.md` - Agentic RAG 计划书
