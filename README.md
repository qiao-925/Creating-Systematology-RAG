# 创建系统学知识库RAG应用 (Creating Systematology RAG Application)

> 基于多策略检索增强生成的智能问答系统，通过并行融合向量、BM25、Grep 检索策略和智能路由，从知识库精准检索并生成带引用来源的答案。

## 1. 🚀 快速开始 (Quick Start)

### 环境准备 (Environment Setup)

**1. 克隆项目**
```bash
git clone <repository-url>
cd Creating-Systematology-RAG
```

**2. 配置 API 密钥**

```bash
cp env.template .env
# 编辑 .env 文件，添加以下配置：
# - DEEPSEEK_API_KEY=your_api_key（必须）
# - CHROMA_CLOUD_API_KEY=your_chroma_api_key（必须）
# - CHROMA_CLOUD_TENANT=your_chroma_tenant（必须）
# - CHROMA_CLOUD_DATABASE=your_chroma_database（必须）
```

**3. 安装并启动**
```bash
make              # 安装依赖 + 运行测试（推荐首次运行）
make run          # 启动 Web 应用

# Windows PowerShell用户如果遇到乱码：
.\Makefile.ps1 run   # 使用PowerShell包装脚本（已修复UTF-8编码）

# 其他常用命令
make start        # = make + make run（一键启动）
make help         # 查看所有命令
make test         # 运行所有测试
make clean        # 清理生成文件
```

**4. 主题切换**

应用支持 **Light/Dark 模式**切换：
- 点击右上角 "⋮" → "Settings" → 选择主题
- 或使用系统主题偏好自动切换
- 所有组件（包括自定义组件）都会自动适配主题

### Chroma Cloud 配置说明

本项目使用 **Chroma Cloud** 作为向量数据库，需要配置以下环境变量：

1. **CHROMA_CLOUD_API_KEY**: Chroma Cloud API 密钥
2. **CHROMA_CLOUD_TENANT**: Chroma Cloud 租户 ID
3. **CHROMA_CLOUD_DATABASE**: Chroma Cloud 数据库名称

**配置步骤**：
1. 在 Chroma Cloud 平台创建账户并获取连接信息
2. 在 `.env` 文件中设置上述三个环境变量
3. 启动应用后会自动连接到 Chroma Cloud

**注意事项**：
- Chroma Cloud 需要网络连接，确保网络畅通
- 配置错误时会直接抛出错误，不会回退到本地模式
- 向量数据存储在云端，无需本地存储目录

---

项目支持**GPU优先、CPU兜底**模式。由于 `uv` 在 Windows 平台上默认锁定 CPU 版本的 PyTorch，**需要手动安装 CUDA 版本**以获得 GPU 加速：

```bash
# 1. 安装基础依赖（首次运行会自动执行）
make install

# 2. 手动安装 CUDA 版本的 PyTorch（覆盖 CPU 版本）
uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# 3. 验证安装
uv run --no-sync python -c "import torch; print(f'版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

**性能对比**：
- 🚀 **GPU模式**：索引构建约5分钟
- 🐌 **CPU模式**：索引构建约30分钟+

> 💡 **注意**：
> - 项目可以在纯CPU环境运行，但性能较慢
> - 在 Windows 平台上需要手动安装 GPU 版本以获得最佳性能
> - **安装 CUDA 版本后，避免再次运行 `make install`、`make ready`、`make start` 等会触发 `uv sync` 的命令**（会覆盖 CUDA 版本）
> - 日常使用只需 `make run` 启动应用，已自动配置 `--no-sync` 选项

> 💡 **Windows 用户**：需先安装 Make 工具 → `choco install make -y`  
> 详细安装过程 → [Windows Make 工具安装指南](agent-task-log/2025-10-09-3_Windows-Make工具安装与Makefile配置_快速摘要.md)

---

## 2. 技术栈 (Tech Stack)

- **Python 3.12+** - 编程语言
- **uv** - 依赖管理和包管理
- **LlamaIndex** - RAG 核心框架（含 ReActAgent）
- **Git** - GitHub仓库本地克隆（自研实现）
- **DeepSeek API** - 大语言模型（支持推理链和JSON输出）
- **Chroma Cloud** - 向量数据库（云端托管）
- **Streamlit** - Web 界面（单页应用，支持 Dark 模式，优先使用原生组件）
- **HuggingFace Embeddings** - 本地向量模型（支持镜像和离线）
- **pytest** - 测试框架
- **LlamaDebugHandler** - 内置可观测性
- **RAGAS** - RAG评估框架
- **structlog** - 结构化日志系统
- **Pydantic** - 数据验证和类型安全

---

## 3. 🤖 Agentic RAG 特性

### 核心能力

项目支持两种 RAG 模式（可通过 UI 切换）：

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **传统 RAG** | 固定检索策略，规则驱动 | 简单查询、低延迟需求 |
| **Agentic RAG** | Agent 自主决策，动态组合工具 | 复杂查询、多意图查询 |

### 规划 Agent 工具集

规划 Agent（ReActAgent）支持 6 个工具：

**查询处理工具**：
- `analyze_intent` - 意图理解（分析查询复杂度、主题、是否需要改写）
- `rewrite_query` - 查询改写（保留实体、扩展语义）
- `decompose_multi_intent` - 多意图分解（将复杂查询拆分为子查询）

**检索工具**：
- `vector_search` - 向量语义检索
- `hybrid_search` - 混合检索（向量+BM25）
- `multi_search` - 多策略融合检索（向量+BM25+Grep+RRF融合）

### 降级机制

AgenticQueryEngine 支持三级降级：
1. Agent 执行失败 → 降级到 ModularQueryEngine
2. ModularQueryEngine 失败 → 降级到纯 LLM 回答
3. LLM 失败 → 返回友好错误信息

---

## 4. 📐 架构设计

### 核心设计原则

1. **模块化优先**：三层架构（前端层、业务层、基础设施层），职责清晰，低耦合高内聚
2. **可插拔设计**：所有核心组件（Embedding、DataSource、Observer、Reranker、Retriever）支持可插拔替换
3. **配置驱动**：集中管理配置，支持运行时切换，无需修改代码
4. **架构统一**：前端代码独立组织（frontend/），单页应用架构，功能通过弹窗实现
5. **原生组件优先**：优先使用 Streamlit 原生组件（`st.chat_input()`、`st.dialog()` 等），减少自定义代码
6. **主题适配**：完整支持 Light/Dark 模式切换，使用 CSS 变量实现主题适配
7. **可观测性优先**：集成 LlamaDebugHandler、RAGAS，行为透明可追踪
8. **工程实践**：结构化日志（structlog）、类型安全（Pydantic），提升代码质量

### RAG 链路整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Streamlit)                  │
├─────────────────────────────────────────────────────────────┤
│                        RAG API Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  RAGService  │  │  FastAPI App │  │ Chat Router  │       │
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

**查询处理流程**：
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

**核心组件**：

| 组件 | 位置 | 功能 |
|------|------|------|
| `RAGService` | `rag_api/rag_service.py` | 统一服务入口，延迟加载引擎 |
| `ModularQueryEngine` | `rag_engine/core/engine.py` | 传统 RAG 引擎 |
| `AgenticQueryEngine` | `rag_engine/agentic/engine.py` | Agentic 引擎（ReActAgent） |
| `QueryProcessor` | `rag_engine/processing/query_processor.py` | 查询意图理解+改写 |
| `create_retriever` | `rag_engine/retrieval/factory.py` | 检索器工厂 |
| `create_reranker` | `rag_engine/reranking/factory.py` | 重排序器工厂 |
| `IndexManager` | `infrastructure/indexer/` | 向量索引管理 |

**检索策略**：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `vector` | 向量语义检索 | 通用语义查询 |
| `bm25` | 关键词检索 | 精确术语匹配 |
| `hybrid` | 向量+BM25+RRF融合 | 兼顾语义和关键词 |
| `grep` | 正则/文本检索 | 代码、文件名查询 |
| `multi` | 多策略组合 | 复杂查询 |

**关键配置**：
- `RETRIEVAL_STRATEGY`：检索策略（vector/bm25/hybrid/grep/multi）
- `SIMILARITY_TOP_K`：检索数量
- `ENABLE_RERANK` / `RERANKER_TYPE`：重排序配置
- `ENABLE_AUTO_ROUTING`：自动路由模式
- `use_agentic_rag`：Agentic RAG 模式

### 模块化三层架构

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

**三层职责**：

| 层次 | 职责 | 特点 |
|------|------|------|
| **前端层** | 用户交互与展示 | 只调用RAGService，不持有业务模块 |
| **业务层** | 核心业务逻辑与编排 | 能力模块通过协议协作，流水线编排 |
| **基础设施层** | 技术基础设施 | 无业务逻辑，提供资源和框架能力 |

### 主要工作流程

```
开始（用户操作：Web界面）

  │
  ├─→ [阶段1] 数据加载阶段
  │     │
  │     ├─→ [1.1] 数据源识别与Git仓库处理
  │     │     │
│     │     ├─ DataImportService [backend/infrastructure/data_loader/service.py]
│     │     │   ├─ 识别数据源类型（GitHub/本地）
│     │     │   └─ 调用对应的 DataSource.load()
│     │     │
│     │     └─ GitRepositoryManager [backend/infrastructure/git/manager.py]（如果是 GitHub 源）
  │     │         ├─ 初始化：创建本地存储目录（data/github_repos/）
  │     │         ├─ 检查仓库是否存在，判断首次克隆或增量更新
  │     │         ├─ 首次克隆：
  │     │         │   ├─ 执行 git clone --branch {branch} --single-branch --depth 1
  │     │         │   ├─ 浅克隆优化（只获取最新提交）
  │     │         │   ├─ 重试机制（最多3次）
  │     │         │   └─ 网络错误时使用指数退避
  │     │         ├─ 增量更新：
  │     │         │   ├─ 执行 git pull origin {branch}
  │     │         │   └─ 检查分支是否匹配
  │     │         ├─ 获取 Commit SHA（git rev-parse HEAD）
  │     │         └─ 缓存管理：检查缓存有效性，记录仓库路径和commit信息
  │     │
│     ├─→ [1.2] 文件路径获取与过滤
│     │     └─ GitHubSource/LocalFileSource [backend/infrastructure/data_loader/source/]
  │     │         ├─ 递归遍历目录结构
  │     │         ├─ 排除特定目录：.git, __pycache__, node_modules, .venv, venv, .pytest_cache
  │     │         ├─ 排除特定文件：.pyc, .pyo, .lock, .log
  │     │         ├─ 只包含真实文件（排除符号链接等）
  │     │         ├─ 应用过滤器：
  │     │         │   ├─ 目录过滤（filter_directories，可选）
  │     │         │   └─ 扩展名过滤（filter_file_extensions，可选）
  │     │         └─ 构建 SourceFile 对象（包含路径、仓库信息、commit SHA、GitHub链接）
  │     │
│     └─→ [1.3] 文档解析
│           └─ DocumentParser.parse_files() [backend/infrastructure/data_loader/parser.py]
  │               ├─ 解析文件为文档对象
  │               │   └─ 缓存有效则直接返回，跳过解析
  │               ├─ 验证文件：检查存在性、可读性，过滤无效文件
  │               ├─ 按目录分组（批量处理优化）：相同目录文件批量解析
  │               ├─ 解析文件：
  │               │   ├─ 单个文件：使用 SimpleDirectoryReader 解析
  │               │   ├─ 目录批量：批量解析同一目录的文件
  │               │   └─ 支持格式：.md, .txt, .py, .js, .json, .yaml, .yml, .html, .pdf 等
  │               ├─ 构建 LlamaDocument 对象：
  │               │   ├─ 文档文本内容
  │               │   ├─ 文件元数据（路径、来源、URL等）
  │               │   └─ 文档唯一标识
  │               ├─ 文本清理（可选）：清理多余空白、规范化换行符
  │               └─ 返回解析后的文档列表
  │
  ├─→ [阶段2] 索引构建阶段
  │     │
│     ├─→ [2.1] 文档分块（Chunking）
│     │     └─ IndexManager.build_index() [backend/infrastructure/indexer/index_manager.py]
  │     │         ├─ 检查断点续传：
  │     │         │   ├─ 检查哪些文档已经向量化
  │     │         │   └─ 跳过已处理文档，只处理新文档或更新的文档
  │     │         ├─ 选择构建模式：
  │     │         │   ├─ 批处理模式（INDEX_BATCH_MODE=True）：按目录分组，分批处理
  │     │         │   └─ 正常模式（默认）：直接处理所有文档
  │     │         ├─ 初始化分块器：SentenceSplitter
  │     │         │   ├─ chunk_size：分块大小（默认512）
  │     │         │   └─ chunk_overlap：块重叠大小（默认20）
  │     │         ├─ 执行分块：
  │     │         │   ├─ 按句子边界分割
  │     │         │   ├─ 使用滑动窗口（overlap）保持上下文连续性
  │     │         │   ├─ 智能处理代码块、列表等特殊结构
  │     │         │   └─ 每个文档被分割成多个 Node 对象
  │     │         └─ 批处理模式特殊处理：
  │     │             ├─ 按目录深度分组（GROUP_DEPTH）
  │     │             ├─ 控制每批文档数量（DOCS_PER_BATCH）
  │     │             └─ 支持 checkpoint，可以中断后继续
  │     │
│     ├─→ [2.2] 向量化（Embedding）
│     │     └─ Embedding 工厂 [backend/infrastructure/embeddings/factory.py]
  │     │         ├─ 获取 Embedding 模型：
  │     │         │   ├─ 本地模型：LocalEmbedding（HuggingFace模型）
  │     │         │   ├─ API 模型：APIEmbedding（远程API调用）
  │     │         │   └─ 通过 config.EMBEDDING_TYPE 选择（local 或 api）
  │     │         ├─ 向量化节点：
  │     │         │   ├─ 对每个 Node 的文本调用 Embedding 模型
  │     │         │   ├─ 生成固定维度的向量（如768维、1024维）
  │     │         │   └─ 批处理优化：EMBED_BATCH_SIZE 控制批量大小
  │     │         └─ 向量维度检查：
  │     │             ├─ 检查新向量维度是否与现有索引匹配
  │     │             └─ 维度不匹配时给出警告或错误提示
  │     │
│     └─→ [2.3] 存储到向量数据库
│           └─ IndexManager [backend/infrastructure/indexer/index_manager.py]
  │               ├─ 初始化向量存储：
  │               │   ├─ 使用 Chroma Cloud 作为向量存储后端
  │               │   ├─ Collection 名称：可自定义（默认 default）
  │               │   └─ 连接到云端数据库
  │               ├─ 创建或加载索引：
  │               │   ├─ 新索引：VectorStoreIndex.from_documents()
  │               │   └─ 增量添加：index.insert_ref_docs() 或 index.insert_nodes()
  │               ├─ 存储向量：
  │               │   ├─ 向量数据：每个节点的 embedding 向量
  │               │   ├─ 元数据：节点元数据（文件路径、来源等）
  │               │   └─ 文本内容：原始文本（用于展示和引用）
  │               ├─ 构建向量 ID 映射：
  │               │   └─ 记录文件路径到向量 ID 的映射（用于增量更新和删除）
  │               └─ 更新缓存状态（如果启用）：
  │                   ├─ 标记向量化步骤完成
  │                   └─ 记录向量数量、文档 hash 等信息
  │
  ├─→ [阶段3] 查询阶段（使用索引）
  │     │
│     ├─→ [3.1] 接收用户查询
│     │     └─ RAGService.query() [backend/business/rag_api/rag_service.py]
│     │         └─ Web界面：app.py → frontend/main.py → RAGService
  │     │
│     ├─→ [3.2] 查询引擎初始化与策略选择
│     │     └─ ModularQueryEngine [backend/business/rag_engine/query/engine.py]
  │     │         │
  │     │         ├─ 固定策略模式（默认）：
  │     │         │   ├─ 策略验证：检查策略是否在 SUPPORTED_STRATEGIES 中
  │     │         │   ├─ 创建检索器：通过 create_retriever() 工厂方法创建
  │     │         │   ├─ 创建查询引擎：使用检索器创建 RetrieverQueryEngine
  │     │         │   └─ 记录日志：记录初始化的策略配置
  │     │         │
  │     │         └─ 自动路由模式（可选）：
  │     │             ├─ 延迟创建：不在初始化时创建检索器
  │     │             ├─ 创建路由器：初始化 QueryRouter 实例
  │     │             └─ 准备策略：准备多种检索策略的创建逻辑（延迟加载）
  │     │
  │     ├─→ [3.3] 检索策略执行
  │     │     │
  │     │     ├─ 固定策略模式：
  │     │     │   └─ 使用预创建的 query_engine 直接执行检索
  │     │     │
  │     │     ├─ 自动路由模式：
  │     │     │   ├─ QueryRouter.route() [backend/business/rag_engine/routers/query_router.py]
  │     │     │   │   ├─ 查询分析：_analyze_query() 分析查询文本
  │     │     │   │   ├─ 规则匹配：
  │     │     │   │   │   ├─ 文件名关键词 → files_via_metadata 模式
  │     │     │   │   │   ├─ 宽泛主题词 → files_via_content 模式
  │     │     │   │   │   └─ 默认 → chunk 模式
  │     │     │   │   ├─ 动态创建检索器：根据决策创建对应检索器
  │     │     │   │   └─ 记录路由决策日志
  │     │     │   └─ 执行查询：使用选定的检索器执行查询
  │     │     │
│     │     └─ 多策略检索（retrieval_strategy="multi"）：
│     │         └─ MultiStrategyRetriever [backend/business/rag_engine/retrievers/multi_strategy_retriever.py]
│     │             ├─ 并行执行多个检索器：
│     │             │   ├─ VectorRetriever（语义相似度）
│     │             │   ├─ BM25Retriever（关键词匹配）
│     │             │   └─ GrepRetriever（正则表达式）
│     │             ├─ ResultMerger.merge() [backend/business/rag_engine/retrievers/result_merger.py]
  │     │             │   ├─ RRF 融合：倒数排名融合（Reciprocal Rank Fusion）
  │     │             │   ├─ 加权融合：支持自定义权重
  │     │             │   ├─ 去重：基于内容哈希去重
  │     │             │   └─ 记录合并结果数量
  │     │             └─ 返回合并后的结果
  │     │
│     ├─→ [3.4] 后处理（Post-processing）
│     │     └─ PostprocessorFactory [backend/business/rag_engine/query/postprocessor_factory.py]
  │     │         ├─ 相似度阈值过滤：
  │     │         │   ├─ 过滤低相似度结果
  │     │         │   └─ 可配置阈值（similarity_cutoff）
  │     │         └─ 重排序（Reranker，可选）：
  │     │             ├─ SentenceTransformer 重排序
  │     │             ├─ BGE 重排序（BAAI/bge-reranker-base）
  │     │             ├─ Top-N 重排序：可配置重排序后保留的结果数量
  │     │             └─ 批量重排序优化
  │     │
│     ├─→ [3.5] 生成（Generation）
│     │     └─ QueryExecutor [backend/business/rag_engine/query/query_executor.py]
  │     │         ├─ 构建 Prompt：
  │     │         │   ├─ 包含检索到的上下文
  │     │         │   ├─ 包含用户查询
  │     │         │   └─ 包含对话历史（多轮对话）
  │     │         ├─ 调用 DeepSeek LLM（deepseek-reasoner）：
  │     │         │   ├─ 使用 LLM 工厂创建实例
  │     │         │   └─ 支持推理链输出
  │     │         ├─ 获取响应：
  │     │         │   ├─ 推理链（reasoning_content）
  │     │         │   └─ 答案内容（content）
  │     │         └─ 多轮对话优化：
  │     │             └─ 自动过滤推理链，确保不传入下一轮对话
  │     │
│     └─→ [3.6] 响应格式化
│           └─ ResponseFormatter [backend/business/rag_engine/response_formatter/formatter.py]
  │               ├─ 提取引用来源（source_nodes）：
  │               │   ├─ 提取文本内容
  │               │   ├─ 提取相似度分数
  │               │   └─ 提取元数据（文件路径、来源等）
  │               ├─ 格式化答案和元数据：
  │               │   ├─ 格式化答案文本
  │               │   ├─ 格式化引用来源
  │               │   └─ 包含推理链（如果启用）
  │               └─ 返回 RAGResponse：
  │                   ├─ 答案文本
  │                   ├─ 引用来源列表
  │                   └─ 元数据（推理链、查询信息等）
  │
└─→ [阶段4] 会话管理（多轮对话）
      └─ ChatManager [backend/business/chat/manager.py]
            ├─ 维护会话历史
            └─ 支持多轮对话（仅内存，不持久化）
```

### 目录结构

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
│   │   ├── rag_api/               # RAG API
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
│   │
│
├── docs/                           # 📚 文档中心
│   ├── ARCHITECTURE.md            # 架构设计文档
│   ├── API.md                     # API参考文档
│   └── RUNNING_FLOW.md            # 运行流程详解
│
├── data/                           # 📁 数据目录
│   └── github_repos/               # GitHub仓库（本地克隆）
│
├── logs/                           # 📋 日志目录
├── agent-task-log/                 # 📝 AI Agent任务记录
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
- `ChatManager.query()`: 对话管理，维护会话历史

> 📖 详细结构 → [架构设计](docs/ARCHITECTURE.md) | [运行流程](docs/RUNNING_FLOW.md)

---

## 5. 💾 缓存机制 (Cache System)

项目实现了多层次的缓存机制，用于提升性能和减少重复计算。了解缓存机制有助于调试和性能优化。

### 5.1 内存缓存（运行时缓存）

**Embedding 实例缓存**
- **位置**: `backend/infrastructure/embeddings/factory.py`, `backend/infrastructure/embeddings/cache.py`
- **机制**: 全局变量 `_global_embedding_instance` 存储 BaseEmbedding 实例，单例模式避免重复加载
- **清理**: `clear_embedding_cache()` 或 `clear_all_cache()`
- **用途**: Embedding 模型加载成本高（数GB大小、GPU内存占用），全局缓存避免重复加载

**Reranker 模型缓存**
- **位置**: `backend/business/rag_engine/reranking/factory.py`
- **机制**: 全局字典 `_reranker_cache` 存储重排序器实例，Key: `"{reranker_type}:{model}:{top_n}"`
- **清理**: `clear_reranker_cache()`
- **用途**: 避免重复加载重排序模型

**Streamlit Session State 缓存**
- **位置**: `app.py`, `frontend/main.py`
- **机制**: Streamlit 的 `st.session_state` 存储会话状态
- **清理**: 程序退出时自动清除，或通过 `st.session_state.clear()` 手动清除
- **主要缓存项**: `embed_model`, `index_manager`, `chat_manager`, `rag_service`, `boot_ready`

### 5.2 文件缓存（持久化缓存）

**GitHub 仓库本地缓存**
- **位置**: `data/github_repos/{owner}/{repo}_{branch}/`
- **机制**: Git 仓库本地克隆，支持增量更新（git pull）
- **配置**: `GITHUB_REPOS_PATH`（默认: `data/github_repos`）
- **清理**: 直接删除对应目录，或通过 `GitRepositoryManager` 管理
- **用途**: 避免重复克隆，支持增量拉取变更

**向量数据库（Chroma Cloud）**
- **位置**: Chroma Cloud（云端托管）
- **机制**: 云端向量数据库，数据存储在云端，无需本地存储目录
- **配置**: `CHROMA_CLOUD_API_KEY`, `CHROMA_CLOUD_TENANT`, `CHROMA_CLOUD_DATABASE`
- **清理**: 通过 Chroma Cloud 控制台或 `IndexManager.clear_index()` 清除集合
- **用途**: 持久化存储向量索引，支持大规模数据


**用户数据缓存**
- **位置**: `data/users.json`
- **机制**: JSON 文件存储用户信息（邮箱、密码哈希等）
- **清理**: 删除文件会清除所有用户数据
- **用途**: 用户认证和隔离

**GitHub 同步状态缓存**
- **位置**: `data/github_sync_state.json`
- **机制**: JSON 文件存储 GitHub 仓库同步状态（最后同步的 commit SHA、文件哈希等）
- **清理**: 删除文件会清除所有同步状态
- **用途**: 追踪仓库变更，支持增量更新

**活动日志缓存**
- **位置**: `logs/activity/{date}.log`
- **机制**: 日志文件记录用户操作，按日期组织
- **配置**: `ACTIVITY_LOG_PATH`（默认: `logs/activity`）
- **清理**: 删除对应日志文件
- **用途**: 行为追踪和数据分析

### 5.3 外部缓存（第三方库自动管理）

**HuggingFace 模型缓存**
- **位置**: `~/.cache/huggingface/`（系统默认）
- **机制**: HuggingFace Transformers 自动管理，下载的模型文件缓存在此目录
- **配置**: `HF_ENDPOINT`（默认: `https://hf-mirror.com`），`HF_OFFLINE_MODE`（默认: `false`）
- **清理**: 删除 `~/.cache/huggingface/` 目录，或通过环境变量 `HF_HOME` 指定其他路径
- **用途**: 模型文件缓存，支持离线模式

**Python 字节码缓存**
- **位置**: `__pycache__/`（各目录下）
- **机制**: Python 自动生成 `.pyc` 文件，加速模块导入
- **清理**: 删除所有 `__pycache__/` 目录
- **用途**: 加速 Python 模块导入

**pytest 测试缓存**
- **位置**: `.pytest_cache/`
- **机制**: pytest 测试框架缓存测试结果
- **清理**: 删除 `.pytest_cache/` 目录
- **用途**: 加速测试执行

**Streamlit 缓存装饰器**
- **位置**: `frontend/main.py`（使用 `@st.cache_resource` 装饰器的函数）
- **机制**: Streamlit 自动管理资源缓存
- **清理**: Streamlit 自动管理，或通过 UI 清除
- **用途**: 缓存昂贵的资源加载操作

### 5.4 缓存重要性分类

**高重要性**（不建议删除）:
- 向量数据库（Chroma Cloud 云端存储）
- 用户数据 (`data/users.json`)

**中等重要性**（可选择性清理）:
- GitHub 仓库本地缓存 (`data/github_repos/`)
- GitHub 仓库缓存 (`data/github_repos/`)
- GitHub 同步状态 (`data/github_sync_state.json`)

**低重要性**（可安全清理）:
- HuggingFace 模型缓存 (`~/.cache/huggingface/`)
- Python 字节码缓存 (`__pycache__/`)
- 测试缓存 (`.pytest_cache/`)
- 活动日志 (`logs/`)

### 5.5 调试注意事项

**缓存可能导致的问题**：
1. **文档更新不生效**：检查 GitHub 同步状态，可能需要重新同步仓库
2. **模型切换不生效**：检查 Embedding 缓存，调用 `clear_embedding_cache()` 清理
3. **索引维度不匹配**：检查 Embedding 缓存，确保使用正确的模型
4. **会话状态异常**：清理 Streamlit Session State 或重启应用
5. **GitHub 仓库未更新**：检查 `data/github_repos/` 目录，手动删除后重新克隆

**推荐清理策略**：
- **日常清理**：Python 字节码缓存、pytest 测试缓存、旧的活动日志
- **定期清理**：GitHub 仓库本地缓存（如需要）
- **谨慎清理**：向量数据库、用户数据、GitHub 仓库缓存（需确认）

---

## 6. 📚 相关文档 (Related Documents)

### Prompt 模板

- [📖 Prompt 模板说明](prompts/README.md) - Prompt 模板集中管理与使用指南

### Cursor 规则编写指引

参考 Cursor 官方建议整理规则体系时需要注意：

- **单一职责**：每条规则聚焦一个主题或流程，避免混合多个场景。
- **结构化元信息**：使用 YAML `description`、适用阶段等字段，方便系统识别加载时机。
- **标题层级规范**：遵循清晰的标题序号，便于快速阅读与检索。
- **触发条件明确**：注明规则类型（Always / Auto Attached / Agent Requested）及执行步骤。
- **Checklist 与示例**：提供核对项和示例，帮助执行时避免遗漏。
- **关联提示**：标注与其他规则的依赖或后续步骤。

> 详情可参阅官方文档：[Cursor 规则上下文指南](https://cursor.com/cn/docs/context/rules)

### AI Agent 任务记录

- [📖 任务归档](agent-task-log/README.md) - AI Agent 执行任务的完整记录

---

## 💡 致谢

本项目的知识库聚焦于钱学森先生的系统学思想和系统科学领域，向这位伟大的科学家致敬！

---

**最后更新**: 2026-01-21（修复文档路径和目录结构描述）  
**License**: MIT