# 开发者指南

> 面向开发者的详细代码说明和开发指南

## 目录

- [快速上手](#快速上手)
- [代码结构说明](#代码结构说明)
- [核心API参考](#核心api参考)
- [常见开发任务](#常见开发任务)
- [调试技巧](#调试技巧)
- [最佳实践](#最佳实践)

---

## 快速上手

### 开发环境设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd Creating-Systematology-RAG

# 2. 安装开发依赖
uv sync

# 3. 配置环境变量
cp env.template .env
# 编辑 .env 文件

# 4. 运行测试
python -m pytest tests/  # 如果有测试

# 5. 启动开发服务器
streamlit run app.py
```

### 项目结构说明

```
Creating-Systematology-RAG/
├── src/                        # 核心业务逻辑
│   ├── __init__.py            # 包初始化
│   ├── config.py              # 配置管理 [重要]
│   ├── data_loader.py         # 数据加载 [扩展点]
│   ├── indexer.py             # 索引构建 [核心]
│   ├── query_engine.py        # 查询引擎 [核心]
│   └── chat_manager.py        # 对话管理 [核心]
├── app.py                      # Streamlit Web 应用
├── main.py                     # CLI 命令行工具
├── data/                       # 数据目录
├── vector_store/              # 向量数据库存储
├── sessions/                  # 会话记录
└── docs/                      # 文档
    ├── ARCHITECTURE.md        # 架构设计 [先读这个]
    ├── DEVELOPER_GUIDE.md     # 本文件
    └── API.md                 # API 文档
```

**阅读顺序建议**：
1. `docs/ARCHITECTURE.md` - 理解整体架构
2. `docs/DEVELOPER_GUIDE.md` - 本文，了解开发细节
3. `src/config.py` - 理解配置管理
4. `src/indexer.py` - 理解核心索引逻辑
5. `src/query_engine.py` 或 `src/chat_manager.py` - 根据需求选择

---

## 代码结构说明

### 1. 配置管理（src/config.py）

**文件职责**：统一管理所有配置

**核心代码解析**：

```python
class Config:
    def __init__(self):
        # 1. 项目根目录（基于代码文件位置自动确定）
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # 2. API 配置（从环境变量读取）
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        
        # 3. 路径配置（支持相对路径和绝对路径）
        self.VECTOR_STORE_PATH = self._get_path("VECTOR_STORE_PATH", "vector_store")
```

**关键方法 `_get_path` 解析**：
```python
def _get_path(self, env_var: str, default: str) -> Path:
    """智能路径处理
    - 如果环境变量中是绝对路径，直接使用
    - 如果是相对路径，相对于 PROJECT_ROOT
    """
    path_str = os.getenv(env_var, default)
    path = Path(path_str)
    
    if not path.is_absolute():
        path = self.PROJECT_ROOT / path  # 转换为绝对路径
        
    return path
```

**使用方式**：
```python
from src.config import config

# 直接使用全局配置实例
print(config.DEEPSEEK_API_KEY)
print(config.VECTOR_STORE_PATH)
```

**扩展配置**：
```python
# 在 Config.__init__ 中添加新配置
self.MY_NEW_CONFIG = os.getenv("MY_NEW_CONFIG", "default_value")

# 在 .env 文件中设置
MY_NEW_CONFIG=my_value
```

---

### 2. 数据加载器（src/data_loader.py）

**文件职责**：加载和预处理各类数据源

**类图**：
```
                   ┌─────────────────┐
                   │ LlamaDocument   │  ← LlamaIndex 的文档类
                   └────────▲────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────┴────────┐  ┌──────┴───────┐  ┌────────┴─────────┐
│MarkdownLoader  │  │  WebLoader   │  │DocumentProcessor │
└────────────────┘  └──────────────┘  └──────────────────┘
```

**MarkdownLoader 详解**：

```python
class MarkdownLoader:
    def load_file(self, file_path: Path) -> Optional[LlamaDocument]:
        # 步骤 1：读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 步骤 2：提取标题（用于元数据）
        title = self._extract_title(content)  # 查找第一个 "# 标题"
        
        # 步骤 3：构建 LlamaDocument
        doc = LlamaDocument(
            text=content,                    # 原始文本
            metadata={                       # 元数据
                "file_path": str(file_path),
                "file_name": file_path.name,
                "title": title,
                "source_type": "markdown",
            }
        )
        return doc
```

**为什么需要元数据？**
- 在查询结果中显示来源
- 方便过滤和分类
- 便于调试和追踪

**WebLoader 关键点**：

```python
class WebLoader:
    def load_url(self, url: str) -> Optional[LlamaDocument]:
        # 步骤 1：发送 HTTP 请求
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        
        # 步骤 2：解析 HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 步骤 3：移除无用标签
        for script in soup(["script", "style"]):  # 删除 JS 和 CSS
            script.decompose()
        
        # 步骤 4：提取纯文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 步骤 5：清理格式
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 合并多余空行
```

**DocumentProcessor 的作用**：

```python
@staticmethod
def clean_text(text: str) -> str:
    """清理文本
    1. 移除多余空白
    2. 统一换行
    3. 去除首尾空格
    """
    text = re.sub(r'[ \t]+', ' ', text)      # 多个空格 → 单个空格
    text = re.sub(r'\n{3,}', '\n\n', text)   # 多个换行 → 两个换行
    return text.strip()
```

**添加新数据源示例**：

```python
class SQLLoader:
    """从数据库加载数据"""
    
    def __init__(self, connection_string: str):
        self.conn = create_connection(connection_string)
    
    def load_table(self, table_name: str) -> List[LlamaDocument]:
        # 1. 查询数据库
        rows = self.conn.execute(f"SELECT * FROM {table_name}")
        
        # 2. 每行转换为文档
        documents = []
        for row in rows:
            doc = LlamaDocument(
                text=row['content'],
                metadata={
                    "source_type": "database",
                    "table": table_name,
                    "id": row['id']
                }
            )
            documents.append(doc)
        
        return documents
```

---

### 3. 索引构建器（src/indexer.py）

**文件职责**：构建和管理向量索引

**初始化流程详解**：

```python
class IndexManager:
    def __init__(self, ...):
        # 步骤 1：加载 Embedding 模型
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-base-zh-v1.5",  # 中文优化模型
            trust_remote_code=True,
        )
        # 首次运行会下载模型到 ~/.cache/huggingface/
        
        # 步骤 2：全局配置（影响所有 LlamaIndex 操作）
        Settings.embed_model = self.embed_model      # 设置 embedding
        Settings.chunk_size = 512                    # 分块大小
        Settings.chunk_overlap = 50                  # 重叠大小
        
        # 步骤 3：初始化 Chroma
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir)  # SQLite 存储路径
        )
        
        # 步骤 4：创建或获取集合
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        
        # 步骤 5：包装为 LlamaIndex 的 VectorStore
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )
```

**索引构建的两种模式**：

```python
def build_index(self, documents: List[LlamaDocument]) -> VectorStoreIndex:
    # 模式 1：从头创建索引
    if self._index is None:
        self._index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=True
        )
        # 内部流程：
        # 1. 分块（SentenceSplitter）
        # 2. 每个块 → embed_model → 向量
        # 3. 向量 + 元数据 → Chroma 存储
    
    # 模式 2：增量添加
    else:
        for doc in documents:
            self._index.insert(doc)
        # 适用于已有索引，只添加新文档
```

**为什么需要 StorageContext？**

```python
self.storage_context = StorageContext.from_defaults(
    vector_store=self.vector_store
)
```

`StorageContext` 是 LlamaIndex 的存储抽象层：
- 管理向量存储
- 管理文档存储（可选）
- 管理索引结构存储（可选）
- 便于在不同存储后端间切换

**Chroma 的数据结构**：

```
Chroma Collection
├── id: 唯一标识符
├── embedding: 向量 [768维浮点数]
├── document: 文本内容
└── metadata: {
    "file_name": "xxx.md",
    "title": "xxx",
    ...
}
```

**查询向量数据库的底层流程**：

```python
# 1. 用户问题向量化
question = "什么是系统科学？"
question_vector = embed_model.get_text_embedding(question)  # [768]

# 2. Chroma 相似度搜索（余弦相似度）
results = chroma_collection.query(
    query_embeddings=[question_vector],
    n_results=3  # top 3
)

# 3. 返回最相似的文档块
```

---

### 4. 查询引擎（src/query_engine.py）

**文件职责**：处理查询，生成带引用的答案

**CitationQueryEngine 工作原理**：

```python
self.query_engine = CitationQueryEngine.from_args(
    index,
    llm=self.llm,
    similarity_top_k=3,         # 检索 3 个文档
    citation_chunk_size=512,    # 引用块大小
)
```

**内部流程（简化版）**：

```python
def query(self, question: str):
    # 步骤 1：检索相关文档
    retrieved_nodes = index.retrieve(question, top_k=3)
    
    # 步骤 2：构建带编号的上下文
    context = ""
    for i, node in enumerate(retrieved_nodes, 1):
        context += f"[{i}] {node.text}\n\n"
    
    # 步骤 3：构建 Prompt
    prompt = f"""
    基于以下上下文回答问题，并在答案中引用来源编号 [1], [2], [3]。
    
    上下文：
    {context}
    
    问题：{question}
    
    答案：
    """
    
    # 步骤 4：调用 LLM
    answer = llm.complete(prompt)
    
    # 步骤 5：解析引用
    # answer 中包含 [1], [2] 等引用标记
    
    return answer, retrieved_nodes
```

**DeepSeek API 调用细节**：

```python
from llama_index.llms.openai import OpenAI

self.llm = OpenAI(
    api_key="sk-xxx",
    api_base="https://api.deepseek.com/v1",  # 关键：DeepSeek 端点
    model="deepseek-chat",
    temperature=0.1,  # 低温度 → 更确定性的输出
)

# 实际调用
response = self.llm.complete(prompt)
# 等价于：
# POST https://api.deepseek.com/v1/completions
# {
#   "model": "deepseek-chat",
#   "prompt": "...",
#   "temperature": 0.1
# }
```

**temperature 参数说明**：
- `0.0`：完全确定性，每次输出相同
- `0.1-0.3`：较确定，适合问答
- `0.7-1.0`：较随机，适合创作

**提取引用来源的代码**：

```python
def query(self, question: str) -> Tuple[str, List[dict]]:
    response = self.query_engine.query(question)
    
    # 提取答案
    answer = str(response)
    
    # 提取引用来源
    sources = []
    if hasattr(response, 'source_nodes'):
        for i, node in enumerate(response.source_nodes, 1):
            source = {
                'index': i,                    # 引用编号
                'text': node.node.text,        # 原文
                'score': node.score,           # 相似度分数
                'metadata': node.node.metadata # 元数据（文件名等）
            }
            sources.append(source)
    
    return answer, sources
```

---

### 5. 对话管理器（src/chat_manager.py）

**文件职责**：管理多轮对话和上下文

**数据结构设计**：

```python
@dataclass
class ChatTurn:
    """单轮对话"""
    question: str            # 用户问题
    answer: str              # AI 回答
    sources: List[dict]      # 引用来源
    timestamp: str           # 时间戳

class ChatSession:
    """对话会话"""
    session_id: str                  # 会话 ID
    history: List[ChatTurn]          # 对话历史
    created_at: str                  # 创建时间
    updated_at: str                  # 更新时间
```

**为什么分离数据和逻辑？**
- `ChatSession`：纯数据，易于序列化和存储
- `ChatManager`：业务逻辑，处理对话流程

**CondensePlusContextChatEngine 详解**：

```python
self.chat_engine = CondensePlusContextChatEngine.from_defaults(
    retriever=index.as_retriever(similarity_top_k=3),
    llm=self.llm,
    memory=self.memory,
    context_prompt="你是系统科学专家..."
)
```

**内部工作流程**：

```python
# 假设对话历史：
# User: 什么是系统科学？
# AI: 系统科学是研究系统一般规律的学科...

# 当前问题：
user_message = "它有哪些分支？"

# 步骤 1：Condense（问题凝练）
# 结合历史上下文，生成独立问题
condensed_question = condense_llm.complete(
    f"历史对话：{memory}\n当前问题：{user_message}\n\n"
    f"请生成一个独立的、完整的问题："
)
# 输出："系统科学有哪些分支？"

# 步骤 2：检索相关文档
retrieved_docs = retriever.retrieve(condensed_question)

# 步骤 3：生成回答
answer = llm.complete(
    f"上下文：{retrieved_docs}\n"
    f"对话历史：{memory}\n"
    f"问题：{user_message}\n"
    f"答案："
)

# 步骤 4：更新记忆
memory.put(ChatMessage(role="user", content=user_message))
memory.put(ChatMessage(role="assistant", content=answer))
```

**会话持久化实现**：

```python
def save(self, save_dir: Path):
    # 序列化为 JSON
    data = self.to_dict()  # 转换为字典
    
    file_path = save_dir / f"{self.session_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # ensure_ascii=False: 保持中文可读
    # indent=2: 格式化输出

@classmethod
def load(cls, file_path: Path):
    # 从 JSON 反序列化
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return cls.from_dict(data)
```

**会话恢复时记忆的重建**：

```python
def load_session(self, file_path: Path):
    # 1. 加载会话数据
    self.current_session = ChatSession.load(file_path)
    
    # 2. 重建记忆
    self.memory.reset()
    for turn in self.current_session.history:
        self.memory.put(ChatMessage(role="user", content=turn.question))
        self.memory.put(ChatMessage(role="assistant", content=turn.answer))
    # 现在 AI 能"记起"之前的对话
```

---

## 核心API参考

### ConfigManager API

```python
from src.config import config

# 访问配置
api_key = config.DEEPSEEK_API_KEY
vector_path = config.VECTOR_STORE_PATH

# 验证配置
is_valid, error = config.validate()

# 确保目录存在
config.ensure_directories()
```

### DataLoader API

```python
from src.data_loader import (
    MarkdownLoader,
    WebLoader,
    load_documents_from_directory,
    load_documents_from_urls
)

# 方式 1：使用 Loader 类
loader = MarkdownLoader()
doc = loader.load_file(Path("document.md"))
docs = loader.load_directory(Path("./docs"), recursive=True)

# 方式 2：使用便捷函数（推荐）
docs = load_documents_from_directory("./data/raw", recursive=True)
docs = load_documents_from_urls(["http://example.com/article"])
```

### IndexManager API

```python
from src.indexer import IndexManager

# 创建索引管理器
index_manager = IndexManager(
    collection_name="my_docs",
    chunk_size=512,
    chunk_overlap=50
)

# 构建索引
index = index_manager.build_index(documents)

# 获取索引
index = index_manager.get_index()

# 获取统计
stats = index_manager.get_stats()

# 清空索引
index_manager.clear_index()

# 测试搜索
results = index_manager.search("查询文本", top_k=5)
```

### QueryEngine API

```python
from src.query_engine import QueryEngine, SimpleQueryEngine

# 创建查询引擎（带引用）
query_engine = QueryEngine(index_manager)

# 查询
answer, sources = query_engine.query("什么是系统科学？")

# 格式化输出
from src.query_engine import format_sources
print(answer)
print(format_sources(sources))

# 简单查询（无引用）
simple_engine = SimpleQueryEngine(index_manager)
answer = simple_engine.query("快速问题")
```

### ChatManager API

```python
from src.chat_manager import ChatManager

# 创建对话管理器
chat_manager = ChatManager(index_manager)

# 开始新会话
session = chat_manager.start_session()

# 对话
answer, sources = chat_manager.chat("什么是系统科学？")
answer, sources = chat_manager.chat("它有哪些应用？")  # 理解"它"指系统科学

# 获取当前会话
session = chat_manager.get_current_session()

# 保存会话
chat_manager.save_current_session()

# 加载会话
chat_manager.load_session(Path("sessions/session_xxx.json"))

# 重置会话
chat_manager.reset_session()
```

---

## 常见开发任务

### 任务 1：添加 PDF 支持

**步骤**：

1. 安装依赖：
```bash
uv add pypdf
```

2. 创建 PDFLoader：
```python
# src/data_loader.py

from pypdf import PdfReader

class PDFLoader:
    def load_file(self, file_path: Path) -> Optional[LlamaDocument]:
        reader = PdfReader(file_path)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        return LlamaDocument(
            text=text,
            metadata={
                "file_path": str(file_path),
                "file_name": file_path.name,
                "source_type": "pdf",
                "page_count": len(reader.pages)
            }
        )
```

3. 在 UI 中添加支持（app.py）：
```python
uploaded_files = st.file_uploader(
    "选择文件",
    type=['md', 'markdown', 'pdf'],  # 添加 pdf
    accept_multiple_files=True
)
```

### 任务 2：添加文档过滤

```python
# src/indexer.py

class IndexManager:
    def search_by_metadata(
        self,
        query: str,
        filters: dict,
        top_k: int = 5
    ) -> List[dict]:
        """按元数据过滤搜索
        
        示例：
        results = index_manager.search_by_metadata(
            query="系统科学",
            filters={"source_type": "markdown", "title": "钱学森"}
        )
        """
        retriever = self.index.as_retriever(
            similarity_top_k=top_k,
            filters=filters  # Chroma 支持元数据过滤
        )
        nodes = retriever.retrieve(query)
        return [self._node_to_dict(node) for node in nodes]
```

### 任务 3：添加查询日志

```python
# 新建 src/logger.py

import logging
from datetime import datetime

class QueryLogger:
    def __init__(self, log_file: str = "query_log.json"):
        self.log_file = log_file
    
    def log_query(self, question: str, answer: str, sources: List[dict]):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "num_sources": len(sources),
            "source_files": [s['metadata'].get('file_name') for s in sources]
        }
        
        # 追加到日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

# 使用
# src/query_engine.py

from src.logger import QueryLogger

class QueryEngine:
    def __init__(self, ...):
        self.logger = QueryLogger()
    
    def query(self, question: str):
        answer, sources = ...  # 原有逻辑
        
        # 记录日志
        self.logger.log_query(question, answer, sources)
        
        return answer, sources
```

### 任务 4：实现文档更新检测

```python
# src/indexer.py

import hashlib

class IndexManager:
    def get_document_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def is_document_updated(self, file_path: Path) -> bool:
        """检查文档是否更新"""
        current_hash = self.get_document_hash(file_path)
        
        # 从元数据中获取旧哈希
        # 需要在索引时保存哈希值到元数据
        
        return current_hash != stored_hash
    
    def incremental_update(self, directory: Path):
        """增量更新：只重新索引修改过的文档"""
        for file in directory.glob("**/*.md"):
            if self.is_document_updated(file):
                # 删除旧文档
                self.delete_document(str(file))
                
                # 重新索引
                doc = load_document(file)
                doc.metadata['file_hash'] = self.get_document_hash(file)
                self.build_index([doc])
```

---

## 调试技巧

### 1. 查看检索到的文档

```python
# 在 query_engine.py 中添加调试代码

def query(self, question: str):
    response = self.query_engine.query(question)
    
    # 调试：打印检索到的文档
    print("\n=== 检索到的文档 ===")
    for i, node in enumerate(response.source_nodes, 1):
        print(f"\n[{i}] 相似度: {node.score:.4f}")
        print(f"文件: {node.node.metadata.get('file_name')}")
        print(f"内容: {node.node.text[:200]}...")
    
    return answer, sources
```

### 2. 测试 Embedding 质量

```python
# 测试脚本

from src.indexer import IndexManager

index_manager = IndexManager()

# 测试查询
queries = [
    "什么是系统科学？",
    "钱学森的贡献",
    "系统工程方法"
]

for query in queries:
    print(f"\n查询: {query}")
    results = index_manager.search(query, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. 分数: {result['score']:.4f}")
        print(f"   文件: {result['metadata']['file_name']}")
```

### 3. 性能分析

```python
import time

def query_with_timing(self, question: str):
    start = time.time()
    
    # 检索阶段
    retrieval_start = time.time()
    retrieved_nodes = self.index.retrieve(question)
    retrieval_time = time.time() - retrieval_start
    
    # 生成阶段
    generation_start = time.time()
    answer = self.llm.complete(...)
    generation_time = time.time() - generation_start
    
    total_time = time.time() - start
    
    print(f"检索耗时: {retrieval_time:.2f}s")
    print(f"生成耗时: {generation_time:.2f}s")
    print(f"总耗时: {total_time:.2f}s")
    
    return answer
```

### 4. 使用 LlamaIndex 的调试工具

```python
# 启用详细日志
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("llama_index").setLevel(logging.DEBUG)

# 现在会看到所有 LlamaIndex 的内部操作
```

---

## 最佳实践

### 1. 错误处理

```python
# 好的做法
def load_file(self, file_path: Path) -> Optional[LlamaDocument]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self._create_document(content, file_path)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None
    except UnicodeDecodeError:
        print(f"❌ 文件编码错误: {file_path}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {file_path} - {e}")
        return None
```

### 2. 配置验证

```python
# 启动时验证配置
def main():
    is_valid, error = config.validate()
    if not is_valid:
        print(f"❌ 配置错误: {error}")
        sys.exit(1)
    
    # 继续执行...
```

### 3. 资源清理

```python
# 使用上下文管理器
class IndexManager:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理资源
        if self.chroma_client:
            # Chroma 会自动处理
            pass

# 使用
with IndexManager() as index_manager:
    index_manager.build_index(documents)
# 自动清理
```

### 4. 单元测试

```python
# tests/test_data_loader.py

import pytest
from src.data_loader import MarkdownLoader

def test_markdown_loader():
    loader = MarkdownLoader()
    
    # 测试文件加载
    doc = loader.load_file(Path("test.md"))
    assert doc is not None
    assert doc.metadata['source_type'] == 'markdown'
    
    # 测试标题提取
    assert doc.metadata['title'] == '测试标题'
```

### 5. 代码组织

```python
# 好的做法：将复杂逻辑分解为小函数

class QueryEngine:
    def query(self, question: str):
        # 主流程清晰
        retrieved_docs = self._retrieve_documents(question)
        context = self._build_context(retrieved_docs)
        answer = self._generate_answer(question, context)
        sources = self._extract_sources(retrieved_docs)
        return answer, sources
    
    def _retrieve_documents(self, question: str):
        # 专注于检索逻辑
        ...
    
    def _build_context(self, docs):
        # 专注于上下文构建
        ...
```

---

## 常见问题

### Q1：如何处理中文分词？

**A**：bge-base-zh-v1.5 模型内置了中文分词，无需额外处理。

### Q2：如何优化检索精度？

**A**：
1. 调整 `chunk_size`（更小的块更精确，但上下文少）
2. 增加 `similarity_top_k`（检索更多文档）
3. 使用更好的 embedding 模型
4. 实现混合检索（向量 + 关键词）

### Q3：如何处理超长文档？

**A**：
```python
# 方法 1：增大 chunk_size
Settings.chunk_size = 1024

# 方法 2：使用层次化索引
# 先索引摘要，再索引详细内容

# 方法 3：使用 LlamaIndex 的 HierarchicalNodeParser
from llama_index.core.node_parser import HierarchicalNodeParser
```

### Q4：如何实现多语言支持？

**A**：
```python
# 使用多语言 embedding 模型
self.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
```

---

## 总结

本开发者指南涵盖了：
- ✅ 详细的代码解析
- ✅ 核心 API 使用方法
- ✅ 常见开发任务示例
- ✅ 调试技巧
- ✅ 最佳实践

**下一步建议**：
1. 阅读 [架构设计文档](ARCHITECTURE.md) 了解整体架构
2. 运行示例代码，理解工作流程
3. 尝试实现一个小功能
4. 查看 LlamaIndex 官方文档深入学习

## 相关文档

- [架构设计](ARCHITECTURE.md) - 系统架构和设计思路
- [API参考](API.md) - 完整的API接口文档
- [技术决策](DECISIONS.md) - 技术选型的原因
- [开发日志](CHANGELOG.md) - 项目进展记录

祝开发顺利！🚀

