# API 参考文档

> 详细的API接口文档

## 目录

- [src.config](#srcconfig)
- [src.data_loader](#srcdata_loader)
- [src.indexer](#srcindexer)
- [src.query_engine](#srcquery_engine)
- [src.chat_manager](#srcchat_manager)

---

## src.config

### Config 类

全局配置管理类，单例模式。

**导入方式**：
```python
from src.config import config  # 使用全局实例
```

#### 属性

| 属性名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `PROJECT_ROOT` | Path | 项目根目录 | 自动检测 |
| `DEEPSEEK_API_KEY` | str | DeepSeek API密钥 | 从环境变量读取 |
| `DEEPSEEK_API_BASE` | str | API端点 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | str | 模型名称 | `deepseek-chat` |
| `EMBEDDING_MODEL` | str | Embedding模型 | `BAAI/bge-base-zh-v1.5` |
| `VECTOR_STORE_PATH` | Path | 向量数据库路径 | `./vector_store` |
| `CHROMA_COLLECTION_NAME` | str | 集合名称 | `systematology_docs` |
| `RAW_DATA_PATH` | Path | 原始数据路径 | `./data/raw` |
| `PROCESSED_DATA_PATH` | Path | 处理后数据路径 | `./data/processed` |
| `CHUNK_SIZE` | int | 文本分块大小 | 512 |
| `CHUNK_OVERLAP` | int | 分块重叠大小 | 50 |
| `SIMILARITY_TOP_K` | int | 检索相似文档数量 | 3 |
| `APP_TITLE` | str | 应用标题 | `系统科学知识库RAG` |
| `APP_PORT` | int | 应用端口 | 8501 |

#### 方法

##### `validate() -> tuple[bool, Optional[str]]`

验证配置是否完整和合法。

**返回**：
- `(True, None)`：配置有效
- `(False, error_message)`：配置无效，包含错误信息

**示例**：
```python
is_valid, error = config.validate()
if not is_valid:
    print(f"配置错误: {error}")
```

##### `ensure_directories() -> None`

确保所有必要的目录存在，不存在则创建。

**示例**：
```python
config.ensure_directories()
```

---

## src.data_loader

### MarkdownLoader 类

加载本地Markdown文件。

#### 方法

##### `load_file(file_path: Path) -> Optional[LlamaDocument]`

加载单个Markdown文件。

**参数**：
- `file_path` (Path): 文件路径

**返回**：
- `LlamaDocument`: 文档对象
- `None`: 加载失败

**示例**：
```python
from pathlib import Path
from src.data_loader import MarkdownLoader

loader = MarkdownLoader()
doc = loader.load_file(Path("document.md"))
if doc:
    print(f"标题: {doc.metadata['title']}")
    print(f"内容长度: {len(doc.text)}")
```

##### `load_directory(directory_path: Path, recursive: bool = True) -> List[LlamaDocument]`

加载目录中的所有Markdown文件。

**参数**：
- `directory_path` (Path): 目录路径
- `recursive` (bool): 是否递归加载子目录，默认 `True`

**返回**：
- `List[LlamaDocument]`: 文档列表

**示例**：
```python
docs = loader.load_directory(Path("./data"), recursive=True)
print(f"加载了 {len(docs)} 个文档")
```

---

### WebLoader 类

从URL加载网页内容。

#### 构造函数

```python
WebLoader(timeout: int = 10)
```

**参数**：
- `timeout` (int): HTTP请求超时时间（秒），默认 10

#### 方法

##### `load_url(url: str) -> Optional[LlamaDocument]`

从URL加载网页内容。

**参数**：
- `url` (str): 网页URL

**返回**：
- `LlamaDocument`: 文档对象
- `None`: 加载失败

**示例**：
```python
from src.data_loader import WebLoader

loader = WebLoader(timeout=15)
doc = loader.load_url("https://example.com/article")
if doc:
    print(f"标题: {doc.metadata['title']}")
    print(f"域名: {doc.metadata['domain']}")
```

##### `load_urls(urls: List[str]) -> List[LlamaDocument]`

批量加载多个URL。

**参数**：
- `urls` (List[str]): URL列表

**返回**：
- `List[LlamaDocument]`: 成功加载的文档列表

**示例**：
```python
urls = [
    "https://example.com/article1",
    "https://example.com/article2"
]
docs = loader.load_urls(urls)
```

---

### DocumentProcessor 类

文档预处理器（静态方法）。

#### 方法

##### `clean_text(text: str) -> str`

清理文本内容。

**处理内容**：
- 移除多余的空白字符
- 合并多余的空行
- 去除行首行尾空白

**参数**：
- `text` (str): 原始文本

**返回**：
- `str`: 清理后的文本

**示例**：
```python
from src.data_loader import DocumentProcessor

clean = DocumentProcessor.clean_text(raw_text)
```

##### `enrich_metadata(document: LlamaDocument, additional_metadata: dict) -> LlamaDocument`

为文档添加额外的元数据。

**参数**：
- `document` (LlamaDocument): 原始文档
- `additional_metadata` (dict): 要添加的元数据

**返回**：
- `LlamaDocument`: 更新后的文档

**示例**：
```python
doc = DocumentProcessor.enrich_metadata(
    doc,
    {"category": "系统科学", "author": "钱学森"}
)
```

##### `filter_by_length(documents: List[LlamaDocument], min_length: int = 50) -> List[LlamaDocument]`

过滤掉太短的文档。

**参数**：
- `documents` (List[LlamaDocument]): 文档列表
- `min_length` (int): 最小长度，默认 50

**返回**：
- `List[LlamaDocument]`: 过滤后的文档列表

---

### 便捷函数

#### `load_documents_from_directory(directory_path: str | Path, recursive: bool = True, clean: bool = True) -> List[LlamaDocument]`

从目录加载所有Markdown文档。

**参数**：
- `directory_path`: 目录路径
- `recursive`: 是否递归加载
- `clean`: 是否清理文本

**示例**：
```python
from src.data_loader import load_documents_from_directory

docs = load_documents_from_directory("./data/raw", recursive=True)
```

#### `load_documents_from_urls(urls: List[str], clean: bool = True) -> List[LlamaDocument]`

从URL列表加载文档。

**参数**：
- `urls`: URL列表
- `clean`: 是否清理文本

**示例**：
```python
from src.data_loader import load_documents_from_urls

urls = ["https://example.com/article"]
docs = load_documents_from_urls(urls)
```

---

## src.indexer

### IndexManager 类

索引管理器，负责构建和管理向量索引。

#### 构造函数

```python
IndexManager(
    collection_name: Optional[str] = None,
    persist_dir: Optional[Path] = None,
    embedding_model: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
)
```

**参数**：
- `collection_name`: Chroma集合名称，默认从配置读取
- `persist_dir`: 向量存储持久化目录，默认从配置读取
- `embedding_model`: Embedding模型名称，默认从配置读取
- `chunk_size`: 文本分块大小，默认从配置读取
- `chunk_overlap`: 文本分块重叠大小，默认从配置读取

**示例**：
```python
from src.indexer import IndexManager

# 使用默认配置
index_manager = IndexManager()

# 自定义配置
index_manager = IndexManager(
    collection_name="my_collection",
    chunk_size=1024,
    chunk_overlap=100
)
```

#### 方法

##### `build_index(documents: List[LlamaDocument], show_progress: bool = True) -> VectorStoreIndex`

构建或更新索引。

**参数**：
- `documents`: 文档列表
- `show_progress`: 是否显示进度条，默认 `True`

**返回**：
- `VectorStoreIndex`: 索引对象

**说明**：
- 如果索引不存在，创建新索引
- 如果索引已存在，增量添加文档

**示例**：
```python
index = index_manager.build_index(documents)
```

##### `get_index() -> VectorStoreIndex`

获取现有索引。

**返回**：
- `VectorStoreIndex`: 索引对象

**说明**：
- 如果内存中有缓存，直接返回
- 否则尝试从向量存储加载
- 都没有则创建空索引

**示例**：
```python
index = index_manager.get_index()
```

##### `clear_index() -> None`

清空索引，删除所有数据。

**示例**：
```python
index_manager.clear_index()
```

##### `get_stats() -> dict`

获取索引统计信息。

**返回**：
```python
{
    "collection_name": str,      # 集合名称
    "document_count": int,       # 文档数量
    "embedding_model": str,      # Embedding模型
    "chunk_size": int,           # 分块大小
    "chunk_overlap": int,        # 重叠大小
}
```

**示例**：
```python
stats = index_manager.get_stats()
print(f"文档数量: {stats['document_count']}")
```

##### `search(query: str, top_k: int = 5) -> List[dict]`

搜索相似文档（用于测试）。

**参数**：
- `query`: 查询文本
- `top_k`: 返回结果数量，默认 5

**返回**：
```python
[
    {
        "text": str,             # 文档文本
        "score": float,          # 相似度分数
        "metadata": dict,        # 元数据
    },
    ...
]
```

**示例**：
```python
results = index_manager.search("系统科学", top_k=3)
for result in results:
    print(f"分数: {result['score']:.4f}")
    print(f"内容: {result['text'][:100]}...")
```

---

### 便捷函数

#### `create_index_from_directory(directory_path: str | Path, collection_name: Optional[str] = None, recursive: bool = True) -> IndexManager`

从目录创建索引。

**参数**：
- `directory_path`: 文档目录路径
- `collection_name`: 集合名称
- `recursive`: 是否递归加载

**返回**：
- `IndexManager`: 索引管理器对象

**示例**：
```python
from src.indexer import create_index_from_directory

index_manager = create_index_from_directory("./data/raw")
```

#### `create_index_from_urls(urls: List[str], collection_name: Optional[str] = None) -> IndexManager`

从URL列表创建索引。

**参数**：
- `urls`: URL列表
- `collection_name`: 集合名称

**返回**：
- `IndexManager`: 索引管理器对象

**示例**：
```python
from src.indexer import create_index_from_urls

urls = ["https://example.com/article"]
index_manager = create_index_from_urls(urls)
```

---

## src.query_engine

### QueryEngine 类

带引用溯源的查询引擎。

#### 构造函数

```python
QueryEngine(
    index_manager: IndexManager,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    similarity_top_k: Optional[int] = None,
    citation_chunk_size: int = 512,
)
```

**参数**：
- `index_manager`: 索引管理器
- `api_key`: DeepSeek API密钥，默认从配置读取
- `api_base`: API端点，默认从配置读取
- `model`: 模型名称，默认从配置读取
- `similarity_top_k`: 检索相似文档数量，默认从配置读取
- `citation_chunk_size`: 引用块大小，默认 512

**示例**：
```python
from src.query_engine import QueryEngine

query_engine = QueryEngine(index_manager)
```

#### 方法

##### `query(question: str) -> Tuple[str, List[dict]]`

执行查询并返回带引用的答案。

**参数**：
- `question`: 用户问题

**返回**：
- `(answer, sources)`: 
  - `answer` (str): 答案文本
  - `sources` (List[dict]): 引用来源列表

**sources 格式**：
```python
[
    {
        "index": int,            # 引用编号
        "text": str,             # 原文
        "score": float,          # 相似度分数
        "metadata": dict,        # 元数据
    },
    ...
]
```

**示例**：
```python
answer, sources = query_engine.query("什么是系统科学？")
print(f"答案: {answer}")
print(f"引用来源数: {len(sources)}")
```

---

### SimpleQueryEngine 类

简单查询引擎（不带引用溯源）。

#### 构造函数

```python
SimpleQueryEngine(
    index_manager: IndexManager,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    similarity_top_k: Optional[int] = None,
)
```

**参数**：同 `QueryEngine`，但无 `citation_chunk_size`

#### 方法

##### `query(question: str) -> str`

执行简单查询。

**参数**：
- `question`: 用户问题

**返回**：
- `str`: 答案文本（无引用信息）

**示例**：
```python
from src.query_engine import SimpleQueryEngine

simple_engine = SimpleQueryEngine(index_manager)
answer = simple_engine.query("快速问题")
```

---

### 便捷函数

#### `format_sources(sources: List[dict]) -> str`

格式化引用来源为可读文本。

**参数**：
- `sources`: 引用来源列表

**返回**：
- `str`: 格式化的文本

**示例**：
```python
from src.query_engine import format_sources

answer, sources = query_engine.query("问题")
print(answer)
print(format_sources(sources))
```

#### `create_query_engine(index_manager: IndexManager, with_citation: bool = True) -> QueryEngine | SimpleQueryEngine`

创建查询引擎（便捷函数）。

**参数**：
- `index_manager`: 索引管理器
- `with_citation`: 是否使用引用溯源，默认 `True`

**返回**：
- `QueryEngine` 或 `SimpleQueryEngine`

**示例**：
```python
from src.query_engine import create_query_engine

# 带引用
engine = create_query_engine(index_manager, with_citation=True)

# 不带引用
engine = create_query_engine(index_manager, with_citation=False)
```

---

## src.chat_manager

### ChatTurn 类

单轮对话数据类。

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `question` | str | 用户问题 |
| `answer` | str | AI回答 |
| `sources` | List[dict] | 引用来源 |
| `timestamp` | str | 时间戳 |

#### 方法

##### `to_dict() -> dict`

转换为字典（用于序列化）。

##### `from_dict(data: dict) -> ChatTurn`

从字典创建对象（类方法）。

---

### ChatSession 类

对话会话管理。

#### 构造函数

```python
ChatSession(session_id: Optional[str] = None)
```

**参数**：
- `session_id`: 会话ID，如果不提供则自动生成

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `session_id` | str | 会话ID |
| `history` | List[ChatTurn] | 对话历史 |
| `created_at` | str | 创建时间 |
| `updated_at` | str | 更新时间 |

#### 方法

##### `add_turn(question: str, answer: str, sources: List[dict]) -> None`

添加一轮对话。

**参数**：
- `question`: 用户问题
- `answer`: AI回答
- `sources`: 引用来源

##### `get_history(last_n: Optional[int] = None) -> List[ChatTurn]`

获取对话历史。

**参数**：
- `last_n`: 获取最近N轮对话，`None` 表示获取全部

**返回**：
- `List[ChatTurn]`: 对话历史列表

##### `clear_history() -> None`

清空对话历史。

##### `save(save_dir: Path) -> None`

保存会话到文件。

**参数**：
- `save_dir`: 保存目录

**示例**：
```python
session.save(Path("./sessions"))
```

##### `load(file_path: Path) -> ChatSession`

从文件加载会话（类方法）。

**参数**：
- `file_path`: 会话文件路径

**返回**：
- `ChatSession`: 会话对象

**示例**：
```python
session = ChatSession.load(Path("./sessions/session_xxx.json"))
```

---

### ChatManager 类

对话管理器。

#### 构造函数

```python
ChatManager(
    index_manager: IndexManager,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    memory_token_limit: int = 3000,
    similarity_top_k: Optional[int] = None,
)
```

**参数**：
- `index_manager`: 索引管理器
- `api_key`: DeepSeek API密钥，默认从配置读取
- `api_base`: API端点，默认从配置读取
- `model`: 模型名称，默认从配置读取
- `memory_token_limit`: 记忆token限制，默认 3000
- `similarity_top_k`: 检索相似文档数量，默认从配置读取

**示例**：
```python
from src.chat_manager import ChatManager

chat_manager = ChatManager(index_manager)
```

#### 方法

##### `start_session(session_id: Optional[str] = None) -> ChatSession`

开始新会话。

**参数**：
- `session_id`: 会话ID，默认自动生成

**返回**：
- `ChatSession`: 会话对象

**示例**：
```python
session = chat_manager.start_session()
```

##### `load_session(file_path: Path) -> None`

加载已有会话。

**参数**：
- `file_path`: 会话文件路径

**示例**：
```python
chat_manager.load_session(Path("./sessions/session_xxx.json"))
```

##### `chat(message: str) -> Tuple[str, List[dict]]`

进行对话。

**参数**：
- `message`: 用户消息

**返回**：
- `(answer, sources)`:
  - `answer` (str): 回答
  - `sources` (List[dict]): 引用来源列表

**说明**：
- 自动管理上下文
- 理解指代（如"它"、"这个"等）

**示例**：
```python
answer, sources = chat_manager.chat("什么是系统科学？")
answer, sources = chat_manager.chat("它有哪些分支？")  # "它"自动理解为"系统科学"
```

##### `get_current_session() -> Optional[ChatSession]`

获取当前会话。

**返回**：
- `ChatSession`: 当前会话对象
- `None`: 没有活动会话

##### `save_current_session(save_dir: Optional[Path] = None) -> None`

保存当前会话。

**参数**：
- `save_dir`: 保存目录，默认为 `项目根目录/sessions`

**示例**：
```python
chat_manager.save_current_session()
```

##### `reset_session() -> None`

重置当前会话（清空历史）。

**示例**：
```python
chat_manager.reset_session()
```

---

## 类型定义

### LlamaDocument

LlamaIndex 的文档类型。

```python
from llama_index.core import Document as LlamaDocument

doc = LlamaDocument(
    text="文档内容",
    metadata={
        "file_name": "example.md",
        "title": "示例文档",
        "custom_field": "自定义值"
    }
)
```

---

## 错误处理

所有API在失败时的行为：

### 返回 None
- `MarkdownLoader.load_file()` - 文件不存在或读取失败
- `WebLoader.load_url()` - 网络请求失败

### 抛出异常
- `IndexManager.build_index()` - 索引构建失败
- `QueryEngine.query()` - API调用失败
- `ChatManager.chat()` - 对话失败

### 静默失败
- 批量操作（如 `load_urls()`）会跳过失败项，继续处理其余项

---

## 使用示例

### 完整流程示例

```python
from src.config import config
from src.data_loader import load_documents_from_directory
from src.indexer import IndexManager
from src.chat_manager import ChatManager

# 1. 验证配置
is_valid, error = config.validate()
if not is_valid:
    print(f"配置错误: {error}")
    exit(1)

# 2. 加载文档
documents = load_documents_from_directory(config.RAW_DATA_PATH)
print(f"加载了 {len(documents)} 个文档")

# 3. 构建索引
index_manager = IndexManager()
index_manager.build_index(documents)

# 4. 创建对话管理器
chat_manager = ChatManager(index_manager)
chat_manager.start_session()

# 5. 对话
answer, sources = chat_manager.chat("什么是系统科学？")
print(f"答案: {answer}")

answer, sources = chat_manager.chat("它有哪些应用？")
print(f"答案: {answer}")

# 6. 保存会话
chat_manager.save_current_session()
```

---

## 总结

本API文档涵盖了所有核心模块的接口，包括：
- ✅ 详细的参数说明
- ✅ 返回值格式
- ✅ 使用示例
- ✅ 错误处理说明

## 相关文档

- [架构设计](ARCHITECTURE.md) - 系统架构和设计思路
- [开发者指南](DEVELOPER_GUIDE.md) - 详细的代码说明和开发指南
- [技术决策](DECISIONS.md) - 技术选型的原因
- [开发日志](CHANGELOG.md) - 项目进展记录

