# API 参考文档

> 详细的API接口文档

## 目录

- [src.config](#srcconfig)
- [src.data_loader](#srcdata_loader)
- [src.indexer](#srcindexer)
- [src.query_engine](#srcquery_engine)
- [src.chat_manager](#srcchat_manager)
- [src.phoenix_utils](#srcphoenix_utils)

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
| `GITHUB_TOKEN` | str | GitHub访问令牌 | 从环境变量读取（可选） |
| `GITHUB_DEFAULT_BRANCH` | str | 默认分支名称 | `main` |

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

### load_documents_from_github 函数

从 GitHub 仓库加载文档（使用 LangChain GitLoader + 本地 Git 克隆）。

**新特性**：
- 首次加载会克隆仓库到本地（`data/github_repos/`）
- 后续使用 `git pull` 增量更新，比 API 方式更快
- 支持两级增量检测：commit SHA 快速检测 + 文件哈希精细比对

#### 函数签名

```python
def load_documents_from_github(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
    clean: bool = True,
    show_progress: bool = True,
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> List[LlamaDocument]
```

**参数**：
- `owner` (str): 仓库所有者（用户名或组织名）
- `repo` (str): 仓库名称
- `branch` (Optional[str]): 分支名称，默认为 `"main"`
- `clean` (bool): 是否清理文本中的多余空白，默认 `True`
- `show_progress` (bool): 是否显示进度信息，默认 `True`
- `filter_directories` (Optional[List[str]]): 只加载指定目录，如 `["docs", "examples"]`
- `filter_file_extensions` (Optional[List[str]]): 只加载指定扩展名，如 `[".md", ".py"]`

**注意**：
- ⚠️ 仅支持公开仓库，私有仓库无法访问

**返回**：
- `List[LlamaDocument]`: 文档列表，失败时返回空列表

**元数据**：
每个文档包含以下元数据：
- `source_type`: `"github"`
- `repository`: 格式为 `"owner/repo"`
- `branch`: 分支名称
- `file_path`: 文件在仓库中的路径
- `file_name`: 文件名
- `url`: GitHub 文件链接

**示例**：
```python
from src.data_loader import load_documents_from_github

# 加载公开仓库
docs = load_documents_from_github("microsoft", "TypeScript", branch="main")

# 只加载特定目录和文件类型
docs = load_documents_from_github(
    "owner", "repo",
    filter_directories=["docs"],
    filter_file_extensions=[".md"]
)

for doc in docs:
    print(f"文件: {doc.metadata['file_path']}")
    print(f"URL: {doc.metadata['url']}")
```

**注意事项**：
- 首次克隆大型仓库可能需要较长时间
- 本地仓库存储在 `data/github_repos/owner/repo_branch/`
- 使用浅克隆（`--depth 1`）节省空间和时间
- 自动排除 `.git/`, `__pycache__/`, `.pyc` 等文件

##### `load_repositories(repo_configs: List[dict]) -> List[LlamaDocument]`

批量加载多个 GitHub 仓库。

**参数**：
- `repo_configs` (List[dict]): 仓库配置列表，每个配置包含：
  - `owner` (str): 仓库所有者（必需）
  - `repo` (str): 仓库名称（必需）
  - `branch` (Optional[str]): 分支名称（可选）

**返回**：
- `List[LlamaDocument]`: 所有仓库的文档列表

**示例**：
```python
repo_configs = [
    {"owner": "microsoft", "repo": "TypeScript", "branch": "main"},
    {"owner": "facebook", "repo": "react", "branch": "main"}
]

docs = loader.load_repositories(repo_configs)
print(f"从 {len(repo_configs)} 个仓库加载了 {len(docs)} 个文件")
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

#### `load_documents_from_github(owner: str, repo: str, branch: Optional[str] = None, clean: bool = True) -> List[LlamaDocument]`

从 GitHub 仓库加载文档（仅支持公开仓库）。

**参数**：
- `owner` (str): 仓库所有者
- `repo` (str): 仓库名称
- `branch` (Optional[str]): 分支名称，默认为 `"main"`
- `clean` (bool): 是否清理文本，默认 `True`

**返回**：
- `List[LlamaDocument]`: 文档列表

**示例**：
```python
from src.data_loader import load_documents_from_github

# 公开仓库
docs = load_documents_from_github("microsoft", "TypeScript", branch="main")
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

## src.phoenix_utils

Phoenix可观测性工具模块，提供RAG流程的实时追踪和可视化功能。

### 主要函数

#### `start_phoenix_ui(port: int = 6006) -> Optional[Any]`

启动Phoenix可视化平台并配置OpenTelemetry追踪。

**参数**：
- `port` (int, 可选)：Phoenix Web界面端口，默认6006

**返回**：
- Phoenix会话对象（如果启动成功）
- `None`（如果启动失败，如依赖未安装）

**功能**：
1. 启动Phoenix Web应用（http://localhost:6006）
2. 配置OpenTelemetry追踪器
3. 自动追踪所有LlamaIndex操作

**示例**：
```python
from src.phoenix_utils import start_phoenix_ui

# 启动Phoenix（默认端口6006）
session = start_phoenix_ui()

# 启动Phoenix（自定义端口）
session = start_phoenix_ui(port=7007)

# 之后的所有LlamaIndex操作都会被自动追踪
```

**追踪的操作**：
- 🔍 检索操作（向量相似度搜索）
- 🤖 LLM调用（prompt和响应）
- 📊 Embedding计算
- ⏱️ 各环节耗时

**访问界面**：
- 启动成功后访问：http://localhost:6006
- 实时查看追踪数据和可视化图表

---

#### `stop_phoenix_ui() -> None`

停止Phoenix可视化平台。

**示例**：
```python
from src.phoenix_utils import stop_phoenix_ui

stop_phoenix_ui()
```

**注意**：通常不需要手动调用，应用退出时会自动清理。

---

#### `is_phoenix_running() -> bool`

检查Phoenix是否正在运行。

**返回**：
- `True`：Phoenix正在运行
- `False`：Phoenix未运行

**示例**：
```python
from src.phoenix_utils import is_phoenix_running

if is_phoenix_running():
    print("Phoenix 正在运行")
else:
    print("Phoenix 未运行")
```

---

#### `get_phoenix_url() -> str`

获取Phoenix Web界面的访问URL。

**返回**：
- Phoenix访问地址字符串（如 `http://localhost:6006`）

**示例**：
```python
from src.phoenix_utils import get_phoenix_url

url = get_phoenix_url()
print(f"Phoenix URL: {url}")
```

---

### Phoenix功能特性

Phoenix提供以下可视化和分析功能：

1. **追踪视图（Traces）**：
   - 查看每次查询的完整执行链路
   - 时间线视图展示各环节耗时
   - 查看LLM的完整prompt和响应

2. **向量空间（Embeddings）**：
   - 可视化文档的向量分布
   - 探索embedding聚类
   - 检查语义相似性

3. **性能分析（Performance）**：
   - 统计检索时间
   - 统计LLM调用时间
   - Token使用量分析

4. **评估（Evaluations）**：
   - 查询质量评分
   - 检索相关性分析
   - 生成质量指标

---

### 集成示例

**完整的调试工作流**：

```python
from src.config import config
from src.indexer import IndexManager
from src.query_engine import QueryEngine
from src.phoenix_utils import start_phoenix_ui, get_phoenix_url

# 1. 启动Phoenix
phoenix_session = start_phoenix_ui()
print(f"Phoenix已启动: {get_phoenix_url()}")

# 2. 创建查询引擎（启用调试）
index_manager = IndexManager()
query_engine = QueryEngine(index_manager, enable_debug=True)

# 3. 执行查询（所有操作自动被追踪）
answer, sources, trace_info = query_engine.query(
    "什么是系统科学？",
    collect_trace=True
)

# 4. 查看追踪信息
print(f"检索耗时: {trace_info['retrieval_time']:.2f}秒")
print(f"平均相似度: {trace_info['avg_score']:.3f}")

# 5. 在浏览器中打开Phoenix查看完整追踪
# 访问 http://localhost:6006
```

**Web界面使用**：

在Streamlit应用（`app.py`）中，Phoenix已集成到侧边栏的"🔍 调试模式"中：

1. 点击"启动Phoenix UI"按钮
2. Phoenix会在后台启动
3. 点击显示的链接访问Phoenix界面
4. 执行查询时，追踪数据自动发送到Phoenix
5. 在Phoenix界面实时查看分析结果

---

### 技术说明

**OpenTelemetry集成**：
- Phoenix使用OpenTelemetry标准进行追踪
- `LlamaIndexInstrumentor`自动注入追踪代码
- 无需修改业务代码，即可实现全链路追踪

**与LlamaDebugHandler的区别**：

| 特性 | LlamaDebugHandler | Phoenix |
|------|------------------|---------|
| 输出方式 | 控制台/文件日志 | Web界面可视化 |
| 启动成本 | 轻量级，即时 | 需要启动Web服务 |
| 分析能力 | 文本日志 | 图表、统计、探索 |
| 适用场景 | 快速调试 | 深度分析 |

**推荐使用场景**：
- **快速调试**：使用LlamaDebugHandler
- **深度分析**：使用Phoenix
- **最佳实践**：两者结合使用

---

## 总结

本API文档涵盖了所有核心模块的接口，包括：
- ✅ 详细的参数说明
- ✅ 返回值格式
- ✅ 使用示例
- ✅ 错误处理说明

## 相关文档

- [架构设计](ARCHITECTURE.md) - 系统架构和设计思路
- [技术决策](DECISIONS.md) - 技术选型的原因
- [项目追踪](TRACKER.md) - 任务管理与进度追踪

