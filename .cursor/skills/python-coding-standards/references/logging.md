# 日志规范详细说明

## 1. 日志获取

统一通过 `src.logger.setup_logger` 获取 logger：

```python
from src.logger import setup_logger

logger = setup_logger(__name__)
```

## 2. 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| `DEBUG` | 调试信息，详细执行过程 | `logger.debug("Query parsed: %s", parsed_query)` |
| `INFO` | 正常运行信息 | `logger.info("Index loaded: %d documents", count)` |
| `WARNING` | 警告，可能的问题 | `logger.warning("Cache miss, rebuilding...")` |
| `ERROR` | 错误，但程序可继续 | `logger.error("Failed to connect: %s", error)` |
| `EXCEPTION` | 错误+堆栈跟踪 | `logger.exception("Unexpected error")` |

## 3. 正确用法

```python
# ✅ 正确：使用 logger
logger.info("Processing query: %s", query)
logger.error("Failed to process: %s", error)
logger.exception("Unexpected error occurred")

# ❌ 错误：使用 print
print(f"Processing query: {query}")  # 禁止
```

## 4. 错误路径日志

```python
try:
    result = process_query(query)
except ValueError as e:
    # 使用 logger.error 记录已知错误
    logger.error("Invalid query format: %s", e)
    raise
except Exception as e:
    # 使用 logger.exception 记录未知错误（包含堆栈）
    logger.exception("Unexpected error processing query")
    raise
```

## 5. 日志格式

- 使用 `%s` 占位符，不要使用 f-string
- 包含足够上下文信息
- 避免敏感信息（密码、token）

```python
# ✅ 正确：使用占位符
logger.info("User %s requested %s", user_id, action)

# ❌ 错误：使用 f-string（性能较差）
logger.info(f"User {user_id} requested {action}")
```

## 6. 测试代码例外

测试代码和示例代码可以使用 `print`，但业务代码必须使用 logger。
