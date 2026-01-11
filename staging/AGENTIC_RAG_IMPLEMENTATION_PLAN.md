# Agentic RAG 系统实施执行计划书

## 文档信息

- **项目名称**：Agentic RAG 系统实施
- **文档版本**：v2.3
- **创建日期**：2026-01-08
- **最后更新**：2026-01-08
- **文档状态**：待审核

**注意**：本文档为执行计划书，内容较多（约1100行），超出常规文档300行限制。为保持计划完整性，采用单文档形式。如需拆分，可拆分为主计划书+详细技术文档。

---

## 1. 项目概述

### 1.1 项目背景

在研究查询改写和意图理解时发现基于 Agent 的实现方案，由此发散到更底层架构：将整个后端 RAG 链路全部纳入 Agentic RAG 架构，Agentic RAG 作为最底层架构来组织系统所有功能。

**核心思想**：将"检索-生成"这一核心流程的各个环节都赋予自主的规划、决策与反思能力，实现从"静态流程"到"动态智能体"的架构演进。

**核心流程**：规划-增强检索-反思生成
- 规划：Query Planning Agent 作为"大脑"，动态规划检索策略和执行方案
- 增强检索：支持多轮、多策略、多跳推理的智能检索
- 反思生成：生成后反思，评估质量并可能触发重试

**定位**：本方案属于**前沿主流**方向，与业界前沿趋势高度一致，是解决开放探索、复杂推理问题的最有潜力的路径，正快速从实验室和先锋项目走向更广泛的应用。

### 1.2 项目目标

- **核心目标**：实现完整 Agentic RAG 系统，将整个 RAG 链路纳入 Agent 架构
- **技术目标**：基于 LlamaIndex ReActAgent 构建多 Agent 架构，Agentic RAG 作为底层架构
- **业务目标**：提升复杂查询处理能力，支持跨领域关联与多视角分析
- **质量目标**：保持 API 兼容性，确保平滑迁移

### 1.3 项目范围

**包含范围**：
- 多 Agent 架构设计与实现（8 个 Agent：查询规划、检索、后处理、生成、反思、任务分解、跨领域、兜底）
- 工具封装（20 个工具：查询规划 4 个、检索 7 个、后处理 2 个、生成 1 个、反思 2 个、任务分解 2 个、跨领域 2 个、兜底 2 个）
- 动态协调器实现（AgentOrchestrator）
- 成本控制机制
- 完整测试覆盖
- Agent 工程化四大支柱（Prompt 引擎、MCP、会话管理、可观测性）

**不包含范围**：
- 前端 UI 改动（通过 RAGService 隔离）
- 数据索引流程改动
- 外部工具集成（后续扩展）

---

## 2. 技术架构设计

### 2.1 架构理念

**Agentic RAG 核心思想**：将"检索-生成"这一核心流程的各个环节都赋予自主的规划、决策与反思能力，实现从"静态流程"到"动态智能体"的架构演进。

**核心流程**：**规划-增强检索-反思生成**
- **规划**：Query Planning Agent 作为"大脑"，动态规划检索策略和执行方案
- **增强检索**：Retrieval Agent 可规划策略、调用多种工具，支持多轮、多策略检索
- **反思生成**：Generation Agent 生成答案后，Reflection Agent 评估质量并可能触发重试

**架构演进方向**：
- 从"工具"到"伙伴"：RAG 从独立系统转变为 Agent 生态的子模块
- 从"静态"到"动态"：强调动态、可编排的框架，而非固定流程
- 从"单一"到"多轮"：支持递归/迭代检索、多跳推理、反思循环

**定位**：本方案属于**前沿主流**方向，是解决开放探索、复杂推理问题的最有潜力的路径，正快速从实验室和先锋项目走向更广泛的应用。

### 2.2 完整 RAG 链路架构

```
用户查询
    ↓
[主协调 Agent] AgentOrchestrator
    ├─ [查询规划 Agent] QueryPlanningAgent（理解+改写+策略选择）
    │   ├─ 意图理解：分析查询类型、复杂度、关键实体
    │   ├─ 查询改写：优化查询表达，补充领域关键词
    │   └─ 策略选择：评估各策略适用性，选择最优策略
    │   └─ 工具：意图分析工具、改写工具、策略评估工具、策略选择工具
    │
    ├─ [检索 Agent] RetrievalAgent（检索执行）
    │   └─ 工具：7种检索工具（vector/bm25/hybrid/grep/multi/files）
    │
    ├─ [后处理 Agent] PostProcessingAgent（结果优化）
    │   └─ 工具：相似度过滤、重排序
    │
    ├─ [生成 Agent] GenerationAgent（答案生成）
    │   └─ 工具：LLM生成、格式化工具
    │
    ├─ [反思 Agent] ReflectionAgent（质量评估，可选）
    │   └─ 工具：质量评估工具、策略调整工具
    │
    ├─ [任务分解 Agent] TaskDecompositionAgent（复杂查询，可选）
    │   └─ 工具：任务规划工具、子任务执行工具
    │
    ├─ [跨领域 Agent] CrossDomainAgent（概念关联，可选）
    │   └─ 工具：概念提取工具、关联发现工具
    │
    └─ [兜底 Agent] FallbackAgent（异常处理，可选）
        └─ 工具：降级检索工具、纯LLM生成工具
    ↓
最终答案
```

**说明**：
- **核心流程**：Query Planning Agent → Retrieval Agent → PostProcessing Agent → Generation Agent
- **增强功能**：Reflection Agent、Task Decomposition Agent、Cross Domain Agent（根据查询特点动态调用）
- **容错机制**：Fallback Agent（异常时触发）

### 2.3 Agent 职责划分

#### 核心 Agent（必须，P0）

| Agent | 职责 | 工具集 | 说明 |
|-------|------|--------|------|
| **查询规划 Agent** | 意图理解、查询改写、策略选择 | 意图分析、改写、策略评估、策略选择 | 合并 QueryProcessor + QueryRouter |
| **检索 Agent** | 检索执行 | 7种检索工具 | RAG 核心功能 |
| **后处理 Agent** | 结果优化 | 相似度过滤、重排序 | 优化检索结果 |
| **生成 Agent** | 答案生成 | LLM生成、格式化 | RAG 核心功能 |
| **兜底 Agent** | 异常处理、降级 | 降级检索、纯LLM生成 | 容错机制 |

#### 增强 Agent（可选，P1）

| Agent | 职责 | 工具集 | 调用条件 |
|-------|------|--------|---------|
| **反思 Agent** | 质量评估、策略调整 | 质量评估、策略调整 | 质量阈值 < 0.8 且启用反思 |
| **任务分解 Agent** | 复杂查询拆解 | 任务规划、子任务执行 | 复杂度 ≥ 0.7 且需要分解 |
| **跨领域 Agent** | 概念关联、多视角 | 概念提取、关联发现 | 检测到跨领域关键词 |

**Agent 分类说明**：
- **核心 Agent**：完成基础 RAG 流程（查询规划 → 检索 → 后处理 → 生成）
- **增强 Agent**：根据查询特点动态调用，提升答案质量
- **兜底 Agent**：异常时触发，确保系统可用性

### 2.4 工具集设计

#### 查询规划工具（4种）
1. `analyze_intent` - 意图分析（查询类型、复杂度、关键实体）
2. `rewrite_query` - 查询改写（优化表达、补充关键词）
3. `evaluate_strategies` - 策略评估（评估各策略适用性）
4. `select_strategy` - 策略选择（选择最优检索策略）

#### 检索工具（7种）
1. `vector_search` - 向量检索
2. `bm25_search` - BM25 检索
3. `hybrid_search` - 混合检索
4. `grep_search` - Grep 检索
5. `multi_search` - 多策略检索
6. `files_via_metadata` - 文件元数据检索
7. `files_via_content` - 文件内容检索

#### 后处理工具（2种）
1. `similarity_filter` - 相似度过滤
2. `rerank` - 重排序

#### 生成工具（1种）
1. `format_response` - 响应格式化

#### 反思工具（2种）
1. `evaluate_quality` - 质量评估（相关性、准确性、完整性）
2. `suggest_adjustment` - 策略调整建议

#### 任务分解工具（2种）
1. `analyze_complexity` - 复杂度分析
2. `decompose_task` - 任务分解

#### 跨领域工具（2种）
1. `extract_concepts` - 概念提取
2. `find_relations` - 关联发现

#### 兜底工具（2种）
1. `fallback_retrieval` - 降级检索（简单策略）
2. `pure_llm_generation` - 纯LLM生成（无检索）

### 2.5 AgentOrchestrator 功能

**主协调 Agent（AgentOrchestrator）的核心功能**：

#### 1. Agent 注册与管理
- 注册所有 Agent（查询规划、检索、后处理、生成、兜底、反思等）
- 管理 Agent 的启用/禁用状态（根据配置）
- 提供 Agent 发现和调用接口

#### 2. 执行流程协调（核心）
- **决定调用哪些 Agent**：根据查询特点动态选择
- **决定调用顺序**：规划执行流程
- **条件执行**：
  - 复杂查询 → 调用 Task Decomposition Agent
  - 跨领域查询 → 调用 Cross Domain Agent
  - 质量不足 → 调用 Reflection Agent
  - 异常情况 → 调用 Fallback Agent

#### 3. 数据传递与状态管理
- 在 Agent 间传递数据（查询、理解结果、检索结果、生成结果等）
- 维护执行状态（当前阶段、已执行步骤、中间结果）
- 管理共享上下文（避免 Agent 间直接共享状态）

#### 4. 成本控制
- 统计 LLM 调用次数（上限：50 次/查询）
- 检测超时（上限：120 秒）
- 在超限时停止执行并返回已收集结果

#### 5. 错误处理与降级
- 捕获 Agent 执行异常
- 触发降级策略（Fallback Agent）
- 记录错误信息用于分析和优化

#### 6. 条件判断与决策
- 判断查询复杂度（是否需要任务分解）
- 判断是否需要跨领域分析
- 判断是否需要反思（质量评估）
- 判断是否需要兜底（异常处理）

#### 7. 流式输出协调
- 协调流式输出（token、sources、reasoning）
- 在流式过程中检查成本控制
- 管理流式输出的生命周期

**Orchestrator 的职责边界**：
- ✅ **负责**：流程编排、数据传递、成本控制、错误处理、条件判断
- ❌ **不负责**：查询理解、检索执行、答案生成等具体业务逻辑（由各 Agent 负责）

**设计模式**：编排者模式（Orchestrator Pattern）
- Orchestrator = 指挥家：决定演奏顺序、协调各乐手
- Agent = 乐手：执行具体任务（查询理解、检索、生成等）

### 2.6 Agent 调用顺序与决策流程

#### 核心流程：规划-增强检索-反思生成

**核心理念**：将"检索-生成"流程的各个环节赋予自主的规划、决策与反思能力。

```
用户查询
    ↓
┌─────────────────────────────────────────┐
│ 【规划阶段】Query Planning Agent        │
│ - 理解查询意图                          │
│ - 改写查询（如需要）                    │
│ - 规划检索策略和执行方案                │
│ - 动态决策：是否需要任务分解、跨领域分析│
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 【增强检索阶段】Retrieval Agent          │
│ - 使用规划的策略执行检索                │
│ - 支持多轮检索（基于初步结果发起多轮查询）│
│ - 支持多策略检索（混合搜索、多跳推理）   │
│ - 动态调整检索策略                      │
└─────────────────────────────────────────┘
    ↓
[PostProcessing Agent]
    └─ 优化检索结果（过滤、重排序）
    ↓
┌─────────────────────────────────────────┐
│ 【生成阶段】Generation Agent            │
│ - 基于检索结果生成答案                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 【反思阶段】Reflection Agent（可选）     │
│ - 评估答案质量                          │
│ - 如果质量不足 → 调整策略 → 重新检索    │
│ - 最多反思 3 轮                         │
└─────────────────────────────────────────┘
    ↓
返回答案
```

**流程特点**：
- ✅ **规划驱动**：Query Planning Agent 作为"大脑"，动态规划整个流程
- ✅ **增强检索**：支持多轮、多策略、多跳推理的智能检索
- ✅ **反思生成**：生成后反思，评估质量并可能触发重试
- ✅ **动态决策**：每个环节都可以自主决策，而非固定流程

#### 增强流程（条件执行）

**复杂查询流程**：
```
复杂查询（complexity ≥ 0.7）
    ↓
[Task Decomposition Agent]
    ├─ 分解为子任务
    └─ 规划执行顺序
    ↓
并行/顺序执行子任务
    ├─ 每个子任务：检索 → 后处理 → 生成
    └─ 合并子任务结果
    ↓
[Generation Agent]
    └─ 整合最终答案
```

**跨领域查询流程**：
```
跨领域查询（检测到跨领域关键词）
    ↓
[Cross Domain Agent]
    ├─ 提取相关概念
    └─ 发现概念关联
    ↓
补充检索（使用关联概念）
    ↓
[Retrieval Agent] → [PostProcessing Agent] → [Generation Agent]
```

**质量反思流程**：
```
生成后质量检查
    ↓
判断是否需要反思（质量阈值 < 0.8）
    ├─ 是 → [Reflection Agent]
    │   ├─ 评估答案质量
    │   ├─ 如果质量不足 → 调整策略 → 重新检索
    │   └─ 最多反思 3 轮
    └─ 否 → 直接返回答案
```

**异常处理流程**：
```
任何阶段失败
    ↓
[Fallback Agent]
    ├─ 检测异常类型
    ├─ 一级降级：简单检索（vector_search）
    ├─ 二级降级：纯LLM生成（无检索）
    └─ 三级降级：返回错误信息
```

#### 决策矩阵

| 查询类型 | 复杂度 | 调用顺序 |
|---------|--------|---------|
| 简单查询 | < 0.5 | Query Planning → Retrieval → PostProcessing → Generation |
| 中等查询 | 0.5-0.7 | Query Planning → Retrieval → PostProcessing → Generation → Reflection（可选） |
| 复杂查询 | ≥ 0.7 | Query Planning → Task Decomposition → 并行检索 → PostProcessing → Generation → Reflection |
| 跨领域查询 | 任意 | Query Planning → Cross Domain → Retrieval → PostProcessing → Generation |

### 2.7 成本控制机制

- **LLM 调用上限**：50 次/查询
- **超时时间**：120 秒
- **自适应反思深度**：1-3 轮（根据查询复杂度）
- **Agent 调用限制**：每个 Agent 最多调用 3 次（避免死循环）

### 2.8 架构优势

**统一架构**：
- ✅ 所有功能都由 Agent 组织，架构一致
- ✅ 每个环节都可以智能决策，灵活可扩展
- ✅ 易于添加新 Agent 和工具

**智能决策**：
- ✅ Query Planning Agent 可以动态决定是否需要改写和选择策略
- ✅ PostProcessing Agent 可以动态调整过滤和重排序策略
- ✅ Reflection Agent 可以动态调整策略

**容错机制**：
- ✅ Fallback Agent 处理异常情况
- ✅ 多级降级策略（Agent 失败 → 简单检索 → 纯LLM）

---

## 3. 详细实施计划

### 阶段 1：基础架构搭建（1 周）

#### 目标
搭建多 Agent 基础架构，建立开发框架

#### 任务清单

**1.1 目录结构创建**
- [ ] 创建 `backend/business/rag_engine/agentic/` 目录
- [ ] 创建子目录：`prompts/`、`tools/`、`utils/`
- [ ] 创建 `__init__.py` 文件

**1.2 基础类实现**
- [ ] 实现 `BaseAgent` 基类
  - Agent 通用接口
  - LLM 初始化
  - 工具管理
- [ ] 实现 `ReActAgent` 基础类
  - 基于 LlamaIndex ReActAgent
  - 思考-行动-观察循环
  - 工具调用机制

**1.3 协调器框架**
- [ ] 实现 `AgentOrchestrator` 基础框架
  - Agent 注册机制
  - 执行流程框架
  - 成本控制框架

**1.4 成本控制机制**
- [ ] 实现 `CostController` 类
  - LLM 调用计数
  - 超时检测
  - 停止条件判断

**1.5 配置支持**
- [ ] 更新 `application.yml`，新增 Agentic RAG 配置
- [ ] 更新 `Config` 类，新增配置属性
- [ ] 实现配置加载逻辑

**1.6 代码规范约束**
- [ ] 明确文件行数限制（≤300行）
- [ ] 明确类型提示要求（所有函数、方法、类）
- [ ] 明确日志规范（使用 `backend.infrastructure.logger.get_logger`）
- [ ] 实现代码规范检查工具

**1.7 依赖版本检查**
- [ ] 检查 LlamaIndex 版本（≥0.9.0）
- [ ] 验证 LlamaIndex ReActAgent 可用性
- [ ] 验证依赖兼容性
- [ ] 记录依赖版本要求

**1.8 基础测试**
- [ ] 编写 `BaseAgent` 单元测试
- [ ] 编写 `CostController` 单元测试
- [ ] 编写配置加载测试
- [ ] 编写代码规范检查测试

#### 交付物
- Agent 基类框架
- Orchestrator 基础实现
- 成本控制机制
- 配置支持

#### 验收标准
- [ ] 所有基础类可以正常实例化
- [ ] 成本控制机制正常工作
- [ ] 配置可以正确加载
- [ ] 代码规范检查通过（文件行数≤300行，类型提示完整）
- [ ] 依赖版本验证通过
- [ ] 单元测试通过率 100%

---

### 阶段 2：工具封装（1 周）

#### 目标
将现有所有功能封装为 LlamaIndex Tool

#### 任务清单

**2.1 查询规划工具封装**
- [ ] 封装 `analyze_intent` 工具（意图分析）
- [ ] 封装 `rewrite_query` 工具（查询改写）
- [ ] 封装 `evaluate_strategies` 工具（策略评估）
- [ ] 封装 `select_strategy` 工具（策略选择）

**2.3 检索工具封装**
- [ ] 封装 `vector_search` 工具
- [ ] 封装 `bm25_search` 工具
- [ ] 封装 `hybrid_search` 工具
- [ ] 封装 `grep_search` 工具
- [ ] 封装 `multi_search` 工具
- [ ] 封装 `files_via_metadata` 工具
- [ ] 封装 `files_via_content` 工具

**2.4 后处理工具封装**
- [ ] 封装 `similarity_filter` 工具
- [ ] 封装 `rerank` 工具

**2.5 生成工具封装**
- [ ] 封装 `format_response` 工具

**2.6 反思工具封装**
- [ ] 封装 `evaluate_quality` 工具（质量评估）
- [ ] 封装 `suggest_adjustment` 工具（策略调整）

**2.7 任务分解工具封装**
- [ ] 封装 `analyze_complexity` 工具（复杂度分析）
- [ ] 封装 `decompose_task` 工具（任务分解）

**2.8 跨领域工具封装**
- [ ] 封装 `extract_concepts` 工具（概念提取）
- [ ] 封装 `find_relations` 工具（关联发现）

**2.9 兜底工具封装**
- [ ] 封装 `fallback_retrieval` 工具（降级检索）
- [ ] 封装 `pure_llm_generation` 工具（纯LLM生成）

**2.10 工具注册机制**
- [ ] 实现工具注册表
- [ ] 实现工具动态加载
- [ ] 实现工具描述生成

**2.11 工具测试**
- [ ] 编写每个工具的单元测试
- [ ] 编写工具集成测试
- [ ] 验证工具调用正确性

#### 交付物
- 20 个工具实现（4+7+2+1+2+2+2+2，合并查询规划和路由工具）
- 工具注册表
- 工具使用文档

#### 验收标准
- [ ] 所有工具可以正常调用
- [ ] 工具描述准确完整
- [ ] 工具返回格式正确
- [ ] 单元测试通过率 100%

---

### 阶段 3：核心 Agent 实现（1.5 周）

#### 目标
实现核心 Agent（查询分析、路由、检索、后处理、生成、兜底），完成基础 Agentic RAG 流程

#### 任务清单

**3.1 Prompt 模板设计与管理**
- [ ] 设计查询规划 Agent Prompt 模板（合并查询分析和路由）
- [ ] 设计检索 Agent Prompt 模板
- [ ] 设计后处理 Agent Prompt 模板
- [ ] 设计生成 Agent Prompt 模板
- [ ] 设计兜底 Agent Prompt 模板
- [ ] 实现 Prompt 文件化管理（类似 `query_rewrite_template.txt`）
  - 模板文件存储在 `backend/business/rag_engine/agentic/prompts/templates/`
  - 支持从文件加载，支持运行时更新
  - 提供默认模板作为后备
- [ ] 实现 Prompt 加载机制
- [ ] 实现 Prompt 版本管理（记录模板版本）

**3.2 查询规划 Agent 实现**
- [ ] 实现 `QueryPlanningAgent` 类（合并查询分析和路由）
  - 意图理解逻辑（替代 QueryProcessor）
  - 查询改写逻辑
  - 复杂度评估逻辑
  - 策略评估逻辑（替代 QueryRouter）
  - 策略选择逻辑
- [ ] 集成查询规划工具（意图分析、改写、策略评估、策略选择）
- [ ] 实现分层决策（简单查询跳过LLM）
- [ ] 实现策略选择决策（根据查询特点选择最优策略）

**3.4 检索 Agent 实现**
- [ ] 实现 `RetrievalAgent` 类
  - 检索执行逻辑
  - 结果评估逻辑
  - 策略调整机制
- [ ] 集成检索工具

**3.5 后处理 Agent 实现**
- [ ] 实现 `PostProcessingAgent` 类
  - 相似度过滤逻辑（替代 PostProcessor）
  - 重排序逻辑
  - 结果优化逻辑
- [ ] 集成后处理工具

**3.6 生成 Agent 实现**
- [ ] 实现 `GenerationAgent` 类
  - 上下文构建逻辑
  - 答案生成逻辑
  - 格式化逻辑
- [ ] 集成生成工具
- [ ] 实现引用溯源

**3.7 兜底 Agent 实现**
- [ ] 实现 `FallbackAgent` 类
  - 异常检测逻辑
  - 降级策略执行
  - 纯LLM生成逻辑
- [ ] 集成兜底工具

**3.8 Orchestrator 集成**
- [ ] 实现 AgentOrchestrator 核心功能
  - Agent 注册与管理
  - 执行流程协调（决定调用哪些 Agent、调用顺序）
  - 数据传递与状态管理
  - 成本控制（LLM 调用次数、超时检测）
  - 错误处理与降级
  - 条件判断与决策（复杂度、跨领域、质量等）
  - 流式输出协调
- [ ] 集成查询规划 Agent
- [ ] 集成检索 Agent
- [ ] 集成后处理 Agent
- [ ] 集成生成 Agent
- [ ] 集成兜底 Agent
- [ ] 实现基础执行流程（Query Planning → Retrieval → PostProcessing → Generation）
- [ ] 实现条件执行逻辑（Task Decomposition、Cross Domain、Reflection）

**3.9 Agentic Query Engine**
- [ ] 实现 `AgenticQueryEngine` 类
  - 保持 API 兼容性
  - 集成 Orchestrator
  - 实现 `query()` 方法
  - 实现 `stream_query()` 方法（流式输出支持）
    - 支持流式 token 输出（`type: 'token'`）
    - 支持流式 sources 输出（`type: 'sources'`）
    - 支持流式 reasoning 输出（`type: 'reasoning'`）
    - 支持完成事件（`type: 'done'`）
    - 支持错误事件（`type: 'error'`）
    - 与成本控制机制协调（流式过程中检查超时和调用次数）

**3.10 集成测试**
- [ ] 编写查询规划 Agent 集成测试（合并查询分析和路由）
- [ ] 编写检索 Agent 集成测试
- [ ] 编写后处理 Agent 集成测试
- [ ] 编写生成 Agent 集成测试
- [ ] 编写兜底 Agent 集成测试
- [ ] 编写 AgentOrchestrator 集成测试（流程协调、条件执行）
- [ ] 编写 Agentic Query Engine 集成测试

#### 交付物
- QueryPlanningAgent 实现（合并 QueryProcessor + QueryRouter）
- RetrievalAgent 实现
- PostProcessingAgent 实现（替代 PostProcessor）
- GenerationAgent 实现
- FallbackAgent 实现
- AgentOrchestrator 实现（流程协调、条件执行、成本控制）
- AgenticQueryEngine 实现
- 基础 Agentic RAG 流程

#### 验收标准
- [ ] Query Planning Agent 可以正确理解意图、改写查询、选择策略
- [ ] Retrieval Agent 可以正确执行检索
- [ ] PostProcessing Agent 可以正确优化结果
- [ ] Generation Agent 可以生成高质量答案
- [ ] Fallback Agent 可以正确处理异常
- [ ] AgentOrchestrator 可以正确协调 Agent 执行流程
- [ ] AgentOrchestrator 可以正确进行条件判断和决策
- [ ] AgenticQueryEngine API 与 ModularQueryEngine 兼容
- [ ] 集成测试通过率 100%

---

### 阶段 4：反思 Agent（1 周）

#### 目标
实现质量评估与策略调整机制

#### 任务清单

**4.1 反思 Prompt 模板**
- [ ] 设计反思 Agent Prompt 模板
- [ ] 设计检索结果评估模板
- [ ] 实现质量评分机制

**4.2 反思 Agent 实现**
- [ ] 实现 `ReflectionAgent` 类
  - 答案质量评估
  - 检索结果评估
  - 策略调整建议
- [ ] 实现评估维度（相关性、准确性、完整性、清晰度）
- [ ] 实现评分机制（0-1 分）

**4.3 自适应反思深度**
- [ ] 实现深度判断逻辑
- [ ] 根据查询复杂度调整深度
- [ ] 实现反思循环控制

**4.4 策略调整机制**
- [ ] 实现重试逻辑
- [ ] 实现策略切换逻辑
- [ ] 实现查询改写逻辑

**4.5 Orchestrator 集成**
- [ ] 集成反思 Agent
- [ ] 实现反思流程
- [ ] 实现策略调整流程

**4.6 测试**
- [ ] 编写反思 Agent 单元测试
- [ ] 编写反思机制集成测试
- [ ] 验证质量评估准确性

#### 交付物
- ReflectionAgent 实现
- 反思机制完整实现
- 质量评估系统

#### 验收标准
- [ ] 反思 Agent 可以正确评估答案质量
- [ ] 自适应深度机制正常工作
- [ ] 策略调整机制有效
- [ ] 测试通过率 100%

---

### 阶段 5：任务分解 Agent（1 周）

#### 目标
支持复杂查询分解为子任务

#### 任务清单

**5.1 任务分解 Prompt 模板**
- [ ] 设计任务分解 Prompt 模板
- [ ] 设计子任务规划模板

**5.2 任务分解 Agent 实现**
- [ ] 实现 `TaskDecompositionAgent` 类
  - 查询复杂度分析
  - 子任务分解逻辑
  - 执行顺序规划
- [ ] 实现子任务依赖分析

**5.3 子任务执行机制（并发控制）**
- [ ] 实现子任务并行执行
  - 使用 `asyncio` 或 `concurrent.futures` 实现并发
  - 控制最大并发数（避免资源竞争）
  - 实现任务队列管理
- [ ] 实现子任务顺序执行（依赖关系）
- [ ] 实现结果合并逻辑
- [ ] 实现并发资源限制（避免过多并发导致性能下降）

**5.4 Orchestrator 集成**
- [ ] 集成任务分解 Agent
- [ ] 实现复杂查询处理流程
- [ ] 实现子任务调度

**5.5 测试**
- [ ] 编写任务分解 Agent 单元测试
- [ ] 编写复杂查询处理测试
- [ ] 验证子任务执行正确性

#### 交付物
- TaskDecompositionAgent 实现
- 复杂查询处理能力

#### 验收标准
- [ ] 任务分解 Agent 可以正确分解复杂查询
- [ ] 子任务执行机制正常
- [ ] 结果合并逻辑正确
- [ ] 测试通过率 100%

---

### 阶段 6：跨领域 Agent（1 周）

#### 目标
实现概念关联与多视角分析

#### 任务清单

**6.1 跨领域 Prompt 模板**
- [ ] 设计跨领域 Prompt 模板
- [ ] 设计概念关联模板

**6.2 跨领域 Agent 实现**
- [ ] 实现 `CrossDomainAgent` 类
  - 概念提取逻辑
  - 关联发现逻辑
  - 多视角分析逻辑
- [ ] 实现概念关联算法

**6.3 补充检索机制**
- [ ] 实现相关概念检索
- [ ] 实现多视角检索
- [ ] 实现结果整合

**6.4 Orchestrator 集成**
- [ ] 集成跨领域 Agent
- [ ] 实现跨领域分析流程
- [ ] 实现补充检索流程

**6.5 测试**
- [ ] 编写跨领域 Agent 单元测试
- [ ] 编写概念关联测试
- [ ] 验证多视角分析效果

#### 交付物
- CrossDomainAgent 实现
- 跨领域关联能力

#### 验收标准
- [ ] 跨领域 Agent 可以正确提取概念
- [ ] 概念关联机制有效
- [ ] 多视角分析功能正常
- [ ] 测试通过率 100%

---

### 阶段 7：服务层适配（1 周）

#### 目标
更新服务层，集成 AgenticQueryEngine

#### 任务清单

**7.1 RAGService 适配**
- [ ] 更新导入路径
- [ ] 替换 ModularQueryEngine 为 AgenticQueryEngine
- [ ] 保持 API 兼容性
- [ ] 更新初始化逻辑

**7.2 ChatManager 适配**
- [ ] 更新导入路径
- [ ] 替换 ModularQueryEngine 为 AgenticQueryEngine
- [ ] 保持 API 兼容性
- [ ] 更新初始化逻辑

**7.3 初始化系统适配**
- [ ] 更新 `registry.py` 导入路径
- [ ] 更新检查逻辑

**7.4 测试更新**
- [ ] 更新 RAGService 测试
- [ ] 更新 ChatManager 测试
- [ ] 更新集成测试

#### 交付物
- RAGService 适配完成
- ChatManager 适配完成
- 初始化系统适配完成

#### 验收标准
- [ ] RAGService 可以正常使用
- [ ] ChatManager 可以正常使用
- [ ] 所有测试通过
- [ ] API 兼容性验证通过

---

### 阶段 8：测试与优化（1 周）

#### 目标
完整测试覆盖与性能优化

#### 任务清单

**8.1 测试用例编写**
- [ ] 编写 Agentic Query Engine 集成测试
- [ ] 编写多 Agent 协作测试
- [ ] 编写成本控制测试
- [ ] 编写错误处理测试
- [ ] 编写性能测试
- [ ] 编写流式输出测试
- [ ] 编写并发控制测试

**8.1.1 测试数据准备**
- [ ] 准备测试数据集（简单查询、复杂查询、跨领域查询）
- [ ] 准备 Mock 数据（Mock LLM 响应、Mock 检索结果）
- [ ] 准备测试环境配置
- [ ] 实现测试数据生成工具

**8.2 测试用例更新**
- [ ] 更新现有集成测试
- [ ] 更新现有单元测试
- [ ] 更新 E2E 测试

**8.3 性能优化与基准测试**
- [ ] 分析性能瓶颈
- [ ] 优化 LLM 调用次数
- [ ] 优化工具调用效率
- [ ] 优化结果合并逻辑
- [ ] 性能基准测试
  - 与现有 ModularQueryEngine 性能对比
  - 测试指标：响应时间、LLM 调用次数、内存使用
  - 建立性能基准线
  - 记录性能优化前后对比

**8.4 错误处理与降级策略**
- [ ] 完善错误处理机制
  - Agent 执行失败处理
  - 工具调用失败处理（重试机制，最多3次）
  - LLM 调用失败处理（重试机制，最多2次）
  - 超时处理（触发降级策略）
- [ ] 实现降级策略
  - 一级降级：Agent 失败 → 回退到简单检索（vector_search）
  - 二级降级：检索失败 → 使用纯 LLM 生成（无检索）
  - 三级降级：LLM 失败 → 返回错误信息
- [ ] 实现超时处理
  - 超时检测（120秒）
  - 超时后立即停止，返回已收集结果
  - 记录超时原因和已执行步骤

**8.5 文档完善**
- [ ] 编写架构文档
- [ ] 编写使用文档
- [ ] 编写 API 文档
- [ ] 编写测试文档

#### 交付物
- 完整测试覆盖
- 性能优化报告
- 完整文档

#### 验收标准
- [ ] 测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 性能满足要求
- [ ] 文档完整准确

---

## 4. 代码规范约束

### 4.1 文件行数限制

**⚠️ 强制要求：单个代码文件必须 ≤ 300 行**

- **检查时机**：创建新文件时、修改现有文件后
- **执行方式**：
  1. 如果文件超过 300 行，**必须立即拆分**
  2. 拆分前与用户讨论职责划分方案
  3. 拆分后每个文件必须 ≤ 300 行
- **禁止行为**：❌ 不允许以"功能复杂"、"暂时无法拆分"等理由超过 300 行

### 4.2 类型提示要求

**所有函数、方法、类声明必须补全类型提示**

- 缺值返回使用 `-> None`
- 公共 API（类、函数、模块）必须提供完整 docstring（参数、返回值、异常）
- 使用 `typing` 模块提供类型注解

### 4.3 日志规范

**业务代码统一通过 `backend.infrastructure.logger.get_logger` 获取 logger，禁止使用 `print`**

- 测试示例代码除外
- 错误路径必须使用 `logger.error` 或 `logger.exception`
- 关键操作使用 `logger.info`
- 调试信息使用 `logger.debug`

### 4.4 代码结构顺序

1. 模块 docstring
2. 导入（标准库/第三方/本地）
3. 常量
4. 类
5. 函数

### 4.5 验收检查

每个阶段完成后必须检查：
- [ ] 所有文件 ≤ 300 行
- [ ] 所有函数、方法、类有类型提示
- [ ] 公共 API 有完整 docstring
- [ ] 日志使用规范（无 `print`，使用 `logger`）

---

## 5. Agent 间通信协议

### 5.1 数据传递格式

#### Agent 输入格式
```python
AgentInput = {
    "query": str,                    # 原始查询
    "understanding": Dict[str, Any],  # 查询理解结果（来自 QueryProcessor）
    "context": Dict[str, Any],       # 上下文信息（可选）
    "previous_results": List[Dict], # 之前 Agent 的结果（可选）
}
```

#### Agent 输出格式
```python
AgentOutput = {
    "result": Any,                   # Agent 执行结果
    "metadata": {
        "agent_name": str,           # Agent 名称
        "execution_time": float,     # 执行时间（秒）
        "llm_calls": int,            # LLM 调用次数
        "tools_used": List[str],     # 使用的工具列表
        "confidence": float,         # 置信度（0-1）
    },
    "next_agents": List[str],        # 建议的下一个 Agent（可选）
}
```

### 5.2 状态管理

- **Agent 状态**：每个 Agent 维护自己的状态（通过实例变量）
- **共享状态**：通过 Orchestrator 传递，不直接共享
- **状态持久化**：查询执行过程中的状态不持久化（每次查询独立）

### 5.3 通信流程

```
Orchestrator
    ↓ (传递 AgentInput)
Agent A
    ↓ (返回 AgentOutput)
Orchestrator
    ↓ (处理结果，决定下一步)
Agent B
    ↓ (返回 AgentOutput)
...
```

---

## 6. 流式输出支持

### 6.1 流式输出事件类型

| 事件类型 | 说明 | 数据格式 |
|---------|------|---------|
| `token` | 流式 token | `{'type': 'token', 'data': str}` |
| `sources` | 引用来源 | `{'type': 'sources', 'data': List[Dict]}` |
| `reasoning` | 推理链内容 | `{'type': 'reasoning', 'data': str}` |
| `done` | 完成事件 | `{'type': 'done', 'data': Dict}` |
| `error` | 错误事件 | `{'type': 'error', 'data': {'message': str}}` |

### 6.2 流式输出实现策略

1. **生成阶段流式**：GenerationAgent 使用 LLM 流式 API
2. **Agent 执行流式**：每个 Agent 执行过程中可以 yield 中间结果
3. **成本控制协调**：流式过程中持续检查超时和调用次数

### 6.3 流式输出与成本控制

- 流式输出过程中，每个 token 到达时检查：
  - 是否超时（120秒）
  - LLM 调用次数是否超限（50次）
- 如果超限，立即停止流式输出，返回已生成内容

---

## 7. 错误处理与降级策略

### 7.1 错误分类

| 错误类型 | 处理方式 | 降级策略 |
|---------|---------|---------|
| **Agent 执行失败** | 记录错误，尝试下一个 Agent | 一级降级：回退到简单检索 |
| **工具调用失败** | 重试（最多3次） | 如果重试失败，跳过该工具 |
| **LLM 调用失败** | 重试（最多2次） | 二级降级：使用纯 LLM（无检索） |
| **超时** | 立即停止 | 返回已收集结果 |
| **成本超限** | 立即停止 | 返回已收集结果 |

### 7.2 降级策略层级

```
正常流程：多 Agent 协作
    ↓ (失败)
一级降级：简单检索（vector_search）
    ↓ (失败)
二级降级：纯 LLM 生成（无检索）
    ↓ (失败)
三级降级：返回错误信息
```

### 7.3 错误恢复机制

- **自动重试**：工具调用失败自动重试（最多3次）
- **策略切换**：检索策略失败，自动切换到备用策略
- **部分结果返回**：即使部分 Agent 失败，也返回已成功的结果

---

## 8. Agent 工程化四大支柱

### 8.1 架构概览

现代 Agent 工程化落地的四大支柱：

```
┌─────────────────────────────────────────────────────────┐
│  1. Prompt引擎：智能体的"灵魂"与"剧本"                    │
│     - 角色与指令定义                                     │
│     - 思维链模板                                         │
│     - 上下文填充机制                                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  2. MCP（模型上下文协议）：智能体的"标准武器库"           │
│     - 标准化工具接口                                     │
│     - 工具发现与调用                                     │
│     - 框架解耦                                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  3. 会话管理：智能体的"记忆"与"状态"                     │
│     - 短期记忆（对话历史）                               │
│     - 长期记忆（向量数据库）                             │
│     - 会话状态（工作流进度）                             │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  4. 可观测性：智能体的"仪表盘"与"黑匣子"                 │
│     - 链路追踪                                           │
│     - 评估与测试                                         │
│     - 监控与告警                                         │
└─────────────────────────────────────────────────────────┘
```

### 8.2 四大支柱在本架构中的体现

#### 8.2.1 Prompt 引擎

**实现方式**：
- **Prompt 模板文件化管理**：存储在 `backend/business/rag_engine/agentic/prompts/templates/`
- **角色与指令**：每个 Agent 有独立的 Prompt 模板，定义其角色、目标和约束
- **思维链模板**：使用 ReAct 模式（思考-行动-观察循环）
- **上下文填充**：Orchestrator 自动将查询、历史结果、工具输出等填入模板

**当前实现**：
- ✅ Prompt 模板文件化（类似 `query_rewrite_template.txt`）
- ✅ 支持运行时更新模板
- ✅ 提供默认模板作为后备
- ⚠️ 需要增强：更系统的 Prompt 版本管理和 A/B 测试

**计划增强**：
- [ ] 实现 Prompt 版本管理
- [ ] 支持 Prompt A/B 测试
- [ ] 集成 Prompt 评估机制

#### 8.2.2 MCP（模型上下文协议）

**当前状态**：
- ⚠️ **未实现**：当前工具封装为 LlamaIndex Tool，未采用 MCP 标准

**计划实现**：
- [ ] **阶段 1**：将现有工具封装为 LlamaIndex Tool（兼容现有框架）
- [ ] **阶段 2**：引入 MCP 支持，将工具改造成 MCP 服务器
- [ ] **阶段 3**：使用 MCP 客户端发现和调用工具

**MCP 优势**：
- ✅ 工具标准化，框架解耦
- ✅ 易于集成社区工具和公司内部工具
- ✅ 支持工具的动态发现和调用

**实施路径**：
1. 先完成 LlamaIndex Tool 封装（阶段 2）
2. 后续引入 MCP 支持（阶段 2 或后续扩展）

#### 8.2.3 会话管理

**当前实现**：
- ✅ **短期记忆**：ChatManager 管理对话历史
- ✅ **会话状态**：Orchestrator 管理执行状态（当前阶段、已执行步骤）
- ⚠️ **长期记忆**：未实现向量化长期记忆

**计划增强**：
- [ ] 实现向量化长期记忆（存储用户偏好、历史结论）
- [ ] 增强会话状态管理（复杂工作流状态）
- [ ] 集成 LangGraph 等编排框架（如需要）

**架构设计**：
```
会话管理
    ├─ 短期记忆（ChatManager）
    │   └─ 对话历史、上下文
    ├─ 会话状态（Orchestrator）
    │   └─ 执行状态、中间结果
    └─ 长期记忆（向量数据库，待实现）
        └─ 用户偏好、历史结论
```

#### 8.2.4 可观测性

**当前实现**：
- ✅ **链路追踪**：ObserverManager 集成 Phoenix、LlamaDebug
- ✅ **日志记录**：结构化日志记录关键步骤
- ⚠️ **评估与测试**：未实现自动化评估
- ⚠️ **监控与告警**：未实现监控大盘和告警

**计划增强**：
- [ ] 集成 LangSmith 或类似工具（链路追踪增强）
- [ ] 实现自动化评估流水线（答案相关性、毒性、成本等）
- [ ] 建立监控大盘（延迟、成本、错误率）
- [ ] 设置告警机制（阈值告警）

**当前架构**：
```
可观测性
    ├─ ObserverManager（协调器）
    │   ├─ PhoenixObserver（追踪可视化）
    │   ├─ LlamaDebugObserver（调试日志）
    │   └─ （预留：RAGAS、Metrics）
    ├─ 日志系统（结构化日志）
    └─ 追踪信息（执行路径记录）
```

### 8.3 技术栈选择

#### 8.3.1 当前技术栈

**当前选择**：
- **智能体框架**：LlamaIndex ReActAgent
- **编排**：AgentOrchestrator（自定义）
- **可观测性**：ObserverManager + Phoenix
- **工具协议**：LlamaIndex Tool（计划引入 MCP）
- **向量数据库**：Chroma（已使用）

**选择理由**：
- ✅ 使用 LlamaIndex：项目已基于 LlamaIndex，保持一致性
- ✅ 自定义 Orchestrator：更灵活，符合 RAG 特定需求
- ✅ 复用现有 Observer：已有 ObserverManager，平滑迁移
- ⚠️ 计划引入 MCP：工具标准化，提升可扩展性

#### 8.3.2 业界推荐技术栈（参考）

基于业界实践的前沿技术栈选型：

| 层次 | 推荐选项 | 说明 | 适用场景 |
|------|---------|------|---------|
| **框架/编排层** | **LangChain / LangGraph** | 生态成熟，对复杂状态流（规划、反思循环）支持最好 | 复杂工作流、多 Agent 协作 |
| | **Dify** | 国内流行，开箱即用，可视化好 | 快速构建、可视化需求 |
| | **LlamaIndex** | 专注 RAG，与向量数据库集成好 | RAG 专用场景（当前选择） |
| **向量数据库/知识层** | **Milvus** | 企业级大规模数据 | 大规模生产环境 |
| | **Chroma** | 轻量，适合原型 | 中小规模、开发测试（当前使用） |
| | **Pinecone** | 托管服务，易用 | 云原生场景 |
| **工具协议层** | **MCP** | 未来工具集成的开放标准 | 工具标准化、框架解耦（计划引入） |
| **可观测性层** | **LangSmith** | 链路追踪、评估、监控 | 生产环境必备（推荐） |
| | **Langfuse** | 开源替代方案 | 成本敏感场景 |
| | **Phoenix** | 开源追踪工具 | 开发调试（当前使用） |

#### 8.3.3 技术栈演进路径

**阶段 1（当前）**：
- LlamaIndex ReActAgent + 自定义 Orchestrator + Phoenix
- 快速实现核心功能，保持项目一致性

**阶段 2（中期优化）**：
- 引入 MCP 支持（工具标准化）
- 增强可观测性（考虑 LangSmith 集成）
- 保持 LlamaIndex 框架

**阶段 3（长期演进）**：
- 评估 LangGraph 等编排框架（如需要复杂工作流）
- 根据规模考虑 Milvus 等企业级向量数据库
- 持续优化可观测性和评估体系

#### 8.3.4 与业界趋势对比

| 对比维度 | **本方案核心** | **当前业界前沿趋势** | **一致性** |
|---------|--------------|-------------------|----------|
| **架构演进** | 从"静态流程"到"动态智能体"，规划 Agent 作为大脑 | RAG 转变为 Agent 生态子模块，强调动态、可编排 | ✅ 高度一致 |
| **检索模式** | 检索 Agent 化，可规划策略、调用多种工具 | 递归/迭代检索，多跳推理，混合搜索 | ✅ 高度一致 |
| **生成与反思** | 生成后引入反思环节，评估质量并可能触发重试 | 反思是 Agentic RAG 标志性能力，减少幻觉 | ✅ 高度一致 |
| **技术栈** | Prompt、MCP、编排、可观测性 | LangChain/LangGraph、MCP、LangSmith | ✅ 高度一致 |

**结论**：本方案与业界前沿趋势高度一致，属于**引领方向的"前沿主流"**。

### 8.4 实施优先级

| 支柱 | 当前状态 | 优先级 | 实施阶段 |
|------|---------|--------|---------|
| **Prompt 引擎** | ✅ 基础实现 | 🔴 高 | 阶段 3（核心 Agent） |
| **MCP** | ❌ 未实现 | 🟡 中 | 阶段 2（工具封装）或后续扩展 |
| **会话管理** | ✅ 基础实现 | 🟡 中 | 阶段 7（服务层适配）或后续扩展 |
| **可观测性** | ✅ 基础实现 | 🔴 高 | 阶段 8（测试与优化） |

---

## 9. 性能监控与可观测性（详细）

### 9.1 监控指标

| 指标 | 说明 | 收集方式 |
|------|------|---------|
| **LLM 调用次数** | 每次查询的 LLM 调用总数 | CostController 统计 |
| **执行时间** | 查询总执行时间 | Orchestrator 记录 |
| **Agent 执行时间** | 每个 Agent 的执行时间 | Agent 记录 |
| **工具调用次数** | 每个工具的调用次数 | Tool 包装器统计 |
| **错误率** | Agent 执行失败率 | Orchestrator 统计 |
| **降级触发率** | 降级策略触发频率 | Orchestrator 统计 |

### 9.2 可观测性集成

- **复用现有 Observer 系统**：集成 `ObserverManager`
- **日志记录**：关键步骤记录日志（Agent 执行、工具调用、错误）
- **追踪信息**：记录完整的执行路径（哪些 Agent 被执行，使用了哪些工具）

### 9.3 性能分析

- **性能瓶颈识别**：分析哪个 Agent 或工具最耗时
- **成本分析**：分析 LLM 调用分布（哪个 Agent 调用最多）
- **优化建议**：基于监控数据提供优化建议

### 9.4 可观测性增强计划

**短期（阶段 8）**：
- [ ] 增强链路追踪（记录每个 Agent 的输入输出）
- [ ] 实现基础评估指标（答案相关性、成本）
- [ ] 建立监控大盘（延迟、成本、错误率）

**中期（后续扩展）**：
- [ ] 集成 LangSmith 或类似工具
- [ ] 实现自动化评估流水线
- [ ] 设置告警机制（阈值告警）

---

## 10. 回滚策略

### 9.1 回滚机制

**保留 ModularQueryEngine 作为降级选项**

- 在 `backend/business/rag_engine/core/` 目录保留 `ModularQueryEngine` 实现
- 通过配置或环境变量控制使用哪个引擎
- 如果 AgenticQueryEngine 出现问题，可以快速切换回 ModularQueryEngine

### 9.2 回滚触发条件

- AgenticQueryEngine 初始化失败
- AgenticQueryEngine 执行错误率过高（>10%）
- 性能严重下降（响应时间 >60秒）
- 用户手动触发回滚

### 9.3 回滚实现

```python
# 在 RAGService 中实现回滚逻辑
if config.USE_AGENTIC_RAG and agentic_engine_available:
    query_engine = AgenticQueryEngine(...)
else:
    query_engine = ModularQueryEngine(...)  # 降级选项
```

---

## 11. Prompt 模板管理

### 10.1 模板存储方式

- **文件化存储**：Prompt 模板存储在 `backend/business/rag_engine/agentic/prompts/templates/` 目录
- **文件命名**：`{agent_name}_prompt.txt`（如 `retrieval_agent_prompt.txt`）
- **默认模板**：代码中提供默认模板作为后备

### 10.2 模板加载机制

- **优先级**：文件模板 > 默认模板
- **运行时更新**：支持运行时重新加载模板（无需重启）
- **版本管理**：记录模板版本，便于追踪变更

### 10.3 模板更新策略

- **开发阶段**：直接修改模板文件
- **生产环境**：通过配置或 API 更新模板
- **版本控制**：模板文件纳入 Git 版本控制

---

## 12. 文件清单

### 11.1 新增文件（39 个）

#### 核心 Agent 文件（10 个）
```
backend/business/rag_engine/agentic/
├── __init__.py
├── base_agent.py
├── react_agent.py
├── query_planning_agent.py      # 新增：查询规划 Agent（合并查询分析和路由）
├── retrieval_agent.py
├── postprocessing_agent.py      # 新增：后处理 Agent
├── generation_agent.py
├── reflection_agent.py
├── task_decomposition_agent.py
├── cross_domain_agent.py
├── fallback_agent.py            # 新增：兜底 Agent
└── orchestrator.py
```

#### Prompt 模板文件（8 个）
```
backend/business/rag_engine/agentic/prompts/
├── __init__.py
├── query_planning_prompt.py     # 新增：查询规划 Prompt（合并查询分析和路由）
├── retrieval_prompt.py
├── postprocessing_prompt.py     # 新增：后处理 Prompt
├── generation_prompt.py
├── reflection_prompt.py
├── task_decomposition_prompt.py
├── cross_domain_prompt.py
└── fallback_prompt.py           # 新增：兜底 Prompt
```

#### 工具文件（6 个）
```
backend/business/rag_engine/agentic/tools/
├── __init__.py
├── query_planning_tools.py      # 新增：查询规划工具（合并查询分析和路由工具）
├── retrieval_tools.py
├── postprocessing_tools.py
├── generation_tools.py
├── reflection_tools.py          # 新增：反思工具
├── task_decomposition_tools.py  # 新增：任务分解工具
├── cross_domain_tools.py        # 新增：跨领域工具
└── fallback_tools.py            # 新增：兜底工具
```

#### 工具函数文件（3 个）
```
backend/business/rag_engine/agentic/utils/
├── __init__.py
├── cost_control.py
└── result_merger.py
```

#### 主入口文件（1 个）
```
backend/business/rag_engine/agentic/engine.py
```

#### 测试文件（13 个）
```
tests/integration/
├── test_agentic_query_engine.py
├── test_agentic_agents.py
└── test_agentic_orchestrator.py

tests/unit/agentic/
├── test_query_planning_agent.py     # 新增：查询规划 Agent（合并查询分析和路由）
├── test_retrieval_agent.py
├── test_postprocessing_agent.py     # 新增
├── test_generation_agent.py
├── test_reflection_agent.py
├── test_task_decomposition_agent.py # 新增
├── test_cross_domain_agent.py       # 新增
├── test_fallback_agent.py           # 新增
├── test_orchestrator.py
├── test_tools.py
└── test_cost_control.py
```

### 11.2 修改文件（11 个）

| 文件路径 | 改动类型 | 改动行数估算 |
|---------|---------|------------|
| `backend/business/rag_engine/core/engine.py` | 🔴 完全替换 | ~700 行 |
| `backend/business/rag_api/rag_service.py` | 🔄 修改 | ~20 行 |
| `backend/business/chat/manager.py` | 🔄 修改 | ~10 行 |
| `backend/infrastructure/initialization/registry.py` | 🔄 修改 | ~5 行 |
| `application.yml` | ➕ 新增配置 | ~30 行 |
| `backend/infrastructure/config/settings.py` | ➕ 新增属性 | ~20 行 |
| `tests/integration/test_modular_query_engine.py` | 🔄 重命名+修改 | ~100 行 |
| `tests/integration/test_rag_service_integration.py` | 🔄 修改 | ~50 行 |
| `tests/integration/test_auto_routing_integration.py` | 🔄 修改 | ~30 行 |
| `tests/unit/test_rag_service.py` | 🔄 修改 | ~30 行 |
| `tests/unit/test_query_engine.py` | 🔄 修改 | ~30 行 |

---

## 13. 风险评估与应对

### 5.1 高风险项

| 风险项 | 风险描述 | 影响 | 概率 | 应对措施 |
|-------|---------|------|------|---------|
| **核心引擎替换** | ModularQueryEngine 完全替换，影响所有查询功能 | 🔴 高 | 🟡 中 | 1. 保持 API 接口不变<br>2. 分阶段实施<br>3. 充分测试<br>4. 保留降级选项 |
| **性能影响** | Agent 架构可能增加延迟和成本 | 🟡 中 | 🟡 中 | 1. 成本控制机制<br>2. 超时保护<br>3. 性能监控<br>4. 优化 LLM 调用 |

### 5.2 中等风险项

| 风险项 | 风险描述 | 影响 | 概率 | 应对措施 |
|-------|---------|------|------|---------|
| **测试覆盖** | 大量测试用例需要更新 | 🟡 中 | 🟢 低 | 1. 保持 API 兼容性<br>2. 复用现有测试逻辑<br>3. 新增专项测试 |
| **服务层适配** | RAGService、ChatManager 需要适配 | 🟡 中 | 🟢 低 | 1. 保持接口不变<br>2. 最小化改动 |

### 5.3 低风险项

| 风险项 | 风险描述 | 影响 | 概率 | 应对措施 |
|-------|---------|------|------|---------|
| **配置新增** | 新增配置项 | 🟢 低 | 🟢 低 | 1. 默认值设置<br>2. 向后兼容 |
| **前端影响** | 前端无需改动 | 🟢 低 | 🟢 低 | 1. 保持 RAGService 接口不变 |

---

## 14. 测试策略

### 6.1 测试层级

#### 单元测试（Unit Tests）
- **目标**：测试单个 Agent、工具、工具函数
- **覆盖率**：≥ 80%
- **重点**：Agent 逻辑、工具调用、成本控制

#### 集成测试（Integration Tests）
- **目标**：测试 Agent 间协作、Orchestrator 流程
- **覆盖率**：≥ 70%
- **重点**：多 Agent 协作、完整查询流程

#### E2E 测试（End-to-End Tests）
- **目标**：测试完整用户流程
- **覆盖率**：≥ 50%
- **重点**：RAGService 集成、ChatManager 集成

### 6.2 测试重点

1. **API 兼容性测试**
   - 验证 AgenticQueryEngine API 与 ModularQueryEngine 兼容
   - 验证返回格式一致

2. **功能测试**
   - 验证每个 Agent 功能正常
   - 验证工具调用正确
   - 验证成本控制有效

3. **性能测试**
   - 验证响应时间合理
   - 验证 LLM 调用次数可控
   - 验证超时机制有效

4. **错误处理测试**
   - 验证错误处理机制
   - 验证降级策略
   - 验证异常恢复

---

## 15. 验收标准

### 7.1 功能验收

- [ ] 所有 Agent 功能正常
- [ ] 工具调用正确
- [ ] 多 Agent 协作正常
- [ ] 成本控制有效
- [ ] 超时机制有效

### 7.2 质量验收

- [ ] API 兼容性验证通过
- [ ] 测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档完整准确

### 7.3 性能验收

- [ ] 平均响应时间 ≤ 30 秒（复杂查询）
- [ ] LLM 调用次数 ≤ 50 次/查询
- [ ] 超时机制正常工作
- [ ] 内存使用合理

### 7.4 兼容性验收

- [ ] RAGService 接口兼容
- [ ] ChatManager 接口兼容
- [ ] 前端无需改动
- [ ] 配置向后兼容

---

## 16. 时间估算

### 8.1 阶段时间估算

| 阶段 | 任务 | 时间估算 | 累计时间 |
|------|------|---------|---------|
| 阶段 1 | 基础架构搭建 | 1 周 | 1 周 |
| 阶段 2 | 工具封装 | 1 周 | 2 周 |
| 阶段 3 | 核心 Agent 实现 | 1.5 周 | 3.5 周 |
| 阶段 4 | 反思 Agent | 1 周 | 4.5 周 |
| 阶段 5 | 任务分解 Agent | 1 周 | 5.5 周 |
| 阶段 6 | 跨领域 Agent | 1 周 | 6.5 周 |
| 阶段 7 | 服务层适配 | 1 周 | 7.5 周 |
| 阶段 8 | 测试与优化 | 1 周 | 8.5 周 |

**总计：8.5 周（约 2 个月）**

### 8.2 关键里程碑

| 里程碑 | 时间点 | 交付物 |
|-------|--------|--------|
| M1：基础架构完成 | 第 1 周末 | Agent 基类、Orchestrator 框架 |
| M2：工具封装完成 | 第 2 周末 | 20 个工具实现（合并查询规划和路由工具） |
| M3：核心 Agent 完成 | 第 3.5 周末 | QueryPlanningAgent、RetrievalAgent、PostProcessingAgent、GenerationAgent、FallbackAgent |
| M4：完整 Agent 完成 | 第 6.5 周末 | 所有 Agent 实现 |
| M5：服务适配完成 | 第 7.5 周末 | RAGService、ChatManager 适配 |
| M6：项目完成 | 第 8.5 周末 | 完整系统、测试、文档 |

---

## 17. 依赖关系

### 9.1 技术依赖

| 依赖项 | 版本要求 | 状态 |
|-------|---------|------|
| LlamaIndex | ≥ 0.9.0 | ✅ 已安装 |
| DeepSeek API | 最新 | ✅ 已配置 |
| Python | ≥ 3.9 | ✅ 已满足 |

### 9.2 模块依赖

```
AgenticQueryEngine
    ├─ AgentOrchestrator
    │   ├─ QueryPlanningAgent
    │   │   └─ Query Planning Tools (4种：意图分析、改写、策略评估、策略选择)
    │   ├─ RetrievalAgent
    │   │   └─ Retrieval Tools (7种)
    │   ├─ PostProcessingAgent
    │   │   └─ Postprocessing Tools (2种)
    │   ├─ GenerationAgent
    │   │   └─ Generation Tools (1种)
    │   ├─ ReflectionAgent
    │   │   └─ Reflection Tools (2种)
    │   ├─ TaskDecompositionAgent
    │   │   └─ Task Decomposition Tools (2种)
    │   ├─ CrossDomainAgent
    │   │   └─ Cross Domain Tools (2种)
    │   └─ FallbackAgent
    │       └─ Fallback Tools (2种)
    └─ CostController
```

### 9.3 服务依赖

```
RAGService
    └─ AgenticQueryEngine
        └─ AgentOrchestrator

ChatManager
    └─ AgenticQueryEngine
        └─ AgentOrchestrator
```

---

## 18. 配置设计

### 10.1 新增配置项

```yaml
# application.yml
agentic_rag:
  # 注意：Agentic RAG 默认开启，无需 enabled 配置
  max_llm_calls: 50               # 单个查询最大 LLM 调用次数
  timeout_seconds: 120            # 超时时间（秒）
  
  reflection:
    enabled: true                 # 是否启用反思机制
    adaptive_depth: true          # 是否自适应反思深度
    min_depth: 1                  # 最小反思深度
    max_depth: 3                  # 最大反思深度
    quality_threshold: 0.8        # 质量阈值（≥0.8 不重试）
  
  agents:
    query_planning:
      enabled: true                # 是否启用查询规划 Agent
      max_strategies: 3            # 最多尝试的策略数
    
    retrieval:
      enabled: true               # 是否启用检索 Agent
    
    postprocessing:
      enabled: true               # 是否启用后处理 Agent
    
    generation:
      enabled: true                # 是否启用生成 Agent
    
    reflection:
      enabled: true                # 是否启用反思 Agent
    
    task_decomposition:
      enabled: true                # 是否启用任务分解 Agent
      complexity_threshold: 0.7    # 复杂度阈值（≥0.7 触发分解）
    
    cross_domain:
      enabled: true                # 是否启用跨领域 Agent
    
    fallback:
      enabled: true                # 是否启用兜底 Agent
```

### 10.2 配置加载实现

```python
# backend/infrastructure/config/settings.py
_PROPERTY_MAPPING = {
    # ... 现有配置 ...
    
    # Agentic RAG 配置（注意：无需 AGENTIC_RAG_ENABLED，默认开启）
    'AGENTIC_RAG_MAX_LLM_CALLS': lambda m: m.agentic_rag.max_llm_calls,
    'AGENTIC_RAG_TIMEOUT_SECONDS': lambda m: m.agentic_rag.timeout_seconds,
    'AGENTIC_RAG_REFLECTION_ENABLED': lambda m: m.agentic_rag.reflection.enabled,
    'AGENTIC_RAG_REFLECTION_ADAPTIVE_DEPTH': lambda m: m.agentic_rag.reflection.adaptive_depth,
    'AGENTIC_RAG_REFLECTION_MIN_DEPTH': lambda m: m.agentic_rag.reflection.min_depth,
    'AGENTIC_RAG_REFLECTION_MAX_DEPTH': lambda m: m.agentic_rag.reflection.max_depth,
    'AGENTIC_RAG_REFLECTION_QUALITY_THRESHOLD': lambda m: m.agentic_rag.reflection.quality_threshold,
    'AGENTIC_RAG_AGENTS_QUERY_PLANNING_ENABLED': lambda m: m.agentic_rag.agents.query_planning.enabled,
    'AGENTIC_RAG_AGENTS_QUERY_PLANNING_MAX_STRATEGIES': lambda m: m.agentic_rag.agents.query_planning.max_strategies,
    'AGENTIC_RAG_AGENTS_RETRIEVAL_ENABLED': lambda m: m.agentic_rag.agents.retrieval.enabled,
    'AGENTIC_RAG_AGENTS_POSTPROCESSING_ENABLED': lambda m: m.agentic_rag.agents.postprocessing.enabled,
    'AGENTIC_RAG_AGENTS_GENERATION_ENABLED': lambda m: m.agentic_rag.agents.generation.enabled,
    'AGENTIC_RAG_AGENTS_REFLECTION_ENABLED': lambda m: m.agentic_rag.agents.reflection.enabled,
    'AGENTIC_RAG_AGENTS_TASK_DECOMPOSITION_ENABLED': lambda m: m.agentic_rag.agents.task_decomposition.enabled,
    'AGENTIC_RAG_AGENTS_TASK_DECOMPOSITION_COMPLEXITY_THRESHOLD': lambda m: m.agentic_rag.agents.task_decomposition.complexity_threshold,
    'AGENTIC_RAG_AGENTS_CROSS_DOMAIN_ENABLED': lambda m: m.agentic_rag.agents.cross_domain.enabled,
    'AGENTIC_RAG_AGENTS_FALLBACK_ENABLED': lambda m: m.agentic_rag.agents.fallback.enabled,
}
```

### 10.3 实现说明

- **AgenticQueryEngine 将作为默认查询引擎**，直接替换 ModularQueryEngine
- **无需通过配置开关控制是否启用**，默认开启
- **各子 Agent**（query_planning、retrieval、postprocessing、generation、reflection、task_decomposition、cross_domain、fallback）可通过各自的 `enabled` 配置控制

---

## 19. 文档计划

### 11.1 技术文档

- [ ] 架构设计文档
- [ ] API 文档
- [ ] Agent 设计文档
- [ ] 工具使用文档
- [ ] Prompt 模板文档

### 11.2 用户文档

- [ ] 使用指南
- [ ] 配置说明
- [ ] 常见问题
- [ ] 最佳实践

### 11.3 开发文档

- [ ] 开发指南
- [ ] 测试指南
- [ ] 部署指南
- [ ] 故障排查

---

## 20. 后续扩展计划

### 12.1 短期扩展（3 个月内）

- [ ] 外部工具集成（计算器、API 调用）
- [ ] 知识图谱集成
- [ ] 流式输出优化
- [ ] 性能优化

### 12.2 长期扩展（6 个月以上）

- [ ] 多模态支持（图像、音频）
- [ ] 分布式 Agent 架构
- [ ] 自适应学习机制
- [ ] 用户反馈集成

---

## 21. 附录

### 13.1 术语表

| 术语 | 说明 |
|------|------|
| Agentic RAG | 基于 Agent 的检索增强生成系统 |
| ReAct Agent | 思考-行动-观察循环的 Agent |
| Orchestrator | 多 Agent 协调器 |
| Tool | Agent 可调用的工具（函数） |
| Prompt | 提示词模板 |

### 13.2 参考资源

- [LlamaIndex ReActAgent 文档](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/react_agent/)
- [LlamaIndex Tools 文档](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/tools/)
- [Agentic RAG 最佳实践](https://docs.llamaindex.ai/en/stable/examples/agent/agentic_rag/)

---

## 22. 审批与确认

### 14.1 计划审批

- [ ] 技术方案审核通过
- [ ] 时间计划确认
- [ ] 资源配置确认
- [ ] 风险评估确认

### 14.2 执行确认

- [ ] 开发环境准备就绪
- [ ] 依赖项安装完成
- [ ] 团队分工明确
- [ ] 开始执行

---

**文档状态**：✅ v2.3 已完成，待审核

**文档说明**：
- **v2.3 更新**：明确"规划-增强检索-反思生成"核心流程
  - 明确 Agentic RAG 核心思想：将检索-生成流程的各个环节赋予自主的规划、决策与反思能力
  - 明确核心流程：规划-增强检索-反思生成
  - 补充业界趋势对比：架构演进、检索模式、生成与反思、技术栈
  - 更新技术栈选择：补充业界推荐技术栈和演进路径
  - 明确定位：属于"前沿主流"方向，引领 RAG 技术演进
- **v2.2 更新**：补充 Agent 工程化四大支柱
  - 新增"Agent 工程化四大支柱"章节（第8章）
  - 明确四大支柱：Prompt 引擎、MCP、会话管理、可观测性
  - 分析当前架构与四大支柱的对应关系
  - 明确实施优先级和增强计划
  - 更新可观测性章节，补充 LangSmith 等最佳实践
- **v2.1 更新**：优化 Agent 架构设计
  - 合并 QueryPlanningAgent（合并 QueryAnalysisAgent + RoutingAgent）
  - 明确 Agent 分类：核心 Agent（5个）+ 增强 Agent（3个）
  - 明确 AgentOrchestrator 功能：流程协调、条件执行、成本控制、错误处理
  - 明确 Agent 调用顺序和决策流程
  - 工具集优化至 20 个工具（合并查询规划和路由工具）
  - Agent 总数优化至 8 个（核心 5 个 + 增强 3 个）
- **v2.0 更新**：将整个 RAG 链路纳入 Agentic RAG 架构
  - 新增 PostProcessingAgent（替代 PostProcessor）
  - 新增 FallbackAgent（处理兜底逻辑）
  - 架构理念：Agentic RAG 作为底层架构，统一组织所有 RAG 功能
- 代码规范约束、错误处理、性能监控、回滚策略等关键内容已补充
- 流式输出、Prompt 模板管理、Agent 通信协议等实施细节已明确

**下一步**：根据此计划书进行详细计划和执行细节商榷

