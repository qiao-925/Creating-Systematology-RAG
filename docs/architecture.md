# 架构设计文档

> 本文档详细描述系统的架构设计、模块交互关系、工作流程和关键决策。

---

## 1. 核心设计原则

1. **模块化优先**：三层架构（前端层、业务层、基础设施层），职责清晰，低耦合高内聚
2. **可插拔设计**：所有核心组件（Embedding、DataSource、Observer、Reranker、Retriever）支持可插拔替换
3. **配置驱动**：集中管理配置，支持运行时切换，无需修改代码
4. **架构统一**：前端代码独立组织（frontend/），单页应用架构，功能通过弹窗实现
5. **原生组件优先**：优先使用 Streamlit 原生组件（`st.chat_input()`、`st.dialog()` 等），减少自定义代码
6. **主题适配**：完整支持 Light/Dark 模式切换，使用 CSS 变量实现主题适配
7. **可观测性优先**：集成 LlamaDebugHandler、RAGAS，行为透明可追踪
8. **工程实践**：结构化日志（structlog）、类型安全（Pydantic），提升代码质量

---

## 2. 系统整体架构

### 2.1 RAG 链路整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Streamlit)                  │
├─────────────────────────────────────────────────────────────┤
│                        RAG Service Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  RAGService  │  │  Chat Manager │  │ Session Store  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      RAG Engine Layer                        │
│  ┌────────────────────┐  ┌────────────────────┐             │
│  │ ModularQueryEngine │  │ AgenticQueryEngine │             │
│  │   (传统 RAG)       │  │  (Agentic RAG)     │             │
│  └────────────────────┘  └────────────────────┘             │
├─────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                     │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Indexer │  │ Embedding │  │   LLMs   │  │  Observers  │  │
│  └─────────┘  └───────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 查询处理流程

```
用户查询
    ↓
QueryProcessor (意图理解 + 改写)
    ↓
┌─────────────────────────────┐
│ 路由决策 (QueryRouter)       │
│   - 简单查询 → vector        │
│   - 精确查询 → grep          │
│   - 复杂查询 → hybrid/multi  │
└─────────────────────────────┘
    ↓
检索执行 (Retriever)
    ↓
后处理 (Reranker + SimilarityCutoff)
    ↓
LLM 响应生成 (DeepSeek)
    ↓
格式化输出 (ResponseFormatter)
```

---

## 3. 三层架构详解

### 3.1 架构分层图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层（Presentation）                      │
│  ┌──────────────┐  ┌──────────────────┐                    │
│  │  app.py      │→ │  frontend/main.py│                    │
│  │ (Streamlit)  │  │  单页应用入口    │                    │
│  └──────┬───────┘  └────────┬─────────┘                    │
│         │                   │                               │
│         └───────────┬───────┘                               │
│                     │                                       │
│             只调用 RAGService                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   业务层（Business）                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          RAGService (统一服务接口)                    │  │
│  │  query(question) -> RAGResponse                      │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│         ┌────────────┼────────────┐                        │
│         ▼            ▼            ▼                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │Pipeline  │  │Strategy  │  │Context   │                │
│  │Executor  │  │Manager   │  │Manager   │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │             │             │                        │
│  ┌────┴─────────────┴─────────────┴────┐                  │
│  │    能力模块（通过协议协作）            │                  │
│  │  Retriever → Generator → Formatter   │                  │
│  │  → FallbackStrategy                  │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  通过依赖注入获取基础设施层资源                               │
└───────────────────────────┬────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               基础设施层（Infrastructure）                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Config   │  │ Logger   │  │DataSource│  │ Chroma   │  │
│  │ Embedding│  │ Observer │  │ Git      │  │ LLM      │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────────────────────────────────┐                  │
│  │  ModuleRegistry (模块注册中心)        │                  │
│  │  - 模块元数据管理                     │                  │
│  │  - 工厂函数创建实例                   │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  向上提供统一服务接口，无业务逻辑                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 各层职责

| 层次 | 职责 | 特点 |
|------|------|------|
| **前端层** | 用户交互与展示 | 只调用RAGService，不持有业务模块 |
| **业务层** | 核心业务逻辑与编排 | 能力模块通过协议协作，流水线编排 |
| **基础设施层** | 技术基础设施 | 无业务逻辑，提供资源和框架能力 |

### 3.3 依赖方向

**⚠️ 强制约束**：
- 前端层 → 业务层 → 基础设施层（单向依赖）
- **禁止反向依赖**：基础设施层不能依赖业务层或前端层
- **禁止跨层访问**：前端层不能直接访问基础设施层

---

## 4. 核心组件

### 4.1 组件索引

| 组件 | 位置 | 功能 |
|------|------|------|
| `RAGService` | `rag_api/rag_service.py` | 统一服务入口，延迟加载引擎 |
| `ModularQueryEngine` | `rag_engine/core/engine.py` | 传统 RAG 引擎 |
| `AgenticQueryEngine` | `rag_engine/agentic/engine.py` | Agentic 引擎（ReActAgent） |
| `QueryProcessor` | `rag_engine/processing/query_processor.py` | 查询意图理解+改写 |
| `create_retriever` | `rag_engine/retrieval/factory.py` | 检索器工厂 |
| `create_reranker` | `rag_engine/reranking/factory.py` | 重排序器工厂 |
| `IndexManager` | `infrastructure/indexer/` | 向量索引管理 |
| `AppConfig` | `frontend/components/config_panel/models.py` | 统一配置模型 |

### 4.2 检索策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `vector` | 向量语义检索 | 通用语义查询 |
| `bm25` | 关键词检索 | 精确术语匹配 |
| `hybrid` | 向量+BM25+RRF融合 | 兼顾语义和关键词 |
| `grep` | 正则/文本检索 | 代码、文件名查询 |
| `multi` | 多策略组合 | 复杂查询 |

### 4.3 关键配置

- `RETRIEVAL_STRATEGY`：检索策略（vector/bm25/hybrid/grep/multi）
- `SIMILARITY_TOP_K`：检索数量
- `ENABLE_RERANK` / `RERANKER_TYPE`：重排序配置
- `ENABLE_AUTO_ROUTING`：自动路由模式
- `use_agentic_rag`：Agentic RAG 模式

---

## 5. 模块交互关系

### 5.1 模块依赖图

**三层架构依赖关系**：
```
前端层
  └─→ RAGService（业务层）
        └─→ IndexManager、QueryEngine（基础设施层）
```

**业务层内部依赖**：
```
RAGService
  ├─→ ModularQueryEngine / AgenticQueryEngine
  │     ├─→ QueryProcessor（查询处理）
  │     ├─→ create_retriever()（检索器工厂）
  │     ├─→ create_reranker()（重排序器工厂）
  │     └─→ ResponseFormatter（响应格式化）
  └─→ ChatManager（对话管理）
```

**基础设施层内部依赖**：
```
IndexManager
  ├─→ Embedding（向量化）
  ├─→ ChromaVectorStore（向量存储）
  └─→ DocumentParser（文档解析）

DataImportService
  ├─→ GitHubSource / LocalFileSource（数据源）
  └─→ DocumentParser（文档解析）
```

### 5.2 核心接口定义

| 接口 | 位置 | 签名 | 说明 |
|------|------|------|------|
| `RAGService.query()` | `rag_api/rag_service.py` | `query(question: str, session_id: Optional[str]) -> RAGResponse` | 统一查询入口 |
| `ModularQueryEngine.query()` | `rag_engine/core/engine.py` | `query(query: str) -> QueryResult` | 传统 RAG 查询 |
| `AgenticQueryEngine.query()` | `rag_engine/agentic/engine.py` | `query(query: str) -> QueryResult` | Agentic RAG 查询 |
| `IndexManager.build_index()` | `indexer/core/manager.py` | `build_index(documents: List[Document]) -> None` | 索引构建 |
| `DataImportService.import_from_github()` | `data_loader/service.py` | `import_from_github(...) -> ImportResult` | GitHub 数据导入 |

### 5.3 跨模块协作模式

**工厂模式**：
- `create_retriever()`：根据策略类型创建对应的检索器
- `create_reranker()`：根据类型创建重排序器
- `create_embedding()`：根据配置创建 Embedding 实例
- `create_llm()`：创建 LLM 实例

**依赖注入**：
- 所有组件通过构造函数注入依赖
- 示例：`RAGService(index_manager: IndexManager)`
- 禁止静态单例或隐式全局变量

**延迟加载**：
- RAGService 中的引擎按需初始化（`@property` 装饰器）
- 避免启动时加载所有组件，提升启动速度

---

## 6. 主要工作流程

### 6.1 数据加载阶段

```
[阶段1] 数据加载阶段
│
├─→ [1.1] 数据源识别与Git仓库处理
│     │
│     ├─ DataImportService [backend/infrastructure/data_loader/service.py]
│     │   ├─ 识别数据源类型（GitHub/本地）
│     │   └─ 调用对应的 DataSource.load()
│     │
│     └─ GitRepositoryManager [backend/infrastructure/git/manager.py]（如果是 GitHub 源）
│         ├─ 初始化：创建本地存储目录（data/github_repos/）
│         ├─ 检查仓库是否存在，判断首次克隆或增量更新
│         ├─ 首次克隆：
│         │   ├─ 执行 git clone --branch {branch} --single-branch --depth 1
│         │   ├─ 浅克隆优化（只获取最新提交）
│         │   ├─ 重试机制（最多3次）
│         │   └─ 网络错误时使用指数退避
│         ├─ 增量更新：
│         │   ├─ 执行 git pull origin {branch}
│         │   └─ 检查分支是否匹配
│         ├─ 获取 Commit SHA（git rev-parse HEAD）
│         └─ 缓存管理：检查缓存有效性，记录仓库路径和commit信息
│
├─→ [1.2] 文件路径获取与过滤
│     └─ GitHubSource/LocalFileSource [backend/infrastructure/data_loader/source/]
│         ├─ 递归遍历目录结构
│         ├─ 排除特定目录：.git, __pycache__, node_modules, .venv, venv, .pytest_cache
│         ├─ 排除特定文件：.pyc, .pyo, .lock, .log
│         ├─ 只包含真实文件（排除符号链接等）
│         ├─ 应用过滤器：
│         │   ├─ 目录过滤（filter_directories，可选）
│         │   └─ 扩展名过滤（filter_file_extensions，可选）
│         └─ 构建 SourceFile 对象（包含路径、仓库信息、commit SHA、GitHub链接）
│
└─→ [1.3] 文档解析
      └─ DocumentParser.parse_files() [backend/infrastructure/data_loader/parser.py]
          ├─ 解析文件为文档对象
          │   └─ 缓存有效则直接返回，跳过解析
          ├─ 验证文件：检查存在性、可读性，过滤无效文件
          ├─ 按目录分组（批量处理优化）：相同目录文件批量解析
          ├─ 解析文件：
          │   ├─ 单个文件：使用 SimpleDirectoryReader 解析
          │   ├─ 目录批量：批量解析同一目录的文件
          │   └─ 支持格式：.md, .txt, .py, .js, .json, .yaml, .yml, .html, .pdf 等
          ├─ 构建 LlamaDocument 对象：
          │   ├─ 文档文本内容
          │   ├─ 文件元数据（路径、来源、URL等）
          │   └─ 文档唯一标识
          ├─ 文本清理（可选）：清理多余空白、规范化换行符
          └─ 返回解析后的文档列表
```

### 6.2 索引构建阶段

```
[阶段2] 索引构建阶段
│
├─→ [2.1] 文档分块（Chunking）
│     └─ IndexManager.build_index() [backend/infrastructure/indexer/index_manager.py]
│         ├─ 检查断点续传：
│         │   ├─ 检查哪些文档已经向量化
│         │   └─ 跳过已处理文档，只处理新文档或更新的文档
│         ├─ 选择构建模式：
│         │   ├─ 批处理模式（INDEX_BATCH_MODE=True）：按目录分组，分批处理
│         │   └─ 正常模式（默认）：直接处理所有文档
│         ├─ 初始化分块器：SentenceSplitter
│         │   ├─ chunk_size：分块大小（默认512）
│         │   └─ chunk_overlap：块重叠大小（默认20）
│         ├─ 执行分块：
│         │   ├─ 按句子边界分割
│         │   ├─ 使用滑动窗口（overlap）保持上下文连续性
│         │   ├─ 智能处理代码块、列表等特殊结构
│         │   └─ 每个文档被分割成多个 Node 对象
│         └─ 批处理模式特殊处理：
│             ├─ 按目录深度分组（GROUP_DEPTH）
│             ├─ 控制每批文档数量（DOCS_PER_BATCH）
│             └─ 支持 checkpoint，可以中断后继续
│
├─→ [2.2] 向量化（Embedding）
│     └─ Embedding 工厂 [backend/infrastructure/embeddings/factory.py]
│         ├─ 获取 Embedding 模型：
│         │   ├─ 本地模型：LocalEmbedding（HuggingFace模型）
│         │   ├─ API 模型：APIEmbedding（远程API调用）
│         │   └─ 通过 config.EMBEDDING_TYPE 选择（local 或 api）
│         ├─ 向量化节点：
│         │   ├─ 对每个 Node 的文本调用 Embedding 模型
│         │   ├─ 生成固定维度的向量（如768维、1024维）
│         │   └─ 批处理优化：EMBED_BATCH_SIZE 控制批量大小
│         └─ 向量维度检查：
│             ├─ 检查新向量维度是否与现有索引匹配
│             └─ 维度不匹配时给出警告或错误提示
│
└─→ [2.3] 存储到向量数据库
      └─ IndexManager [backend/infrastructure/indexer/index_manager.py]
          ├─ 初始化向量存储：
          │   ├─ 使用 Chroma Cloud 作为向量存储后端
          │   ├─ Collection 名称：可自定义（默认 default）
          │   └─ 连接到云端数据库
          ├─ 创建或加载索引：
          │   ├─ 新索引：VectorStoreIndex.from_documents()
          │   └─ 增量添加：index.insert_ref_docs() 或 index.insert_nodes()
          ├─ 存储向量：
          │   ├─ 向量数据：每个节点的 embedding 向量
          │   ├─ 元数据：节点元数据（文件路径、来源等）
          │   └─ 文本内容：原始文本（用于展示和引用）
          ├─ 构建向量 ID 映射：
          │   └─ 记录文件路径到向量 ID 的映射（用于增量更新和删除）
          └─ 更新缓存状态（如果启用）：
              ├─ 标记向量化步骤完成
              └─ 记录向量数量、文档 hash 等信息
```

### 6.3 查询阶段

```
[阶段3] 查询阶段（使用索引）
│
├─→ [3.1] 接收用户查询
│     └─ RAGService.query() [backend/business/rag_api/rag_service.py]
│         └─ Web界面：app.py → frontend/main.py → RAGService
│
├─→ [3.2] 查询引擎初始化与策略选择
│     └─ ModularQueryEngine [backend/business/rag_engine/query/engine.py]
│         │
│         ├─ 固定策略模式（默认）：
│         │   ├─ 策略验证：检查策略是否在 SUPPORTED_STRATEGIES 中
│         │   ├─ 创建检索器：通过 create_retriever() 工厂方法创建
│         │   ├─ 创建查询引擎：使用检索器创建 RetrieverQueryEngine
│         │   └─ 记录日志：记录初始化的策略配置
│         │
│         └─ 自动路由模式（可选）：
│             ├─ 延迟创建：不在初始化时创建检索器
│             ├─ 创建路由器：初始化 QueryRouter 实例
│             └─ 准备策略：准备多种检索策略的创建逻辑（延迟加载）
│
├─→ [3.3] 检索策略执行
│     │
│     ├─ 固定策略模式：
│     │   └─ 使用预创建的 query_engine 直接执行检索
│     │
│     ├─ 自动路由模式：
│     │   ├─ QueryRouter.route() [backend/business/rag_engine/routers/query_router.py]
│     │   │   ├─ 查询分析：_analyze_query() 分析查询文本
│     │   │   ├─ 规则匹配：
│     │   │   │   ├─ 文件名关键词 → files_via_metadata 模式
│     │   │   │   ├─ 宽泛主题词 → files_via_content 模式
│     │   │   │   └─ 默认 → chunk 模式
│     │   │   ├─ 动态创建检索器：根据决策创建对应检索器
│     │   │   └─ 记录路由决策日志
│     │   └─ 执行查询：使用选定的检索器执行查询
│     │
│     └─ 多策略检索（retrieval_strategy="multi"）：
│         └─ MultiStrategyRetriever [backend/business/rag_engine/retrievers/multi_strategy_retriever.py]
│             ├─ 并行执行多个检索器：
│             │   ├─ VectorRetriever（语义相似度）
│             │   ├─ BM25Retriever（关键词匹配）
│             │   └─ GrepRetriever（正则表达式）
│             ├─ ResultMerger.merge() [backend/business/rag_engine/retrievers/result_merger.py]
│             │   ├─ RRF 融合：倒数排名融合（Reciprocal Rank Fusion）
│             │   ├─ 加权融合：支持自定义权重
│             │   ├─ 去重：基于内容哈希去重
│             │   └─ 记录合并结果数量
│             └─ 返回合并后的结果
│
├─→ [3.4] 后处理（Post-processing）
│     └─ PostprocessorFactory [backend/business/rag_engine/query/postprocessor_factory.py]
│         ├─ 相似度阈值过滤：
│         │   ├─ 过滤低相似度结果
│         │   └─ 可配置阈值（similarity_cutoff）
│         └─ 重排序（Reranker，可选）：
│             ├─ SentenceTransformer 重排序
│             ├─ BGE 重排序（BAAI/bge-reranker-base）
│             ├─ Top-N 重排序：可配置重排序后保留的结果数量
│             └─ 批量重排序优化
│
├─→ [3.5] 生成（Generation）
│     └─ QueryExecutor [backend/business/rag_engine/query/query_executor.py]
│         ├─ 构建 Prompt：
│         │   ├─ 包含检索到的上下文
│         │   ├─ 包含用户查询
│         │   └─ 包含对话历史（多轮对话）
│         ├─ 调用 DeepSeek LLM（deepseek-reasoner）：
│         │   ├─ 使用 LLM 工厂创建实例
│         │   └─ 支持推理链输出
│         ├─ 获取响应：
│         │   ├─ 推理链（reasoning_content）
│         │   └─ 答案内容（content）
│         └─ 多轮对话优化：
│             └─ 自动过滤推理链，确保不传入下一轮对话
│
└─→ [3.6] 响应格式化
      └─ ResponseFormatter [backend/business/rag_engine/response_formatter/formatter.py]
          ├─ 提取引用来源（source_nodes）：
          │   ├─ 提取文本内容
          │   ├─ 提取相似度分数
          │   └─ 提取元数据（文件路径、来源等）
          ├─ 格式化答案和元数据：
          │   ├─ 格式化答案文本
          │   ├─ 格式化引用来源
          │   └─ 包含推理链（如果启用）
          └─ 返回 RAGResponse：
              ├─ 答案文本
              ├─ 引用来源列表
              └─ 元数据（推理链、查询信息等）
```

### 6.4 会话管理阶段

```
[阶段4] 会话管理（多轮对话）
└─ ChatManager [backend/business/chat/manager.py]
      ├─ 维护当前会话上下文
      └─ 支持多轮对话（仅内存）
```

### 6.5 数据流向总结

**查询流程数据流**：
```
用户输入
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
      create_retriever() [工厂模式]
      ↓
      Retriever.retrieve() [检索相关文档]
      ↓
      [后处理] SimilarityCutoff + Reranker
      ↓
      LLM.generate() [生成答案]
      ↓
      ResponseFormatter.format() [格式化响应]
      ↓
      RAGResponse {answer, sources, metadata}
```

**索引构建流程数据流**：
```
数据源（GitHub/本地）
  ↓
DataImportService.import_from_github() / import_from_directory()
  ↓
GitRepositoryManager.clone() / pull() [如果是 GitHub]
  ↓
GitHubSource / LocalFileSource.load() [获取文件列表]
  ↓
DocumentParser.parse_files() [解析为 LlamaDocument]
  ↓
IndexManager.build_index(documents)
  ↓
SentenceSplitter [分块为 Node]
  ↓
Embedding.embed_nodes() [生成向量]
  ↓
ChromaVectorStore [存储到 Chroma Cloud]
  ↓
VectorStoreIndex [索引构建完成]
```

---

## 7. 目录结构

```
Creating-Systematology-RAG/
│
├── app.py                          # 🖥️ Streamlit Web应用入口（单页应用）
│
├── .streamlit/                     # ⚙️ Streamlit 配置文件
│   └── config.toml                # 主题配置（Light/Dark 模式）
│
├── frontend/                       # 🎨 前端层（Presentation Layer）
│   ├── main.py                    # 主入口（单页应用）
│   ├── components/               # UI组件（优先使用 Streamlit 原生组件）
│   │   ├── chat_display.py       # 聊天显示（含可观测性信息）
│   │   ├── chat_input_with_mode.py # 聊天输入（支持 Agentic 模式切换）
│   │   ├── config_panel/         # 配置面板模块（统一配置管理）
│   │   │   ├── models.py         # AppConfig 数据模型 + LLM 预设
│   │   │   ├── panel.py          # 主配置面板
│   │   │   ├── llm_presets.py    # LLM 预设面板（精确/平衡/创意）
│   │   │   └── rag_params.py     # RAG 参数面板（Top-K、相似度阈值等）
│   │   ├── file_viewer.py        # 文件查看（弹窗）
│   │   ├── observability_summary.py # 可观测性摘要展示
│   │   ├── sidebar.py             # 侧边栏
│   │   ├── sources_panel.py      # 引用来源面板
│   │   └── settings_dialog.py   # 设置弹窗（使用 st.dialog()）
│   ├── settings/                  # 设置模块
│   │   └── data_source.py        # 数据源管理
│   ├── utils/                     # 工具函数
│   │   ├── services.py           # 服务封装
│   │   ├── state.py              # 状态管理
│   │   └── sources.py            # 来源处理
│   └── tests/                     # 前端测试
│
├── backend/                        # 💻 后端代码（核心业务逻辑）
│   │
│   ├── business/                   # 业务层（Business Layer）
│   │   ├── rag_engine/            # RAG引擎
│   │   │   ├── agentic/          # Agentic RAG 模块
│   │   │   │   ├── agent/        # Agent 实现（规划 Agent、工具）
│   │   │   │   └── prompts/      # Agent Prompt 模板
│   │   │   └── ...                # 传统 RAG 模块
│   │   ├── rag_api/               # RAG Service
│   │   │   ├── models.py         # 数据模型（Pydantic）
│   │   │   └── ...                 # API模块
│   │   └── chat/                  # 对话管理
│   │       └── manager.py         # ChatManager
│   │
│   └── infrastructure/             # 基础设施层（Infrastructure Layer）
│       ├── data_loader/            # 数据加载
│       │   ├── source_loader.py   # 统一数据加载入口
│       │   └── ...                 # 数据加载模块
│       ├── indexer/                # 索引构建
│       │   ├── index_manager.py   # 索引管理器
│       │   └── ...                 # 索引构建模块
│       ├── embeddings/            # 向量化（可插拔）
│       │   ├── factory.py         # Embedding 工厂
│       │   └── ...                 # Embedding 实现
│       ├── llms/                  # 大语言模型
│       │   └── factory.py         # LLM 工厂
│       ├── observers/             # 可观测性（可插拔）
│       │   ├── factory.py         # Observer 工厂
│       │   └── ...                 # Observer 实现
│       ├── config/                # 配置管理
│       │   └── settings.py        # 配置设置
│       ├── git/                   # Git 操作
│       │   └── manager.py         # Git 仓库管理器
│       └── logger_structlog.py    # 结构化日志系统
│
├── docs/                           # 📚 文档中心
│   ├── architecture.md            # 架构设计文档（本文档）
│   └── quick-start-advanced.md    # 高级配置指南
│
├── data/                           # 📁 数据目录
│   └── github_repos/               # GitHub仓库（本地克隆）
│
├── logs/                           # 📋 日志目录
│
├── aha-moments/                    # 💡 知识沉淀（技术决策、设计洞察）
│   ├── README.md                  # 索引文档
│   └── YYYY-MM-DD_标题.md         # 各个 aha moment 文档
│
├── agent-task-log/                 # 📝 AI Agent 任务记录
│   ├── README.md                  # 任务日志说明
│   ├── ongoing/                   # 进行中的任务
│   └── archive/YYYY-MM/           # 按月归档（已完成任务）
│
└── Makefile                        # 🛠️ 构建脚本
```

**模块依赖关系**：
```
frontend → business → infrastructure
   ↓          ↓            ↓
app.py   RAGService   Config/Logger/Embedding/LLM
```

**核心函数**：
- `DataImportService.import_from_github()`: GitHub 数据导入
- `DataImportService.import_from_directory()`: 本地目录导入
- `IndexManager.build_index()`: 索引构建，分块→向量化→存储
- `ModularQueryEngine.query()`: 模块化查询，支持多种检索策略
- `RAGService.query()`: 统一服务接口，协调各模块执行
- `ChatManager.chat()/stream_chat()`: 对话管理，维护当前会话上下文

---

## 8. 已实现模块统计

### 8.1 总体规模

- 后端代码：143 个 Python 文件
- 前端代码：26 个 Python 文件（新增配置面板模块）
- 测试代码：99 个 Python 文件
- **总计：268 个文件**

### 8.2 按层级统计

| 层级 | 模块数 | 主要职责 |
|------|--------|----------|
| **前端层** | 26 | 用户交互与展示（UI 组件、统一配置面板、状态管理） |
| **业务层** | 43 | 核心业务逻辑（RAG 引擎、API、对话管理） |
| **基础设施层** | 78 | 技术基础设施（配置、数据加载、索引、向量化、LLM、可观测性） |
| **测试层** | 99 | 测试覆盖（单元、集成、性能、E2E） |

### 8.3 核心功能模块

| 功能领域 | 模块数 | 说明 |
|----------|--------|------|
| **RAG 引擎** | 35 | 传统 RAG + Agentic RAG（核心引擎、检索、重排序、路由、处理、格式化） |
| **数据加载** | 18 | GitHub + 本地文件导入（数据源、解析、同步） |
| **索引构建** | 20 | 向量索引管理（构建、增量更新、工具） |
| **向量化** | 9 | Embedding 模型管理（本地模型、API 模型、缓存） |
| **检索策略** | 6 | 多种检索策略（vector/bm25/hybrid/grep/multi/file-level） |
| **重排序** | 4 | 结果重排序（SentenceTransformer、BGE） |
| **可观测性** | 5 | 日志、调试、评估（LlamaDebugHandler、RAGAS） |
| **前端 UI** | 26 | Streamlit 界面组件（单页应用、统一配置面板、主题切换） |
| **配置管理** | 5 | 统一配置系统（LLM 预设、RAG 参数、应用配置） |
| **测试** | 99 | 单元、集成、性能、E2E 测试 |

### 8.4 核心特性实现状态

- ✅ **传统 RAG**：ModularQueryEngine（固定策略模式）
- ✅ **Agentic RAG**：AgenticQueryEngine（ReActAgent 模式）
- ✅ **自动路由**：QueryRouter（智能策略选择）
- ✅ **多策略检索**：MultiStrategyRetriever（向量+BM25+Grep+RRF融合）
- ✅ **查询处理**：QueryProcessor（意图理解 + 改写）
- ✅ **响应格式化**：ResponseFormatter（带引用来源）
- ✅ **数据源**：GitHub + 本地文件（支持增量同步）
- ✅ **向量化**：本地模型 + API 模型
- ✅ **可观测性**：LlamaDebugHandler + RAGAS

### 8.5 测试覆盖情况

- ✅ **单元测试**：46 个文件（核心功能全覆盖）
- ✅ **集成测试**：15 个文件（主要流程覆盖）
- ✅ **性能测试**：6 个文件（关键性能指标）
- ✅ **E2E 测试**：1 个文件（核心工作流）
- ✅ **测试工具**：12 个文件（测试辅助工具）

---

## 9. 架构决策记录

### 9.1 关键架构决策

#### 决策1：三层架构设计

- **问题**：如何组织代码，确保职责清晰、低耦合高内聚？
- **决策**：采用三层架构（前端层、业务层、基础设施层）
- **理由**：
  - 职责清晰：每层有明确的职责边界
  - 低耦合：单向依赖，禁止反向依赖和跨层访问
  - 易于测试：可以独立测试每一层
  - 易于维护：修改某一层不影响其他层

#### 决策2：可插拔设计

- **问题**：如何支持不同实现之间的切换（如不同的 Embedding 模型、检索策略）？
- **决策**：所有核心组件支持可插拔替换，通过工厂模式和抽象基类实现
- **理由**：
  - 灵活性：可以轻松切换不同的实现
  - 可测试性：可以使用 Mock 实现进行测试
  - 可扩展性：新增实现只需实现接口，无需修改现有代码

#### 决策3：延迟加载

- **问题**：如何优化启动速度，避免启动时加载所有组件？
- **决策**：RAGService 中的引擎使用延迟加载（`@property` 装饰器）
- **理由**：
  - 启动速度：避免启动时加载所有组件，提升用户体验
  - 资源优化：按需加载，避免不必要的资源消耗
  - 灵活性：可以根据实际使用情况动态加载组件

#### 决策4：配置管理分离

- **问题**：如何管理配置，确保敏感信息安全？
- **决策**：分离环境变量（`.env`）和 YAML 配置（`application.yml`）
- **理由**：
  - 安全性：敏感信息（API keys）存储在环境变量中，不提交到代码库
  - 灵活性：非敏感配置存储在 YAML 中，便于修改
  - 可维护性：配置集中管理，便于查找和修改

### 9.2 技术选型理由

**LlamaIndex**：
- **理由**：成熟的 RAG 框架，提供完整的 Document、Node、Index、QueryEngine 抽象
- **优势**：支持多种检索策略、可插拔设计、丰富的生态系统

**Chroma Cloud**：
- **理由**：云端托管，无需本地部署，支持大规模数据
- **优势**：易于使用、自动扩展、无需维护

**DeepSeek API**：
- **理由**：支持推理链输出，适合复杂查询场景
- **优势**：推理能力强、API 稳定、成本合理

**Streamlit**：
- **理由**：快速构建 Web 界面，原生组件丰富
- **优势**：开发效率高、原生组件支持好、主题适配完善

### 9.3 AI 辅助开发工具

本项目使用以下 AI 辅助开发工具提升开发效率：

**[Cursor IDE](https://cursor.com)**：
- AI 驱动的代码编辑器
- 支持多模态交互（代码、文档、对话）

**[Cursor Browser](https://cursor.com/cn/docs/agent/browser)**：
- 浏览器自动化，支持可视化编辑 UI
- 自动化测试（功能测试、视觉回归）
- 无障碍审计（WCAG 标准检查）

**[Agent Skills](https://agentskills.io)** 开放标准：
- AI 能力扩展体系，位于 `.cursor/skills/`
- 按功能领域组织（代码质量、文档规范、架构设计、任务管理等）
- 支持知识（SKILL.md）+ 脚本（scripts/）的统一管理

---

## 10. 编码规范与设计模式

### 10.1 编码规范

- **类型提示**：所有函数、方法、类声明必须补全类型提示
- **日志规范**：统一通过 `backend.infrastructure.logger.get_logger()` 获取 logger，禁止使用 `print`
- **异常处理**：捕获具体异常类型，记录日志后合理抛出，严禁裸 `except`
- **文件行数**：单个代码文件必须 ≤ 300 行（硬性限制）

### 10.2 设计模式使用

- **工厂模式**：`create_retriever()`, `create_reranker()`, `create_embedding()`, `create_llm()`
- **依赖注入**：所有组件通过构造函数注入依赖，禁止静态单例
- **可插拔设计**：所有核心组件（Embedding、DataSource、Observer、Reranker、Retriever）支持可插拔替换
- **延迟加载**：RAGService 中的引擎按需初始化，避免启动时加载所有组件

---

**最后更新**: 2026-01-24
