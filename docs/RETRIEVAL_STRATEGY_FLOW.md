# 检索策略执行流程说明

## 📋 概述

本文档说明当前检索策略的执行流程机制，以及如何记录策略选择的决策原因。

---

## 🔄 当前策略执行流程

### 1. 初始化阶段

#### 1.1 固定策略模式（默认）

```python
# 用户明确指定检索策略
engine = ModularQueryEngine(
    index_manager=index_manager,
    retrieval_strategy="multi"  # 或 vector, bm25, hybrid, grep
)
```

**执行流程**：
1. **策略验证**：检查策略是否在 `SUPPORTED_STRATEGIES` 中
2. **创建检索器**：通过 `create_retriever()` 工厂方法创建对应的检索器
3. **创建查询引擎**：使用检索器创建 `RetrieverQueryEngine`
4. **记录日志**：记录初始化的策略配置

**关键代码位置**：
- `src/query/modular/engine.py` - 初始化逻辑
- `src/query/modular/retriever_factory.py` - 检索器创建

#### 1.2 自动路由模式

```python
# 启用自动路由
engine = ModularQueryEngine(
    index_manager=index_manager,
    enable_auto_routing=True  # 启用自动路由
)
```

**执行流程**：
1. **延迟创建**：不在初始化时创建检索器，而是在查询时动态创建
2. **创建路由器**：初始化 `QueryRouter` 实例
3. **准备策略**：准备多种检索策略的创建逻辑（延迟加载）

**关键代码位置**：
- `src/routers/query_router.py` - 路由决策逻辑

---

### 2. 查询执行阶段

#### 2.1 固定策略模式

```
用户查询
  ↓
ModularQueryEngine.query()
  ↓
使用预创建的 query_engine
  ↓
执行检索 → 后处理 → 生成答案
```

**日志记录**：
- ✅ 记录查询文本
- ✅ 记录检索结果数量
- ❌ **缺少策略选择原因记录**

#### 2.2 自动路由模式

```
用户查询
  ↓
ModularQueryEngine.query()
  ↓
QueryRouter.route() - 分析查询意图
  ↓
_analyze_query() - 决策选择策略
  ↓
动态创建对应的检索器
  ↓
执行检索 → 后处理 → 生成答案
```

**决策流程**：
1. **查询分析**：`_analyze_query()` 分析查询文本
2. **规则匹配**：
   - 文件名关键词 → `files_via_metadata`
   - 宽泛主题词 → `files_via_content`
   - 默认 → `chunk`
3. **创建检索器**：根据决策创建对应检索器
4. **执行查询**：使用选定的检索器执行查询

**日志记录**：
- ✅ 记录路由决策结果
- ❌ **缺少决策原因详细记录**（为什么选择该策略）

---

### 3. 多策略检索执行流程

当使用 `retrieval_strategy="multi"` 时：

```
用户查询
  ↓
MultiStrategyRetriever.retrieve()
  ↓
并行执行多个检索器：
  - VectorRetriever
  - BM25Retriever
  - GrepRetriever
  ↓
ResultMerger.merge() - 合并结果
  ↓
返回合并后的结果
```

**日志记录**：
- ✅ 记录并行检索的结果数量
- ✅ 记录合并后的结果数量
- ❌ **缺少各策略选择原因记录**
- ❌ **缺少合并策略和权重说明**

---

## 📊 当前日志记录情况

### ✅ 已有日志

1. **初始化日志**：
   ```python
   logger.info(f"   检索策略: {self.retrieval_strategy}")
   ```

2. **路由决策日志**：
   ```python
   logger.info(f"查询路由决策: query={query[:50]}..., decision={routing_decision}")
   ```

3. **多策略检索日志**：
   ```python
   logger.info(f"多策略检索完成: 查询={query[:50]}..., 检索器结果数=..., 合并后结果数=...")
   ```

### ❌ 缺失日志

1. **策略选择原因**：
   - 为什么选择该策略？
   - 基于什么规则/条件？

2. **多策略详细信息**：
   - 哪些策略被启用？
   - 各策略的权重是多少？
   - 合并策略是什么？

3. **决策上下文**：
   - 查询特征分析
   - 匹配的关键词
   - 决策置信度

---

## 🎯 改进目标

### 目标1：记录策略选择决策原因

**场景1：固定策略**
- 记录：用户指定 / 配置默认 / 策略管理器选择
- 原因：配置来源、默认策略说明

**场景2：自动路由**
- 记录：匹配的规则、关键词、查询特征
- 原因：为什么选择该路由模式

**场景3：多策略检索**
- 记录：启用的策略列表、权重分配、合并策略
- 原因：为什么使用多策略、各策略的用途

### 目标2：增强日志可读性

- 使用结构化日志格式
- 包含决策时间戳
- 记录查询特征分析
- 提供策略性能对比（如适用）

---

## 🔗 相关代码位置

- **策略初始化**：`src/query/modular/engine.py` (第30-144行)
- **检索器创建**：`src/query/modular/retriever_factory.py`
- **路由决策**：`src/routers/query_router.py` (第84-111行)
- **多策略检索**：`src/retrievers/multi_strategy_retriever.py`
- **查询执行**：`src/query/modular/query_executor.py`
- **策略管理**：`src/business/strategy_manager.py`

---

## 📈 查询处理

查询处理（意图理解+改写）和策略选择详情请参考：[查询处理与策略选择](QUERY_PROCESSING.md)

---

**最后更新**: 2025-11-03

