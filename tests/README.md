# 测试使用指南

> 从零开始，循序渐进掌握项目测试体系

## 📖 目录

- [第一步：环境准备](#第一步环境准备)
- [第二步：快速验证](#第二步快速验证)
- [第三步：深入测试](#第三步深入测试)
- [第四步：高级用法](#第四步高级用法)
- [测试体系说明](#测试体系说明)
- [常见问题](#常见问题)

---

## 第一步：环境准备

### 1.1 安装测试依赖

```bash
# 使用 uv 安装测试依赖
uv sync --extra test

# 或使用 make 命令
make install-test
```

**安装的依赖包括**：
- `pytest` - 测试框架
- `pytest-cov` - 覆盖率报告
- `pytest-mock` - Mock 工具
- `pytest-benchmark` - 性能测试
- `pytest-asyncio` - 异步测试支持

### 1.2 验证安装

```bash
pytest --version
```

预期输出：`pytest 7.4.0` 或更高版本

---

## 第二步：快速验证

### 2.1 运行第一个测试（30秒）⚡

从最简单的配置测试开始：

```bash
pytest tests/unit/test_config.py -v
```

**预期输出**：
```
tests/unit/test_config.py::TestConfig::test_config_initialization PASSED [6%]
tests/unit/test_config.py::TestConfig::test_config_default_values PASSED [13%]
tests/unit/test_config.py::TestConfig::test_config_validation_success PASSED [20%]
...
====== 15 passed in 0.50s ======
```

✅ **恭喜！** 如果看到这个输出，说明测试环境配置成功！

### 2.2 运行所有单元测试（1-2分钟）

```bash
pytest tests/unit -v
```

这将运行约 60 个单元测试，涵盖所有核心模块。
只运行上次失败的测试（最常用）
pytest --lf -v
# 或
pytest --last-failed -v

### 2.3 快速检查代码质量

```bash
# 运行快速测试（跳过慢速测试）
pytest tests/unit -m "not slow" -v

# 或使用 make 命令
make test-fast
```

---

## 第三步：深入测试

### 3.1 按模块测试

测试特定功能模块：

```bash
# 测试配置模块（15个测试）
pytest tests/unit/test_config.py -v

# 测试数据加载（20个测试）
pytest tests/unit/test_data_loader.py -v

# 测试索引构建（15个测试）
pytest tests/unit/test_indexer.py -v

# 测试查询引擎（8个测试）
pytest tests/unit/test_query_engine.py -v

# 测试对话管理（15个测试）
pytest tests/unit/test_chat_manager.py -v
```

### 3.2 集成测试（2-3分钟）

测试模块间的协作：

```bash
# 数据处理流程
pytest tests/integration/test_data_pipeline.py -v

# 查询流程
pytest tests/integration/test_query_pipeline.py -v

# 所有集成测试
pytest tests/integration -v
```

### 3.3 查看测试覆盖率

```bash
# 终端查看
pytest tests/unit --cov=src --cov-report=term-missing

# 生成 HTML 报告（推荐）
pytest tests/unit --cov=src --cov-report=html
# 然后在浏览器打开 htmlcov/index.html

# 或使用 make 命令
make test-cov
```

**预期覆盖率**：
```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
src/__init__.py               1      0   100%
src/config.py                85      4    95%   45-47
src/data_loader.py          120      8    93%   115-122
src/indexer.py              150     12    92%   78-85, 145-150
src/query_engine.py          95      8    92%   67-74
src/chat_manager.py         105     10    90%   88-97
-------------------------------------------------------
TOTAL                       556     42    92%
```

---

## 第四步：高级用法

### 4.1 运行特定测试

```bash
# 运行特定测试类
pytest tests/unit/test_config.py::TestConfig -v

# 运行特定测试函数
pytest tests/unit/test_config.py::TestConfig::test_config_initialization -v

# 使用关键字过滤
pytest tests/unit -k "validation" -v
```

### 4.2 测试标记

```bash
# 只运行单元测试
pytest -m unit -v

# 跳过慢速测试
pytest -m "not slow" -v

# 只运行需要真实API的测试
pytest -m requires_real_api -v

# 运行集成测试
pytest -m integration -v
```

### 4.3 调试测试

```bash
# 显示详细输出
pytest -vv

# 显示完整错误信息
pytest --tb=long

# 失败时进入调试器
pytest --pdb

# 只运行上次失败的测试
pytest --lf

# 先运行失败的测试
pytest --ff
```

### 4.4 性能测试

```bash
# 运行性能测试
pytest tests/performance -v

# 生成性能基准报告
pytest tests/performance --benchmark-only
```

### 4.5 并行测试（可选）

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用多核心运行测试
pytest tests/unit -n auto
```

---

## 测试体系说明

### 📂 测试结构

```
tests/
├── conftest.py              # 共享 fixtures 和配置
├── unit/                    # 单元测试（~60个）
│   ├── test_config.py          # 配置管理测试（15个）
│   ├── test_data_loader.py     # 数据加载测试（20个）
│   ├── test_indexer.py         # 索引构建测试（15个）
│   ├── test_query_engine.py    # 查询引擎测试（8个）
│   └── test_chat_manager.py    # 对话管理测试（15个）
├── integration/             # 集成测试（~15个）
│   ├── test_data_pipeline.py   # 数据处理流程（8个）
│   └── test_query_pipeline.py  # 查询流程（7个）
├── performance/             # 性能测试（~13个）
│   └── test_performance.py     # 性能基准测试
└── fixtures/                # 测试数据
    └── sample_docs/
```

### 📊 测试覆盖概览

| 功能模块 | 测试数量 | 覆盖率 | 说明 |
|---------|---------|-------|------|
| 配置管理 | 15 | 95%+ | API密钥、参数验证 |
| 数据加载 | 20 | 90%+ | Markdown、Web加载 |
| 索引构建 | 15 | 90%+ | 向量化、存储、检索 |
| 查询引擎 | 8 | 85%+ | 查询、引用溯源 |
| 对话管理 | 15 | 85%+ | 会话、历史管理 |
| 集成流程 | 15 | 关键路径 | 端到端流程 |
| 性能基准 | 13 | 基准测试 | 速度、扩展性 |

**总计**: 88+ 个测试用例，总体覆盖率 ~92%

### 🎯 测试策略

#### 单元测试策略
- ✅ 使用 Mock 隔离外部依赖（API、网络）
- ✅ 测试每个函数的正常和异常情况
- ✅ 参数化测试覆盖多种输入组合
- ✅ 快速执行（大部分 < 0.1秒）

#### 集成测试策略
- ✅ 测试模块间的真实交互
- ✅ 验证数据在模块间正确传递
- ✅ 测试完整的业务流程
- ✅ 使用临时数据库避免污染

#### 性能测试策略
- ✅ 测试不同数据规模下的性能
- ✅ 设置性能基准
- ✅ 监控性能退化
- ✅ 标记为 `slow` 可跳过

---

## 实战场景演示

### 场景1：修改配置模块后

```bash
# 1. 快速验证配置模块
pytest tests/unit/test_config.py -v

# 2. 确保相关模块正常
pytest tests/unit -k "config" -v

# 3. 检查覆盖率
pytest tests/unit/test_config.py --cov=src/config --cov-report=term
```

### 场景2：添加新的数据加载功能

```bash
# 1. 运行数据加载测试
pytest tests/unit/test_data_loader.py -v

# 2. 运行数据流程集成测试
pytest tests/integration/test_data_pipeline.py -v

# 3. 查看详细覆盖率
pytest tests/unit/test_data_loader.py --cov=src/data_loader --cov-report=html
```

### 场景3：优化索引性能

```bash
# 1. 运行性能测试（建立基准）
pytest tests/performance/test_performance.py::test_indexing_speed -v

# 2. 修改代码...

# 3. 再次运行性能测试（对比）
pytest tests/performance/test_performance.py::test_indexing_speed -v

# 4. 确保功能正常
pytest tests/unit/test_indexer.py -v
```

### 场景4：准备发布前

```bash
# 完整测试流程
make test              # 运行所有测试
make test-cov          # 生成覆盖率报告
make clean             # 清理临时文件

# 或一次性完成
make test-all
```

---

## 常见问题

### Q1: 如何跳过需要真实 API 的测试？

**A**: 测试会自动检测 API 密钥。如果没有设置 `DEEPSEEK_API_KEY`，相关测试会自动跳过。

```bash
# 查看跳过的测试
pytest tests/ -v -rs
```

### Q2: 测试运行很慢怎么办？

**A**: 使用以下方法加速：

```bash
# 1. 跳过慢速测试
pytest -m "not slow"

# 2. 只运行单元测试
pytest tests/unit

# 3. 并行运行
pytest -n auto

# 4. 只运行失败的测试
pytest --lf
```

### Q3: 如何调试失败的测试？

**A**: 逐步排查：

```bash
# 1. 查看详细错误
pytest tests/unit/test_xxx.py -vv --tb=long

# 2. 添加打印输出
pytest tests/unit/test_xxx.py -s

# 3. 进入调试器
pytest tests/unit/test_xxx.py --pdb

# 4. 只运行失败的测试
pytest --lf -vv
```

### Q4: 测试覆盖率太低怎么办？

**A**: 查找未覆盖代码：

```bash
# 生成详细报告
pytest --cov=src --cov-report=html

# 查看哪些行未覆盖
pytest --cov=src --cov-report=term-missing

# 浏览器查看详细信息
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

### Q5: 如何编写新的测试？

**A**: 参考现有测试，遵循 AAA 模式：

```python
class TestYourModule:
    """模块测试类"""
    
    def test_specific_function(self, sample_data):
        """测试特定功能
        
        使用 AAA 模式：
        - Arrange: 准备测试数据
        - Act: 执行被测试代码
        - Assert: 验证结果
        """
        # Arrange（准备）
        input_data = "test input"
        expected = "expected output"
        
        # Act（执行）
        result = function_to_test(input_data)
        
        # Assert（断言）
        assert result == expected
        assert isinstance(result, str)
```

### Q6: 如何使用 fixtures？

**A**: fixtures 定义在 `conftest.py` 中：

```python
def test_example(sample_documents, temp_vector_store):
    """使用共享 fixtures
    
    可用的 fixtures:
    - sample_documents: 测试文档列表
    - temp_vector_store: 临时向量存储目录
    - mock_api_key: Mock 的 API 密钥
    """
    # 使用 fixtures 进行测试
    assert len(sample_documents) > 0
```

---

## 快捷命令速查

### 基础命令

```bash
make install-test    # 安装测试依赖
make test           # 运行所有测试
make test-fast      # 快速测试（跳过慢速）
make test-cov       # 测试 + 覆盖率报告
make clean          # 清理临时文件
```

### 常用测试命令

```bash
# 按类型
pytest tests/unit            # 单元测试
pytest tests/integration     # 集成测试
pytest tests/performance     # 性能测试

# 按标记
pytest -m unit              # 单元测试标记
pytest -m integration       # 集成测试标记
pytest -m "not slow"        # 跳过慢速测试

# 输出控制
pytest -v                   # 详细输出
pytest -vv                  # 更详细输出
pytest -s                   # 显示 print 输出
pytest -q                   # 简洁输出

# 调试
pytest --lf                 # 只运行失败的
pytest --ff                 # 先运行失败的
pytest --pdb                # 失败时进入调试器

# 覆盖率
pytest --cov=src                              # 基础覆盖率
pytest --cov=src --cov-report=term-missing    # 显示未覆盖行
pytest --cov=src --cov-report=html            # HTML报告
```

---

## 💡 最佳实践

### 开发时

1. **每次修改后运行相关测试**
   ```bash
   # 修改了 config.py
   pytest tests/unit/test_config.py -v
   ```

2. **使用持续测试（可选）**
   ```bash
   pip install pytest-watch
   ptw -- tests/unit
   ```

3. **提交前运行完整测试**
   ```bash
   make test
   ```

### 编写测试时

1. **测试命名清晰**
   ```python
   def test_load_markdown_extracts_title():  # ✅ 好
   def test_load():                           # ❌ 不好
   ```

2. **一个测试一个断言焦点**
   ```python
   # ✅ 好
   def test_config_has_api_key():
       assert config.api_key is not None
   
   def test_config_api_key_is_string():
       assert isinstance(config.api_key, str)
   
   # ❌ 不好 - 测试太多东西
   def test_config():
       assert config.api_key is not None
       assert isinstance(config.api_key, str)
       assert config.chunk_size > 0
       # ...太多了
   ```

3. **使用 fixtures 共享设置**
   ```python
   @pytest.fixture
   def prepared_data():
       return {"key": "value"}
   
   def test_with_fixture(prepared_data):
       assert prepared_data["key"] == "value"
   ```

---

## 📚 相关资源

- 📖 [完整测试指南](../docs/TESTING_GUIDE.md) - 详细的测试体系文档
- 🚀 [快速开始](../docs/TEST_QUICKSTART.md) - 5分钟上手
- 💻 [开发者指南](../docs/DEVELOPER_GUIDE.md) - 开发规范

---

## ✅ 验证清单

在提交代码前，确保：

- [ ] 运行 `make test` 并全部通过
- [ ] 覆盖率 > 80%（运行 `make test-cov` 检查）
- [ ] 新功能有对应的测试
- [ ] 修复的 Bug 有回归测试
- [ ] 测试命名清晰易懂
- [ ] 清理了临时文件（`make clean`）

---

**💡 提示**: 
- 新手：从"第一步"和"第二步"开始
- 日常开发：常用"第三步"和"实战场景"
- 遇到问题：查看"常见问题"和"调试"部分

**记住**: 好的测试是代码质量的保障！🎯
