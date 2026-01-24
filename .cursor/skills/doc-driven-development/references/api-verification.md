# API 验证流程详细说明

## 1. 问题识别阶段

### 1.1 识别问题类型

| 问题类型 | 特征 | 处理方式 |
|----------|------|----------|
| API 不存在 | `AttributeError: 'X' has no attribute 'Y'` | 查找正确的 API |
| 参数错误 | `TypeError: unexpected keyword argument` | 查找正确的参数 |
| 行为异常 | 结果不符合预期 | 查找正确的用法 |
| 版本问题 | 某版本后 API 变更 | 查找版本差异 |

### 1.2 收集错误信息

必须收集的信息：
- 完整的错误堆栈
- 相关代码片段
- 使用的库/框架版本

```python
# 示例：收集版本信息
import llama_index
print(llama_index.__version__)
```

## 2. 文档查阅阶段

### 2.1 查找官方文档

优先级顺序：
1. 官方文档网站
2. API 参考文档
3. GitHub README
4. 官方示例代码

### 2.2 验证 API 用法

检查项：
- [ ] 方法名是否正确
- [ ] 必需参数是否提供
- [ ] 参数类型是否正确
- [ ] 返回值类型是否符合预期

### 2.3 查找类似问题

搜索资源：
- GitHub Issues
- Stack Overflow
- 官方论坛/Discord

## 3. 实施修复阶段

### 3.1 基于文档实现

```python
# 错误：基于猜测实现
index.query(question, top_k=10)  # 可能参数名不对

# 正确：基于文档实现
# 查阅文档后确认正确的参数名
index.query(question, similarity_top_k=10)
```

### 3.2 添加兼容性处理

```python
# 版本兼容性处理
try:
    # 新版本 API
    result = index.as_query_engine()
except AttributeError:
    # 旧版本 API
    result = index.query_engine()
```

### 3.3 验证修复效果

- [ ] 运行测试确认修复
- [ ] 检查是否引入新问题
- [ ] 验证在不同场景下的表现

## 4. 搜索策略

### 4.1 搜索关键词构造

```
# 基础搜索
{库名} {方法名} example

# 错误搜索
{库名} {错误消息}

# 版本搜索
{库名} {版本号} migration guide
```

### 4.2 搜索示例

```
llama_index VectorStoreIndex example
llama_index AttributeError has no attribute 'query'
llama_index 0.10 migration guide
```
