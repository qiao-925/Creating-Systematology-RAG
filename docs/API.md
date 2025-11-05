# API 参考文档

> 核心模块API索引 - 详细接口文档请查看源码docstring

## 📚 模块总览

| 模块 | 核心类 | 主要功能 | 源码位置 |
|------|--------|---------|---------|
| **config** | `Config` | 全局配置管理（单例） | `src/config.py` |
| **data_loader** | `MarkdownLoader`<br>`WebLoader` | 多数据源加载 | `src/data_loader.py` |
| **indexer** | `IndexManager` | 向量索引构建与管理 | `src/indexer.py` |
| **query_engine** | `QueryEngine`<br>`SimpleQueryEngine` | RAG查询与引用溯源 | `src/query_engine.py` |
| **chat_manager** | `ChatManager`<br>`ChatSession` | 多轮对话管理 | `src/chat_manager.py` |
| **user_manager** | `UserManager` | 用户认证与会话 | `src/user_manager.py` |
| **phoenix_utils** | - | Phoenix可观测性工具 | `src/phoenix_utils.py` |

---

## 🔧 核心API

### 1. Config (配置管理)

```python
from src.config import config

# 主要属性
config.DEEPSEEK_API_KEY: str        # API密钥
config.EMBEDDING_MODEL: str         # Embedding模型路径
config.VECTOR_STORE_PATH: Path      # 向量库路径
config.CHUNK_SIZE: int              # 分块大小
config.SIMILARITY_TOP_K: int        # 检索数量

# 核心方法
config.validate() -> tuple[bool, Optional[str]]
config.ensure_directories() -> None
```

### 2. DataLoader (数据加载)

```python
from src.data_loader import (
    load_documents_from_directory,
    load_documents_from_urls,
    load_documents_from_github
)

# 便捷函数
docs = load_documents_from_directory("./data/raw", recursive=True)
docs = load_documents_from_urls(["https://example.com"])
docs = load_documents_from_github("owner", "repo", branch="main")

# 类方法（高级用户）
loader = MarkdownLoader()
doc = loader.load_file(Path("file.md"))

loader = WebLoader(timeout=10)
doc = loader.load_url("https://...")
```

**GitHub加载特性:**
- 🚀 本地Git克隆，支持增量更新（`git pull`）
- 📦 浅克隆（`--depth 1`）节省空间
- 🔄 两级增量检测：commit SHA + 文件哈希

### 3. IndexManager (索引管理)

```python
from src.indexer import IndexManager

# 初始化
index_manager = IndexManager(
    collection_name="my_collection",  # 可选
    embedding_model="model_path",     # 可选
    chunk_size=512                    # 可选
)

# 核心方法
index = index_manager.build_index(documents, show_progress=True)
index = index_manager.get_index()
index_manager.clear_index()
stats = index_manager.get_stats()  # 返回统计信息dict

# 便捷函数
from src.indexer import create_index_from_directory
index_manager = create_index_from_directory("./data")
```

### 4. QueryEngine (查询引擎)

```python
from src.query_engine import QueryEngine

# 初始化
query_engine = QueryEngine(
    index_manager=index_manager,
    similarity_top_k=3  # 可选
)

# 查询（带引用溯源和推理链）
answer, sources, reasoning_content, trace_info = query_engine.query("问题", collect_trace=False)

# sources 格式
# [{"index": 1, "text": "原文", "score": 0.95, "metadata": {...}}, ...]

# reasoning_content 格式（可选）
# 推理链内容字符串，如果模型返回推理过程则包含，否则为 None
```

**SimpleQueryEngine (无引用):**
```python
from src.query_engine import SimpleQueryEngine
simple_engine = SimpleQueryEngine(index_manager)
answer = simple_engine.query("快速问题")
```

**ModularQueryEngine (模块化查询引擎):**
```python
from src.query.modular.engine import ModularQueryEngine

query_engine = ModularQueryEngine(
    index_manager=index_manager,
    retrieval_strategy="vector",  # vector|bm25|hybrid|grep|multi
    enable_rerank=True,
    enable_auto_routing=True
)

# 查询（返回包含推理链）
answer, sources, reasoning_content, trace_info = query_engine.query("问题", collect_trace=False)
```

### 5. ChatManager (对话管理)

```python
from src.chat_manager import ChatManager

# 初始化
chat_manager = ChatManager(
    index_manager=index_manager,
    memory_token_limit=3000  # 可选
)

# 会话管理
session = chat_manager.start_session()
chat_manager.load_session(Path("session.json"))

# 多轮对话（返回包含推理链）
answer, sources, reasoning_content = chat_manager.chat("什么是系统科学？")
answer, sources, reasoning_content = chat_manager.chat("它有哪些应用？")  # 理解上下文

# 推理链内容（可选）
# reasoning_content: Optional[str] - 推理链内容，如果模型返回推理过程则包含，否则为 None

# 会话操作
chat_manager.save_current_session()
chat_manager.reset_session()
session = chat_manager.get_current_session()
```

**ChatSession 类:**
```python
# 会话属性
session.session_id: str
session.history: List[ChatTurn]
session.created_at: str

# 方法
session.add_turn(question, answer, sources, reasoning_content=None)  # reasoning_content 可选
history = session.get_history(last_n=5)
session.clear_history()
session.save(Path("./sessions"))
session = ChatSession.load(Path("session.json"))
```

**ChatTurn 类:**
```python
# 单轮对话属性
turn.question: str
turn.answer: str
turn.sources: List[Dict[str, Any]]
turn.timestamp: str
turn.reasoning_content: Optional[str]  # 推理链内容（可选）
```

### 8. LLM 工厂函数（DeepSeek 推理模型）

```python
from src.llms import (
    create_deepseek_llm,
    create_deepseek_llm_for_query,
    create_deepseek_llm_for_structure
)

# 创建用于查询的 LLM（自然语言输出）
llm = create_deepseek_llm_for_query(
    api_key="your_api_key",  # 可选，默认使用 config.DEEPSEEK_API_KEY
    model="deepseek-reasoner",  # 可选，默认使用 config.LLM_MODEL
    max_tokens=4096  # 可选
)

# 创建用于结构化输出的 LLM（JSON Output）
llm = create_deepseek_llm_for_structure(
    api_key="your_api_key",
    model="deepseek-reasoner",
    max_tokens=1024
)

# 通用工厂函数
llm = create_deepseek_llm(
    api_key="your_api_key",
    model="deepseek-reasoner",
    use_json_output=False,  # 是否启用 JSON Output
    max_tokens=4096
)
```

**推理链处理工具:**
```python
from src.llms import (
    extract_reasoning_content,
    extract_reasoning_from_stream_chunk,
    clean_messages_for_api,
    has_reasoning_content
)

# 从响应中提取推理链内容
reasoning = extract_reasoning_content(response)

# 检查响应是否包含推理链
if has_reasoning_content(response):
    reasoning = extract_reasoning_content(response)

# 清理消息列表，确保不包含 reasoning_content（用于多轮对话）
cleaned_messages = clean_messages_for_api(messages)
```

**DeepSeekLogger (日志包装器):**
```python
from src.llms import wrap_deepseek

# 包装 DeepSeek 实例，自动记录 API 调用和推理链
deepseek_llm = DeepSeek(...)
wrapped_llm = wrap_deepseek(deepseek_llm)

# 所有调用会自动记录到日志，包括推理链内容
```

```python
from src.user_manager import UserManager

user_manager = UserManager()

# 用户注册/登录
success, message = user_manager.register_user(email, password)
success, message = user_manager.login_user(email, password)

# 会话管理
user_manager.get_current_user() -> Optional[dict]
user_manager.logout_user()

# 获取用户专属路径
collection_name = user_manager.get_user_collection_name(email)
session_dir = user_manager.get_user_session_dir(email)
```

### 8. Phoenix可观测性

```python
from src.phoenix_utils import (
    start_phoenix_ui,
    stop_phoenix_ui,
    is_phoenix_running,
    get_phoenix_url
)

# 启动Phoenix
session = start_phoenix_ui(port=6006)
print(f"访问: {get_phoenix_url()}")  # http://localhost:6006

# 检查状态
if is_phoenix_running():
    print("Phoenix运行中")

# 停止（通常自动清理）
stop_phoenix_ui()
```

**Phoenix功能:**
- 🔍 追踪检索和LLM调用
- 📊 可视化向量空间
- ⏱️ 性能分析和Token统计
- 📈 评估查询质量

---

## 🚀 快速使用流程

```python
# 1. 配置验证
from src.config import config
is_valid, error = config.validate()

# 2. 加载文档
from src.data_loader import load_documents_from_directory
docs = load_documents_from_directory(config.RAW_DATA_PATH)

# 3. 构建索引
from src.indexer import IndexManager
index_manager = IndexManager()
index_manager.build_index(docs)

# 4. 对话查询（包含推理链）
from src.chat_manager import ChatManager
chat_manager = ChatManager(index_manager)
chat_manager.start_session()
answer, sources, reasoning_content = chat_manager.chat("什么是系统科学？")

# 推理链内容（可选）
if reasoning_content:
    print(f"推理过程: {reasoning_content}")
```

---

## 📊 数据类型

### LlamaDocument
```python
from llama_index.core import Document as LlamaDocument

doc = LlamaDocument(
    text="文档内容",
    metadata={
        "file_name": "example.md",
        "title": "标题",
        "source_type": "local|github|web"
    }
)
```

### 元数据字段（GitHub来源）
- `source_type`: `"github"`
- `repository`: `"owner/repo"`
- `branch`: 分支名
- `file_path`: 仓库内路径
- `url`: GitHub在线链接

---

## ⚠️ 错误处理

### 返回None的方法
- `MarkdownLoader.load_file()` - 文件不存在/读取失败
- `WebLoader.load_url()` - 网络请求失败

### 抛出异常的方法
- `IndexManager.build_index()` - 索引构建失败
- `QueryEngine.query()` - API调用失败
- `ChatManager.chat()` - 对话失败

### 静默失败（跳过失败项）
- `load_urls()` - 批量URL加载
- `load_repositories()` - 批量仓库加载

---

## 🔗 相关文档

- [架构设计](ARCHITECTURE.md) - 系统架构和设计思路
- [项目结构](PROJECT_STRUCTURE.md) - 代码组织说明
- [测试指南](../tests/README.md) - 测试文档

---

**💡 提示:** 详细的参数说明、返回值格式、完整示例请查看源码中的docstring文档。
