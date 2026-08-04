# 三层架构详细说明

## 1. 架构分层

```
前端层（Presentation Layer）
  - app.py → frontend/main.py
  - 职责：用户交互、UI展示、状态管理
  - 约束：只调用 RAGService，禁止直接访问业务层或基础设施层
    ↓
业务层（Business Layer）
  - RAGService：统一服务入口
  - ModularQueryEngine / AgenticQueryEngine：查询引擎
  - QueryProcessor、ResponseFormatter：查询处理与格式化
  - 职责：核心业务逻辑、流程编排
  - 约束：通过依赖注入获取基础设施能力，不包含技术细节
    ↓
基础设施层（Infrastructure Layer）
  - IndexManager：向量索引管理
  - Embedding：向量化模型（可插拔）
  - LLM：大语言模型（DeepSeek）
  - DataLoader：数据加载（GitHub/本地）
  - Observer：可观测性（LlamaDebugHandler、RAGAS）
  - 职责：技术基础设施，无业务逻辑
```

## 2. 依赖方向

**⚠️ 强制约束**：
- 前端层 → 业务层 → 基础设施层（单向依赖）
- **禁止反向依赖**：基础设施层不能依赖业务层或前端层
- **禁止跨层访问**：前端层不能直接访问基础设施层

## 3. 各层职责详解

### 3.1 前端层

| 组件 | 职责 | 文件位置 |
|------|------|----------|
| main.py | 应用入口、页面路由 | `frontend/main.py` |
| components/* | UI 组件 | `frontend/components/` |
| settings/* | 设置页面 | `frontend/settings/` |

**约束**：
- 只通过 RAGService 访问业务逻辑
- 不直接操作数据库或索引

### 3.2 业务层

| 组件 | 职责 | 文件位置 |
|------|------|----------|
| RAGService | 统一服务入口 | `backend/business/rag_api/rag_service.py` |
| ModularQueryEngine | 传统 RAG 引擎 | `backend/business/rag_engine/core/engine.py` |
| AgenticQueryEngine | Agentic RAG 引擎 | `backend/business/rag_engine/agentic/engine.py` |
| QueryProcessor | 查询处理 | `backend/business/rag_engine/processing/` |
| ResponseFormatter | 响应格式化 | `backend/business/rag_engine/formatting/` |

**约束**：
- 业务逻辑与技术实现分离
- 通过依赖注入获取基础设施能力

### 3.3 基础设施层

| 组件 | 职责 | 文件位置 |
|------|------|----------|
| IndexManager | 索引管理 | `backend/infrastructure/indexer/` |
| Embedding | 向量化 | `backend/infrastructure/embedding/` |
| LLM | 大模型 | `backend/infrastructure/llm/` |
| DataLoader | 数据加载 | `backend/infrastructure/data_loader/` |
| Git | Git 操作 | `backend/infrastructure/git/` |

**约束**：
- 纯技术实现，不包含业务逻辑
- 可独立替换和测试

## 4. 违规示例与修正

### ❌ 违规：前端直接访问基础设施

```python
# 错误：前端直接调用 IndexManager
from backend.infrastructure.indexer import IndexManager
index_manager = IndexManager()
index_manager.build_index(docs)
```

### ✅ 正确：通过业务层访问

```python
# 正确：前端通过 RAGService 访问
from backend.business.rag_api import RAGService
rag_service = RAGService()
rag_service.build_index(docs)
```

### ❌ 违规：基础设施层依赖业务层

```python
# 错误：IndexManager 依赖 RAGService
from backend.business.rag_api import RAGService  # 违反依赖方向
```

### ✅ 正确：保持单向依赖

```python
# 正确：业务层依赖基础设施层
from backend.infrastructure.indexer import IndexManager
```
