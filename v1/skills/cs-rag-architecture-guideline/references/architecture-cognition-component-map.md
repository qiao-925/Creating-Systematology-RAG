# 核心组件地图详细说明

## 1. 查询流程核心组件

| 组件 | 位置 | 职责 | 依赖关系 |
|------|------|------|----------|
| **RAGService** | `backend/business/rag_api/rag_service.py` | 统一服务入口，延迟加载引擎 | 依赖 IndexManager、QueryEngine |
| **ModularQueryEngine** | `backend/business/rag_engine/core/engine.py` | 传统 RAG 引擎 | 依赖 IndexManager、Retriever、LLM |
| **AgenticQueryEngine** | `backend/business/rag_engine/agentic/engine.py` | Agentic RAG 引擎（ReActAgent） | 依赖 IndexManager、Agent、Tools |
| **QueryProcessor** | `backend/business/rag_engine/processing/query_processor.py` | 查询意图理解+改写 | 依赖 LLM |
| **create_retriever** | `backend/business/rag_engine/retrieval/factory.py` | 检索器工厂 | 依赖 IndexManager |
| **ResponseFormatter** | `backend/business/rag_engine/formatting/formatter.py` | 响应格式化 | 无依赖 |
| **IndexManager** | `backend/infrastructure/indexer/core/manager.py` | 向量索引管理 | 依赖 Embedding、Chroma |

## 2. 索引构建核心组件

| 组件 | 位置 | 职责 | 依赖关系 |
|------|------|------|----------|
| **DataImportService** | `backend/infrastructure/data_loader/service.py` | 统一数据导入入口 | 依赖 DataSource |
| **GitRepositoryManager** | `backend/infrastructure/git/manager.py` | Git 仓库管理 | 无依赖 |
| **DocumentParser** | `backend/infrastructure/data_loader/parser.py` | 文档解析 | 依赖 LlamaIndex |
| **IndexManager.build_index()** | `backend/infrastructure/indexer/core/manager.py` | 索引构建 | 依赖 Embedding、Chroma |

## 3. 组件依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                       前端层                                  │
│  ┌─────────────┐                                            │
│  │ main.py     │                                            │
│  └──────┬──────┘                                            │
└─────────┼───────────────────────────────────────────────────┘
          │ 调用
          ▼
┌─────────────────────────────────────────────────────────────┐
│                       业务层                                  │
│  ┌─────────────┐      ┌──────────────────┐                  │
│  │ RAGService  │─────→│ ModularQueryEngine│                 │
│  └──────┬──────┘      │ AgenticQueryEngine│                 │
│         │             └────────┬─────────┘                  │
│         │                      │                            │
│         │             ┌────────▼─────────┐                  │
│         │             │ QueryProcessor   │                  │
│         │             │ ResponseFormatter│                  │
│         │             └──────────────────┘                  │
└─────────┼───────────────────────────────────────────────────┘
          │ 依赖
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    基础设施层                                 │
│  ┌──────────────┐  ┌───────────┐  ┌─────────────┐          │
│  │ IndexManager │  │ Embedding │  │     LLM     │          │
│  └──────────────┘  └───────────┘  └─────────────┘          │
│  ┌──────────────┐  ┌───────────┐  ┌─────────────┐          │
│  │ DataLoader   │  │    Git    │  │  Observer   │          │
│  └──────────────┘  └───────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 4. 组件职责详解

### 4.1 RAGService

**职责**：
- 统一服务入口，隐藏内部复杂性
- 延迟加载引擎，优化启动性能
- 管理会话状态（session_id）

**关键方法**：
- `query(question, session_id)` - 执行查询
- `build_index(documents)` - 构建索引
- `get_engine()` - 获取查询引擎

### 4.2 ModularQueryEngine

**职责**：
- 传统 RAG 查询流程
- 支持多策略检索
- 支持自动路由

**关键方法**：
- `query(question)` - 执行查询
- `_select_retriever()` - 选择检索策略

### 4.3 AgenticQueryEngine

**职责**：
- Agentic RAG 查询流程
- ReActAgent 驱动
- 动态组合工具

**关键方法**：
- `query(question)` - 执行查询
- `_create_agent()` - 创建 Agent
- `_get_tools()` - 获取工具列表

### 4.4 IndexManager

**职责**：
- 向量索引管理
- 索引构建和加载
- 与 Chroma Cloud 交互

**关键方法**：
- `build_index(documents)` - 构建索引
- `load_index()` - 加载索引
- `get_retriever()` - 获取检索器
