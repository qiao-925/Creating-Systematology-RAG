# 命名约定详细说明

## 1. 文件命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 模块文件 | `snake_case.py` | `query_processor.py` |
| 测试文件 | `test_*.py` | `test_query_processor.py` |
| 包目录 | `snake_case/` | `data_loader/` |

## 2. 代码命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 类 | `PascalCase` | `QueryProcessor` |
| 函数 | `snake_case` | `process_query` |
| 变量 | `snake_case` | `query_result` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 私有成员 | `_snake_case` | `_internal_cache` |
| 保护成员 | `_snake_case` | `_process_internal` |

## 3. 命名原则

### 3.1 表意清晰

```python
# ✅ 好的命名
def calculate_similarity_score(query: str, document: str) -> float:
    pass

# ❌ 模糊的命名
def calc(q: str, d: str) -> float:
    pass
```

### 3.2 一致性

- 同一概念使用相同术语
- 避免同义词混用（如 fetch/get/retrieve 混用）

```python
# ✅ 一致的命名
def get_user(user_id: str) -> User: ...
def get_document(doc_id: str) -> Document: ...

# ❌ 不一致的命名
def get_user(user_id: str) -> User: ...
def fetch_document(doc_id: str) -> Document: ...  # fetch vs get
```

### 3.3 避免缩写

```python
# ✅ 完整的命名
document_processor = DocumentProcessor()
query_result = process_query(query)

# ❌ 过度缩写
doc_proc = DocProc()  # 不清晰
qres = proc_q(q)  # 不清晰
```

## 4. 枚举命名

```python
from enum import Enum

class QueryType(Enum):
    """查询类型枚举。"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARISON = "comparison"

# ✅ 使用枚举
query_type = QueryType.FACTUAL

# ❌ 使用散落字符串
query_type = "factual"  # 禁止
```

## 5. 布尔变量命名

使用 `is_`、`has_`、`can_`、`should_` 前缀：

```python
# ✅ 清晰的布尔命名
is_valid = validate_query(query)
has_permission = check_permission(user)
can_proceed = is_valid and has_permission

# ❌ 模糊的布尔命名
valid = validate_query(query)  # 不够清晰
```
