# 测试指南

> 完整的测试体系设计和实施方案

## 目录

- [测试策略](#测试策略)
- [测试金字塔](#测试金字塔)
- [单元测试](#单元测试)
- [集成测试](#集成测试)
- [端到端测试](#端到端测试)
- [RAG特定测试](#rag特定测试)
- [性能测试](#性能测试)
- [测试工具](#测试工具)
- [CI/CD集成](#cicd集成)

---

## 测试策略

### 测试金字塔

```
        /\
       /E2E\         端到端测试（少量，慢速）
      /------\       - 完整用户流程
     /        \      - UI交互测试
    /   集成   \     集成测试（中等数量，中速）
   /------------\    - 模块间交互
  /              \   - API集成
 /    单元测试     \  单元测试（大量，快速）
/------------------\ - 函数级别
                     - 类方法测试
```

### 测试覆盖率目标

| 测试类型 | 数量占比 | 覆盖率目标 | 执行速度 |
|---------|---------|-----------|---------|
| 单元测试 | 70% | 80%+ | < 1秒 |
| 集成测试 | 20% | 60%+ | < 30秒 |
| 端到端测试 | 10% | 关键路径 | < 2分钟 |

---

## 单元测试

### 测试框架：pytest

**为什么选择 pytest？**
- 简洁的语法
- 强大的fixture系统
- 丰富的插件生态
- 易于集成CI/CD

### 测试结构

```
tests/
├── unit/                          # 单元测试
│   ├── test_config.py            # 配置管理测试
│   ├── test_data_loader.py       # 数据加载测试
│   ├── test_indexer.py           # 索引构建测试
│   ├── test_query_engine.py      # 查询引擎测试
│   └── test_chat_manager.py      # 对话管理测试
├── integration/                   # 集成测试
│   ├── test_data_pipeline.py     # 数据处理流程测试
│   ├── test_query_pipeline.py    # 查询流程测试
│   └── test_chat_pipeline.py     # 对话流程测试
├── e2e/                          # 端到端测试
│   ├── test_web_app.py           # Web应用测试
│   └── test_cli.py               # CLI工具测试
├── performance/                   # 性能测试
│   ├── test_indexing_speed.py    # 索引速度测试
│   └── test_query_latency.py     # 查询延迟测试
├── fixtures/                      # 测试数据
│   ├── sample_docs/              # 示例文档
│   └── mock_responses.json       # Mock响应
├── conftest.py                   # pytest配置和共享fixtures
└── pytest.ini                    # pytest配置文件
```

### 单元测试示例

#### 1. 测试配置管理（test_config.py）

```python
import pytest
from pathlib import Path
from src.config import Config

class TestConfig:
    """配置管理单元测试"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = Config()
        assert config.PROJECT_ROOT.exists()
        assert isinstance(config.CHUNK_SIZE, int)
        assert config.CHUNK_SIZE > 0
    
    def test_config_validation_success(self, monkeypatch):
        """测试配置验证成功"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        config = Config()
        is_valid, error = config.validate()
        assert is_valid is True
        assert error is None
    
    def test_config_validation_missing_api_key(self, monkeypatch):
        """测试缺少API密钥"""
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        config = Config()
        is_valid, error = config.validate()
        assert is_valid is False
        assert "DEEPSEEK_API_KEY" in error
    
    def test_config_invalid_chunk_size(self, monkeypatch):
        """测试无效的分块大小"""
        monkeypatch.setenv("CHUNK_SIZE", "0")
        config = Config()
        is_valid, error = config.validate()
        assert is_valid is False
    
    def test_path_resolution(self, tmp_path):
        """测试路径解析"""
        config = Config()
        # 测试相对路径转换为绝对路径
        assert config.VECTOR_STORE_PATH.is_absolute()
```

#### 2. 测试数据加载器（test_data_loader.py）

```python
import pytest
from pathlib import Path
from src.data_loader import (
    MarkdownLoader,
    WebLoader,
    DocumentProcessor
)

class TestMarkdownLoader:
    """Markdown加载器测试"""
    
    @pytest.fixture
    def sample_markdown(self, tmp_path):
        """创建测试用的Markdown文件"""
        md_file = tmp_path / "test.md"
        content = """# 测试标题

这是测试内容。

## 子标题

更多内容。
"""
        md_file.write_text(content, encoding='utf-8')
        return md_file
    
    def test_load_markdown_file(self, sample_markdown):
        """测试加载Markdown文件"""
        loader = MarkdownLoader()
        doc = loader.load_file(sample_markdown)
        
        assert doc is not None
        assert "测试标题" in doc.text
        assert doc.metadata['file_name'] == 'test.md'
        assert doc.metadata['source_type'] == 'markdown'
        assert doc.metadata['title'] == '测试标题'
    
    def test_load_nonexistent_file(self, tmp_path):
        """测试加载不存在的文件"""
        loader = MarkdownLoader()
        doc = loader.load_file(tmp_path / "nonexistent.md")
        assert doc is None
    
    def test_load_directory(self, tmp_path):
        """测试加载目录"""
        # 创建多个测试文件
        (tmp_path / "doc1.md").write_text("# Doc 1")
        (tmp_path / "doc2.md").write_text("# Doc 2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "doc3.md").write_text("# Doc 3")
        
        loader = MarkdownLoader()
        docs = loader.load_directory(tmp_path, recursive=True)
        
        assert len(docs) == 3
        assert all(doc.metadata['source_type'] == 'markdown' for doc in docs)


class TestWebLoader:
    """Web加载器测试"""
    
    def test_load_url_with_mock(self, mocker):
        """测试加载URL（使用mock）"""
        # Mock requests.get
        mock_response = mocker.Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test.</p>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        mocker.patch('requests.get', return_value=mock_response)
        
        loader = WebLoader()
        doc = loader.load_url("https://example.com/test")
        
        assert doc is not None
        assert "Test Content" in doc.text
        assert "This is a test" in doc.text
        assert "console.log" not in doc.text  # script被移除
        assert doc.metadata['source_type'] == 'web'


class TestDocumentProcessor:
    """文档处理器测试"""
    
    def test_clean_text(self):
        """测试文本清理"""
        dirty_text = "这是    多余空格\n\n\n\n多余换行"
        clean = DocumentProcessor.clean_text(dirty_text)
        
        assert "    " not in clean  # 多余空格被清理
        assert "\n\n\n" not in clean  # 多余换行被清理
    
    def test_filter_by_length(self):
        """测试按长度过滤"""
        from llama_index.core import Document
        
        docs = [
            Document(text="短", metadata={}),
            Document(text="这是一个足够长的文档内容，应该被保留下来。" * 2, metadata={})
        ]
        
        filtered = DocumentProcessor.filter_by_length(docs, min_length=50)
        assert len(filtered) == 1
```

#### 3. 测试索引构建器（test_indexer.py）

```python
import pytest
from src.indexer import IndexManager
from llama_index.core import Document

class TestIndexManager:
    """索引管理器测试"""
    
    @pytest.fixture
    def temp_index_manager(self, tmp_path):
        """创建临时索引管理器"""
        return IndexManager(
            collection_name="test_collection",
            persist_dir=tmp_path / "vector_store",
            chunk_size=256,
            chunk_overlap=20
        )
    
    @pytest.fixture
    def sample_documents(self):
        """创建测试文档"""
        return [
            Document(
                text="系统科学是研究系统的科学。",
                metadata={"title": "系统科学", "id": 1}
            ),
            Document(
                text="钱学森是系统科学的创建者。",
                metadata={"title": "钱学森", "id": 2}
            )
        ]
    
    def test_build_index(self, temp_index_manager, sample_documents):
        """测试构建索引"""
        index = temp_index_manager.build_index(sample_documents)
        
        assert index is not None
        stats = temp_index_manager.get_stats()
        assert stats['document_count'] > 0
    
    def test_search(self, temp_index_manager, sample_documents):
        """测试搜索功能"""
        temp_index_manager.build_index(sample_documents)
        
        results = temp_index_manager.search("系统科学", top_k=2)
        
        assert len(results) > 0
        assert results[0]['score'] > 0
        assert "系统科学" in results[0]['text']
    
    def test_clear_index(self, temp_index_manager, sample_documents):
        """测试清空索引"""
        temp_index_manager.build_index(sample_documents)
        stats_before = temp_index_manager.get_stats()
        assert stats_before['document_count'] > 0
        
        temp_index_manager.clear_index()
        stats_after = temp_index_manager.get_stats()
        assert stats_after['document_count'] == 0
```

#### 4. 测试查询引擎（test_query_engine.py）

```python
import pytest
from src.query_engine import QueryEngine
from src.indexer import IndexManager

class TestQueryEngine:
    """查询引擎测试"""
    
    @pytest.fixture
    def mock_llm(self, mocker):
        """Mock LLM响应"""
        mock = mocker.Mock()
        mock.complete.return_value = "这是模拟的回答。"
        return mock
    
    def test_query_with_mock_llm(self, temp_index_manager, sample_documents, mock_llm, mocker):
        """测试查询（使用mock LLM）"""
        temp_index_manager.build_index(sample_documents)
        
        # Mock OpenAI LLM
        mocker.patch('src.query_engine.OpenAI', return_value=mock_llm)
        
        query_engine = QueryEngine(temp_index_manager)
        answer, sources = query_engine.query("什么是系统科学？")
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
```

---

## 集成测试

### 集成测试重点

集成测试关注**模块间的交互**，确保组件协同工作。

#### 示例：数据处理流程测试

```python
# tests/integration/test_data_pipeline.py

import pytest
from pathlib import Path
from src.data_loader import load_documents_from_directory
from src.indexer import IndexManager

class TestDataPipeline:
    """数据处理流程集成测试"""
    
    @pytest.fixture
    def test_data_dir(self, tmp_path):
        """创建测试数据目录"""
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()
        
        # 创建测试文档
        (data_dir / "doc1.md").write_text("# 文档1\n这是测试内容1")
        (data_dir / "doc2.md").write_text("# 文档2\n这是测试内容2")
        
        return data_dir
    
    def test_load_and_index_pipeline(self, test_data_dir, tmp_path):
        """测试从加载到索引的完整流程"""
        # 步骤1：加载文档
        documents = load_documents_from_directory(test_data_dir)
        assert len(documents) == 2
        
        # 步骤2：构建索引
        index_manager = IndexManager(
            collection_name="integration_test",
            persist_dir=tmp_path / "vector_store"
        )
        index = index_manager.build_index(documents)
        assert index is not None
        
        # 步骤3：验证索引
        stats = index_manager.get_stats()
        assert stats['document_count'] > 0
        
        # 步骤4：测试检索
        results = index_manager.search("文档", top_k=2)
        assert len(results) > 0
```

#### 示例：查询流程测试

```python
# tests/integration/test_query_pipeline.py

import pytest
from src.indexer import IndexManager
from src.query_engine import QueryEngine
from llama_index.core import Document

class TestQueryPipeline:
    """查询流程集成测试"""
    
    @pytest.fixture
    def prepared_index(self, tmp_path):
        """准备好的索引"""
        docs = [
            Document(text="系统科学研究系统的一般规律。", metadata={"id": 1}),
            Document(text="钱学森创建了系统学理论体系。", metadata={"id": 2})
        ]
        
        manager = IndexManager(
            collection_name="query_test",
            persist_dir=tmp_path / "vector_store"
        )
        manager.build_index(docs)
        return manager
    
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="需要DEEPSEEK_API_KEY环境变量"
    )
    def test_end_to_end_query(self, prepared_index):
        """端到端查询测试（需要真实API）"""
        query_engine = QueryEngine(prepared_index)
        answer, sources = query_engine.query("什么是系统科学？")
        
        # 验证返回格式
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
        assert len(sources) > 0
        
        # 验证引用来源格式
        for source in sources:
            assert 'index' in source
            assert 'text' in source
            assert 'metadata' in source
```

---

## RAG特定测试

### 1. 检索质量测试

```python
# tests/rag/test_retrieval_quality.py

class TestRetrievalQuality:
    """检索质量测试"""
    
    def test_retrieval_relevance(self, index_manager):
        """测试检索相关性"""
        # 准备测试数据
        test_cases = [
            {
                "query": "系统科学是什么",
                "expected_keywords": ["系统科学", "研究", "规律"]
            },
            {
                "query": "钱学森的贡献",
                "expected_keywords": ["钱学森", "创建", "理论"]
            }
        ]
        
        for case in test_cases:
            results = index_manager.search(case["query"], top_k=3)
            
            # 检查至少一个结果包含期望的关键词
            found = False
            for result in results:
                if any(kw in result['text'] for kw in case['expected_keywords']):
                    found = True
                    break
            
            assert found, f"查询 '{case['query']}' 未找到相关结果"
    
    def test_retrieval_score_threshold(self, index_manager):
        """测试检索分数阈值"""
        results = index_manager.search("系统科学", top_k=5)
        
        # 检查分数递减
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True)
        
        # 检查最高分数合理
        assert scores[0] > 0.3  # 根据实际情况调整阈值
```

### 2. LLM响应质量测试

```python
# tests/rag/test_llm_quality.py

class TestLLMQuality:
    """LLM响应质量测试"""
    
    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="需要API密钥"
    )
    def test_answer_completeness(self, query_engine):
        """测试答案完整性"""
        question = "系统科学包括哪些分支？"
        answer, sources = query_engine.query(question)
        
        # 检查答案不为空
        assert len(answer) > 20
        
        # 检查答案包含引用标记（如果使用CitationQueryEngine）
        # assert '[1]' in answer or '[2]' in answer
        
        # 检查有引用来源
        assert len(sources) > 0
    
    def test_answer_consistency(self, query_engine):
        """测试答案一致性（多次查询）"""
        question = "什么是系统科学？"
        
        answers = []
        for _ in range(3):
            answer, _ = query_engine.query(question)
            answers.append(answer)
        
        # 检查答案长度差异不大（因为temperature=0.1应该较稳定）
        lengths = [len(a) for a in answers]
        assert max(lengths) - min(lengths) < len(answers[0]) * 0.5
```

### 3. 对话上下文测试

```python
# tests/rag/test_chat_context.py

class TestChatContext:
    """对话上下文测试"""
    
    def test_context_memory(self, chat_manager):
        """测试上下文记忆"""
        # 第一轮对话
        answer1, _ = chat_manager.chat("什么是系统科学？")
        assert "系统" in answer1
        
        # 第二轮对话（使用代词"它"）
        answer2, _ = chat_manager.chat("它有哪些应用？")
        
        # 验证能理解"它"指的是系统科学
        assert len(answer2) > 0
        # 答案应该相关
        assert any(kw in answer2 for kw in ["应用", "领域", "使用"])
    
    def test_session_persistence(self, chat_manager, tmp_path):
        """测试会话持久化"""
        # 进行对话
        chat_manager.start_session()
        chat_manager.chat("测试问题1")
        chat_manager.chat("测试问题2")
        
        # 保存会话
        session = chat_manager.get_current_session()
        session.save(tmp_path)
        
        # 加载会话
        from src.chat_manager import ChatSession
        loaded_session = ChatSession.load(tmp_path / f"{session.session_id}.json")
        
        # 验证历史记录
        assert len(loaded_session.history) == 2
        assert loaded_session.history[0].question == "测试问题1"
```

---

## 性能测试

### 性能基准测试

```python
# tests/performance/test_performance.py

import time
import pytest

class TestPerformance:
    """性能测试"""
    
    def test_indexing_speed(self, benchmark, sample_documents):
        """测试索引构建速度"""
        def build_index():
            manager = IndexManager(collection_name="perf_test")
            manager.build_index(sample_documents)
            manager.clear_index()
        
        # 使用pytest-benchmark
        result = benchmark(build_index)
        
        # 设置性能目标（根据实际调整）
        assert result.stats['mean'] < 2.0  # 平均耗时小于2秒
    
    def test_query_latency(self, query_engine):
        """测试查询延迟"""
        start = time.time()
        answer, sources = query_engine.query("测试问题")
        latency = time.time() - start
        
        # 设置延迟目标
        assert latency < 5.0  # 5秒内完成查询
    
    @pytest.mark.parametrize("doc_count", [10, 50, 100])
    def test_scaling(self, doc_count):
        """测试扩展性"""
        # 创建不同数量的文档
        docs = [Document(text=f"文档{i}内容" * 10) for i in range(doc_count)]
        
        # 测试索引时间
        start = time.time()
        manager = IndexManager(collection_name=f"scale_test_{doc_count}")
        manager.build_index(docs)
        duration = time.time() - start
        
        # 验证时间增长合理
        print(f"{doc_count}个文档索引耗时: {duration:.2f}秒")
        assert duration < doc_count * 0.1  # 每个文档不超过0.1秒
```

---

## 测试工具和配置

### 依赖安装

```toml
# pyproject.toml

[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",         # 覆盖率
    "pytest-mock>=3.12.0",       # Mock支持
    "pytest-benchmark>=4.0.0",   # 性能测试
    "pytest-asyncio>=0.21.0",    # 异步测试
    "hypothesis>=6.0.0",         # 属性测试
]
```

### pytest配置

```ini
# pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 标记
markers =
    slow: 慢速测试（需要真实API）
    integration: 集成测试
    unit: 单元测试
    performance: 性能测试

# 覆盖率
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term
    -v
    --tb=short

# 忽略警告
filterwarnings =
    ignore::DeprecationWarning
```

### conftest.py（共享fixtures）

```python
# tests/conftest.py

import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures" / "sample_docs"

@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API密钥"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_12345")

@pytest.fixture(scope="function")
def temp_vector_store(tmp_path):
    """临时向量存储"""
    store_path = tmp_path / "test_vector_store"
    store_path.mkdir()
    return store_path

# 跳过需要API的测试（如果没有配置）
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_api: 需要真实API密钥的测试"
    )

def pytest_collection_modifyitems(config, items):
    if not os.getenv("DEEPSEEK_API_KEY"):
        skip_api = pytest.mark.skip(reason="需要DEEPSEEK_API_KEY环境变量")
        for item in items:
            if "requires_api" in item.keywords:
                item.add_marker(skip_api)
```

---

## CI/CD集成

### GitHub Actions配置

```yaml
# .github/workflows/tests.yml

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --extra test
    
    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## 测试最佳实践

### 1. 测试命名规范

```python
# 好的命名
def test_load_markdown_file_success():
    """加载Markdown文件成功的情况"""
    pass

def test_load_markdown_file_not_found():
    """文件不存在时的情况"""
    pass

# 避免的命名
def test1():  # 不清晰
    pass
```

### 2. AAA模式（Arrange-Act-Assert）

```python
def test_example():
    # Arrange（准备）
    loader = MarkdownLoader()
    file_path = Path("test.md")
    
    # Act（执行）
    result = loader.load_file(file_path)
    
    # Assert（断言）
    assert result is not None
```

### 3. 使用参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("test.md", True),
    ("test.txt", False),
    ("", False),
])
def test_file_extension(input, expected):
    result = is_markdown_file(input)
    assert result == expected
```

### 4. 隔离外部依赖

```python
# 使用mock隔离API调用
def test_with_mock(mocker):
    mock_api = mocker.patch('requests.get')
    mock_api.return_value.text = "mock response"
    
    # 测试代码不会真正调用API
    result = fetch_data()
    assert result == "mock response"
```

---

## 测试执行

### 运行所有测试

```bash
pytest
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit -v

# 只运行集成测试
pytest tests/integration -v

# 运行带标记的测试
pytest -m unit
pytest -m "not slow"
```

### 查看覆盖率

```bash
pytest --cov=src --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

### 性能测试

```bash
pytest tests/performance --benchmark-only
```

---

## 测试检查清单

在提交代码前，确保：

- [ ] 所有新功能都有对应的单元测试
- [ ] 关键流程有集成测试
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 没有跳过的测试（除非有充分理由）
- [ ] 测试代码有清晰的注释
- [ ] Mock了所有外部依赖（API、数据库等）

---

## 下一步

1. **实施单元测试**：从最底层的模块开始
2. **添加集成测试**：测试模块间交互
3. **设置CI/CD**：自动运行测试
4. **持续改进**：定期review测试覆盖率

## 相关文档

- [架构设计](ARCHITECTURE.md) - 了解系统架构
- [开发者指南](DEVELOPER_GUIDE.md) - 开发说明
- [项目结构](PROJECT_STRUCTURE.md) - 目录组织

---

**注意**：测试不是一次性工作，而是持续的过程。随着代码演进，测试也要相应更新。

