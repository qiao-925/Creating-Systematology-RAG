# 集成测试指南

> **文档类型**: 集成测试使用指南  
> **更新日期**: 2025-11-03

---

## 概述

集成测试用于测试多个模块协作和完整业务流程。这些测试验证模块间的交互和端到端功能。

---

## 快速开始

### 运行所有集成测试

```bash
# 方式1: 使用Makefile（推荐）
make test-integration

# 方式2: 直接使用pytest
pytest tests/integration -v
```

### 运行特定测试文件

```bash
# 运行特定测试文件
pytest tests/integration/test_query_pipeline.py -v

# 运行特定测试类
pytest tests/integration/test_rag_service_integration.py::TestRAGServiceIntegration -v

# 运行特定测试方法
pytest tests/integration/test_query_pipeline.py::TestQueryPipeline::test_index_to_retrieval_pipeline -v
```

### 按标记运行

```bash
# 运行标记为integration的测试
pytest -m integration -v

# 跳过GitHub E2E测试（需要网络）
pytest tests/integration -m "not github_e2e" -v
```

---

## 测试文件列表

### RAG服务集成

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_rag_service_integration.py` | RAG 服务完整流程 | ~15 | 文档导入 → 索引构建 → 查询 → 响应 |
| `test_modular_query_engine.py` | 模块化查询引擎 | ~20 | 多种检索策略、查询流程 |

### 查询和处理流程

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_query_pipeline.py` | 查询流水线 | ~7 | 完整查询处理流程 |
| `test_query_processing_integration.py` | 查询处理集成 | ~10 | 查询处理完整流程 |

### 检索策略集成

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_multi_strategy_integration.py` | 多策略检索集成 | ~10 | 多种检索策略协作 |
| `test_auto_routing_integration.py` | 自动路由集成 | ~8 | 查询自动路由到不同策略 |
| `test_reranker_integration.py` | 重排序集成 | ~8 | 检索结果重排序流程 |

### 数据处理和可观测性

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_data_pipeline.py` | 数据处理流水线 | ~8 | 数据加载和处理流程 |
| `test_observability_integration.py` | 可观测性集成 | ~8 | Phoenix 集成和追踪 |
| `test_phoenix_integration.py` | Phoenix 集成 | ~5 | Phoenix 可观测性平台 |

### 端到端测试

| 测试文件 | 测试范围 | 测试数量 | 说明 |
|---------|---------|---------|------|
| `test_github_e2e.py` | GitHub 端到端 | ~10 | GitHub 仓库完整流程 |

---

## 常用命令

### 运行测试

```bash
# 运行所有集成测试
pytest tests/integration -v

# 运行特定文件
pytest tests/integration/test_query_pipeline.py -v

# 跳过需要网络的测试
pytest tests/integration -m "not github_e2e" -v

# 只运行失败的测试
pytest tests/integration --lf -v
```

### 调试测试

```bash
# 详细错误信息
pytest tests/integration/test_xxx.py -vv --tb=long

# 显示print输出
pytest tests/integration/test_xxx.py -s

# 失败时进入调试器
pytest tests/integration/test_xxx.py --pdb
```

### 覆盖率

```bash
# 集成测试覆盖率
pytest tests/integration --cov=src --cov-report=term-missing

# 生成HTML报告
pytest tests/integration --cov=src --cov-report=html
```

---

## 编写规范

### 文件命名

- **格式**: `test_<功能>_integration.py` 或 `test_<功能>_pipeline.py`
- **示例**: 
  - `test_rag_service_integration.py`
  - `test_query_pipeline.py`

### 测试类命名

- **格式**: `Test<功能描述>Integration` 或 `Test<功能>Pipeline`
- **示例**: 
  - `TestRAGServiceIntegration`
  - `TestQueryPipeline`

### 测试函数命名

- **格式**: `test_<流程>_<场景>`
- **示例**:
  - `test_index_to_retrieval_pipeline` (索引到检索流程)
  - `test_multi_strategy_collaboration` (多策略协作)

### 测试标记

使用 pytest 标记区分不同类型的集成测试：

```python
@pytest.mark.integration
class TestQueryPipeline:
    """查询流程集成测试"""
    
    @pytest.mark.slow
    def test_complex_query_flow(self):
        """慢速测试"""
        pass
    
    @pytest.mark.github_e2e
    def test_github_workflow(self):
        """GitHub E2E测试"""
        pass
```

---

## 实战场景

### 场景1: 测试完整查询流程

```bash
# 运行查询流水线测试
pytest tests/integration/test_query_pipeline.py -v

# 运行模块化查询引擎测试
pytest tests/integration/test_modular_query_engine.py -v
```

### 场景2: 测试多策略检索

```bash
# 运行多策略集成测试
pytest tests/integration/test_multi_strategy_integration.py -v

# 运行自动路由测试
pytest tests/integration/test_auto_routing_integration.py -v
```

### 场景3: GitHub集成测试

```bash
# 运行GitHub E2E测试
pytest tests/integration/test_github_e2e.py -v

# 跳过GitHub测试（无网络时）
pytest tests/integration -m "not github_e2e" -v
```

---

## 注意事项

### 外部依赖

集成测试可能需要：
- 真实的向量数据库（ChromaDB）
- 真实的API密钥（部分测试）
- 网络连接（GitHub E2E测试）

### 测试跳过

测试会自动检测环境：
- 没有API密钥时，相关测试会自动跳过
- 使用 `-m "not github_e2e"` 跳过需要网络的测试
- 使用 `-m "not slow"` 跳过慢速测试

### 测试隔离

虽然集成测试涉及多个模块，但仍应：
- 使用临时目录和数据库
- 清理测试数据
- 避免测试间相互影响

---

## 相关文档

- **测试使用指南**: `../README.md` (总入口)
- **单元测试指南**: `../unit/README.md` (单元测试详细说明)
- **Agent测试体系**: `../agent/README.md` (Agent使用指南)

---

**最后更新**: 2025-11-03

