# 2025-10-12 【bugfix】修复：query() 返回值不匹配问题

**【Task Type】**: bugfix
**日期**: 2025-10-12  
**问题**: `ValueError: too many values to unpack (expected 2)`  
**状态**: ✅ 已修复

---

## 问题原因

`RAGQueryEngine.query()` 方法返回 3 个值：
```python
def query(self, question: str, collect_trace: bool = False) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
    return (答案文本, 引用来源列表, 追踪信息字典)
```

但多处调用代码只接收 2 个返回值：
```python
answer, sources = query_engine.query(question)  # ❌ 错误：期望2个，实际3个
```

---

## 修复内容

### 修复的文件 (共5个)

1. **`src/query_engine.py`**
   - 第428行：`HybridQueryEngine.query()` 调用 `local_engine.query()`
   ```python
   # 修复前
   local_answer, local_sources = self.local_engine.query(question)
   
   # 修复后
   local_answer, local_sources, _ = self.local_engine.query(question)
   ```

2. **`main.py`**
   - 第172行：命令行查询
   ```python
   # 修复前
   answer, sources = query_engine.query(args.question)
   
   # 修复后
   answer, sources, _ = query_engine.query(args.question)
   ```

3. **`tests/unit/test_query_engine.py`** (3处)
   - 第75行：`test_query_returns_answer_and_sources`
   - 第89行：`test_query_with_no_sources`
   - 第221行：`test_real_query`
   ```python
   # 修复前
   answer, sources = mock_query_engine.query("测试问题")
   
   # 修复后
   answer, sources, _ = mock_query_engine.query("测试问题")
   ```

4. **`tests/integration/test_query_pipeline.py`** (2处)
   - 第59行：`test_query_with_mock_llm`
   - 第99行：`test_multiple_queries_same_index`
   ```python
   # 修复前
   answer, sources = query_engine.query(question)
   
   # 修复后
   answer, sources, _ = query_engine.query(question)
   ```

---

## 验证结果

✅ **单元测试通过**:
```bash
tests/unit/test_query_engine.py::TestQueryEngine::test_query_returns_answer_and_sources PASSED
tests/unit/test_query_engine.py::TestQueryEngine::test_query_with_no_sources PASSED
```

✅ **集成测试通过**:
```bash
tests/integration/test_query_pipeline.py::TestQueryPipeline::test_query_with_mock_llm PASSED
tests/integration/test_query_pipeline.py::TestQueryPipeline::test_multiple_queries_same_index PASSED
```

✅ **Web 应用**: `app.py` 中的调用已经是正确的（接收3个值）

---

## 技术说明

### 返回值含义

`RAGQueryEngine.query()` 的返回值：
1. **答案文本** (str): LLM 生成的回答
2. **引用来源列表** (List[dict]): 引用的文档来源
3. **追踪信息字典** (Optional[Dict]): 调试和性能追踪信息（可选）

### 为什么使用 `_` 忽略第三个值

大部分调用场景不需要追踪信息（trace），所以使用 Python 的惯例 `_` 来忽略：
```python
answer, sources, _ = query_engine.query(question)
```

这样既修复了返回值不匹配的问题，又保持了代码简洁。

---

## 相关代码

### RAGQueryEngine.query() 签名
```python
def query(self, question: str, collect_trace: bool = False) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
    """执行查询并返回带引用的答案
    
    Returns:
        (答案文本, 引用来源列表, 追踪信息字典)
    """
```

### HybridQueryEngine.query() 签名
```python
def query(self, question: str) -> Tuple[str, List[dict], List[dict]]:
    """执行混合查询
    
    Returns:
        (答案文本, 本地来源列表, 维基百科来源列表)
    """
```

---

**修复完成时间**: 2025-10-12 20:30  
**验证状态**: ✅ 全部通过  
**影响范围**: 5个文件，共6处修改

