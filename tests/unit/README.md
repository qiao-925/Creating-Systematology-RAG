# 单元测试指南

> **文档类型**: 单元测试使用指南  
> **更新日期**: 2025-11-03

---

## 概述

单元测试用于测试单个模块或类的功能，**无外部依赖**（使用Mock）。这是测试金字塔的基础，数量最多，执行最快。

---

## 快速开始

### 运行所有单元测试

```bash
# 方式1: 使用Makefile（推荐）
make test-unit

# 方式2: 直接使用pytest
pytest tests/unit -v
```

### 运行特定测试文件

```bash
# 运行特定测试文件
pytest tests/unit/test_config.py -v

# 运行特定测试类
pytest tests/unit/test_indexer.py::TestIndexManager -v

# 运行特定测试方法
pytest tests/unit/test_indexer.py::TestIndexManager::test_build_index -v
```

### 按关键字过滤

```bash
# 运行包含关键字的测试
pytest tests/unit -k "config" -v

# 运行标记为unit的测试
pytest -m unit -v
```

---

## 测试文件列表

### 核心模块测试

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_config.py` | `src.config` | ~15 | 配置管理、环境变量、参数验证 |
| `test_data_loader.py` | `src.data_loader` | ~20 | Markdown、Web、GitHub 数据加载 |
| `test_indexer.py` | `src.indexer` | ~15 | 索引构建、向量化、检索 |
| `test_query_engine.py` | `src.query_engine` | ~8 | 查询引擎、引用溯源 |
| `test_chat_manager.py` | `src.chat_manager` | ~15 | 对话管理、会话持久化 |

### Embedding 和数据处理

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_embeddings.py` | `src.embeddings` | ~10 | 本地/API Embedding |
| `test_data_source.py` | `src.data_source` | ~8 | 数据源接口和实现 |
| `test_wikipedia_loader.py` | `src.data_loader` | ~6 | Wikipedia 数据加载 |

### 检索和路由

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_query_router.py` | `src.routers` | ~8 | 查询路由逻辑 |
| `test_grep_retriever.py` | `src.retrievers` | ~8 | Grep 检索器 |
| `test_multi_strategy_retriever.py` | `src.retrievers` | ~10 | 多策略检索器 |
| `test_result_merger.py` | `src.retrievers` | ~6 | 结果合并逻辑 |
| `test_reranker.py` | `src.rerankers` | ~8 | 重排序功能 |

### 业务和服务

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_registry.py` | `src.business.registry` | ~8 | 模块注册表 |
| `test_strategy_manager.py` | `src.business.strategy_manager` | ~10 | 策略配置和管理 |
| `test_pipeline_executor.py` | `src.business.pipeline` | ~8 | 流水线执行逻辑 |
| `test_rag_service.py` | `src.business.services` | ~15 | RAG服务单元测试 |
| `test_prompts.py` | `src.business.prompts` | ~20 | 提示工程模块测试 |

### 工具和格式化

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_response_formatter.py` | `src.response_formatter` | ~6 | 响应格式化和验证 |
| `test_github_link.py` | `src.github_link` | ~8 | GitHub链接生成器测试 |

### 可观测性

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_observers.py` | `src.observers` | ~8 | Phoenix、Debug 观察者 |

### 用户和仓库管理

| 测试文件 | 目标模块 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_user_manager.py` | `src.user_manager` | ~8 | 用户注册、登录、隔离 |
| `test_git_repository_manager.py` | `src.git_repository_manager` | ~8 | GitHub 仓库同步 |

---

## 常用命令

### 运行测试

```bash
# 运行所有单元测试
pytest tests/unit -v

# 运行特定文件
pytest tests/unit/test_config.py -v

# 运行并显示覆盖率
pytest tests/unit/test_config.py --cov=src/config --cov-report=term

# 只运行失败的测试
pytest tests/unit --lf -v

# 先运行失败的测试
pytest tests/unit --ff -v
```

### 调试测试

```bash
# 详细错误信息
pytest tests/unit/test_xxx.py -vv --tb=long

# 显示print输出
pytest tests/unit/test_xxx.py -s

# 失败时进入调试器
pytest tests/unit/test_xxx.py --pdb
```

### 覆盖率

```bash
# 基础覆盖率
pytest tests/unit/test_config.py --cov=src/config

# 显示未覆盖行
pytest tests/unit/test_config.py --cov=src/config --cov-report=term-missing

# 生成HTML报告
pytest tests/unit/test_config.py --cov=src/config --cov-report=html
# 然后打开 htmlcov/index.html
```

---

## 编写规范

### 文件命名

- **格式**: `test_<模块名>.py` (如 `test_indexer.py`)
- **对应**: `src/<模块名>.py`

### 测试类命名

- **格式**: `Test<类名>` 或 `Test<功能描述>`
- **示例**: 
  - `TestIndexManager` (测试 `IndexManager` 类)
  - `TestConfigValidation` (测试配置验证功能)

### 测试函数命名

- **格式**: `test_<功能>_<场景>`
- **示例**:
  - `test_build_index_with_valid_documents` (正常流程)
  - `test_build_index_with_empty_documents` (边界条件)
  - `test_build_index_handles_invalid_input` (异常情况)

### 测试模式

遵循 AAA 模式（Arrange-Act-Assert）：

```python
def test_build_index_with_valid_documents():
    # Arrange: 准备测试数据
    documents = [Document(text="test")]
    index_manager = IndexManager()
    
    # Act: 执行被测试的功能
    result = index_manager.build_index(documents)
    
    # Assert: 验证结果
    assert result is not None
    assert index_manager.get_stats()["document_count"] == 1
```

### Mock 使用

单元测试必须使用 Mock，避免外部依赖：

```python
from unittest.mock import Mock, patch

def test_query_with_mocked_embedding():
    # 使用Mock替代真实Embedding模型
    mock_embedding = Mock(return_value=[0.1, 0.2, 0.3])
    
    with patch('src.embeddings.get_embedding', mock_embedding):
        result = query_engine.query("test query")
        assert result is not None
```

---

## 实战场景

### 场景1: 修改配置模块后

```bash
# 验证配置模块
pytest tests/unit/test_config.py -v

# 运行相关模块
pytest tests/unit -k "config" -v

# 查看覆盖率
pytest tests/unit/test_config.py --cov=src/config --cov-report=term
```

### 场景2: 添加新功能后

```bash
# 运行单元测试验证新功能
pytest tests/unit/test_data_loader.py -v

# 运行集成测试验证协作
pytest tests/integration/test_data_pipeline.py -v

# 查看覆盖率
pytest tests/unit/test_data_loader.py --cov=src/data_loader --cov-report=html
```

### 场景3: 优化性能后

```bash
# 运行相关单元测试确保功能正常
pytest tests/unit/test_indexer.py -v

# 运行性能测试验证优化效果
pytest tests/performance/test_performance.py::test_indexing_speed -v
```

---

## 最佳实践

### 1. 测试隔离

- 每个测试应该独立运行
- 使用 fixtures 准备测试环境
- 测试之间不共享状态

### 2. Mock 外部依赖

- 数据库连接 → Mock
- API 调用 → Mock
- 文件系统操作 → Mock 或使用临时文件
- 网络请求 → Mock

### 3. 测试覆盖

- 正常流程（happy path）
- 边界条件（空值、极值）
- 异常情况（错误输入、异常处理）

### 4. 测试速度

- 单元测试应该快速执行（毫秒级）
- 避免真实的外部依赖
- 使用 Mock 替代慢速操作

### 5. 可读性

- 测试名称清晰描述测试内容
- 使用有意义的断言消息
- 添加必要的注释说明复杂逻辑

---

## 常见问题

### Q1: 如何跳过需要真实API的测试？

**A**: 测试会自动检测API密钥。没有设置相关环境变量时测试会自动跳过。

```bash
pytest tests/unit -v -rs  # 查看跳过的测试
```

### Q2: 测试运行很慢怎么办？

**A**: 
- 确保使用 Mock 替代真实依赖
- 只运行相关测试：`pytest tests/unit/test_xxx.py -v`
- 使用 `--lf` 只运行失败的测试

### Q3: 如何调试失败的测试？

**A**: 
```bash
# 详细错误信息
pytest tests/unit/test_xxx.py -vv --tb=long

# 显示print输出
pytest tests/unit/test_xxx.py -s

# 进入调试器
pytest tests/unit/test_xxx.py --pdb
```

---

## 相关文档

- **测试使用指南**: `../README.md` (总入口)
- **Agent测试体系**: `../agent/README.md` (Agent使用指南)
- **测试规范**: `.cursor/rules/testing-standards.mdc` (详细规范)

---

**最后更新**: 2025-11-03

