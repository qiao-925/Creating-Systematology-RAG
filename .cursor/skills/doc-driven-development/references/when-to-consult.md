# 何时查阅文档详细说明

## 1. 应该查阅文档的情况

### 1.1 使用第三方库/框架的新 API

```python
# 不熟悉的 API 调用
from llama_index import VectorStoreIndex

# 应该先查阅：
# - VectorStoreIndex 的构造参数
# - 支持的方法和属性
# - 使用示例
```

### 1.2 遇到 API 调用错误

| 错误类型 | 原因 | 应查阅 |
|----------|------|--------|
| `AttributeError` | 方法/属性不存在 | API 参考文档 |
| `TypeError` | 参数类型错误 | 方法签名文档 |
| `ValueError` | 参数值无效 | 参数说明文档 |

### 1.3 不确定正确的调用方式

```python
# 不确定如何正确使用
index.query(...)  # 参数是什么？返回什么？

# 应该先查阅：
# - 方法签名
# - 参数说明
# - 返回值类型
```

### 1.4 版本差异和兼容性

- 升级库版本后出现问题
- 需要支持多个版本
- API 标记为 deprecated

### 1.5 实现复杂功能

- 需要组合多个 API
- 需要参考官方示例
- 涉及高级用法

## 2. 可以跳过文档的情况

### 2.1 使用项目内部已封装的 API

```python
# 项目内部 API，查阅项目代码即可
from backend.business.rag_api import RAGService
rag_service = RAGService()
```

### 2.2 简单的语法错误或拼写错误

```python
# 明显的拼写错误
pritn("hello")  # 应该是 print
```

### 2.3 明确的逻辑错误

```python
# 逻辑错误，不涉及外部 API
if x > 10:
    return "small"  # 逻辑错误，应该是 "large"
```

## 3. 决策流程图

```
遇到问题
    │
    ▼
是否涉及第三方 API？
    │
    ├─ 是 ──▶ 查阅官方文档
    │
    └─ 否 ──▶ 是否为语法/拼写错误？
                  │
                  ├─ 是 ──▶ 直接修复
                  │
                  └─ 否 ──▶ 检查业务逻辑
```
