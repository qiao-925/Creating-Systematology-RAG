# 架构设计文档

> 本文档详细说明系统科学知识库RAG应用的架构设计、模块关系和实现思路

## 目录

- [架构概览](#架构概览)
- [模块设计](#模块设计)
- [数据流程](#数据流程)
- [核心技术选型](#核心技术选型)
- [扩展指南](#扩展指南)

---

## 架构概览

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Streamlit Web   │         │   CLI 命令行工具         │  │
│  │     (app.py)     │         │     (main.py)           │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
└───────────┼────────────────────────────────┼─────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        业务逻辑层                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  ChatManager     │         │   QueryEngine           │  │
│  │  (对话管理)       │◄────────┤   (查询引擎)            │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
│           │                               │                  │
│           │         ┌─────────────────────▼────┐            │
│           └────────►│   IndexManager            │            │
│                     │   (索引管理)              │            │
│                     └─────────────┬─────────────┘            │
└───────────────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据访问层                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  DataLoader      │         │   Chroma VectorStore    │  │
│  │  (数据加载)       │         │   (向量数据库)           │  │
│  └──────────────────┘         └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        外部服务层                             │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  DeepSeek API    │         │  HuggingFace Embeddings │  │
│  │  (LLM服务)        │         │  (向量化模型)            │  │
│  └──────────────────┘         └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **模块化设计**：每个模块职责单一，低耦合高内聚
2. **依赖注入**：通过构造函数传递依赖，便于测试和替换
3. **配置驱动**：所有配置集中管理，易于调整
4. **分层架构**：清晰的层次划分，便于维护和扩展

---

## 模块设计

### 1. 配置管理模块（src/config.py）

**职责**：统一管理所有配置参数

**核心类**：`Config`

**设计思路**：
- 单例模式：全局唯一配置实例
- 环境变量优先：支持通过 `.env` 文件配置
- 路径自动处理：相对路径自动转换为绝对路径
- 配置验证：启动时验证配置完整性

**关键方法**：
```python
class Config:
    def __init__(self):
        # 加载环境变量
        # 初始化各项配置
        
    def validate(self) -> tuple[bool, Optional[str]]:
        # 验证配置是否完整和合法
        
    def ensure_directories(self):
        # 确保所有必要目录存在
```

**扩展点**：
- 添加新配置项：在 `__init__` 中添加新属性
- 添加验证规则：在 `validate` 方法中添加检查逻辑

---

### 2. 数据加载模块（src/data_loader.py）

**职责**：从多种数据源加载和预处理文档

**核心组件**（使用LlamaIndex官方组件）：
- `SimpleDirectoryReader`：加载本地文件（支持40+格式）
- `SimpleWebPageReader`：抓取网页内容
- `DocumentProcessor`：可选的文档预处理工具

**设计思路**：
- **使用官方组件**：避免重复造轮子，利用LlamaIndex成熟的实现
- **统一接口**：所有加载器返回统一的 `LlamaDocument` 格式
- **容错处理**：内置错误处理，加载失败不中断
- **自动元数据**：自动提取标准元数据（文件路径、名称、类型、时间戳等）

**数据流程**：
```
原始数据源 → LlamaIndex Reader → LlamaDocument → (可选)Processor.clean() → 清洁文档
```

**SimpleDirectoryReader 使用**：
```python
from llama_index.core import SimpleDirectoryReader

def load_documents_from_directory(directory_path, recursive=True):
    """使用官方SimpleDirectoryReader加载文档"""
    reader = SimpleDirectoryReader(
        input_dir=str(directory_path),
        recursive=recursive,
        required_exts=[".md", ".markdown"],  # 可扩展为更多格式
        filename_as_id=True,
    )
    return reader.load_data()
```

**SimpleWebPageReader 使用**：
```python
from llama_index.readers.web import SimpleWebPageReader

def load_documents_from_urls(urls):
    """使用官方SimpleWebPageReader加载网页"""
    reader = SimpleWebPageReader(html_to_text=True)
    return reader.load_data(urls)
```

**优势**：
- **代码简化**：从~300行减少到~50行（减少83%）
- **功能更强**：支持40+文件格式，易于扩展
- **维护成本低**：官方维护和更新
- **自动元数据**：标准化的元数据提取

**扩展点**：
- 新增文件格式：在`required_exts`中添加扩展名（如`.pdf`、`.docx`）
- 自定义元数据：使用`file_metadata`参数添加自定义元数据提取逻辑
- 自定义预处理：使用`DocumentProcessor`进行文本清理

---

### 3. 索引构建模块（src/indexer.py）

**职责**：构建和管理向量索引

**核心类**：`IndexManager`

**设计思路**：
- **向量存储抽象**：使用 LlamaIndex 的抽象层，便于切换向量数据库
- **持久化存储**：使用 Chroma 的 PersistentClient
- **增量更新**：支持在现有索引上添加新文档
- **全局配置**：通过 LlamaIndex 的 Settings 配置 embedding 模型

**初始化流程**：
```
1. 加载 Embedding 模型（HuggingFace）
   ↓
2. 配置 LlamaIndex Settings（全局配置）
   ↓
3. 初始化 Chroma 客户端（持久化存储）
   ↓
4. 创建或获取 Collection
   ↓
5. 构建 VectorStore 和 StorageContext
```

**索引构建流程**：
```
文档列表 → SentenceSplitter (分块) → Embedding (向量化) → Chroma (存储)
```

**核心方法**：
```python
class IndexManager:
    def build_index(self, documents: List[LlamaDocument]) -> VectorStoreIndex:
        # 1. 检查是否已有索引
        # 2. 如果没有：VectorStoreIndex.from_documents()
        # 3. 如果已有：逐个 insert() 文档
        # 4. 返回索引对象
        
    def get_index(self) -> VectorStoreIndex:
        # 1. 如果内存中有缓存，直接返回
        # 2. 否则尝试从向量存储加载
        # 3. 都没有则创建空索引
```

**分块策略**：
- 使用 `SentenceSplitter`（LlamaIndex 内置）
- `chunk_size=512`：每块最多 512 tokens
- `chunk_overlap=50`：相邻块重叠 50 tokens，保持上下文连贯

**扩展点**：
- 切换向量数据库：替换 `ChromaVectorStore` 为其他实现
- 自定义分块：修改 `chunk_size` 和 `chunk_overlap`
- 切换 Embedding 模型：修改配置中的 `EMBEDDING_MODEL`

---

### 4. 查询引擎模块（src/query_engine.py）

**职责**：处理用户查询，生成带引用的答案

**核心类**：
- `QueryEngine`：带引用溯源的查询引擎
- `SimpleQueryEngine`：简单查询引擎（无引用）

**设计思路**：
- **引用溯源核心**：使用 LlamaIndex 的 `CitationQueryEngine`
- **LLM 抽象**：通过 OpenAI 兼容接口集成 DeepSeek
- **分离关注点**：查询逻辑与 LLM 配置分离

**查询流程（CitationQueryEngine）**：
```
用户问题
  ↓
1. 向量检索（Retrieval）
   - 将问题向量化
   - 在 Chroma 中搜索 top_k 个相似文档块
  ↓
2. 上下文构建（Context Building）
   - 整理检索到的文档块
   - 构建 prompt 上下文
  ↓
3. LLM 生成（Generation）
   - 调用 DeepSeek API
   - 生成答案并标注引用
  ↓
4. 结果返回
   - 答案文本
   - 引用来源列表（source_nodes）
```

**核心实现**：
```python
class QueryEngine:
    def __init__(self, index_manager, ...):
        # 1. 配置 DeepSeek LLM
        self.llm = OpenAI(
            api_key=...,
            api_base="https://api.deepseek.com/v1",
            model="deepseek-chat",
            temperature=0.1  # 低温度，更稳定
        )
        
        # 2. 创建 CitationQueryEngine
        self.query_engine = CitationQueryEngine.from_args(
            index,
            llm=self.llm,
            similarity_top_k=3,  # 检索3个最相似文档
            citation_chunk_size=512  # 引用块大小
        )
    
    def query(self, question: str) -> Tuple[str, List[dict]]:
        # 1. 执行查询
        response = self.query_engine.query(question)
        
        # 2. 提取答案和引用
        answer = str(response)
        sources = extract_sources(response.source_nodes)
        
        return answer, sources
```

**DeepSeek 集成要点**：
- 使用 OpenAI SDK（DeepSeek 兼容 OpenAI API）
- 设置 `api_base` 指向 DeepSeek 端点
- `temperature=0.1`：降低随机性，提高答案稳定性

**扩展点**：
- 切换 LLM：修改 `api_base` 和 `model` 参数
- 调整检索数量：修改 `similarity_top_k`
- 自定义 Prompt：继承 `CitationQueryEngine` 并重写 prompt

---

### 5. 对话管理模块（src/chat_manager.py）

**职责**：管理多轮对话、上下文记忆和会话持久化

**核心类**：
- `ChatTurn`：单轮对话数据结构
- `ChatSession`：会话管理
- `ChatManager`：对话管理器

**设计思路**：
- **数据结构分离**：对话数据（ChatSession）与管理逻辑（ChatManager）分离
- **记忆管理**：使用 LlamaIndex 的 `ChatMemoryBuffer`
- **会话持久化**：JSON 格式保存，便于查看和恢复

**对话流程**：
```
用户消息
  ↓
1. 历史上下文加载（从 Memory）
  ↓
2. 问题压缩（Condense Question）
   - 结合历史对话理解当前问题
   - 生成独立的查询语句
  ↓
3. 文档检索（同 QueryEngine）
  ↓
4. 上下文对话生成
   - 结合检索内容和对话历史
   - 生成连贯回答
  ↓
5. 更新记忆
   - 保存用户消息和 AI 回答
  ↓
6. 保存到会话历史
```

**CondensePlusContextChatEngine 工作原理**：
```
历史对话：
  User: 什么是系统科学？
  AI: 系统科学是研究系统一般规律的学科...
  
当前问题：
  User: 它有哪些分支？

处理流程：
  1. Condense: "它" → "系统科学"
     生成独立问题: "系统科学有哪些分支？"
  2. Retrieve: 检索相关文档
  3. Generate: 结合上下文生成答案
```

**会话持久化**：
```python
class ChatSession:
    def save(self, save_dir: Path):
        # 序列化为 JSON
        data = {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'history': [turn.to_dict() for turn in self.history]
        }
        # 保存到文件
        
    @classmethod
    def load(cls, file_path: Path):
        # 从 JSON 文件加载
        # 反序列化为对象
```

**扩展点**：
- 自定义记忆策略：替换 `ChatMemoryBuffer`
- 调整记忆容量：修改 `memory_token_limit`
- 添加会话元数据：扩展 `ChatSession` 类

---

## 数据流程

### 完整数据流程图

```
┌─────────────────┐
│  用户上传文档    │
└────────┬────────┘
         ▼
┌─────────────────────────┐
│  DataLoader.load()      │  ← Markdown/URL
│  返回 LlamaDocument[]   │
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  IndexManager           │
│  .build_index()         │
├─────────────────────────┤
│ 1. SentenceSplitter     │  ← 分块
│ 2. HuggingFace Embed    │  ← 向量化
│ 3. Chroma.add()         │  ← 存储
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  向量索引已就绪          │
└─────────────────────────┘

--- 查询阶段 ---

┌─────────────────┐
│  用户提问        │
└────────┬────────┘
         ▼
┌─────────────────────────┐
│  QueryEngine/ChatManager│
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  1. 问题向量化           │  ← HuggingFace Embed
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  2. 向量相似度搜索       │  ← Chroma.search()
│     返回 top_k 文档      │
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  3. 构建 Prompt          │
│     问题 + 检索文档      │
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  4. 调用 DeepSeek API    │  ← LLM 生成
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  5. 返回答案 + 引用来源   │
└─────────────────────────┘
```

---

## 核心技术选型

### LlamaIndex 架构集成

**为什么选择 LlamaIndex？**
- 专门为 RAG 场景设计
- 内置引用溯源功能
- 抽象层设计良好，易于切换底层实现
- 活跃的社区和完善的文档

**LlamaIndex 核心概念映射**：

| LlamaIndex 概念 | 本项目使用 | 说明 |
|----------------|-----------|------|
| Document | LlamaDocument | 原始文档 |
| Node | 自动创建 | 文档分块后的节点 |
| VectorStoreIndex | IndexManager | 向量索引 |
| VectorStore | ChromaVectorStore | 向量存储后端 |
| Embedding | HuggingFaceEmbedding | 向量化模型 |
| LLM | OpenAI (DeepSeek) | 大语言模型 |
| QueryEngine | CitationQueryEngine | 查询引擎 |
| ChatEngine | CondensePlusContextChatEngine | 对话引擎 |

### Chroma 数据持久化

**存储结构**：
```
vector_store/
└── chroma.sqlite3          # SQLite 数据库
    ├── collections 表       # 集合信息
    ├── embeddings 表        # 向量数据
    └── documents 表         # 文档元数据
```

**为什么选择 Chroma？**
- 轻量级：单机部署，无需额外服务
- 持久化：支持本地文件存储
- 性能：对于中等规模（<1000 文档）足够快
- 易用：Python API 简洁直观

### DeepSeek API 集成

**API 兼容性**：
```python
# DeepSeek 兼容 OpenAI API 格式
OpenAI(
    api_key="sk-xxx",
    api_base="https://api.deepseek.com/v1",  # 关键：指向 DeepSeek
    model="deepseek-chat"
)
```

**请求流程**：
```
LlamaIndex → OpenAI SDK → DeepSeek API → 返回生成文本
```

---

## 扩展指南

### 1. 添加新的数据源

**步骤**：

1. 创建新的 Loader 类：

```python
# src/data_loader.py

class PDFLoader:
    def load_file(self, file_path: Path) -> Optional[LlamaDocument]:
        # 1. 读取 PDF
        # 2. 提取文本
        # 3. 构建元数据
        # 4. 返回 LlamaDocument
        pass
```

2. 添加便捷函数：

```python
def load_documents_from_pdfs(directory: Path) -> List[LlamaDocument]:
    loader = PDFLoader()
    return loader.load_directory(directory)
```

3. 在 UI 中集成（如需要）。

### 2. 切换向量数据库

**从 Chroma 切换到 Qdrant**：

```python
# src/indexer.py

from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

class IndexManager:
    def __init__(self, ...):
        # 替换 Chroma
        client = qdrant_client.QdrantClient(path=str(self.persist_dir))
        self.vector_store = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name
        )
        # 其余代码保持不变
```

**优势**：LlamaIndex 的抽象层使得切换成本极低！

### 3. 切换 LLM

**使用 Azure OpenAI**：

```python
# src/query_engine.py

from llama_index.llms.azure_openai import AzureOpenAI

class QueryEngine:
    def __init__(self, ...):
        self.llm = AzureOpenAI(
            deployment_name="gpt-4",
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint
        )
        # 其余代码保持不变
```

**使用本地 Ollama**：

```python
from llama_index.llms.ollama import Ollama

self.llm = Ollama(model="llama2", request_timeout=120.0)
```

### 4. 自定义分块策略

**使用语义分块**：

```python
# src/indexer.py

from llama_index.core.node_parser import SemanticSplitterNodeParser

Settings.node_parser = SemanticSplitterNodeParser(
    buffer_size=1,
    breakpoint_percentile_threshold=95,
    embed_model=self.embed_model
)
```

### 5. 添加新的查询模式

**实现混合检索（Hybrid Search）**：

```python
# src/query_engine.py

class HybridQueryEngine:
    def __init__(self, index_manager):
        # 1. 向量检索
        self.vector_retriever = index_manager.get_index().as_retriever()
        
        # 2. BM25 关键词检索
        from llama_index.retrievers.bm25 import BM25Retriever
        self.bm25_retriever = BM25Retriever.from_defaults(...)
        
        # 3. 混合检索
        from llama_index.core.retrievers import QueryFusionRetriever
        self.retriever = QueryFusionRetriever(
            [self.vector_retriever, self.bm25_retriever],
            similarity_top_k=5,
        )
```

### 6. 添加评估和监控

**实现查询质量评估**：

```python
# 新建 src/evaluator.py

from llama_index.core.evaluation import FaithfulnessEvaluator

class QueryEvaluator:
    def __init__(self, llm):
        self.faithfulness_evaluator = FaithfulnessEvaluator(llm=llm)
    
    def evaluate_response(self, query, response):
        # 评估答案的忠实度（是否基于检索内容）
        result = self.faithfulness_evaluator.evaluate_response(
            query=query,
            response=response
        )
        return result.passing  # True/False
```

---

## 性能优化建议

### 1. Embedding 模型优化

**当前**：本地 bge-base-zh-v1.5（约400MB）

**优化选项**：
- 使用更小的模型：`m3e-small`（减少内存占用）
- 使用 API：切换到 OpenAI embeddings（更快，但有成本）
- GPU 加速：配置 CUDA 加速向量化

### 2. 索引优化

**批量索引**：
```python
# 不推荐：逐个插入
for doc in documents:
    index.insert(doc)

# 推荐：批量插入
index = VectorStoreIndex.from_documents(documents, ...)
```

**增量索引策略**：
```python
# 只索引新文档
new_docs = filter_new_documents(documents)
index_manager.build_index(new_docs)
```

### 3. 查询优化

**缓存常见查询**：
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(question: str):
    return query_engine.query(question)
```

**调整检索数量**：
```python
# 根据文档数量动态调整
if doc_count < 100:
    similarity_top_k = 3
elif doc_count < 500:
    similarity_top_k = 5
else:
    similarity_top_k = 10
```

---

## 总结

本架构设计遵循以下核心理念：

1. **模块化**：每个模块职责清晰，易于理解和维护
2. **可扩展**：通过抽象和接口设计，支持灵活替换和扩展
3. **配置驱动**：所有关键参数可配置，无需修改代码
4. **文档优先**：详细的文档和注释，降低理解门槛

通过本文档，开发者应该能够：
- 理解整体架构和数据流程
- 快速定位需要修改的模块
- 扩展新功能而不破坏现有系统
- 优化性能和调整参数

## 相关文档

- [开发者指南](DEVELOPER_GUIDE.md) - 详细的代码说明和开发指南
- [API参考](API.md) - 完整的API接口文档
- [技术决策](DECISIONS.md) - 技术选型的原因和考量
- [开发日志](CHANGELOG.md) - 项目进展记录

祝开发愉快！🚀

