# Agent 测试体系指南

> **文档类型**: Agent 测试体系完整指南  
> **版本**: 1.0  
> **更新日期**: 2025-11-03  
> **目标读者**: AI Agent / Cursor AI

---

## 文档说明

本文档是 Agent 理解和使用项目测试体系的**核心指南**。整合了测试体系索引、元数据说明和工具使用指南。

Agent 应优先查阅本文档来：
- 理解测试体系的整体结构
- 查找与特定代码模块相关的测试
- 了解如何选择和运行相关测试
- 理解测试的分类和用途
- 使用 Agent 测试工具

---

## 测试体系概览

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
- **单元测试** (`tests/unit/`) - 数量最多，执行最快，测试单个模块，使用Mock无外部依赖
- **集成测试** (`tests/integration/`) - 测试模块间协作和完整流程
- **E2E测试** (`tests/e2e/`) - 测试完整业务流程，验证端到端功能

---

## 测试分类索引

### 单元测试 (`tests/unit/`)

**目录作用**: 测试单个模块或类的功能，无外部依赖（使用Mock）

**测试文件映射**:

| 测试文件 | 目标模块 | 目标类/功能 | 说明 |
|---------|---------|------------|------|
| `test_config.py` | `src.config` | `Config` | 配置管理、环境变量、参数验证 |
| `test_data_loader.py` | `src.data_loader` | 数据加载器 | Markdown、Web、GitHub 数据加载 |
| `test_indexer.py` | `src.indexer` | `IndexManager` | 索引构建、向量化、检索 |
| `test_chat_manager.py` | `src.chat_manager` | `ChatManager` | 对话管理、会话持久化 |
| `test_embeddings.py` | `src.embeddings` | Embedding 模型 | 本地/API Embedding |
| `test_data_source.py` | `src.data_source` | 数据源抽象 | 数据源接口和实现 |
| `test_query_router.py` | `src.routers` | `QueryRouter` | 查询路由逻辑 |
| `test_grep_retriever.py` | `src.retrievers` | `GrepRetriever` | Grep 检索器 |
| `test_multi_strategy_retriever.py` | `src.retrievers` | `MultiStrategyRetriever` | 多策略检索器 |
| `test_result_merger.py` | `src.retrievers` | `ResultMerger` | 结果合并逻辑 |
| `test_reranker.py` | `src.rerankers` | 重排序器 | 重排序功能 |
| `test_observers.py` | `src.observers` | 可观测性 | Phoenix、Debug 观察者 |
| `test_rag_service.py` | `src.business.rag_api` | RAG服务 | RAG服务单元测试 |
| `test_response_formatter.py` | `src.response_formatter` | 响应格式化 | 响应格式化和验证 |
| `test_user_manager.py` | `src.user_manager` | 用户管理 | 用户注册、登录、隔离 |
| `test_git_repository_manager.py` | `src.git_repository_manager` | Git 仓库管理 | GitHub 仓库同步 |
| `test_wikipedia_loader.py` | `src.data_loader` | Wikipedia 加载器 | Wikipedia 数据加载 |

**快速识别模式**:
- 文件名: `test_<模块名>.py` → 对应 `src/<模块名>.py`
- 文件名: `test_<功能名>.py` → 对应 `src/` 下的相关功能

### 集成测试 (`tests/integration/`)

**目录作用**: 测试多个模块协作和完整业务流程

| 测试文件 | 测试范围 | 说明 |
|---------|---------|------|
| `test_rag_service_integration.py` | RAG 服务完整流程 | 文档导入 → 索引构建 → 查询 → 响应 |
| `test_modular_query_engine.py` | 模块化查询引擎 | 多种检索策略、查询流程 |
| `test_multi_strategy_integration.py` | 多策略检索集成 | 多种检索策略协作 |
| `test_auto_routing_integration.py` | 自动路由集成 | 查询自动路由到不同策略 |
| `test_reranker_integration.py` | 重排序集成 | 检索结果重排序流程 |
| `test_observability_integration.py` | 可观测性集成 | Phoenix 集成和追踪 |
| `test_query_pipeline.py` | 查询流水线 | 完整查询处理流程 |
| `test_query_processing_integration.py` | 查询处理集成 | 查询处理完整流程 |
| `test_data_pipeline.py` | 数据处理流水线 | 数据加载和处理流程 |
| `test_phoenix_integration.py` | Phoenix 集成 | Phoenix 可观测性平台 |
| `test_github_e2e.py` | GitHub 端到端 | GitHub 仓库完整流程 |

### 其他测试类型

- **E2E测试** (`tests/e2e/`) - 完整业务流程测试
- **UI测试** (`tests/ui/`) - Streamlit 用户界面测试
- **性能测试** (`tests/performance/`) - 性能基准测试
- **兼容性测试** (`tests/compatibility/`) - 向后兼容和跨平台兼容性
- **回归测试** (`tests/regression/`) - 验证已修复Bug不会再次出现

---

## 源文件 → 测试文件映射表

**Agent 使用指南**: 当修改某个源文件时，使用此表快速找到相关测试

### 核心模块映射

| 源文件路径 | 主要测试文件 | 次要测试文件 | 说明 |
|-----------|-------------|-------------|------|
| `src/config.py` | `tests/unit/test_config.py` | - | 配置管理 |
| `src/indexer.py` | `tests/unit/test_indexer.py` | `tests/integration/test_data_pipeline.py` | 索引构建 |
| `src/chat_manager.py` | `tests/unit/test_chat_manager.py` | - | 对话管理 |
| `src/data_loader.py` | `tests/unit/test_data_loader.py` | `tests/integration/test_data_pipeline.py` | 数据加载 |
| `src/user_manager.py` | `tests/unit/test_user_manager.py` | - | 用户管理 |

### 业务模块映射

| 源文件路径 | 主要测试文件 | 集成测试 | 说明 |
|-----------|-------------|---------|------|
| `src/business/services/rag_service.py` | `tests/unit/test_rag_service.py` | `tests/integration/test_rag_service_integration.py` | RAG 服务 |
| `src.modular_query_engine` | - | `tests/integration/test_modular_query_engine.py` | 模块化查询引擎 |
| `src/business/modular_query_engine.py` | - | `tests/integration/test_query_pipeline.py` | 模块化查询引擎 |

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

---

## Agent 使用指南

### 场景1: 修改代码后如何选择测试

**步骤**:
1. 识别修改的文件路径（如 `src/indexer.py`）
2. 查询映射表，找到主要测试文件（`tests/unit/test_indexer.py`）
3. 使用工具自动选择：`python tests/tools/agent_test_selector.py src/indexer.py`
4. 检查是否需要运行集成测试（检查次要测试文件列）
5. 运行相关测试

**命令示例**:
```bash
# 修改了 src/indexer.py
pytest tests/unit/test_indexer.py -v

# 使用工具自动选择
python tests/tools/agent_test_selector.py src/indexer.py

# 修改了查询引擎相关代码（可能影响集成）
pytest tests/integration/test_query_pipeline.py -v
```

### 场景2: 添加新功能后如何确保测试覆盖

**步骤**:
1. 确定新功能所属的模块
2. 查找对应的测试文件
3. 检查测试索引元数据（`test_index.json`）确认覆盖范围
4. 如缺少测试，参考测试规范生成测试模板

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
2. 使用工具查询详细信息：`python tests/tools/agent_test_info.py tests/unit/test_xxx.py`
3. 查看测试代码中的 docstring 和注释
4. 运行单个测试获取详细错误信息：`pytest tests/unit/test_xxx.py::TestClass::test_method -vv`
5. 检查测试依赖的 fixtures（`conftest.py`）

---

## Agent 辅助工具

Agent 可以使用以下工具辅助测试：

### 1. agent_test_selector.py

**功能**: 根据修改的文件自动选择相关测试

**使用方法**:
```bash
python tests/tools/agent_test_selector.py src/indexer.py
```

**输出**: 推荐运行的测试文件列表和 pytest 命令

### 2. agent_test_info.py

**功能**: 查询测试文件的详细信息（目的、覆盖范围等）

**使用方法**:
```bash
python tests/tools/agent_test_info.py tests/unit/test_indexer.py
```

**输出**: 测试的详细信息，包括目标模块、覆盖范围、依赖等

### 3. agent_test_summary.py

**功能**: 生成测试执行摘要报告

**使用方法**:
```bash
# 从 pytest 输出生成摘要
pytest tests/unit/test_indexer.py -v | python tests/tools/agent_test_summary.py

# 或直接运行并生成摘要
python tests/tools/agent_test_summary.py tests/unit/test_indexer.py --run
```

### 4. generate_test_index.py

**功能**: 生成测试元数据索引（`test_index.json`）

**使用方法**:
```bash
# 生成或更新测试索引
python tests/tools/generate_test_index.py

# 输出到指定文件
python tests/tools/generate_test_index.py -o tests/test_index_custom.json
```

---

## 测试元数据结构

### 元数据索引的用途

1. **Agent 测试识别**: Agent 可以根据源文件路径快速找到相关测试
2. **测试覆盖分析**: 了解每个测试文件覆盖的功能范围
3. **依赖关系追踪**: 了解测试的依赖关系和前置条件
4. **测试分类查询**: 根据标签和分类快速筛选测试
5. **测试选择自动化**: 支持智能测试选择工具

### 元数据结构

**顶层结构**:
```json
{
  "version": "1.0",
  "generated_at": "2025-11-03T10:00:00",
  "test_files": [
    // 测试文件元数据数组
  ],
  "statistics": {
    // 统计信息
  }
}
```

**测试文件元数据结构**:
```json
{
  "file_path": "tests/unit/test_indexer.py",
  "category": "unit",
  "target_module": "src.indexer",
  "target_class": "IndexManager",
  "target_functions": ["build_index", "query_index", "clear_index"],
  "test_count": 15,
  "description": "测试索引管理器的核心功能，包括索引构建、查询、清理等",
  "coverage": ["build_index", "query_index", "clear_index", "get_stats", "get_index"],
  "dependencies": ["conftest.prepared_index_manager", "conftest.sample_documents"],
  "tags": ["unit", "indexing", "vector_store"],
  "pytest_markers": ["unit"],
  "fixtures_used": ["temp_index_manager", "sample_documents", "temp_vector_store"],
  "related_tests": ["tests/integration/test_data_pipeline.py"],
  "source_files": ["src/indexer.py"]
}
```

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `file_path` | string | ✅ | 测试文件的相对路径 |
| `category` | string | ✅ | 测试分类: `unit`, `integration`, `e2e`, `performance`, `compatibility`, `regression`, `ui` |
| `target_module` | string | ✅ | 目标模块路径（如 `src.indexer`） |
| `target_class` | string | ⚠️ | 目标类名（如果测试特定类） |
| `target_functions` | array | ⚠️ | 目标函数列表（测试的主要功能） |
| `test_count` | number | ✅ | 测试用例数量 |
| `description` | string | ✅ | 测试文件的描述说明 |
| `coverage` | array | ⚠️ | 覆盖的功能列表（函数名、方法名） |
| `dependencies` | array | ⚠️ | 测试依赖（fixtures、外部资源等） |
| `tags` | array | ✅ | 标签列表，用于分类和搜索 |
| `pytest_markers` | array | ⚠️ | pytest 标记（如 `@pytest.mark.slow`） |
| `fixtures_used` | array | ⚠️ | 使用的 fixtures 列表 |
| `related_tests` | array | ⚠️ | 相关的其他测试文件 |
| `source_files` | array | ✅ | 对应的源文件路径列表 |

### 元数据生成

**自动生成工具**:
```bash
# 生成或更新测试索引
python tests/tools/generate_test_index.py

# 输出到指定文件
python tests/tools/generate_test_index.py -o tests/test_index_custom.json
```

**生成逻辑**:
1. 扫描 `tests/` 目录下的所有测试文件
2. 解析测试文件的 AST（抽象语法树）
3. 提取测试类、测试函数、fixtures 等信息
4. 分析源文件导入关系，推断目标模块
5. 提取 docstring 和注释作为描述
6. 生成 JSON 格式的元数据索引

**元数据更新时机**:
- ✅ 添加新的测试文件时
- ✅ 修改测试文件结构时
- ✅ 修改源文件路径或模块结构时
- ✅ 定期维护（如每周）

---

## 测试命名规范

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
  - `test_query_pipeline_handles_empty_query` (测试查询链路处理空查询)

**命名模式**:
- `test_<功能>_normal` - 正常流程
- `test_<功能>_edge_cases` - 边界条件
- `test_<功能>_errors` - 异常情况
- `test_<功能>_with_<条件>` - 特定条件

---

## 快速查找表

### 按模块查找测试

| 模块关键词 | 测试文件 |
|-----------|---------|
| `config` | `tests/unit/test_config.py` |
| `indexer` | `tests/unit/test_indexer.py` |
| `query` | `tests/integration/test_query_pipeline.py` |
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
| 查询功能 | Integration | `test_query_pipeline.py`, `test_modular_query_engine.py` |
| 对话管理 | Unit | `test_chat_manager.py` |
| 数据加载 | Unit + Integration | `test_data_loader.py`, `test_data_pipeline.py` |
| 多策略检索 | Unit + Integration | `test_multi_strategy_retriever.py`, `test_multi_strategy_integration.py` |
| 自动路由 | Unit + Integration | `test_query_router.py`, `test_auto_routing_integration.py` |
| GitHub集成 | Integration | `test_github_e2e.py` |
| Phoenix集成 | Integration | `test_phoenix_integration.py` |

---

## 相关文档

- **测试使用指南**: `../README.md` (人类快速参考)
- **单元测试文档**: `../unit/README.md` (单元测试详细说明)
- **工具文档**: `../tools/README.md` (诊断工具说明)
- **测试规范**: `.cursor/rules/testing-standards.mdc` (测试规范规则)
- **Agent测试整合**: `.cursor/rules/agent-testing-integration.mdc` (Agent整合规则)

---

**最后更新**: 2025-11-03  
**维护者**: 当测试体系变更时，更新本文档和元数据索引

