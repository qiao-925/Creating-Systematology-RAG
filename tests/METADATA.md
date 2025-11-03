# 测试元数据说明文档

> **文档类型**: 测试元数据结构和用途说明  
> **版本**: 1.0  
> **更新日期**: 2025-11-03

---

## 📖 文档说明

本文档说明测试元数据索引（`test_index.json`）的结构、用途和生成方式。元数据索引帮助 Agent 快速理解测试体系，智能选择相关测试。

---

## 🎯 元数据索引的用途

1. **Agent 测试识别**: Agent 可以根据源文件路径快速找到相关测试
2. **测试覆盖分析**: 了解每个测试文件覆盖的功能范围
3. **依赖关系追踪**: 了解测试的依赖关系和前置条件
4. **测试分类查询**: 根据标签和分类快速筛选测试
5. **测试选择自动化**: 支持智能测试选择工具

---

## 📋 元数据结构

### 顶层结构

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

### 测试文件元数据结构

每个测试文件的元数据包含以下字段：

```json
{
  "file_path": "tests/unit/test_indexer.py",
  "category": "unit",
  "target_module": "src.indexer",
  "target_class": "IndexManager",
  "target_functions": ["build_index", "query_index", "clear_index"],
  "test_count": 15,
  "description": "测试索引管理器的核心功能，包括索引构建、查询、清理等",
  "coverage": [
    "build_index",
    "query_index",
    "clear_index",
    "get_stats",
    "get_index"
  ],
  "dependencies": [
    "conftest.prepared_index_manager",
    "conftest.sample_documents"
  ],
  "tags": ["unit", "indexing", "vector_store"],
  "pytest_markers": ["unit"],
  "fixtures_used": [
    "temp_index_manager",
    "sample_documents",
    "temp_vector_store"
  ],
  "related_tests": [
    "tests/integration/test_data_pipeline.py"
  ],
  "source_files": [
    "src/indexer.py"
  ]
}
```

### 字段说明

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

---

## 🔧 元数据生成

### 自动生成工具

使用 `tests/tools/generate_test_index.py` 自动生成元数据索引：

```bash
# 生成或更新测试索引
python tests/tools/generate_test_index.py

# 输出到指定文件
python tests/tools/generate_test_index.py -o tests/test_index_custom.json
```

### 生成逻辑

工具会：
1. 扫描 `tests/` 目录下的所有测试文件
2. 解析测试文件的 AST（抽象语法树）
3. 提取测试类、测试函数、fixtures 等信息
4. 分析源文件导入关系，推断目标模块
5. 提取 docstring 和注释作为描述
6. 生成 JSON 格式的元数据索引

### 手动维护

对于复杂或自动生成不准确的情况，可以手动编辑 `test_index.json` 或添加元数据注释到测试文件中：

```python
"""
测试索引元数据:
- category: unit
- target_module: src.indexer
- target_class: IndexManager
- tags: [unit, indexing]
- description: 测试索引管理器的核心功能
"""
```

---

## 🤖 Agent 使用元数据

### 场景1: 查找相关测试

**输入**: 修改的文件 `src/indexer.py`

**查询流程**:
1. 读取 `test_index.json`
2. 查找 `source_files` 包含 `src/indexer.py` 的条目
3. 返回匹配的测试文件列表

**示例**:
```python
# 使用 agent_test_selector.py
python tests/tools/agent_test_selector.py src/indexer.py
# 输出: tests/unit/test_indexer.py
```

### 场景2: 了解测试覆盖范围

**输入**: 测试文件 `tests/unit/test_indexer.py`

**查询流程**:
1. 读取 `test_index.json`
2. 查找 `file_path` 匹配的条目
3. 返回 `coverage`、`description` 等信息

**示例**:
```python
# 使用 agent_test_info.py
python tests/tools/agent_test_info.py tests/unit/test_indexer.py
# 输出测试的详细信息
```

### 场景3: 选择测试分类

**输入**: 测试分类标签 `unit`

**查询流程**:
1. 读取 `test_index.json`
2. 筛选 `category == "unit"` 或 `tags` 包含 `"unit"` 的条目
3. 返回匹配的测试文件列表

---

## 📊 统计信息结构

元数据索引包含统计信息：

```json
{
  "statistics": {
    "total_test_files": 51,
    "by_category": {
      "unit": 20,
      "integration": 9,
      "e2e": 1,
      "performance": 6,
      "compatibility": 2,
      "regression": 2,
      "ui": 1
    },
    "total_test_cases": 250,
    "coverage_target": 90.0
  }
}
```

---

## 🔄 元数据更新

### 何时更新

- ✅ 添加新的测试文件时
- ✅ 修改测试文件结构时
- ✅ 修改源文件路径或模块结构时
- ✅ 定期维护（如每周）

### 更新命令

```bash
# 重新生成索引
python tests/tools/generate_test_index.py

# 验证索引完整性
python tests/tools/agent_test_info.py --validate
```

---

## ✅ 元数据验证

元数据索引应满足：

- ✅ 所有测试文件都有对应的元数据条目
- ✅ `file_path` 字段路径正确且文件存在
- ✅ `source_files` 中的路径指向存在的源文件
- ✅ `category` 字段符合预定义分类
- ✅ `test_count` 与实际测试数量一致（允许误差）

---

## 🔗 相关文档

- **Agent测试索引**: `tests/AGENTS-TESTING-INDEX.md` (主索引文档)
- **测试规范**: `.cursor/rules/testing-standards.mdc` (测试规范)
- **Agent测试整合**: `.cursor/rules/agent-testing-integration.mdc` (Agent整合规则)

---

**最后更新**: 2025-11-03  
**维护者**: 当元数据结构变更时更新本文档

