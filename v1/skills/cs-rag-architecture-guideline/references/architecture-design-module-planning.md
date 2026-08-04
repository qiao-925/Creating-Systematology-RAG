# 模块规划详细说明

## 1. 模块命名规范

### 1.1 目录结构

```
src/<layer>/<role>/module.py
```

| 元素 | 说明 | 示例 |
|------|------|------|
| `<layer>` | 所属层级 | `business`, `infrastructure` |
| `<role>` | 职责领域 | `rag_engine`, `indexer`, `embedding` |
| `module.py` | 具体模块 | `engine.py`, `manager.py` |

### 1.2 示例

```
backend/
├── business/
│   ├── rag_api/
│   │   └── rag_service.py
│   └── rag_engine/
│       ├── core/
│       │   └── engine.py
│       └── processing/
│           └── query_processor.py
└── infrastructure/
    ├── indexer/
    │   └── manager.py
    └── embedding/
        └── embedder.py
```

## 2. 职责划分原则

### 2.1 单一职责

每个模块/类仅负责单一领域：

```python
# ✅ 单一职责
class QueryProcessor:
    """负责查询处理和意图理解。"""
    pass

class ResponseFormatter:
    """负责响应格式化。"""
    pass

# ❌ God Class
class QueryService:
    """负责查询处理、格式化、缓存、日志...."""
    pass
```

### 2.2 拆分时机

当发现以下情况时，应该拆分：

- 类/模块行数超过 300 行
- 类/模块有多个不相关的职责
- 难以用一句话描述职责

## 3. 可插拔设计

### 3.1 工厂模式

```python
# retriever_factory.py
def create_retriever(retriever_type: str) -> BaseRetriever:
    """根据类型创建检索器。"""
    if retriever_type == "vector":
        return VectorRetriever()
    elif retriever_type == "bm25":
        return BM25Retriever()
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")
```

### 3.2 注册表模式

```python
# module_registry.py
class ModuleRegistry:
    _registry: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, module_class: Type) -> None:
        cls._registry[name] = module_class
    
    @classmethod
    def create(cls, name: str, **kwargs) -> Any:
        if name not in cls._registry:
            raise ValueError(f"Unknown module: {name}")
        return cls._registry[name](**kwargs)
```

## 4. 配置管理

### 4.1 配置位置

- 默认值：`src/config.py`
- 运行时配置：环境变量或配置文件

### 4.2 配置示例

```python
# config.py
class Settings:
    RETRIEVER_TYPE: str = "vector"  # 默认使用向量检索
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    TOP_K: int = 10
```
