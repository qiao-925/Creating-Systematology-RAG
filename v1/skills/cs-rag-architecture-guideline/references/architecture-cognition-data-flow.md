# 数据流向详细说明

## 1. 查询流程数据流

```
用户输入（前端）
  ↓
frontend/main.py → handle_user_queries()
  ↓
RAGService.query(question, session_id)
  ↓
[选择引擎]
  ├─ use_agentic_rag=True → AgenticQueryEngine.query()
  │   └─ ReActAgent → Tools → Retriever → LLM
  │
  └─ use_agentic_rag=False → ModularQueryEngine.query()
      ↓
      QueryProcessor.process() [意图理解+改写]
      ↓
      [路由决策]
      ├─ enable_auto_routing=True → QueryRouter.route()
      │   └─ 根据查询类型选择策略
      │
      └─ enable_auto_routing=False → 使用固定策略
      ↓
      create_retriever() [工厂模式]
      ↓
      Retriever.retrieve() [检索相关文档]
      ↓
      [后处理]
      ├─ SimilarityCutoff [相似度过滤]
      └─ Reranker [重排序，可选]
      ↓
      LLM.generate() [生成答案]
      ↓
      ResponseFormatter.format() [格式化响应]
      ↓
      RAGResponse {answer, sources, metadata}
      ↓
      前端展示
```

## 2. 索引构建流程数据流

```
数据源（GitHub/本地）
  ↓
DataImportService.import_from_github() / import_from_directory()
  ↓
[数据源处理]
  ├─ GitHub → GitRepositoryManager.clone() / pull()
  │   └─ GitHubSource.load() [获取文件列表]
  │
  └─ 本地 → LocalFileSource.load() [获取文件列表]
  ↓
DocumentParser.parse_files() [解析为 LlamaDocument]
  ↓
IndexManager.build_index(documents)
  ↓
[分块]
  └─ SentenceSplitter [分块为 Node]
  ↓
[向量化]
  └─ Embedding.embed_nodes() [生成向量]
  ↓
[存储]
  └─ ChromaVectorStore [存储到 Chroma Cloud]
  ↓
VectorStoreIndex [索引构建完成]
```

## 3. 数据流关键节点

### 3.1 查询流程关键节点

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| **QueryProcessor** | 原始查询 | 处理后查询 + 意图 | 意图理解、查询改写 |
| **QueryRouter** | 处理后查询 + 意图 | 检索策略 | 根据意图选择策略 |
| **Retriever** | 查询 + 策略 | 相关文档 | 执行检索 |
| **Reranker** | 检索结果 | 重排序结果 | 可选，提高相关性 |
| **LLM** | 查询 + 上下文 | 生成答案 | 答案生成 |
| **ResponseFormatter** | 原始响应 | 格式化响应 | 添加来源引用 |

### 3.2 索引构建关键节点

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| **DataSource** | 数据源配置 | 文件列表 | GitHub/本地 |
| **DocumentParser** | 文件列表 | LlamaDocument 列表 | 解析为文档 |
| **SentenceSplitter** | 文档列表 | Node 列表 | 分块 |
| **Embedding** | Node 列表 | 带向量的 Node | 向量化 |
| **ChromaVectorStore** | 带向量的 Node | 存储完成 | 持久化 |

## 4. 数据结构

### 4.1 RAGResponse

```python
@dataclass
class RAGResponse:
    answer: str              # 生成的答案
    sources: List[Source]    # 来源引用列表
    metadata: Dict           # 元数据（耗时、策略等）
```

### 4.2 Source

```python
@dataclass
class Source:
    file_path: str      # 文件路径
    content: str        # 相关内容片段
    score: float        # 相关性分数
    line_range: Tuple   # 行号范围（可选）
```

### 4.3 QueryIntent

```python
@dataclass
class QueryIntent:
    query_type: str     # 查询类型（factual/analytical/...）
    keywords: List[str] # 关键词
    entities: List[str] # 实体
    confidence: float   # 置信度
```

## 5. 性能关键路径

### 5.1 查询延迟瓶颈

1. **Embedding 计算**：查询向量化（~100ms）
2. **向量检索**：Chroma 检索（~50-200ms）
3. **LLM 生成**：答案生成（~1-3s）

### 5.2 索引构建瓶颈

1. **文档解析**：大文件解析（取决于文件大小）
2. **分块**：SentenceSplitter（~10ms/文档）
3. **向量化**：Embedding 计算（~100ms/批次）
4. **存储**：Chroma 写入（~50ms/批次）
