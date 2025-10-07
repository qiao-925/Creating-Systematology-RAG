# 测试快速开始

> 5分钟开始运行测试

## 🚀 快速运行测试

### 方式一：使用Makefile（推荐）

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试  
make test-integration

# 查看覆盖率
make test-cov
```

### 方式二：使用pytest

```bash
# 1. 安装测试依赖
uv sync --extra test

# 2. 运行所有测试
pytest

# 3. 运行特定测试
pytest tests/unit -v
```

### 方式三：使用测试脚本

```bash
# 运行完整测试流程
./run_tests.sh
```

## 📊 测试统计

当前测试覆盖：

```
测试文件：    8个
测试函数：    88个
测试数据：    2个示例文档

分布：
├── 单元测试：   5个文件，约60个测试
├── 集成测试：   2个文件，约15个测试
└── 性能测试：   1个文件，约13个测试
```

## ✅ 测试清单

### 单元测试（tests/unit/）

- [x] **test_config.py** (约15个测试)
  - 配置初始化
  - 配置验证
  - 路径解析
  - 参数化测试

- [x] **test_data_loader.py** (约20个测试)
  - MarkdownLoader功能
  - WebLoader功能
  - DocumentProcessor功能
  - 便捷函数测试
  - 参数化文件扩展名测试

- [x] **test_indexer.py** (约15个测试)
  - 索引构建
  - 索引检索
  - 增量索引
  - 索引清空
  - 参数化分块测试

- [x] **test_query_engine.py** (约8个测试)
  - QueryEngine基础功能
  - SimpleQueryEngine功能
  - 引用来源格式化
  - Mock LLM测试

- [x] **test_chat_manager.py** (约15个测试)
  - ChatTurn数据类
  - ChatSession会话管理
  - ChatManager对话管理
  - 会话持久化

### 集成测试（tests/integration/）

- [x] **test_data_pipeline.py** (约8个测试)
  - 加载→索引流程
  - 增量加载
  - 重建索引
  - 元数据一致性

- [x] **test_query_pipeline.py** (约7个测试)
  - 索引→检索流程
  - 完整查询流程
  - 多次查询
  - 检索相关性

### 性能测试（tests/performance/）

- [x] **test_performance.py** (约6个测试)
  - 索引性能
  - 搜索延迟
  - 扩展性测试
  - 内存使用

## 🎯 测试示例

### 运行单个测试文件

```bash
pytest tests/unit/test_config.py -v
```

### 运行单个测试函数

```bash
pytest tests/unit/test_config.py::TestConfig::test_config_initialization -v
```

### 运行带标记的测试

```bash
# 跳过慢速测试
pytest -m "not slow" -v

# 只运行单元测试
pytest -m unit -v

# 运行性能测试
pytest -m performance -v
```

### 查看详细输出

```bash
pytest -vv --tb=long
```

### 只运行失败的测试

```bash
pytest --lf
```

## 📈 覆盖率报告

运行测试并查看覆盖率：

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 在浏览器中打开
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔍 测试输出说明

### 成功的测试

```
tests/unit/test_config.py::TestConfig::test_config_initialization PASSED [100%]
```

- `PASSED` - 测试通过 ✅
- `[100%]` - 测试进度

### 失败的测试

```
tests/unit/test_config.py::TestConfig::test_example FAILED

AssertionError: assert False
```

- `FAILED` - 测试失败 ❌
- 会显示详细的错误信息

### 跳过的测试

```
tests/unit/test_query_engine.py::TestQueryEngine::test_real_api SKIPPED
```

- `SKIPPED` - 测试被跳过 ⏭️
- 通常是因为缺少API密钥或标记为slow

## ⚡ 常用命令速查

| 需求 | 命令 |
|------|------|
| 运行所有测试 | `make test` 或 `pytest` |
| 只运行单元测试 | `make test-unit` |
| 只运行集成测试 | `make test-integration` |
| 查看覆盖率 | `make test-cov` |
| 跳过慢速测试 | `make test-fast` |
| 运行特定文件 | `pytest tests/unit/test_config.py` |
| 重新运行失败的 | `pytest --lf` |
| 查看详细输出 | `pytest -vv` |

## 💡 开发工作流

### 1. 开发前

```bash
# 确保测试通过
make test-fast
```

### 2. 开发中

```bash
# 只运行相关的测试
pytest tests/unit/test_your_module.py -v
```

### 3. 提交前

```bash
# 运行所有测试（包括慢速测试）
make test

# 检查覆盖率
make test-cov
```

## 🐛 调试失败的测试

### 1. 查看详细错误信息

```bash
pytest tests/unit/test_config.py -vv --tb=long
```

### 2. 进入Python调试器

```bash
pytest --pdb
```

测试失败时会自动进入pdb调试器。

### 3. 只运行失败的测试

```bash
pytest --lf -v
```

### 4. 打印测试输出

```python
def test_example():
    print("调试信息")  # 使用 pytest -s 查看
    assert True
```

```bash
pytest -s  # 显示print输出
```

## ❓ 常见问题

### Q: 测试运行很慢？

A: 使用 `make test-fast` 跳过慢速测试（需要API的测试）。

### Q: 如何只运行修改的测试？

A: 使用 `pytest --lf` 只运行上次失败的测试。

### Q: 覆盖率如何提高？

A: 
1. 查看覆盖率报告找到未覆盖的代码
2. 为未覆盖的函数添加测试
3. 运行 `make test-cov` 验证

### Q: 测试需要API密钥吗？

A: 大部分测试使用Mock，不需要真实API。只有标记为 `@pytest.mark.slow` 的测试需要真实API密钥。

## 📚 相关文档

- [测试指南](TESTING_GUIDE.md) - 完整的测试体系说明
- [开发者指南](DEVELOPER_GUIDE.md) - 开发说明
- [项目结构](PROJECT_STRUCTURE.md) - 目录组织

---

**提示**: 建议每次提交代码前运行 `make test` 确保所有测试通过！

