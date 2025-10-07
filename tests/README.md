# 测试说明

## 快速开始

### 1. 安装测试依赖

```bash
uv sync --extra test
```

### 2. 运行所有测试

```bash
pytest
```

### 3. 运行特定测试

```bash
# 只运行单元测试
pytest tests/unit -v

# 运行特定文件
pytest tests/unit/test_config.py -v

# 运行特定测试函数
pytest tests/unit/test_config.py::TestConfig::test_config_initialization -v
```

### 4. 查看覆盖率

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## 测试组织

```
tests/
├── conftest.py              # 共享fixtures和配置
├── unit/                    # 单元测试
│   ├── test_config.py
│   ├── test_data_loader.py
│   ├── test_indexer.py
│   ├── test_query_engine.py
│   └── test_chat_manager.py
├── integration/             # 集成测试
├── e2e/                     # 端到端测试
├── performance/             # 性能测试
└── fixtures/                # 测试数据
```

## 测试标记

使用pytest标记来分类测试：

```bash
# 只运行单元测试
pytest -m unit

# 跳过慢速测试
pytest -m "not slow"

# 只运行需要API的测试（需要设置真实API密钥）
pytest -m requires_real_api
```

## 编写测试

参考现有测试文件，遵循以下模式：

```python
class TestYourModule:
    """模块测试类"""
    
    def test_specific_function(self, fixture_name):
        """测试特定功能
        
        使用AAA模式：
        - Arrange: 准备测试数据
        - Act: 执行被测试代码
        - Assert: 验证结果
        """
        # Arrange
        ...
        
        # Act
        result = function_to_test()
        
        # Assert
        assert result == expected
```

## 常见问题

### Q: 如何跳过需要API的测试？

A: 测试会自动检测API密钥。如果没有真实的API密钥，会自动跳过。

### Q: 如何查看详细的测试输出？

A: 使用 `-v` 或 `-vv` 参数：

```bash
pytest -vv
```

### Q: 如何只运行失败的测试？

A: 使用 `--lf` 参数：

```bash
pytest --lf
```

更多信息请参考 [测试指南](../docs/TESTING_GUIDE.md)

