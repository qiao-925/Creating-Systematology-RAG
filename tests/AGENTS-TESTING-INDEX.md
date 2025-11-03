# Agent 测试体系索引

> **文档类型**: Agent 测试体系主索引文档  
> **版本**: 1.0  
> **更新日期**: 2025-11-03  
> **目标读者**: AI Agent / Cursor AI

---

## 📖 文档说明

本文档是 Agent 理解和使用项目测试体系的**核心索引**。Agent 应优先查阅本文档来：
- 理解测试体系的整体结构
- 查找与特定代码模块相关的测试
- 了解如何选择和运行相关测试
- 理解测试的分类和用途

---

## 🎯 测试体系概览

### 测试金字塔结构

```
        /\
       /  \     E2E Tests (端到端测试)
      /____\    
     /      \   Integration Tests (集成测试)
    /________\  
   /          \ Unit Tests (单元测试)
  /____________\
```

**层次说明**:
- **单元测试** (`tests/unit/`) - 数量最多，执行最快，测试单个模块
- **集成测试** (`tests/integration/`) - 测试模块间协作和完整流程
- **E2E测试** (`tests/e2e/`) - 测试完整业务流程，验证端到端功能

---

## 📂 测试分类索引

### 1. 单元测试 (`tests/unit/`)

**目录作用**: 测试单个模块或类的功能，无外部依赖（使用Mock）

**测试文件映射**:

| 测试文件 | 目标模块 | 目标类/功能 | 测试数量 | 说明 |
|---------|---------|------------|---------|------|
| `test_config.py` | `src.config` | `Config` | ~15 | 配置管理、环境变量、参数验证 |
| `test_data_loader.py` | `src.data_loader` | 数据加载器 | ~20 | Markdown、Web、GitHub 数据加载 |
| `test_indexer.py` | `src.indexer` | `IndexManager` | ~15 | 索引构建、向量化、检索 |
| `test_query_engine.py` | `src.query_engine` | `QueryEngine` | ~8 | 查询引擎、引用溯源 |
| `test_chat_manager.py` | `src.chat_manager` | `ChatManager` | ~15 | 对话管理、会话持久化 |
| `test_embeddings.py` | `src.embeddings` | Embedding 模型 | ~10 | 本地/API Embedding |
| `test_data_source.py` | `src.data_source` | 数据源抽象 | ~8 | 数据源接口和实现 |
| `test_query_router.py` | `src.routers` | `QueryRouter` | ~8 | 查询路由逻辑 |
| `test_grep_retriever.py` | `src.retrievers` | `GrepRetriever` | ~8 | Grep 检索器 |
| `test_multi_strategy_retriever.py` | `src.retrievers` | `MultiStrategyRetriever` | ~10 | 多策略检索器 |
| `test_result_merger.py` | `src.retrievers` | `ResultMerger` | ~6 | 结果合并逻辑 |
| `test_reranker.py` | `src.rerankers` | 重排序器 | ~8 | 重排序功能 |
| `test_observers.py` | `src.observers` | 可观测性 | ~8 | Phoenix、Debug 观察者 |
| `test_registry.py` | `src.business.registry` | 模块注册表 | ~8 | 模块注册和发现 |
| `test_strategy_manager.py` | `src.business.strategy_manager` | 策略管理 | ~10 | 策略配置和管理 |
| `test_pipeline_executor.py` | `src.business.pipeline` | 流水线执行器 | ~8 | 流水线执行逻辑 |
| `test_response_formatter.py` | `src.response_formatter` | 响应格式化 | ~6 | 响应格式化和验证 |
| `test_user_manager.py` | `src.user_manager` | 用户管理 | ~8 | 用户注册、登录、隔离 |
| `test_git_repository_manager.py` | `src.git_repository_manager` | Git 仓库管理 | ~8 | GitHub 仓库同步 |
| `test_wikipedia_loader.py` | `src.data_loader` | Wikipedia 加载器 | ~6 | Wikipedia 数据加载 |

**快速识别模式**:
- 文件名: `test_<模块名>.py` → 对应 `src/<模块名>.py`
- 文件名: `test_<功能名>.py` → 对应 `src/` 下的相关功能

---

### 2. 集成测试 (`tests/integration/`)

**目录作用**: 测试多个模块协作和完整业务流程

**测试文件列表**:

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_rag_service_integration.py` | RAG 服务完整流程 | ~15 | 文档导入 → 索引构建 → 查询 → 响应 |
| `test_multi_strategy_integration.py` | 多策略检索集成 | ~10 | 多种检索策略协作 |
| `test_auto_routing_integration.py` | 自动路由集成 | ~8 | 查询自动路由到不同策略 |
| `test_reranker_integration.py` | 重排序集成 | ~8 | 检索结果重排序流程 |
| `test_observability_integration.py` | 可观测性集成 | ~8 | Phoenix 集成和追踪 |
| `test_query_pipeline.py` | 查询流水线 | ~7 | 完整查询处理流程 |
| `test_data_pipeline.py` | 数据处理流水线 | ~8 | 数据加载和处理流程 |
| `test_phoenix_integration.py` | Phoenix 集成 | ~5 | Phoenix 可观测性平台 |
| `test_github_e2e.py` | GitHub 端到端 | ~10 | GitHub 仓库完整流程 |

---

### 3. E2E 测试 (`tests/e2e/`)

**目录作用**: 测试完整业务流程，验证端到端功能

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_core_workflows.py` | 核心工作流 | 完整的用户工作流测试 |

---

### 4. UI 测试 (`tests/ui/`)

**目录作用**: 测试 Streamlit 用户界面

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_app.py` | Streamlit 应用 | UI 组件和交互测试 |

---

### 5. 性能测试 (`tests/performance/`)

**目录作用**: 性能基准测试，验证性能指标

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_performance.py` | 基础性能 | 索引构建、查询性能 |
| `test_query_performance.py` | 查询性能 | 查询响应时间 |
| `test_multi_strategy_performance.py` | 多策略性能 | 多策略检索性能 |
| `test_reranker_performance.py` | 重排序性能 | 重排序性能 |
| `test_modular_rag_performance.py` | 模块化RAG性能 | 模块化架构性能 |
| `test_index_build_optimization.py` | 索引构建优化 | 索引构建优化效果 |

---

### 6. 兼容性测试 (`tests/compatibility/`)

**目录作用**: 向后兼容和跨平台兼容性测试

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_backward_compatibility.py` | 向后兼容 | API 和数据结构兼容性 |
| `test_cross_platform.py` | 跨平台 | Windows/Linux/Mac 兼容性 |

---

### 7. 回归测试 (`tests/regression/`)

**目录作用**: 验证已修复Bug不会再次出现

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_core_features.py` | 核心功能回归 | 核心功能回归验证 |
| `test_ui_features.py` | UI功能回归 | UI功能回归验证 |

---

## 🔍 源文件 → 测试文件映射表

**Agent 使用指南**: 当修改某个源文件时，使用此表快速找到相关测试

### 核心模块映射

| 源文件路径 | 主要测试文件 | 次要测试文件 | 说明 |
|-----------|-------------|-------------|------|
| `src/config.py` | `tests/unit/test_config.py` | - | 配置管理 |
| `src/indexer.py` | `tests/unit/test_indexer.py` | `tests/integration/test_data_pipeline.py` | 索引构建 |
| `src/query_engine.py` | `tests/unit/test_query_engine.py` | `tests/integration/test_query_pipeline.py` | 查询引擎 |
| `src/chat_manager.py` | `tests/unit/test_chat_manager.py` | - | 对话管理 |
| `src/data_loader.py` | `tests/unit/test_data_loader.py` | `tests/integration/test_data_pipeline.py` | 数据加载 |
| `src/user_manager.py` | `tests/unit/test_user_manager.py` | - | 用户管理 |

### 业务模块映射

| 源文件路径 | 主要测试文件 | 集成测试 | 说明 |
|-----------|-------------|---------|------|
| `src/business/services/rag_service.py` | - | `tests/integration/test_rag_service_integration.py` | RAG 服务 |
| `src/business/strategy_manager.py` | `tests/unit/test_strategy_manager.py` | `tests/integration/test_multi_strategy_integration.py` | 策略管理 |
| `src/business/registry.py` | `tests/unit/test_registry.py` | - | 模块注册表 |
| `src/business/modular_query_engine.py` | - | `tests/integration/test_query_pipeline.py` | 模块化查询引擎 |
| `src/business/pipeline/executor.py` | `tests/unit/test_pipeline_executor.py` | `tests/integration/test_query_pipeline.py` | 流水线执行器 |

### 检索和路由模块映射

| 源文件路径 | 主要测试文件 | 集成测试 | 说明 |
|-----------|-------------|---------|------|
| `src/routers/query_router.py` | `tests/unit/test_query_router.py` | `tests/integration/test_auto_routing_integration.py` | 查询路由 |
| `src/retrievers/grep_retriever.py` | `tests/unit/test_grep_retriever.py` | - | Grep 检索器 |
| `src/retrievers/multi_strategy_retriever.py` | `tests/unit/test_multi_strategy_retriever.py` | `tests/integration/test_multi_strategy_integration.py` | 多策略检索 |
| `src/retrievers/result_merger.py` | `tests/unit/test_result_merger.py` | - | 结果合并 |
| `src/rerankers/` | `tests/unit/test_reranker.py` | `tests/integration/test_reranker_integration.py` | 重排序 |

### Embedding 和可观测性模块映射

| 源文件路径 | 主要测试文件 | 集成测试 | 说明 |
|-----------|-------------|---------|------|
| `src/embeddings/` | `tests/unit/test_embeddings.py` | - | Embedding 模型 |
| `src/observers/` | `tests/unit/test_observers.py` | `tests/integration/test_observability_integration.py` | 可观测性 |
| `src/phoenix_utils.py` | - | `tests/integration/test_phoenix_integration.py` | Phoenix 工具 |

### 数据源模块映射

| 源文件路径 | 主要测试文件 | 说明 |
|-----------|-------------|------|
| `src/data_source/` | `tests/unit/test_data_source.py` | 数据源抽象 |
| `src/data_loader/wikipedia_loader.py` | `tests/unit/test_wikipedia_loader.py` | Wikipedia 加载器 |
| `src/data_loader/github_loader.py` | - | `tests/integration/test_github_e2e.py` | GitHub 加载器 |
| `src/git_repository_manager.py` | `tests/unit/test_git_repository_manager.py` | Git 仓库管理 |

---

## 🤖 Agent 使用指南

### 场景1: 修改代码后如何选择测试

**步骤**:
1. 识别修改的文件路径（如 `src/indexer.py`）
2. 查询映射表，找到主要测试文件（`tests/unit/test_indexer.py`）
3. 检查是否需要运行集成测试（检查次要测试文件列）
4. 运行相关测试

**命令示例**:
```bash
# 修改了 src/indexer.py
pytest tests/unit/test_indexer.py -v

# 修改了 src/query_engine.py，可能影响集成
pytest tests/unit/test_query_engine.py tests/integration/test_query_pipeline.py -v
```

### 场景2: 添加新功能后如何确保测试覆盖

**步骤**:
1. 确定新功能所属的模块
2. 查找对应的测试文件
3. 检查测试索引元数据（`test_index.json`）确认覆盖范围
4. 如缺少测试，参考 `AGENTS-EXPANSION-ERROR_HANDLING-TESTING.md` 生成测试模板

### 场景3: 运行完整测试套件

**按优先级运行**:
1. 先运行相关单元测试（快速验证）
2. 再运行相关集成测试（验证协作）
3. 最后运行E2E测试（验证完整流程）

**命令**:
```bash
# 运行所有单元测试
pytest tests/unit -v

# 运行所有集成测试
pytest tests/integration -v

# 运行所有测试
pytest tests/ -v
```

### 场景4: 理解测试失败

**分析步骤**:
1. 查看测试文件元数据（`test_index.json`）了解测试目的
2. 查看测试代码中的 docstring 和注释
3. 运行单个测试获取详细错误信息：`pytest tests/unit/test_xxx.py::TestClass::test_method -vv`
4. 检查测试依赖的 fixtures（`conftest.py`）

---

## 📋 测试命名规范

### 文件命名

- **单元测试**: `test_<模块名>.py` (如 `test_indexer.py`)
- **集成测试**: `test_<功能>_integration.py` (如 `test_rag_service_integration.py`)
- **E2E测试**: `test_<工作流>_e2e.py` 或 `test_<功能>_workflow.py`
- **性能测试**: `test_<功能>_performance.py`

### 测试类命名

- **格式**: `Test<类名>` 或 `Test<功能描述>`
- **示例**: 
  - `TestIndexManager` (测试 `IndexManager` 类)
  - `TestDataPipeline` (测试数据处理流水线)

### 测试函数命名

- **格式**: `test_<功能>_<场景>`
- **示例**:
  - `test_build_index_with_valid_documents` (测试使用有效文档构建索引)
  - `test_query_engine_handles_empty_query` (测试查询引擎处理空查询)

**命名模式**:
- `test_<功能>_normal` - 正常流程
- `test_<功能>_edge_cases` - 边界条件
- `test_<功能>_errors` - 异常情况
- `test_<功能>_with_<条件>` - 特定条件

---

## 🛠️ Agent 辅助工具

Agent 可以使用以下工具辅助测试：

1. **`tests/tools/agent_test_selector.py`**
   - 根据修改的文件自动选择相关测试
   - 使用方法: `python tests/tools/agent_test_selector.py src/indexer.py`

2. **`tests/tools/agent_test_info.py`**
   - 查询测试文件的详细信息（目的、覆盖范围等）
   - 使用方法: `python tests/tools/agent_test_info.py tests/unit/test_indexer.py`

3. **`tests/tools/agent_test_summary.py`**
   - 生成测试执行摘要报告
   - 使用方法: `python tests/tools/agent_test_summary.py`

4. **`tests/tools/generate_test_index.py`**
   - 生成测试元数据索引（`test_index.json`）
   - 使用方法: `python tests/tools/generate_test_index.py`

---

## 📊 测试统计信息

- **总测试文件数**: ~51 个
- **单元测试**: ~20 个文件，~100+ 个测试用例
- **集成测试**: ~9 个文件，~80+ 个测试用例
- **E2E测试**: ~1 个文件，~10+ 个测试用例
- **性能测试**: ~6 个文件，~20+ 个测试用例
- **覆盖率目标**: ≥90%

---

## 🔗 相关文档

- **测试使用指南**: `tests/README.md` (人类快速参考)
- **测试详细指南**: `tests/README_TESTING.md` (详细说明)
- **测试元数据**: `tests/METADATA.md` (元数据结构说明)
- **测试规范**: `.cursor/rules/testing-standards.mdc` (测试规范规则)
- **Agent测试整合**: `.cursor/rules/agent-testing-integration.mdc` (Agent整合规则)
- **测试用例生成指南**: `.cursor/agents-expansion/AGENTS-EXPANSION-ERROR_HANDLING-TESTING.md`

---

## ✅ 快速查找表

### 按模块查找测试

| 模块关键词 | 测试文件 |
|-----------|---------|
| `config` | `tests/unit/test_config.py` |
| `indexer` | `tests/unit/test_indexer.py` |
| `query` | `tests/unit/test_query_engine.py` |
| `chat` | `tests/unit/test_chat_manager.py` |
| `data_loader` | `tests/unit/test_data_loader.py` |
| `embedding` | `tests/unit/test_embeddings.py` |
| `router` | `tests/unit/test_query_router.py` |
| `retriever` | `tests/unit/test_grep_retriever.py`, `tests/unit/test_multi_strategy_retriever.py` |
| `reranker` | `tests/unit/test_reranker.py` |
| `rag_service` | `tests/integration/test_rag_service_integration.py` |

### 按功能查找测试

| 功能 | 测试类型 | 测试文件 |
|-----|---------|---------|
| 配置管理 | Unit | `test_config.py` |
| 索引构建 | Unit + Integration | `test_indexer.py`, `test_data_pipeline.py` |
| 查询功能 | Unit + Integration | `test_query_engine.py`, `test_query_pipeline.py` |
| 对话管理 | Unit | `test_chat_manager.py` |
| 数据加载 | Unit + Integration | `test_data_loader.py`, `test_data_pipeline.py` |
| 多策略检索 | Unit + Integration | `test_multi_strategy_retriever.py`, `test_multi_strategy_integration.py` |
| 自动路由 | Unit + Integration | `test_query_router.py`, `test_auto_routing_integration.py` |
| GitHub集成 | Integration | `test_github_e2e.py` |
| Phoenix集成 | Integration | `test_phoenix_integration.py` |

---

**最后更新**: 2025-11-03  
**维护者**: 当测试体系变更时，更新本文档和元数据索引

