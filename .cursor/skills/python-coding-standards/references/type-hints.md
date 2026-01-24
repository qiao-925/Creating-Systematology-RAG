# 类型提示详细规范

## 1. 基础要求

所有函数、方法、类声明必须补全类型提示。

## 2. 函数类型提示

```python
# ✅ 正确：完整类型提示
def process_query(query: str, options: QueryOptions) -> QueryResult:
    """处理查询并返回结果。"""
    pass

# ✅ 正确：无返回值
def log_message(message: str) -> None:
    """记录日志消息。"""
    pass

# ❌ 错误：缺少类型提示
def process_query(query, options):
    pass
```

## 3. 类类型提示

```python
from typing import Optional

class QueryProcessor:
    """查询处理器。"""
    
    def __init__(self, config: ProcessorConfig) -> None:
        self.config: ProcessorConfig = config
        self._cache: Optional[dict] = None
    
    def process(self, query: str) -> QueryResult:
        """处理查询。"""
        pass
```

## 4. 常用类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `Optional[T]` | 可能为 None | `Optional[str]` |
| `List[T]` | 列表 | `List[int]` |
| `Dict[K, V]` | 字典 | `Dict[str, int]` |
| `Tuple[T, ...]` | 元组 | `Tuple[int, str]` |
| `Union[T1, T2]` | 联合类型 | `Union[str, int]` |
| `Callable[[Args], R]` | 可调用对象 | `Callable[[str], int]` |

## 5. 公共 API Docstring

```python
def retrieve_documents(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """检索相关文档。
    
    Args:
        query: 查询字符串
        top_k: 返回的最大文档数
        filters: 可选的过滤条件
    
    Returns:
        相关文档列表，按相关性排序
    
    Raises:
        ValueError: 当 query 为空时
        IndexError: 当索引未就绪时
    """
    pass
```

## 6. 类型检查工具

- **mypy**：静态类型检查
- **pylint**：代码质量检查
- **pyright**：VSCode 类型检查
