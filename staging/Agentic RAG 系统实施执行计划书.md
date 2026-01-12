# Agentic RAG 系统实施执行计划书

## 文档信息

- **项目名称**：Agentic RAG 系统实施
- **文档版本**：v5.0（本质回归版）
- **创建日期**：2026-01-08
- **最后更新**：2026-01-11
- **文档状态**：可执行阶段

---

## 1. 核心价值（为什么）

### 1.1 一句话总结

**让系统自主选择检索策略，提升复杂查询质量**

### 1.2 RAG 的本质

**RAG = 检索 + 生成**

- **检索**：从知识库中获取相关信息
- **生成**：基于检索结果生成答案

### 1.3 Agentic RAG 的本质

**Agentic RAG = RAG + Agent 自主决策**

- **核心**：在检索和生成流程中加入 Agent 的自主决策
- **目标**：通过 Agent 的自主决策提升复杂查询的效果

**最核心的三个步骤**：
1. **规划**（Agent 决策）：Agent 自主选择检索策略
2. **检索**：执行检索，获取相关信息
3. **生成**：基于检索结果生成答案

**其他都是可选项**：后处理、反思、任务分解等都是可选的周边功能

---

## 2. 核心架构（骨架）

### 2.1 核心流程

```
用户查询
  ↓
规划（Agent 决策）
  ├─ 分析查询特征
  └─ 选择检索策略（vector/hybrid/multi）
  ↓
检索
  └─ 执行检索，获取相关信息
  ↓
生成
  └─ 基于检索结果生成答案
  ↓
最终答案
```

### 2.2 核心组件

**3 个核心组件**：
1. **规划 Agent**：ReActAgent，负责策略选择
2. **检索工具**：3个检索工具（vector/hybrid/multi），包装现有检索器
3. **生成逻辑**：复用现有的 LLM 生成逻辑

**1 个入口**：
- **AgenticQueryEngine**：完全替代 ModularQueryEngine，接口保持一致

---

## 3. 具体方案（怎么做）

### 3.1 核心架构

**简化流程**：
```
用户查询
  ↓
AgenticQueryEngine（主入口）
  ↓
规划 Agent（ReActAgent）
  ├─ 工具1：vector_search_tool
  ├─ 工具2：hybrid_search_tool
  └─ 工具3：multi_search_tool
  ↓
检索结果
  ↓
生成答案（复用现有 LLM 生成逻辑）
  ↓
最终答案
```

### 3.2 完全替代方案

**核心原则**：AgenticQueryEngine 完全替代 ModularQueryEngine，接口保持一致

**接口定义**：
```python
class AgenticQueryEngine:
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """与 ModularQueryEngine.query() 完全相同的接口
        
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        pass
    
    def stream_query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> AsyncIterator[str]:
        """与 ModularQueryEngine.stream_query() 完全相同的接口"""
        pass
```

### 3.3 核心实现

**规划 Agent**：
- 使用 LlamaIndex 的 `ReActAgent`
- 3个检索工具：包装现有的检索器（vector/hybrid/multi）
- Agent 自主选择使用哪个工具

**检索**：
- 复用现有的检索器：`create_retriever(strategy='vector/hybrid/multi')`
- 不需要额外的封装，直接调用现有组件

**生成**：
- 复用现有的 LLM 生成逻辑
- 复用现有的 `ResponseFormatter` 格式化

### 3.4 文件结构

```
backend/business/rag_engine/agentic/
├── __init__.py
├── engine.py                     # AgenticQueryEngine - 主入口
├── agent/
│   ├── __init__.py
│   ├── planning.py               # 规划 Agent（ReActAgent）
│   └── tools.py                  # 3个检索工具
└── prompts/
    ├── __init__.py
    ├── loader.py                 # Prompt 加载器
    └── templates/
        └── planning.txt          # 规划 Agent 的 Prompt
```

### 3.5 核心决策

**规划 Agent**：
- 决策：使用 LlamaIndex 的 `ReActAgent`
- 实现：`from llama_index.core.agent import ReActAgent`

**检索工具**：
- 决策：使用 `QueryEngineTool` 包装现有的检索器
- 实现：每个工具包装一个检索器实例（不同策略）

**生成逻辑**：
- 决策：复用现有的 LLM 生成逻辑
- 实现：直接调用现有的生成函数

**历史代码迁移**：
- 决策：**方案A - 直接替换**（更彻底，避免历史债务积累）
- 原则：AgenticQueryEngine 完全替代 ModularQueryEngine，接口保持一致

---

## 4. 需要决策的核心问题

### 4.1 规划 Agent 的实现

**问题1：检索工具如何封装？**
- 选项A：每个工具创建一个 `ModularQueryEngine` 实例（不同策略）
- 选项B：直接封装检索器，使用 `QueryEngineTool` 包装
- 选项C：创建简化的查询引擎，只包含检索部分

**问题2：Agent 如何选择工具？**
- Prompt 如何描述3个工具的功能和适用场景？
- 如何引导 Agent 选择正确的工具？

### 4.2 AgenticQueryEngine 的实现

**问题3：初始化参数**
- 是否完全继承 `ModularQueryEngine` 的所有参数？
- 不需要的参数如何处理（如 `retrieval_strategy`，因为由 Agent 选择）？

**问题4：工作流程**
- Agent 调用工具后，如何获取检索结果？
- 检索结果如何传递给生成逻辑？
- 是否需要后处理（重排序、过滤）？

### 4.3 错误处理和降级

**问题5：降级策略**
- Agent 调用失败时，是否降级到旧的 `ModularQueryEngine`？
- 还是使用简单的固定策略（如 vector）？

---

## 5. 风险控制

### 5.1 风险列表

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|----------|
| **接口不兼容** | 高 | 高 | 先保证接口一致，再增加功能 |
| **性能下降** | 中 | 中 | 设置超时机制，Agent 调用失败时降级 |
| **Agent 选择错误** | 中 | 中 | 优化 Prompt，增加日志记录选择过程 |
| **成本超限** | 低 | 高 | 简单的计数器，超出限制时返回错误 |

### 5.2 应对策略

**接口不兼容**：
- 实施前：明确接口定义，与 ModularQueryEngine 完全一致
- 实施后：完整的功能测试，确保输出格式一致

**性能下降**：
- 设置超时机制：Agent 调用超过 30 秒时降级
- 降级策略：调用失败时使用固定策略（vector）

**Agent 选择错误**：
- 增加日志：记录 Agent 的选择过程和理由
- 优化 Prompt：清晰描述工具的功能和适用场景

---

## 6. 历史代码迁移策略

### 6.1 迁移方案

**选择方案A：直接替换**

**核心原则**：
- AgenticQueryEngine 完全替代 ModularQueryEngine
- 接口保持一致，确保无缝替换
- 一次性彻底迁移，避免历史债务积累

### 6.2 需要替换的位置

| 文件 | 位置 | 替换方式 |
|------|------|----------|
| `rag_service.py` | `modular_query_engine` property | 直接替换导入和实例化 |
| `chat/manager.py` | `__init__` 中的实例化 | 直接替换导入和实例化 |
| `rag_engine/__init__.py` | 公共导出 | 使用类型别名或直接替换 |

### 6.3 实施步骤

**步骤1：实现 AgenticQueryEngine**
- 确保接口与 ModularQueryEngine 完全一致
- 通过接口兼容性测试

**步骤2：替换所有使用点**
- 替换 RAGService 中的导入和实例化
- 替换 ChatManager 中的导入和实例化
- 更新公共导出

**步骤3：测试验证**
- 完整的功能测试
- 性能测试
- 端到端测试

---

## 7. 配置设计

```yaml
agentic_rag:
  max_llm_calls: 35  # 默认值，可配置（15-50次）
  timeout_seconds: 30  # Agent 调用超时时间
```

---

**文档状态**：✅ v5.0 本质回归完成

**下一步**：决策核心问题，开始实施