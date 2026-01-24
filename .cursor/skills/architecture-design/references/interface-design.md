# 接口设计详细说明

## 1. 抽象基类规范

### 1.1 定义契约

```python
from abc import ABC, abstractmethod
from typing import List

class BaseRetriever(ABC):
    """检索器抽象基类。"""
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        """检索相关文档。
        
        Args:
            query: 查询字符串
            top_k: 返回的最大文档数
            
        Returns:
            相关文档列表
        """
        pass
```

### 1.2 常用抽象基类

| 基类 | 职责 | 核心方法 |
|------|------|----------|
| `BaseEmbedding` | 向量化 | `embed_query`, `embed_documents` |
| `BaseRetriever` | 检索 | `retrieve` |
| `BaseDataSource` | 数据加载 | `load` |
| `BaseReranker` | 重排序 | `rerank` |

## 2. Protocol 定义

### 2.1 使用 Protocol

```python
from typing import Protocol, List

class Retriever(Protocol):
    """检索器协议。"""
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        """检索相关文档。"""
        ...
```

### 2.2 Protocol vs ABC

| 特性 | ABC | Protocol |
|------|-----|----------|
| 继承 | 需要显式继承 | 结构性子类型 |
| 运行时检查 | 支持 | 不支持 |
| 适用场景 | 框架内部 | 跨模块接口 |

## 3. 向后兼容

### 3.1 兼容性原则

- 新增参数使用默认值
- 不删除现有参数
- 不改变参数顺序

### 3.2 示例

```python
# v1.0
def retrieve(self, query: str) -> List[Document]:
    pass

# v1.1 - 向后兼容
def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
    pass  # 新增参数有默认值

# ❌ 破坏性变更
def retrieve(self, query: str, top_k: int) -> List[Document]:
    pass  # 新参数无默认值，破坏现有调用
```

### 3.3 破坏性变更处理

如果必须进行破坏性变更：

1. 提供版本策略（如 `retrieve_v2`）
2. 或提供适配层
3. 记录迁移指南

## 4. 依赖注入

### 4.1 构造函数注入

```python
class QueryEngine:
    def __init__(
        self,
        retriever: BaseRetriever,
        llm: BaseLLM,
        formatter: ResponseFormatter
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._formatter = formatter
```

### 4.2 禁止的模式

```python
# ❌ 静态单例
class QueryEngine:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# ❌ 隐式全局变量
retriever = VectorRetriever()  # 模块级别

class QueryEngine:
    def query(self, q: str):
        return retriever.retrieve(q)  # 使用全局变量
```

## 5. LlamaIndex 集成

### 5.1 核心流程

```
Document → Node → Index → QueryEngine
    │         │       │         │
    │         │       │         └─ 执行查询
    │         │       └─ 构建/加载索引
    │         └─ 分块处理
    └─ 原始文档
```

### 5.2 VectorStoreIndex 配置

```python
from llama_index import VectorStoreIndex, StorageContext

# 明确声明各组件来源
index = VectorStoreIndex(
    nodes=nodes,
    storage_context=StorageContext.from_defaults(
        vector_store=chroma_vector_store
    ),
    embed_model=embedding_model
)
```
