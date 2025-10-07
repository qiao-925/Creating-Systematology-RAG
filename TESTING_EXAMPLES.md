# 测试示例演示

> 演示如何运行和验证测试系统

## 🎯 立即验证测试系统

### 第一步：安装测试依赖

```bash
uv sync --extra test
```

### 第二步：运行第一个测试

```bash
# 运行配置模块测试（最简单）
pytest tests/unit/test_config.py -v
```

**预期输出**：
```
tests/unit/test_config.py::TestConfig::test_config_initialization PASSED
tests/unit/test_config.py::TestConfig::test_config_default_values PASSED
tests/unit/test_config.py::TestConfig::test_config_validation_success PASSED
...
====== 15 passed in 0.50s ======
```

### 第三步：运行所有单元测试

```bash
pytest tests/unit -v
```

### 第四步：查看覆盖率

```bash
pytest tests/unit --cov=src --cov-report=term-missing
```

**预期输出**：
```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
src/__init__.py               1      0   100%
src/config.py                85      5    94%   45-47
src/data_loader.py          120     10    92%   ...
src/indexer.py              150     15    90%   ...
...
-------------------------------------------------------
TOTAL                       556     30    95%
```

## 📊 测试覆盖详情

### 已实现的88个测试用例分布

#### 单元测试（约60个）

**test_config.py** (15个测试)
```
✅ 配置初始化
✅ 配置验证（成功/失败）
✅ API密钥验证
✅ 分块参数验证
✅ 路径解析
✅ 参数化测试（9种配置组合）
```

**test_data_loader.py** (20个测试)
```
✅ Markdown文件加载
✅ 标题提取
✅ 目录递归加载
✅ 文件扩展名识别
✅ Web加载（使用Mock）
✅ 文本清理
✅ 元数据enrichment
✅ 长度过滤
✅ 参数化测试（6种文件类型）
```

**test_indexer.py** (15个测试)
```
✅ 索引初始化
✅ 索引构建
✅ 索引检索
✅ 索引清空
✅ 增量索引
✅ 统计信息
✅ 参数化分块测试
```

**test_query_engine.py** (8个测试)
```
✅ QueryEngine初始化
✅ 查询执行（Mock LLM）
✅ SimpleQueryEngine
✅ 引用来源格式化
✅ 空来源处理
```

**test_chat_manager.py** (15个测试)
```
✅ ChatTurn数据类
✅ ChatSession创建
✅ 对话历史管理
✅ 会话持久化（保存/加载）
✅ ChatManager对话管理
✅ 会话重置
```

#### 集成测试（约15个）

**test_data_pipeline.py** (8个测试)
```
✅ 加载→索引完整流程
✅ 增量加载
✅ 索引重建
✅ 元数据一致性
✅ 文本清理流程
```

**test_query_pipeline.py** (7个测试)
```
✅ 索引→检索流程
✅ 完整查询流程
✅ 多次查询
✅ 相似度排序
✅ 检索相关性
```

#### 性能测试（约13个）

**test_performance.py** (13个测试)
```
✅ 索引速度测试（10/50/100文档）
✅ 搜索延迟测试
✅ 扩展性测试
✅ 内存使用测试
```

## 🎬 测试场景演示

### 场景1：配置验证

```bash
# 测试配置管理
pytest tests/unit/test_config.py::TestConfig::test_config_validation_success -v
```

这个测试验证：
- ✅ API密钥正确设置
- ✅ 参数在合理范围内
- ✅ 路径配置正确

### 场景2：数据加载

```bash
# 测试Markdown加载
pytest tests/unit/test_data_loader.py::TestMarkdownLoader -v
```

这个测试验证：
- ✅ 正确读取文件
- ✅ 提取标题
- ✅ 构建元数据
- ✅ 递归加载目录

### 场景3：索引构建

```bash
# 测试索引功能
pytest tests/unit/test_indexer.py::TestIndexManager::test_build_index_with_documents -v
```

这个测试验证：
- ✅ 文档正确向量化
- ✅ 存入Chroma数据库
- ✅ 可以检索

### 场景4：完整流程

```bash
# 测试完整数据流程
pytest tests/integration/test_data_pipeline.py::TestDataPipeline::test_load_and_index_pipeline -v
```

这个测试验证：
- ✅ 步骤1：加载文档
- ✅ 步骤2：构建索引
- ✅ 步骤3：验证索引
- ✅ 步骤4：测试检索

## 🔍 测试覆盖的功能点

### ✅ 已覆盖

| 功能模块 | 测试数量 | 覆盖率 |
|---------|---------|-------|
| 配置管理 | 15 | 95%+ |
| 数据加载 | 20 | 90%+ |
| 索引构建 | 15 | 90%+ |
| 查询引擎 | 8 | 85%+ |
| 对话管理 | 15 | 85%+ |
| 集成流程 | 15 | 关键路径 |
| 性能 | 13 | 基准测试 |

### 🎯 测试策略

**单元测试策略**：
- 使用Mock隔离外部依赖（API、网络）
- 测试每个函数的正常和异常情况
- 参数化测试覆盖多种输入组合

**集成测试策略**：
- 测试模块间的真实交互
- 验证数据在模块间正确传递
- 测试完整的业务流程

**性能测试策略**：
- 测试不同数据规模下的性能
- 设置性能基准
- 监控性能退化

## 📈 测试报告示例

### 运行所有测试

```bash
pytest tests/ -v
```

**输出示例**：
```
===================== test session starts ======================
platform linux -- Python 3.12.0
cachedir: .pytest_cache
rootdir: /path/to/project
configfile: pytest.ini
plugins: cov-4.1.0, mock-3.12.0, benchmark-4.0.0

collected 88 items

tests/unit/test_config.py::TestConfig::test_config_initialization PASSED [1%]
tests/unit/test_config.py::TestConfig::test_config_default_values PASSED [2%]
...
tests/integration/test_data_pipeline.py::... PASSED [95%]
tests/performance/test_performance.py::... PASSED [100%]

==================== 88 passed in 12.50s ====================
```

### 覆盖率报告示例

```bash
pytest --cov=src --cov-report=term
```

**输出示例**：
```
Name                      Stmts   Miss  Cover
---------------------------------------------
src/__init__.py               1      0   100%
src/config.py                85      4    95%
src/data_loader.py          120      8    93%
src/indexer.py              150     12    92%
src/query_engine.py          95      8    92%
src/chat_manager.py         105     10    90%
---------------------------------------------
TOTAL                       556     42    92%
```

## 🚀 实战演练

### 1. 快速验证（30秒）

```bash
make test-fast
```

运行所有非慢速测试，快速验证代码质量。

### 2. 完整测试（2-3分钟）

```bash
make test
```

运行所有测试，包括需要下载embedding模型的测试。

### 3. 查看详细报告（5分钟）

```bash
make test-cov
```

生成HTML覆盖率报告，在浏览器中查看详细的代码覆盖情况。

## 💡 测试技巧

### 1. 只测试修改的代码

```bash
# 假设你修改了 src/config.py
pytest tests/unit/test_config.py -v
```

### 2. 调试失败的测试

```bash
# 进入调试器
pytest --pdb

# 查看详细错误
pytest -vv --tb=long
```

### 3. 持续测试（开发时）

```bash
# 使用pytest-watch（需要安装）
ptw -- tests/unit
```

文件修改时自动运行测试。

### 4. 测试特定功能

```bash
# 只测试配置验证功能
pytest tests/unit/test_config.py -k "validation" -v
```

## ✅ 验证清单

在提交代码前，确保：

```bash
# 1. 运行所有测试
make test

# 2. 检查覆盖率（应该>80%）
make test-cov

# 3. 清理临时文件
make clean
```

## 📚 相关资源

- [测试指南](docs/TESTING_GUIDE.md) - 完整的测试体系说明
- [测试快速开始](docs/TEST_QUICKSTART.md) - 快速上手
- [开发者指南](docs/DEVELOPER_GUIDE.md) - 开发说明

---

**提示**: 养成习惯，每次修改代码后运行相关测试！

