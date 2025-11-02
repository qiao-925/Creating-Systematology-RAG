# 测试指南

## 概述

本目录包含模块化RAG项目的全面测试套件，按照测试金字塔原则组织：

- **单元测试** (`tests/unit/`) - 测试单个模块和组件
- **集成测试** (`tests/integration/`) - 测试模块间协作
- **E2E测试** (`tests/e2e/`) - 测试完整业务流程
- **UI测试** (`tests/ui/`) - 测试Streamlit用户界面
- **性能测试** (`tests/performance/`) - 性能基准测试
- **兼容性测试** (`tests/compatibility/`) - 向后兼容和跨平台测试
- **回归测试** (`tests/regression/`) - 功能回归验证

## 快速开始

### 运行所有测试

```bash
# 运行所有测试
python tests/run_all_tests.py

# 或使用pytest直接运行
pytest tests/ -v
```

### 运行特定类型的测试

```bash
# 仅运行单元测试
pytest tests/unit/ -v

# 仅运行集成测试
pytest tests/integration/ -v

# 仅运行E2E测试
pytest tests/e2e/ -v

# 运行性能测试（需要标记）
pytest tests/performance/ -m performance -v
```

### 生成覆盖率报告

```bash
# 生成覆盖率报告
python tests/generate_coverage_report.py

# 或使用pytest-cov
pytest --cov=src --cov-report=html tests/
```

### 生成综合测试报告

```bash
# 首先生成测试执行结果和覆盖率数据
python tests/run_all_tests.py
python tests/generate_coverage_report.py

# 然后生成综合报告
python tests/generate_test_report.py
```

## 测试结构

### 单元测试

- `test_embeddings.py` - Embedding模块测试
- `test_data_source.py` - 数据源模块测试
- `test_observers.py` - 可观测性模块测试
- `test_query_router.py` - 查询路由测试
- `test_grep_retriever.py` - Grep检索器测试
- `test_multi_strategy_retriever.py` - 多策略检索器测试
- `test_result_merger.py` - 结果合并测试
- `test_pipeline_executor.py` - 流水线执行器测试
- `test_registry.py` - 模块注册表测试
- `test_strategy_manager.py` - 策略管理器测试

### 集成测试

- `test_rag_service_integration.py` - RAG服务集成测试
- `test_multi_strategy_integration.py` - 多策略检索集成测试
- `test_auto_routing_integration.py` - 自动路由集成测试
- `test_reranker_integration.py` - 重排序集成测试
- `test_observability_integration.py` - 可观测性集成测试

### E2E测试

- `test_core_workflows.py` - 核心业务流程E2E测试

### UI测试

- `test_app.py` - Streamlit应用UI测试

### 性能测试

- `test_query_performance.py` - 查询性能测试
- `test_multi_strategy_performance.py` - 多策略检索性能测试
- `test_reranker_performance.py` - 重排序性能测试

### 兼容性测试

- `test_backward_compatibility.py` - 向后兼容性测试
- `test_cross_platform.py` - 跨平台兼容性测试

### 回归测试

- `test_core_features.py` - 核心功能回归测试
- `test_ui_features.py` - UI功能回归测试

## 测试工具

### 测试执行器

`run_all_tests.py` - 批量执行所有测试，按阶段组织，记录失败用例

### 覆盖率生成器

`generate_coverage_report.py` - 生成代码覆盖率报告（HTML、JSON、XML格式）

### 报告生成器

`generate_test_report.py` - 整合测试结果和覆盖率数据，生成综合Markdown报告

## 报告输出

所有报告文件保存在 `tests/reports/` 目录：

- `test_report_YYYYMMDD_HHMMSS.json` - 测试执行结果（JSON）
- `test_summary_YYYYMMDD_HHMMSS.txt` - 测试执行摘要（文本）
- `coverage/html/index.html` - 覆盖率HTML报告
- `coverage/coverage_YYYYMMDD_HHMMSS.json` - 覆盖率数据（JSON）
- `coverage/coverage_YYYYMMDD_HHMMSS.xml` - 覆盖率数据（XML）
- `test_report_YYYYMMDD_HHMMSS.md` - 综合测试报告（Markdown）

## 测试标记

使用pytest标记来分类测试：

- `@pytest.mark.performance` - 性能测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.e2e` - E2E测试
- `@pytest.mark.ui` - UI测试
- `@pytest.mark.slow` - 慢速测试

运行带标记的测试：

```bash
pytest -m performance  # 仅运行性能测试
pytest -m "not slow"   # 排除慢速测试
```

## 测试数据

测试使用的数据文件位于：

- `tests/fixtures/` - 测试夹具和数据文件

## 持续集成

这些测试可以集成到CI/CD流程中：

```yaml
# 示例 GitHub Actions 配置
- name: Run Tests
  run: python tests/run_all_tests.py

- name: Generate Coverage
  run: python tests/generate_coverage_report.py

- name: Generate Report
  run: python tests/generate_test_report.py
```

## 注意事项

1. **性能测试**可能需要较长时间，建议单独运行
2. **E2E测试**需要完整的环境配置，包括索引数据
3. **UI测试**可能需要实际的Streamlit服务运行
4. 某些测试可能需要特定的环境变量或配置

## 维护

定期更新测试用例以确保：

- 新功能有对应的测试
- 修复的bug有回归测试
- 性能基准保持更新
- 覆盖率保持在目标水平（≥80%）


