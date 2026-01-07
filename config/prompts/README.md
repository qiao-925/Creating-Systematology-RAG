# 查询改写模板配置

## 概述

查询改写模板已独立为文件，方便修改和版本控制。

## 文件位置

- **模板文件**: `query_rewrite_template.txt`
- **默认路径**: 项目根目录下的 `query_rewrite_template.txt`

## 使用方法

### 1. 默认行为

如果模板文件存在，`QueryProcessor` 会自动从文件加载模板。如果文件不存在，会使用代码中的默认模板（向后兼容）。

### 2. 修改模板

直接编辑 `query_rewrite_template.txt` 文件即可。修改后：

- **重启应用**：模板会在应用重启时自动加载
- **运行时重新加载**：调用 `processor.reload_template()` 方法

### 3. 自定义模板路径

```python
from backend.business.rag_engine.processing.query_processor import QueryProcessor

# 使用自定义路径（相对路径，相对于项目根目录）
processor = QueryProcessor(template_path="config/custom_template.txt")

# 使用绝对路径
processor = QueryProcessor(template_path="/path/to/custom_template.txt")
```

### 4. 运行时重新加载模板

```python
from backend.business.rag_engine.processing.query_processor import get_query_processor

processor = get_query_processor()

# 重新加载默认模板文件
processor.reload_template()

# 加载自定义模板文件
processor.reload_template("custom_template.txt")
```

## 模板格式要求

1. **编码**: 必须使用 UTF-8 编码
2. **占位符**: 模板中必须包含 `{query}` 占位符
3. **格式**: 支持多行文本，保持原有格式

## 模板变量

当前支持的变量：
- `{query}`: 原始查询字符串（必需）

## 注意事项

1. 模板文件修改后，缓存会自动清空（如果使用 `reload_template()`）
2. 如果模板文件格式错误或加载失败，会自动回退到默认模板
3. 建议在修改模板前备份原文件

## 示例

### 修改模板强调保留实体

在模板文件中添加或修改以下内容：

```text
**重要约束**：
- 如果原始查询包含多个概念（如"A与B的关系"），改写后的查询必须同时包含A和B
- 如果原始查询包含特定术语（如"马克思主义哲学"），改写后的查询必须保留这些术语
```

保存文件后，重启应用或调用 `reload_template()` 即可生效。

