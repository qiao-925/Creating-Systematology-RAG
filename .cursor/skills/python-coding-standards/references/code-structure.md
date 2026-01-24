# 代码结构详细说明

## 1. 文件结构顺序

```python
"""模块 docstring：描述模块功能。"""

# 1. 标准库导入
import os
import sys
from typing import Optional, List

# 2. 第三方库导入
import requests
from llama_index import VectorStoreIndex

# 3. 本地导入
from src.logger import setup_logger
from src.config import Settings

# 4. 常量定义
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 5. 类定义
class QueryProcessor:
    """查询处理器。"""
    pass

# 6. 函数定义
def process_query(query: str) -> str:
    """处理查询。"""
    pass

# 7. 主执行块（可选）
if __name__ == "__main__":
    main()
```

## 2. 导入规范

### 2.1 分组规则

按以下顺序分组，组间空一行：

1. 标准库（`os`, `sys`, `typing`）
2. 第三方库（`requests`, `llama_index`）
3. 本地模块（`src.*`）

### 2.2 排序规则

每组内按字母序排列：

```python
# ✅ 正确：按字母序
from typing import Any, Dict, List, Optional

# ❌ 错误：无序
from typing import Optional, List, Any, Dict
```

### 2.3 导入方式

```python
# ✅ 推荐：明确导入
from typing import Optional, List
from llama_index import VectorStoreIndex

# ⚠️ 谨慎：可能命名冲突
import numpy as np

# ❌ 禁止：通配符导入
from module import *
```

### 2.4 跨包引用

使用绝对导入：

```python
# ✅ 绝对导入
from backend.business.rag_api import RAGService

# ❌ 相对导入（跨包时容易出错）
from ...business.rag_api import RAGService
```

## 3. 类结构

```python
class QueryProcessor:
    """查询处理器。
    
    Attributes:
        config: 处理器配置
        logger: 日志记录器
    """
    
    # 1. 类变量
    DEFAULT_TIMEOUT = 30
    
    # 2. 初始化方法
    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config
        self._cache: Optional[dict] = None
    
    # 3. 公共方法
    def process(self, query: str) -> QueryResult:
        """处理查询。"""
        pass
    
    # 4. 私有方法
    def _validate(self, query: str) -> bool:
        """验证查询。"""
        pass
    
    # 5. 特殊方法
    def __repr__(self) -> str:
        return f"QueryProcessor(config={self.config})"
```

## 4. 函数结构

```python
def process_query(
    query: str,
    options: Optional[QueryOptions] = None,
    *,
    timeout: int = 30
) -> QueryResult:
    """处理查询并返回结果。
    
    Args:
        query: 查询字符串
        options: 可选的查询选项
        timeout: 超时时间（秒）
    
    Returns:
        查询结果
    
    Raises:
        ValueError: 当查询为空时
    """
    # 1. 参数验证
    if not query:
        raise ValueError("Query cannot be empty")
    
    # 2. 设置默认值
    options = options or QueryOptions()
    
    # 3. 主逻辑
    result = _execute_query(query, options)
    
    # 4. 返回结果
    return result
```
